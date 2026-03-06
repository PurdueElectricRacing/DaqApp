use crate::{can, connection, ui};
use chrono::{DateTime, Local};
use log::logger;
use slcan::{Can2Frame, CanFrame};
use core::time;
use std::io::Write;
use std::os::linux::raw;
use std::{thread, time::Duration};
use std::fs::{File, OpenOptions, create_dir_all, exists, write};
use bytemuck::{Pod, Zeroable};

const NO_CONNECTION_SLEEP_MS: u64 = 200;
const READ_RETRY_SLEEP_MS: u64 = 2;
const BUS_LOAD_UPDATE_MS: u128 = 200;

#[repr(C)]
#[derive(Pod, Zeroable, Copy, Clone)]
struct RawFrame {
    ticks_ms: u32,
    identity: u32,
    data: [u8; 8],
}

pub struct Logger {
    file: Option<File>,
    time: DateTime<Local>,
}

impl Logger {
    pub fn new(file: Option<File>) -> Logger{
        Logger {file: file, time: Local::now()}
    }
}

fn process_can_frame(frame: &CanFrame, state: &can::state::State) {
    match frame {
        slcan::CanFrame::Can2(frame2) => {
            let decode_msg_id = util::can::slcan_to_u32_with_extid_flag(&frame2.id());
            let raw_msg_id = util::can::slcan_to_u32_without_extid_flag(&frame2.id());

            let data = frame2.data().unwrap_or(&[]);
            let timestamp = chrono::Local::now();
            let raw_bytes = data.to_vec();

            let decoded = state
                .parser
                .as_ref()
                .and_then(|parser| parser.decode_msg(decode_msg_id, data));

            match decoded {
                Some(decoded) => {
                    let parsed_msg = messages::ParsedMessage {
                        timestamp,
                        raw_bytes,
                        decoded,
                    };
                    state
                        .can_to_ui_tx
                        .send(messages::MsgFromCan::ParsedMessage(parsed_msg))
                        .expect("Failed to send parsed CAN message");
                }
                None => {
                    if state.parser.is_some() {
                        log::error!(
                            "Failed to parse: frame ID 0x{:X} ({}), data: {:02X?}",
                            raw_msg_id,
                            raw_msg_id,
                            data
                        );
                    } else {
                        log::warn!(
                            "No DBC loaded. Received frame ID 0x{:X} ({}), data: {:02X?}",
                            raw_msg_id,
                            raw_msg_id,
                            data
                        );
                    }

                    let unparsed_msg = messages::UnparsedMessage {
                        timestamp,
                        raw_bytes,
                        msg_id: raw_msg_id,
                    };
                    state
                        .can_to_ui_tx
                        .send(messages::MsgFromCan::UnparsedMessage(unparsed_msg))
                        .expect("Failed to send unparsed CAN message");
                }
            }

            data.len()
        }

        slcan::CanFrame::CanFd(frame_fd) => {
            let msg_id_raw = util::can::slcan_to_u32_without_extid_flag(&frame_fd.id());
            log::warn!(
                "Received CAN FD frame id=0x{:X} len={}",
                msg_id_raw,
                frame_fd.data().len()
            );
            frame_fd.data().len()
        }
    }
}

pub fn start_can_thread(
    can_to_ui_tx: std::sync::mpsc::Sender<messages::MsgFromCan>,
    ui_to_can_rx: std::sync::mpsc::Receiver<messages::MsgFromUi>,
    selected_source: Option<connection::ConnectionSource>,
) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        let mut state = can::state::State::new(can_sender, ui_receiver);
        let mut driver: Option<Box<dyn can::driver::Driver>> = None;
        let mut current_source: Option<connection::ConnectionSource> = selected_source;

        let mut last_log = Logger::new(None);

        // MAIN LOOP
        loop {
            // Process UI messages first (DBC load, new message to send, etc.)
            while let Ok(msg) = state.ui_to_can_rx.try_recv() {
                match msg {
                    messages::MsgFromUi::DbcSelected(path) => {
                        match can_decode::Parser::from_dbc_file(&path) {
                            Ok(parser) => {
                                state.parser = Some(parser);
                                log::info!("Loaded DBC from {:?}", path);
                            }
                            Err(e) => log::error!("Failed to load DBC {:?}: {e}", path),
                        }
                    }
                    messages::MsgFromUi::Connect(source) => {
                        // Close existing connection if any
                        if let Some(mut old_driver) = state.driver.take() {
                            let _ = old_driver.close();
                        }
                        state.is_connected = false;
                        state
                            .can_to_ui_tx
                            .send(messages::MsgFromCan::Disconnection)
                            .expect("Failed to send disconnected message");
                        state.current_source = Some(source);
                    }
                    messages::MsgFromUi::AddSendMessage(add_send_msg) => {
                        state.add_send_message(add_send_msg);
                    }
                    messages::MsgFromUi::DeleteSendMessage { msg_id } => {
                        state.delete_send_message(msg_id);
                    }
                }
            }

            let msgs_to_send = state.send_this_tick();
            for msg in msgs_to_send {
                if let Some(ref mut active_driver) = state.driver {
                    let id = if msg.is_msg_id_extended {
                        slcan::ExtendedId::new(msg.msg_id & util::can::EXTENDED_ID_MASK)
                            .map(slcan::Id::Extended)
                    } else if msg.msg_id <= util::can::STANDARD_ID_MASK {
                        slcan::StandardId::new(msg.msg_id as u16).map(slcan::Id::Standard)
                    } else {
                        log::warn!(
                            "Invalid message ID {} for sending CAN frame (exceeds 11 bits for standard)",
                            msg.msg_id
                        );
                        None
                    };

                    if let Some(id) = id {
                        if let Some(can2_frame) = slcan::Can2Frame::new_data(id, &msg.msg_bytes) {
                            let frame = slcan::CanFrame::Can2(can2_frame);
                            match active_driver.write_frame(frame) {
                                Ok(_) => {
                                    log::info!(
                                        "Sent CAN frame with ID 0x{:X} ({}), data: {:02X?}",
                                        msg.msg_id,
                                        msg.msg_id,
                                        msg.msg_bytes
                                    );
                                    state
                                        .can_to_ui_tx
                                        .send(messages::MsgFromCan::MessageSent {
                                            msg_id: msg.msg_id,
                                            timestamp: chrono::Local::now(),
                                            amount_left: state
                                                .send_msgs
                                                .get(&msg.msg_id)
                                                .map(|info| info.amount),
                                            // If the message is removed after the send, this
                                            // will return None, which is what we want to indicate
                                            // no more sends left
                                        })
                                        .expect("Failed to send message sent confirmation");
                                }
                                Err(e) => {
                                    log::error!("Failed to send CAN frame: {:?}", e);
                                    state.is_connected = false;
                                    if let Some(ref source) = state.current_source {
                                        let error_msg = source.display_name();
                                        state
                                            .can_to_ui_tx
                                            .send(messages::MsgFromCan::ConnectionFailed(error_msg))
                                            .expect("Failed to send connection failed message");
                                    }
                                    state.driver = None;
                                }
                            }
                        } else {
                            log::error!(
                                "Cannot send CAN frame: data length {} exceeds 8 bytes",
                                msg.msg_bytes.len()
                            );
                            continue;
                        }
                    } else {
                        log::warn!("Invalid message ID {} for sending CAN frame", msg.msg_id);
                    }
                } else {
                    log::warn!("Cannot send CAN frame, no active connection");
                }
            }

            // Attempt to connect if we don't have a driver but have a source
            if state.driver.is_none() {
                if let Some(ref source) = state.current_source {
                    match can::driver::create_driver(source) {
                        Ok(new_driver) => {
                            state.driver = Some(new_driver);
                            state.is_connected = true;
                            state
                                .can_to_ui_tx
                                .send(messages::MsgFromCan::ConnectionSuccessful)
                                .expect("Failed to send connection successful message");
                            log::info!("Connected to {:?}", source);
                        }
                        Err(e) => {
                            log::error!("Failed to create driver for {:?}: {:?}", source, e);
                            let error_msg = source.display_name();
                            state
                                .can_to_ui_tx
                                .send(messages::MsgFromCan::ConnectionFailed(error_msg))
                                .expect("Failed to send connection failed message");
                            std::thread::sleep(std::time::Duration::from_millis(
                                NO_CONNECTION_SLEEP_MS,
                            ));
                            continue;
                        }
                    }
                } else {
                    // No source configured, just sleep
                    std::thread::sleep(std::time::Duration::from_millis(NO_CONNECTION_SLEEP_MS));
                    continue;
                }
            }

            // Try to read a frame from the driver
            let Some(ref mut active_driver) = state.driver else {
                std::thread::sleep(std::time::Duration::from_millis(NO_CONNECTION_SLEEP_MS));
                continue;
            };

            match active_driver.read_frame() {
                Ok(frame) => {
                    process_can_frame(&frame, &state);
                    log_frame(&frame, &mut last_log);
                }
                Err(can::driver::DriverError::ReadError(error_type)) => {
                    match error_type {
                        can::driver::DriverReadError::Timeout => {
                            // Normal timeout, just retry
                            std::thread::sleep(std::time::Duration::from_millis(
                                READ_RETRY_SLEEP_MS,
                            ));
                        }
                        other => {
                            // Actual error, disconnect
                            log::error!("Driver read error: {:?}", other);
                            state.is_connected = false;
                            if let Some(ref source) = state.current_source {
                                let error_msg = source.display_name();
                                state
                                    .can_to_ui_tx
                                    .send(messages::MsgFromCan::ConnectionFailed(error_msg))
                                    .expect("Failed to send connection failed message");
                            }
                            state.driver = None;
                        }
                    }
                }
                Err(e) => {
                    log::error!("Unexpected driver error: {:?}", e);
                    state.is_connected = false;
                    state.driver = None;
                }
            }
        }

        unreachable!("CAN thread should never exit on its own");
    })
}

// Log every CAN frame within a certain amount of time
pub fn log_frame(frame: &CanFrame, last_log: &mut Logger) {
    match create_dir_all("./logs/") {
        Ok(_) => {}
        Err(e) => {log::error!("Error with logs directory: {}", e)}
    }

    let now = Local::now();
    let difference = now - last_log.time;

    if last_log.file.is_none() || difference.num_minutes() > 3 {
        let filename = format!("./logs/{}.log", now.format("%Y-%m-%d_%H-%M-%S"));
        match OpenOptions::new().write(true).append(true).create(true).open(&filename) {
            Ok(f) => {
                last_log.file = Some(f);
                last_log.time = now;
            }
            Err(e) => {
                log::error!("Error creating file: {}", e);
                return;
            }
        }
    }

    if let Some(file) = &mut last_log.file {
        let ticks = now.timestamp_millis() as u32;
        let raw_message = match frame {
            CanFrame::Can2(frame2) => {
                let id = match frame2.id() {
                    slcan::Id::Standard(sid) => sid.as_raw() as u32,
                    slcan::Id::Extended(eid) => eid.as_raw(),
                };
                let mut raw_data = [0u8; 8];
                if let Some(data_slice) = frame2.data() {
                    raw_data[..data_slice.len().min(8)].copy_from_slice(&data_slice[..data_slice.len().min(8)]);
                }
                RawFrame { ticks_ms: ticks, identity: id, data: raw_data }
            }
            CanFrame::CanFd(frame_fd) => {
                let id = match frame_fd.id() {
                    slcan::Id::Standard(sid) => sid.as_raw() as u32,
                    slcan::Id::Extended(eid) => eid.as_raw(),
                };
                let mut raw_data = [0u8; 8];
                let data_slice = frame_fd.data();
                raw_data[..data_slice.len().min(8)].copy_from_slice(&data_slice[..data_slice.len().min(8)]);
                RawFrame { ticks_ms: ticks, identity: id, data: raw_data }
            }
        };

        if let Err(e) = file.write_all(bytemuck::bytes_of(&raw_message)) {
            log::error!("Error writing to file: {}", e);
        }
    }
}