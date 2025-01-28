use logfile_parser::traits::defaults::DefaultValues;
use logfile_parser::traits::keyword_provider::KeywordProvider;
use serde::Deserialize;

#[derive(Deserialize)]
pub struct RoadTrafficKeyedData ;

impl KeywordProvider for RoadTrafficKeyedData {
    fn keywords_source() -> Vec<String> {
        //not in every event, will get replaced with activity attribute some time 
        vec!["STAGE".to_string()]
    }

    fn keywords_activity() -> Vec<String> {
        vec!["concept:name".to_string()]
    }

    fn keywords_timestamp() -> Vec<String> {
        vec!["time:timestamp".to_string()]
    }
}

impl DefaultValues for RoadTrafficKeyedData {
    
}