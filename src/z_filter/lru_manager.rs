use crate::z_filter::attribute::Attribute;
use crate::z_filter::config::Config;
use crate::z_filter::lru_entry::LRUEntry;
use chrono::{DateTime, Duration, Utc};
use logfile_parser::parsing_structures::event_sourced::EventSource;
use std::collections::{HashMap, VecDeque};

#[derive(Debug, Clone)]
pub struct LruManager {
    cache: HashMap<Attribute, VecDeque<LRUEntry>>, // Maps each attribute to its LRU list
    max_users: usize, // z-value: max users before output
    max_age: Duration, // ∆t: maximum age for LRU entries
}

impl LruManager {
    pub fn new(max_users: usize, max_age: Duration) -> Self {
        Self { cache: HashMap::new(), max_users, max_age }
    }

    pub fn from(config: Config) -> Self {
        Self::new(config.max_users, config.max_age)
    }

    pub fn process_event(&mut self, event: EventSource) -> Option<EventSource> {
        if let Some((case, activity, source, timestamp)) = event.disassemble() {
            //TODO umstellen
            self.process(case, activity, timestamp, source)
        } else {
            None
        }
    }

    fn process(&mut self, case: String, activity: String, timestamp: DateTime<Utc>, source: Vec<String>) -> Option<EventSource> {
        let lru = self.cache.entry(Attribute::new(&activity)).or_insert(VecDeque::new());
        Self::check_attribute(lru, &case, &timestamp);
        Self::evict_old_users(lru, &timestamp, &self.max_age);
        Self::exceed_z(lru, self.max_users, case, activity, source, timestamp)
    }

    fn check_attribute(lru: &mut VecDeque<LRUEntry>, user: &String, timestamp: &DateTime<Utc>) {
        //check if user already exists for the attribute
        if let Some(pos) = lru.iter().position(|entry| { entry.user == *user }) {
            //user exists at position 'pos' in the lru
            let mut entry = lru.remove(pos).unwrap(); // safe unwrap as there is a user at the position
            //refresh timestamp
            entry.timestamp = *timestamp;
            //push refreshed entry to the front
            lru.push_front(entry);
        } else {
            // user was not found in the list, so just add the user
            lru.push_front(LRUEntry::new(user, *timestamp));
        }
    }
    fn evict_old_users(lru: &mut VecDeque<LRUEntry>, current_time: &DateTime<Utc>, max_age: &Duration) {
        while let Some(entry) = lru.back() {
            if *current_time - entry.timestamp > *max_age {
                //remove oldest users if exceeding threshold
                let _ = lru.pop_back();
            } else {
                break;
            }
        }
    }

    fn exceed_z(lru: &mut VecDeque<LRUEntry>,
                max_users: usize,
                case: String,
                activity: String,
                source: Vec<String>,
                timestamp: DateTime<Utc>) -> Option<EventSource> {
        //sanity
        if lru.len() >= max_users {
            Some(EventSource::new(case, Some(activity), source, Some(timestamp)))
        } else {
            None
        }
    }
}