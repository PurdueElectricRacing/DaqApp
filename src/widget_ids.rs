use crate::action;

pub struct WidgetIds {
    counters: std::collections::HashMap<action::WidgetType, usize>,
}

impl WidgetIds {
	pub fn new() -> Self {
		Self {
			counters: std::collections::HashMap::new(),
		}
	}

    pub fn next(&mut self, kind: action::WidgetType) -> usize {
        let counter = self.counters.entry(kind).or_insert(1);
        let id = *counter;
        *counter += 1;
        id
    }
}