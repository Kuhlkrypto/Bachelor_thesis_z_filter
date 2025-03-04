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

/// Asynchronously runs the simulator with the given log and configuration.
///
/// # Arguments
/// * `log` - The event source log to be processed.
/// * `config` - The configuration parameters for filtering.
/// * `filter_method` - The filtering method to be used (Classic or Improved).
///
/// # Returns
/// * A result containing a vector of processed event sources or an IO error.
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

/// Parses an optional argument as a u32 integer. If parsing fails, the program exits with an error.
///
/// # Arguments
/// * `arg` - An optional string argument.
///
/// # Returns
/// * The parsed u32 value or exits if the value is invalid.
fn help_parse(arg: Option<String>) -> u32 {
    if let Some(n_val) = arg {
        if let Ok(n_val) = n_val.parse::<u32>() {
            return n_val;
        } else {
            eprintln!("Please provide a positive integer");
            exit(1);
        }
    }
    0
}

/// Processes command-line arguments and extracts necessary parameters.
///
/// # Arguments
/// * `args` - Vector of command-line arguments.
///
/// # Returns
/// * A tuple containing the file path, z-value, duration, and filtering method.
fn preprocess_args(mut args: Vec<String>) -> (String, u32, Duration, ZFilteringMethod) {
    if args.len() != 5 {
        eprintln!("Error: wrong number of arguments");
        eprintln!("Usage: {} <file> <z-value> <delta t> <Filter_method: 0-classic (default), !=0 -improved>", args[0]);
        exit(1);
    }
    // set filtering method
    let filter_method = match str::parse::<i32>(&args.pop().unwrap()) {
        Ok(value) => {
            if value == 0 {
                ZFilteringMethod::BasicZfilter
            } else {
                ZFilteringMethod::BalancedZfilter
            }
        }
        Err(_) => ZFilteringMethod::BasicZfilter,
    };

    // parse time parameter
    let res = parse_duration(&args.pop().unwrap());
    if let Err(e) = res {
        eprintln!("Error: {}", e);
        exit(1);
    }
    let t: Duration = res.unwrap();

    // parse z parameter
    let z = help_parse(args.pop());
    let path = args.pop().unwrap(); // Safe unwrap since length check is done earlier.

    (path, z, t, filter_method)
}

/// Parses a time duration string and converts it into a `Duration` object.
///
/// # Arguments
/// * `input` - A string representing duration (e.g., "5s", "10m").
///
/// # Returns
/// * A `Result` containing the parsed `Duration` or an error message.
fn parse_duration(input: &str) -> Result<Duration, String> {
    if input == "inf" {
        return Ok(Duration::seconds(i64::MAX / 1000));
    }
    let (value, unit) = input.split_at(input.len() - 1);
    let value: i64 = value.parse().map_err(|_| "Invalid Number".to_string())?;
    if value < 0 || value > i64::MAX / 1000 {
        return Err(format!("Duration out of Scope; Min: 0, Max: {}", i64::MAX / 1000));
    }
    match unit {
        "s" => Ok(Duration::seconds(value)),
        "m" => Ok(Duration::minutes(value)),
        "h" => Ok(Duration::hours(value)),
        "d" => Ok(Duration::days(value)),
        _ => Err("Invalid duration unit".to_string()),
    }
}

/// Extracts the base name of a file from its path.
///
/// # Arguments
/// * `path` - A reference to a `Path` object.
///
/// # Returns
/// * The extracted file name as a string.
fn excert_base_name(path: Box<&Path>) -> String {
    if let Some(file_stem) = path.file_stem() {
        if let Some(file_extension) = file_stem.to_str() {
            return file_extension.to_string();
        }
    }
    eprintln!("Error: Unrecognized file name");
    exit(1);
}

/// Sorts events by case ID and timestamp.
async fn sort_log(events: &mut Vec<EventSource>) {
    events.sort_by(|a, b| {
        match a.get_case_id().parse::<u32>().unwrap().cmp(&b.get_case_id().parse::<u32>().unwrap()) {
            std::cmp::Ordering::Equal => a.get_timestamp().cmp(b.get_timestamp()),
            other => other,
        }
    });
}

/// Sorts events by timestamp.
async fn sort_by_timestamp(events: &mut Vec<EventSource>) {
    events.sort_by(|a, b| a.get_timestamp().cmp(b.get_timestamp()));
}

/// Entry point for the filtering program.
#[tokio::main(flavor = "multi_thread")]
async fn main() {
    // collect arguments
    let args: Vec<String> = env::args().collect();

    // process arguments into a valid format
    let (path_file, z, t, filter_method) = preprocess_args(args);

    // set result folder to the parent of the to be filtered file
    let mut result_folder = Path::new(&path_file);
    result_folder = if result_folder.parent().is_none(){
        result_folder.parent().unwrap()
    } else {
        // if not possible use the same folder
        result_folder
    };
    // set filtering mode
    let result_folder = result_folder.join("results_filtering_".to_string() + match filter_method {
        ZFilteringMethod::BasicZfilter => "basic",
        ZFilteringMethod::BalancedZfilter => "balanced",
    } + "/");
    let file_name = excert_base_name(Box::new(Path::new(&path_file)));
    match EventSourceLog::read_from_csv(&path_file) {
        Ok(mut log) => {
            // sort by timestamp before filtering
            sort_by_timestamp(log.get_log_mut()).await;

            // start filtering algorithm and wait for return value
            match kickoff(log, Config::new(z as usize, t), filter_method).await {
                Ok(mut log) => {// OK: published event source instance from the filtering algorithms
                    // sort according to case and timestamp
                    sort_log(&mut log).await;
                    let a = EventSourceLog::from(log);
                    // generate time parameter for filename
                    let t_string = if t.eq(&Duration::seconds(i64::MAX / 1000)) {
                        String::from("PT0INF0S")
                    } else {
                        t.to_string()
                    };
                    // print results
                    if !a.get_log().is_empty() {
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
