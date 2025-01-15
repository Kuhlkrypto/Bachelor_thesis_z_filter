use crate::z_filter::lru_manager::LruManager;
use async_trait::async_trait;
use logfile_parser::parsing_structures::event_sourced::EventSource;
use sourced_simulator::simulator::node_communicator::NodeCommunicator;
use std::cmp::PartialEq;
use std::sync::Arc;


#[derive(Clone, PartialEq, Debug)]
pub enum ZFilteringMethod {
    ClassicZfilter,
    ImprovedZfilter,
}
#[derive(Clone)]
pub struct ZFilter {
    lru_manager: LruManager,
    zfiltering_method: ZFilteringMethod,
}
impl ZFilter {
    pub fn new(lru_manager: LruManager, filter_method: ZFilteringMethod) -> Self {
        Self { lru_manager, zfiltering_method: filter_method }
    }
}


#[async_trait]
impl sourced_simulator::simulator_traits::node_executions::NodeExecutions for ZFilter {
    async fn execute_event_queue_trigger(&mut self, event: EventSource, comm: Arc<NodeCommunicator>) {
        if let Some((case, activity, source, timestamp)) = event.disassemble() {
            if self.lru_manager.process(&case, &activity, &timestamp, &source) {
                match self.zfiltering_method {
                    ZFilteringMethod::ClassicZfilter => {
                        let event = EventSource::new(case, Some(activity), source, Some(timestamp));
                        comm.publish_to_collector(event).await;
                    }
                    ZFilteringMethod::ImprovedZfilter => {
                        for event in  self.lru_manager.release_other_entries(&activity) {
                            comm.publish_to_collector(event.to_event_source(activity.clone())).await;
                        }
                    }
                }
            }
        }
    }

    async fn execute_node_trigger(&mut self, _event: EventSource, _comm: Arc<NodeCommunicator>) {
        //not needed, ignore
    }
}

mod tests {
    use crate::z_filter::config::Config;
    use crate::z_filter::lru_manager::LruManager;
    use crate::z_filter::z_anon::{ZFilter, ZFilteringMethod};
    use chrono::{Duration, Utc};
    use logfile_parser::parsing_structures::event_sourced::{EventSource, EventSourceLog};

    #[tokio::test]
    async fn test_z_filter() {
        let mut vec = vec![
            EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
            EventSource::new(String::from("1"), Some(String::from("ac2")), vec!["A".to_string()], Some(Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac2")), vec!["A".to_string()], Some(Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac2")), vec!["A".to_string()], Some(Utc::now() + Duration::hours(10))),
            //--------------------------------------------Source B
            EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["B".to_string()], Some(Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["B".to_string()], Some(Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac1")), vec!["B".to_string()], Some(Utc::now())),
            EventSource::new(String::from("1"), Some(String::from("ac2")), vec!["B".to_string()], Some(Utc::now())),
            EventSource::new(String::from("2"), Some(String::from("ac2")), vec!["B".to_string()], Some(Utc::now())),
            EventSource::new(String::from("3"), Some(String::from("ac2")), vec!["B".to_string()], Some(Utc::now() + Duration::hours(10))),
        ];

        match sourced_simulator::create_default_simulator(
            ZFilter::new(LruManager::from(Config::new(3, Duration::hours(10)), ZFilteringMethod::ImprovedZfilter), ZFilteringMethod::ImprovedZfilter),
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

    #[tokio::test]
    async fn test_z_time_improved(){
        let mut vec = vec![
        EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
        EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
        EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
        EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
        EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now())),
        EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now() + Duration::hours(10))),
        EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now() + Duration::hours(10))),
        EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now() + Duration::hours(10))),
        EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now() + Duration::hours(21))),
        EventSource::new(String::from("1"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now() + Duration::hours(21))),
        EventSource::new(String::from("2"), Some(String::from("ac1")), vec!["A".to_string()], Some(Utc::now() + Duration::hours(21))),

        ];


        match sourced_simulator::create_default_simulator(
            ZFilter::new(LruManager::from(Config::new(2, Duration::hours(10)), ZFilteringMethod::ImprovedZfilter), ZFilteringMethod::ImprovedZfilter),
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
