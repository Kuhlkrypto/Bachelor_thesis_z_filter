#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Attribute {
    id: String, // Identifier for the attribute
}

impl Attribute {
    pub fn new(id: &str) -> Attribute {
        Attribute { id: id.to_string() }
    }
}
