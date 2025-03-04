use chrono::{Duration};


/// configuration struct for the lru manager, setting z threshold and time parameter
#[derive(Clone)]
pub struct Config {
    pub(crate) max_users: usize,// z threshold
    pub(crate) max_age: Duration,// time parameter / time-window
}

impl Config {
    /// create new config instance
    pub fn new(max_users: usize, max_age: Duration) -> Self {
        Config { max_users, max_age }
    }
}

impl Default for Config {
    /// default configuration
    fn default() -> Self {
        Config::new(1, Duration::hours(24))
    }
}