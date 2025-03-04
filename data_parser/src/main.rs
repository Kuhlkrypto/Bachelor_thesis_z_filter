mod keywords;

use crate::keywords::bpi2017::Bpi2017;
use crate::keywords::hospital_log::HospitalLogKeyword;
use crate::keywords::road_traffic::RoadTrafficKeyedData;
use crate::keywords::sepsis_cases::SepsisCasesKeywords;
use std::{fs, env};
use std::path::{PathBuf};


fn join_with_current_dir(folder_name: &str) -> PathBuf {
    let current_dir = env::current_dir().expect("Error getting current directory.");
    let folder_path = current_dir.join(folder_name);
    folder_path
}


fn main() {
    // source path of the files which should be parsed
    let source_path = "data_xes/";
    // result path
    let result_path = "data_work/";

    let result_path = join_with_current_dir(result_path).display().to_string();
    let data_path_raw = join_with_current_dir(source_path);//Path::new(source_path);

    // read specified directory
    if let Ok(entries) = fs::read_dir(&data_path_raw) {
        for entry in entries {
            // print which file will be parsed next
            println!("{:?}", entry);
            let log;
            if let Ok(ref entry) = entry {
                //  Hospital Log
                if entry.file_name().to_str().unwrap().starts_with("Hospital") {
                    log = logfile_parser::parse_anything_known::<HospitalLogKeyword>(entry.path().to_str().unwrap());

                // Road Traffic Fine Management
                } else if entry.file_name().to_str().unwrap().starts_with("Road") {
                    log = logfile_parser::parse_anything_known::<RoadTrafficKeyedData>(entry.path().to_str().unwrap())

                // Sepsis Case Event Log
                } else if entry.file_name().to_str().unwrap().starts_with("Sepsis") {
                    log = logfile_parser::parse_anything_known::<SepsisCasesKeywords>(entry.path().to_str().unwrap())

                // Business Process Intelligence Logs
                } else if entry.file_name().to_str().unwrap().starts_with("BPI") {
                    //BPI 12, 17 and 18 have the same keywords
                    log = logfile_parser::parse_anything_known::<Bpi2017>(entry.path().to_str().unwrap())
                } else { continue; }

                let filename = entry.file_name().to_str().unwrap().strip_suffix(".xes").unwrap().to_string();
                let path = result_path.to_string() + &filename;

                // print log to CSV
                if let Some(log) = log {
                    log.print_to_csv(&path, &filename)
                } else {
                    eprintln!("Something went wrong parsing the log file {}", &filename);
                }
            }
        }
    } else {
        eprintln!("Error reading directory data, directory does not exist: {:?}", data_path_raw);
    }
}
