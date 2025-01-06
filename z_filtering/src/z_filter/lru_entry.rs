use chrono::{DateTime, Utc};
#[derive(Debug, Clone)]
pub struct LRUEntry {
    pub(crate) user: String, //case id in this case
    pub timestamp: DateTime<Utc>,
}

impl LRUEntry {
    pub fn new(user: &str, timestamp: DateTime<Utc>) -> LRUEntry {
        LRUEntry { user: user.to_string(), timestamp }
    }
}
