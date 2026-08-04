use crate::messages;
use chrono::{DateTime, Local, Timelike};
use eframe::egui;
use std::collections::VecDeque;
use walkers::{HttpTiles, Map, MapMemory, Plugin, Position, Projector, lon_lat, sources::OpenStreetMap};

// default starting is ross ade
const DEFAULT_CENTER_LAT: f64 = 40.4344;
const DEFAULT_CENTER_LON: f64 = -86.9183;

// amount of line segments behind dot
const TRAIL_LENGTH: usize = 20;

pub struct GpsPlot {
    pub title: String,
    tiles: Option<HttpTiles>,
    map_memory: MapMemory,
    current_fix: Option<(DateTime<Local>, f64, f64)>, // (timestamp, lat, lon)
    trail: VecDeque<Position>,
}

impl GpsPlot {
    pub fn new(instance_num: usize) -> Self {
        Self {
            title: format!("GPS Plot #{}", instance_num), // set widget title
            tiles: None, // map tiles created later in show
            map_memory: MapMemory::default(), // initialize map state
            current_fix: None, // no gps data yet
            trail: VecDeque::new(), // start with empty trail
        }
    }  

    fn extract_sample(msg: &messages::MsgFromCan) -> Option<(DateTime<Local>, f64, f64)> {
        let messages::MsgFromCan::ParsedMessage(parsed) = msg else {
            return None; // ignore if msg isn't a parsed can message
        };

        if parsed.decoded.name != "GPS_Position" {
            return None; // ignore non gps messages
        }

        let mut lat = None;
        let mut lon = None;

        for (_, sig) in &parsed.decoded.signals { // loop through all gps signals
            match sig.name.as_str() {
                "Latitude" => lat = Some(sig.value.physical), // save lat
                "Longitude" => lon = Some(sig.value.physical), // save long
                _ => {} // ignore other signals
            }
        }

        match (lat, lon) {
            (Some(lat), Some(lon)) => Some((parsed.timestamp, lat, lon)), // return GPS data
            _ => None, // missing lat or lon
        }
    }

    pub fn handle_can_message(&mut self, msg: &messages::MsgFromCan) {
        if let Some(sample) = Self::extract_sample(msg) { // if msg is valid gps data sample is timestamp, lat, long
            let (_, lat, lon) = sample; // pulls out lat and long
            self.current_fix = Some(sample); // replaces old pos w new pos

            self.trail.push_back(lon_lat(lon, lat)); // add point to trail
            while self.trail.len() > TRAIL_LENGTH { // make sure trail length doesnt exceed
                self.trail.pop_front();
            }
        }
    }

    pub fn show(&mut self, ui: &mut egui::Ui) -> egui_tiles::UiResponse {
        let tiles = self
            .tiles
            .get_or_insert_with(|| HttpTiles::new(OpenStreetMap, ui.ctx().clone())); // create map tiles if they don't exist

        match self.current_fix {
            Some((timestamp, lat, lon)) => { // if gps data exists show it
                ui.label(format!(
                    "Last fix: {lat:.6}, {lon:.6}  @ {:02}:{:02}:{:02}.{}",
                    timestamp.hour(),
                    timestamp.minute(),
                    timestamp.second(),
                    timestamp.timestamp_subsec_millis() / 100
                ));
            }
            None => {
                ui.label("Waiting for GPS_Position CAN message..."); // no gps data yet
            }
        }

        ui.add_space(4.0); // add spacing

        let has_fix = self.current_fix.is_some(); // check if gps data exists

        let car_position = self
            .current_fix
            .map(|(_, lat, lon)| lon_lat(lon, lat)) // use current gps position
            .unwrap_or_else(|| lon_lat(DEFAULT_CENTER_LON, DEFAULT_CENTER_LAT)); // otherwise use default position

        // centering map on car unless user moves
        if has_fix && self.map_memory.detached().is_none() {
            self.map_memory.center_at(car_position);
        }

        ui.add(
            Map::new(Some(tiles), &mut self.map_memory, car_position).with_plugin(CarDot {
                trail: self.trail.iter().copied().collect(), // pass trail to plugin
                visible: has_fix, // only draw if gps exists
                color: egui::Color32::BLACK, // draw in black
            }),
        );

        egui_tiles::UiResponse::None // nothing else to return
    }
}

// drawing cars path
struct CarDot {
    trail: Vec<Position>,
    visible: bool,
    color: egui::Color32,
}

impl Plugin for CarDot {
    fn run(
        self: Box<Self>,
        ui: &mut egui::Ui,
        _response: &egui::Response,
        projector: &Projector,
        _map_memory: &MapMemory,
    ) {
        if !self.visible || self.trail.is_empty() {
            return;
        }

        let painter = ui.painter();
        let n = self.trail.len();
        let screen_points: Vec<egui::Pos2> = self
            .trail
            .iter()
            .map(|position| projector.project(*position).to_pos2())
            .collect();

        // drawing the trail as a bunch of connected lines
        for i in 1..screen_points.len() { // 0.0 for oldest segment, 1.0 for most recent segment
            let age = i as f32 / n as f32;
            let fade = 0.15 + 0.85 * age;
            let width = 1.0 + 2.5 * age;

            painter.line_segment(
                [screen_points[i - 1], screen_points[i]],
                egui::Stroke::new(width, self.color.gamma_multiply(fade)),
            );
        }

        if let Some(&current) = screen_points.last() { // dot for current pos
            painter.circle_filled(current, 4.0, self.color);
            painter.circle_stroke(current, 4.0, egui::Stroke::new(1.5, egui::Color32::WHITE));
        }
    }
}