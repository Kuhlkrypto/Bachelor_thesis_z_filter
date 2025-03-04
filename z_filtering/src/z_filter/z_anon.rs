use crate::z_filter::lru_manager::LruManager;
use async_trait::async_trait;
use logfile_parser::parsing_structures::event_sourced::EventSource;
use sourced_simulator::simulator::node_communicator::NodeCommunicator;
use std::cmp::PartialEq;
use std::sync::Arc;

/// Enum representing different Z-filtering methods.
#[derive(Clone, PartialEq, Debug)]
pub enum ZFilteringMethod {
    BasicZfilter,   // Basic Z-filtering method
    BalancedZfilter, // Improved Z-filtering method with additional processing
}

/// Struct implementing the ZFilter logic.
#[derive(Clone)]
pub struct ZFilter {
    lru_manager: LruManager,  // LRU manager for handling event sources
    zfiltering_method: ZFilteringMethod, // Filtering method to be used
}

impl ZFilter {
    /// Creates a new instance of ZFilter with a given LRU manager and filtering method.
    pub fn new(lru_manager: LruManager, filter_method: ZFilteringMethod) -> Self {
        Self { lru_manager, zfiltering_method: filter_method }
    }
}

#[async_trait]
impl sourced_simulator::simulator_traits::node_executions::NodeExecutions for ZFilter {
    /// Processes the event queue and applies filtering before sending events to the collector.
    async fn execute_event_queue_trigger(&mut self, event: EventSource, comm: Arc<NodeCommunicator>) {
        if let Some((case, activity, source, timestamp)) = event.disassemble() {
            // check whether z-anonymity condition is satisfied
            if self.lru_manager.process(&case, &activity, &timestamp, &source) {

                // match filtering method
                match self.zfiltering_method {
                    ZFilteringMethod::BasicZfilter => {
                        // Publish event directly to the collector.
                        let event = EventSource::new(case, Some(activity), source, timestamp);
                        comm.publish_to_collector(event).await;
                    }
                    ZFilteringMethod::BalancedZfilter => {
                        // Release other related entries before publishing.
                        for event in self.lru_manager.release_other_entries(&activity) {
                            // create new event source object and publish the event
                            comm.publish_to_collector(event.to_event_source(activity.clone())).await;
                        }
                    }
                }
            }
        }
    }

    /// Placeholder function, not needed for this implementation.
    async fn execute_node_trigger(&mut self, _event: EventSource, _comm: Arc<NodeCommunicator>) {
        // Not needed, ignore
    }
}

#[allow(unused_imports, dead_code)]
mod tests {
    use crate::z_filter::config::Config;
    use crate::z_filter::lru_manager::LruManager;
    use crate::z_filter::z_anon::{ZFilter, ZFilteringMethod};
    use chrono::{Duration, Utc};
    use logfile_parser::parsing_structures::event_sourced::{EventSource, EventSourceLog};

    /// Test Z-filtering with a sample event source log.
    #[tokio::test]
    async fn test_z_filter() {
        let vec = vec![
            EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], (Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac1")), vec!["A".to_string()], (Utc::now())),
            EventSource::new(String::from("1"), Some(String::from("ac2")), vec!["A".to_string()], (Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac2")), vec!["A".to_string()], (Utc::now())),
            EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], (Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac2")), vec!["A".to_string()], (Utc::now() + Duration::hours(10))),
            //--------------------------------------------Source B
            EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["B".to_string()], (Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["B".to_string()], (Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac1")), vec!["B".to_string()], (Utc::now())),
            EventSource::new(String::from("1"), Some(String::from("ac2")), vec!["B".to_string()], (Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac2")), vec!["B".to_string()], (Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac2")), vec!["B".to_string()], (Utc::now() + Duration::hours(10))),
        ];

        match sourced_simulator::create_default_simulator(
            ZFilter::new(LruManager::from(Config::new(3, Duration::hours(10)), ZFilteringMethod::BalancedZfilter), ZFilteringMethod::BalancedZfilter),
            EventSourceLog::from(vec.clone())).await {
            Ok(simulator) => {
                let res = simulator.run().await;
                assert_eq!(res.len(), 6);
            }
            Err(e) => {
                panic!("{}", e);
            }
        }
    }

    /// Test improved Z-time filtering over an extended time range.
    #[tokio::test]
    async fn test_z_time_improved() {
        let vec = vec![
            EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], (Utc::now())),
            EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], (Utc::now())),
            EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], (Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], (Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], (Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], (Utc::now() + Duration::hours(10))),
            EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], (Utc::now() + Duration::hours(21))),
        ];

        match sourced_simulator::create_default_simulator(
            ZFilter::new(LruManager::from(Config::new(2, Duration::hours(10)), ZFilteringMethod::BalancedZfilter), ZFilteringMethod::BalancedZfilter),
            EventSourceLog::from(vec.clone())).await {
            Ok(simulator) => {
                let res = simulator.run().await;
                assert_eq!(res.len(), 8);
            }
            Err(e) => {
                panic!("{}", e);
            }
        }
    }
}
