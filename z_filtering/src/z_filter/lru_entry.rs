use chrono::{DateTime, Utc};
use logfile_parser::parsing_structures::event_sourced::EventSource;

/// struct representing an entry in the lru
#[derive(Debug, Clone)]
pub struct LRUEntry {
    pub(crate) user: String, // user id or case id for event logs
    pub timestamp: DateTime<Utc>, // time of execution
    pub source: Vec<String>,// custom source attribute
    pub published: bool,// indicates whether this entry was published
}

impl LRUEntry {
    /// creates a new object of the lru entry
    pub fn new(user: &str, timestamp: DateTime<Utc>, source: Vec<String>) -> LRUEntry {
        LRUEntry { user: user.to_string(), timestamp, source, published: false }
    }

    /// creates an event source instance from the containing attribute and additional activity
    pub fn to_event_source(self, activity: String) -> EventSource {
        EventSource::new(self.user, Some(activity),self.source, self.timestamp)
    }

}
