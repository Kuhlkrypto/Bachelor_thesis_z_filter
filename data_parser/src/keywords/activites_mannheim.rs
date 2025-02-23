use logfile_parser::traits::defaults::DefaultValues;
use logfile_parser::traits::keyword_provider::KeywordProvider;
use serde::Deserialize;

#[derive(Deserialize)]
pub struct DummyActivitesMannheim;

impl KeywordProvider for DummyActivitesMannheim {
    fn keywords_source() -> Vec<String> {
        vec!["lifecycle:transition".to_string()]
    }

    fn keywords_activity() -> Vec<String> {
        vec!["concept:name".to_string()]
    }

    fn keywords_timestamp() -> Vec<String> {
        vec!["time:timestamp".to_string()]
    }

}


impl DefaultValues for DummyActivitesMannheim {}