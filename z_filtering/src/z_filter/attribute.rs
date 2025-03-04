
/// attribute struct containing a string
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Attribute {
    id: String, // Identifier for the attribute, activity attribute in case of event logs
}

impl Attribute {
    pub fn new(id: &str) -> Attribute {
        Attribute { id: id.to_string() }
    }
}
