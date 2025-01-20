mod keywords;

use std::path::Path;
use std::fs;
use crate::keywords::activites_mannheim::DummyActivitesMannheim;
use crate::keywords::bpi2017::Bpi2017;
use crate::keywords::hospitallog::HospitalLogKeyword;
use crate::keywords::road_traffic::RoadTrafficKeyedData;
use crate::keywords::Sepsis_cases::SepsisCasesKeywords;

fn main() {
    let data_path_raw = Path::new("/home/fabian/Github/Bachelor_thesis_z_filter/data_xes");
    let result_path = "/home/fabian/Github/Bachelor_thesis_z_filter/data_csv/";
    let entries = fs::read_dir(&data_path_raw).unwrap();
    for entry in entries {
        let log;
        if let Ok(ref entry) = entry {
            if entry.file_name().to_str().unwrap().starts_with("edited") || entry.file_name().to_str().unwrap().starts_with("activitylog") {
             log = logfile_parser::parse_anything_known::<DummyActivitesMannheim>(entry.path().to_str().unwrap());
            } else if entry.file_name().to_str().unwrap().starts_with("Hospital") {
                 log = logfile_parser::parse_anything_known::<HospitalLogKeyword>(entry.path().to_str().unwrap());

            } else if entry.file_name().to_str().unwrap().starts_with("Road") {
                log = logfile_parser::parse_anything_known::<RoadTrafficKeyedData>(entry.path().to_str().unwrap())
            }else if entry.file_name().to_str().unwrap().starts_with("Sepsis") {
                log = logfile_parser::parse_anything_known::<SepsisCasesKeywords>(entry.path().to_str().unwrap())
            }else if entry.file_name().to_str().unwrap().starts_with("BPI") {
                //BPI 12, 17 and 18 have the same keywords
                log = logfile_parser::parse_anything_known::<Bpi2017>(entry.path().to_str().unwrap())

            }
            else { continue; }
            let filename = entry.file_name().to_str().unwrap().strip_suffix(".xes").unwrap().to_string();
            let path = result_path.to_string() + &filename;
            log.unwrap().print_to_csv(&path, &filename);
        }
    }



}
