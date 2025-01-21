mod z_filter;

use chrono::Duration;

use logfile_parser::parsing_structures::event_sourced::{EventSource, EventSourceLog};
use std::env;
use std::io::Error;
use std::path::Path;
use std::process::exit;

use crate::z_filter::config::Config;
use crate::z_filter::lru_manager::LruManager;
use crate::z_filter::z_anon::{ZFilter, ZFilteringMethod};

///executable for testing greater logfiles

async fn kickoff(log: EventSourceLog, config: Config, filter_method: ZFilteringMethod) -> Result<Vec<EventSource>, Error> {
    match sourced_simulator::create_default_simulator(
        ZFilter::new(LruManager::from(config, filter_method.clone()), filter_method),
        log).await {
        Ok(simulator) => {
            Ok(simulator.run().await)
        }
        Err(e) => {
            Err(e)
        }
    }
}


fn help_parse(arg: Option<String>) -> u32 {
    if let Some(n_val) = arg {
        if let Ok(n_val) = n_val.parse::<u32>() {
            return n_val;
        } else {
            eprintln!("Please provide an integer");
            exit(1);
        }
    }
    0
}


fn preprocess_args(mut args: Vec<String>) -> (String, u32, Duration, ZFilteringMethod) {
    if args.len() != 5 {
        eprintln!("Error: wrong number of arguments");
        eprintln!("Usage: {} <file> <z-value> <delta t> <Filter_method: 0-classic (default), !=0 -improved>", args[0]);
        exit(1);
    }

    // Filtering Method
    // safe unwrap due to first if-clause
    let filter_method = match str::parse::<i32>(&args.pop().unwrap()) {
        Ok(value) => {
            if value == 0 {
                ZFilteringMethod::ClassicZfilter
            } else {
                ZFilteringMethod::ImprovedZfilter
            }
        }
        Err(_) => {
            ZFilteringMethod::ClassicZfilter
        }
    };


    let res = parse_duration(&args.pop().unwrap());
    if let Err(e) = res {
        eprintln!("Error: {}", e);
        std::process::exit(1);
    }
    let t: Duration = res.unwrap();


    let z = help_parse(args.pop());
    let path = args.pop().unwrap(); //safe unwrap

    (path, z, t, filter_method)
}

fn parse_duration(input: &str) -> Result<Duration, String> {
    if input == "inf"{
        return Ok(Duration::seconds(i64::MAX/1000));
    }
    let (value, unit) = input.split_at(input.len() - 1);
    let value: u64 = value.parse().map_err(|_| "Invalid Number".to_string())?;

    match unit {
        "s" => {
            Ok(Duration::seconds(value as i64))
        }
        "m" => {
            Ok(Duration::minutes(value as i64))
        }
        "h" => {
            Ok(Duration::hours(value as i64))
        }
        "d" => {
            Ok(Duration::days(value as i64))
        }
        _ => {
            Ok(Duration::seconds(value as i64))
        }
    }
}

fn excert_base_name(path: Box<&Path>) -> String {
    if let Some(file_stem) = path.file_stem() {
        if let Some(file_extension) = file_stem.to_str() {
            return file_extension.to_string();
        }
    }
    eprintln!("Error: Unrecognized file name");
    exit(1);
}


async fn sort_log(events: &mut Vec<EventSource>) {
    events.sort_by(|a, b| {
        match a.get_case_id().parse::<u32>().unwrap().cmp(&b.get_case_id().parse::<u32>().unwrap()) {
            std::cmp::Ordering::Equal => {
                a.get_timestamp().cmp(b.get_timestamp())
            }
            other => other,
        }
    });
}

async fn sort_by_timestamp(events: &mut Vec<EventSource>) {
    events.sort_by(|a, b| {
        a.get_timestamp().cmp(b.get_timestamp())
    })
}


#[tokio::main(flavor = "multi_thread")]
async fn main() {
    let args: Vec<String> = env::args().collect();
    let (path_file, z, t, filter_method) = preprocess_args(args);
    let mut result_folder = Path::new(&path_file);
    result_folder = result_folder.parent().unwrap();
    let result_folder = result_folder.join("results_filtering_".to_string() + match filter_method {
        ZFilteringMethod::ClassicZfilter => "classic",
        ZFilteringMethod::ImprovedZfilter => "improved",
    } + "/");
    println!("Z: {}, t: {}, Path: {:?}", z, t, path_file);
    let file_name = excert_base_name(Box::new(Path::new(&path_file)));
    eprintln!("{}", file_name);
    match EventSourceLog::read_from_csv(&path_file) {
        Ok(mut log) => {
            sort_by_timestamp(log.get_log_mut()).await;
            match kickoff(log, Config::new(z as usize, t), filter_method).await {
                Ok(mut log) => {
                    sort_log(&mut log).await;
                    let a = EventSourceLog::from(log);
                    let t_string= if t.eq(&Duration::seconds(i64::MAX/1000)){
                         String::from("PT0INF0S")
                    } else {
                        t.to_string()
                    };
                    if a.get_log().len() > 0{
                        a.print_to_csv(<&str>::try_from(result_folder.as_os_str()).unwrap(), &(file_name + "Z" + &z.to_string() + &t_string));
                    }
                }
                Err(e) => {
                    eprintln!("Error: {}", e);
                    exit(1);
                }
            }
        }
        Err(e) => eprintln!("Error: {}", e),
    }
}

