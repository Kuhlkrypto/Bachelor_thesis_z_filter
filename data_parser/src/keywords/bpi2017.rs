use logfile_parser::traits::defaults::DefaultValues;
use logfile_parser::traits::keyword_provider::KeywordProvider;
use serde::Deserialize;
#[derive(Deserialize)]
pub struct Bpi2017;

impl KeywordProvider for Bpi2017 {
    fn keywords_source() -> Vec<String> {
        vec![String::from("org:resource")]
    }

    fn keywords_activity() -> Vec<String> {
        vec![String::from("concept:name")]
    }

    fn keywords_timestamp() -> Vec<String> {
        vec![String::from("time:timestamp")]
    }
}

impl DefaultValues for Bpi2017 {
    
}