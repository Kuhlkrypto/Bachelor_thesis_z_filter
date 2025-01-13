use logfile_parser::traits::defaults::DefaultValues;
use logfile_parser::traits::keyword_provider::KeywordProvider;
use serde::Deserialize;

#[derive(Deserialize)]
pub struct SepsisCasesKeywords;

impl KeywordProvider for SepsisCasesKeywords {
    fn keywords_source() -> Vec<String> {
        vec!["org:group".to_string()]
    }

    fn keywords_activity() -> Vec<String> {
        vec!["concept:name".to_string()]
    }

    fn keywords_timestamp() -> Vec<String> {
        vec!["time:timestamp".to_string()]
    }
}


impl DefaultValues for SepsisCasesKeywords {}