use chrono::{DateTime, Utc};
use logfile_parser::parsing_structures::event_sourced::EventSource;

#[derive(Debug, Clone)]
pub struct LRUEntry {
    pub(crate) user: String, //case id in this case
    pub timestamp: DateTime<Utc>,
    pub source: Vec<String>,
    pub published: bool,
}

impl LRUEntry {
    pub fn new(user: &str, timestamp: DateTime<Utc>, source: Vec<String>) -> LRUEntry {
        LRUEntry { user: user.to_string(), timestamp, source, published: false }
    }

    pub fn to_event_source(self, activity: String) -> EventSource {
        EventSource::new(self.user, Some(activity),self.source, self.timestamp)
    }

}
