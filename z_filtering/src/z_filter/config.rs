use chrono::{Duration};
#[derive(Clone)]
pub struct Config {
    pub(crate) max_users: usize,
    pub(crate) max_age: Duration,
}

impl Config {
    pub fn new(max_users: usize, max_age: Duration) -> Self {
        Config { max_users, max_age }
    }
}

impl Default for Config {
    fn default() -> Self {
        Config::new(0, Duration::default())
    }
}