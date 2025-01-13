use crate::z_filter::attribute::Attribute;
use crate::z_filter::config::Config;
use crate::z_filter::lru_entry::LRUEntry;
use chrono::{DateTime, Duration, Utc};
use logfile_parser::parsing_structures::event_sourced::EventSource;
use std::collections::{HashMap, VecDeque};

#[derive(Debug, Clone)]
pub struct LruManager {
    cache: HashMap<Attribute, VecDeque<LRUEntry>>, // Maps each attribute to its LRU list
    users: HashMap<Attribute, u32>,
    max_users: usize, // z-value: max users before output
    max_age: Duration, // ∆t: maximum age for LRU entries
}

impl LruManager {
    pub fn new(max_users: usize, max_age: Duration) -> Self {
        Self { cache: HashMap::new(), users: HashMap::new(), max_users, max_age }
    }


    pub fn from(config: Config) -> Self {
        Self::new(config.max_users, config.max_age)
    }

    pub fn process(&mut self, case: &String, activity: &String, timestamp: &DateTime<Utc>, source: &Vec<String>) -> bool {
        //check whether attribute is in hashmap, create a new entry if not
        let lru = self.cache.entry(Attribute::new(activity)).or_insert(VecDeque::new());
        let users = self.users.entry(Attribute::new(activity)).or_insert(0);
        Self::check_user(lru, users, case, timestamp, source);
        Self::evict_old_users(lru, users, timestamp, &self.max_age);
        *users as usize >= self.max_users
    }

    fn check_user(lru: &mut VecDeque<LRUEntry>, users: &mut u32, user: &String, timestamp: &DateTime<Utc>, source: &Vec<String>) {
        //check if user already exists for the attribute
        if let Some(pos) = lru.iter().position(|entry| { entry.user == *user }) {
            //user exists at position 'pos' in the lru
            let mut entry = lru.remove(pos).unwrap(); // safe unwrap as there is a user at the position
            //refresh timestamp
            entry.timestamp = *timestamp;
            //push refreshed entry to the front
            lru.push_front(entry);
            *users += 1;
        } else {
            // user was not found in the list, so just add the user
            lru.push_front(LRUEntry::new(user, *timestamp, source.clone()));
            *users += 1;
        }
    }
    fn evict_old_users(lru: &mut VecDeque<LRUEntry>,users: &mut u32, current_time: &DateTime<Utc>, max_age: &Duration) {
        while let Some(entry) = lru.back() {
            if *current_time - entry.timestamp > *max_age {
                //remove oldest users if exceeding threshold
                let _ = lru.pop_back();
                //None is possible in the improved Variation
                *users -= 1;
            } else {
                break;
            }
        }
    }

    fn exceed_z(lru_entry: &mut VecDeque<LRUEntry>,
                users: &mut u32,
                max_users: usize,
                case: String,
                activity: String,
                source: Vec<String>,
                timestamp: DateTime<Utc>) -> Option<EventSource> {
        // Publish Event Source if Lru entry is long enough (length greater equal Z/max_users)
        if *users as usize >= max_users {
            Some(EventSource::new(case, Some(activity), source, Some(timestamp)))
        } else {
            None
        }
    }

    pub fn release_other_entries(&mut self, activity: &String) -> Option<EventSource> {
        if let Some(lru) = self.cache.get_mut(&Attribute::new(activity)){
            if let Some(entry) = lru.pop_back(){
                return Some(entry.to_event_source(activity.clone()))
            }
        }
        None
    }
}

mod tests{
    use logfile_parser::parsing_structures::event_sourced::EventSourceLog;
    use crate::z_filter::z_anon::{ZFilter, ZFilteringMethod};
    use super::*;


    static  Z: usize = 2;
    fn init_event_source(a: String, u: String) -> EventSource{
        EventSource::new(
            u,
            Some(a.clone()),
            vec![a],
            Some(Utc::now()))
    }
    fn init_event_sources_equal_user_activity(i: u32) -> Vec<EventSource> {
        let mut vec = Vec::new();
        for j in 0..i{
            vec.push(init_event_source(j.to_string(), j.to_string()));

        }

        vec

    }
    #[test]
    fn test_distinct_attributes_distinct_user(){
        let  res = init_event_sources_equal_user_activity(10);
        let mut lru = LruManager::from(Config::new(Z, Duration::hours(10)));

        for e in res{
            if let Some((case, activity, source, timestamp)) = e.disassemble() {
                assert_eq!(lru.process(&case, &activity, &timestamp, &source), false);
            } else {
                assert!(false);
            }
        }
    }

    #[test]
    fn test_distinct_attributes_same_user(){
        let mut vec = Vec::new();
        let user = String::from("test");
        for i in 0..10{
            vec.push(init_event_source(i.to_string(), user.clone()));
        }
        let mut lru = LruManager::from(Config::new(Z, Duration::hours(10)));
        for e in vec{
            if let Some((case, activity, source, timestamp)) = e.disassemble() {
                assert_eq!(lru.process(&case, &activity, &timestamp, &source), false);
            }
        }
    }

    #[test]
    fn test_different_users_same_attribute(){
        let attribute: String = String::from("test");
        let mut vec = Vec::new();
        for i in 0..10{
            vec.push(init_event_source(attribute.clone(), i.to_string()));
        }
        let mut lru = LruManager::from(Config::new(Z, Duration::hours(10)));
        for (i,e) in vec.into_iter().enumerate(){
            let result;
            if let Some((case, activity, source, timestamp)) = e.disassemble(){
                result = lru.process(&case, &activity, &timestamp, &source);
            } else {
                assert!(false);
                return;
            }
            if i < Z -1{
                assert_eq!(result, false);
            } else {
                assert_eq!(result, true);
            }
        }
    }

    #[test]
    /// A test whether the eviction loop really evicts user before looking whether it should be outputted
    fn test_delta_time_limit(){
        let mut vec = Vec::new();
        let user = String::from("test");
        vec.push(EventSource::new(user.clone(), Some(user.clone()), vec![], Some(Utc::now())));
        vec.push(EventSource::new(String::from("lol"), Some(user.clone()), vec![], Some(Utc::now() + Duration::hours(10))));
        let mut lru = LruManager::from(Config::new(Z, Duration::hours(10)));
        for e in vec.into_iter(){
            if let Some((case, activity, source, timestamp)) = e.disassemble() {
                assert_eq!(lru.process(&case, &activity, &timestamp, &source), false)
            }else {
                assert!(false);
            }
        }

    }

    #[test]
    fn test_delta_time(){
        let mut vec = Vec::new();
        let user = String::from("test");
        vec.push(EventSource::new(user.clone(), Some(user.clone()), vec![], Some(Utc::now())));
        vec.push(EventSource::new(String::from("lol"), Some(user.clone()), vec![], Some(Utc::now() + Duration::hours(9))));
        let mut lru = LruManager::from(Config::new(Z, Duration::hours(10)));
        for (i,e) in vec.into_iter().enumerate(){
            if let Some((case, activity, source, timestamp)) = e.disassemble() {
                let res = lru.process(&case, &activity, &timestamp, &source);

            if i == 0{
                assert_eq!(res, false);
            } else {
                assert_eq!(res, true);
            }
            }

        }
    }


    #[tokio::test]
    async fn test_in_simulator(){
        let mut vec = vec![
            EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
            EventSource::new(String::from("1"), Some(String::from("ac2")), vec!["A".to_string()], Some(Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac2")), vec!["A".to_string()], Some(Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac2")), vec!["A".to_string()], Some(Utc::now())),
            //--------------------------------------------Source B
            EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["B".to_string()], Some(Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["B".to_string()], Some(Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac1")), vec!["B".to_string()], Some(Utc::now())),
            EventSource::new(String::from("1"), Some(String::from("ac2")), vec!["B".to_string()], Some(Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac2")), vec!["B".to_string()], Some(Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac2")), vec!["B".to_string()], Some(Utc::now())),
        ];

        match sourced_simulator::create_default_simulator(
            ZFilter::new(LruManager::from(Config::new(3,Duration::hours(10))), ZFilteringMethod::ClassicZfilter),
            EventSourceLog::from(vec.clone())).await{
            Ok(simulator) => {
                let res = simulator.run().await;
                assert_eq!(res.len(), 4);

            }
            Err(e) => {
                panic!("{}", e);
            }
        }
    }
}