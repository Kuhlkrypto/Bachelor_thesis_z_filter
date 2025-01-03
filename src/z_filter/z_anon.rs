use crate::z_filter::lru_manager::LruManager;
use async_trait::async_trait;
use logfile_parser::parsing_structures::event_sourced::EventSource;
use sourced_simulator::simulator::node_communicator::NodeCommunicator;
use std::sync::Arc;

#[derive(Clone)]
pub struct ZFilter {
    lru_manager: LruManager,
}
impl ZFilter {
    pub fn new(lru_manager: LruManager) -> Self {
        Self { lru_manager }
    }
}


#[async_trait]
impl sourced_simulator::simulator_traits::node_executions::NodeExecutions for ZFilter {

    async fn execute_event_queue_trigger(&mut self, event: EventSource, comm: Arc<NodeCommunicator>) {
        match self.lru_manager.process_event(event) {
            Some(event) => {
                comm.publish_to_collector_event(event).await;
            }
            None => {
                //ignore
            }
        }
    }

    async fn execute_node_trigger(&mut self, _event: EventSource, _comm: Arc<NodeCommunicator>) {
        //not needed, ignore
    }
}