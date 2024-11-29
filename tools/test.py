
import argparse
import can
from datetime import datetime
from canbus import CANBus

DAQ_BL_CMD_RST        = 0x05

DAQ_BL_CMD_NTP_DATE   = 0x10
DAQ_BL_CMD_NTP_TIME   = 0x11
DAQ_BL_CMD_NTP_GET    = 0x12

DAQ_BL_CMD_LOG_ENABLE = 0x20
DAQ_BL_CMD_LOG_STATUS = 0x21

def daq_uds_ntp(canbus, txmsg):
    dt = datetime.now()
    year_bcd = ((dt.year % 100) // 10) << 4 | (dt.year % 10)
    month_bcd = (dt.month // 10) << 4 | (dt.month % 10)
    weekday_bcd = dt.weekday() + 1  # STM32 starts Monday at 0x1
    day_bcd = (dt.day // 10) << 4 | (dt.day % 10)

    hour_bcd = (dt.hour // 10) << 4 | (dt.hour % 10)
    minute_bcd = (dt.minute // 10) << 4 | (dt.minute % 10)
    second_bcd = (dt.second // 10) << 4 | (dt.second % 10)

    # DAQ NTP
    time_data = (hour_bcd & 0xff) << 16 | (minute_bcd & 0xff) << 8 | second_bcd & 0xff
    date_data = (year_bcd & 0xff) << 20 | (month_bcd & 0xff) << 12 | (weekday_bcd & 0xf) << 8 | day_bcd & 0xff

    data = txmsg.encode({"cmd": DAQ_BL_CMD_NTP_DATE, "data": date_data})
    canbus.send_msg(can.Message(arbitration_id=txmsg.frame_id, data=data))

    data = txmsg.encode({"cmd": DAQ_BL_CMD_NTP_TIME, "data": time_data})
    canbus.send_msg(can.Message(arbitration_id=txmsg.frame_id, data=data))

    data = txmsg.encode({"cmd": DAQ_BL_CMD_NTP_GET, "data": 0})
    canbus.send_msg(can.Message(arbitration_id=txmsg.frame_id, data=data))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--node", default="daq",
        help="node name to flash, e.g. main_module",
    )
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )
    parser.add_argument('-s', "--socket", action='store_true',
        help="use linux socket backend instead of gs_usb (linux only)",
    )

    args = parser.parse_args()
    node = args.node
    canbus = CANBus(verbose=args.verbose, use_socket=args.socket)
    canbus.connect()

    txmsg = canbus.db.get_message_by_name(f"{node}_bl_cmd")
    daq_uds_ntp(canbus, txmsg)

    # daq logging
    data = txmsg.encode({"cmd": DAQ_BL_CMD_LOG_ENABLE, "data": 0})
    canbus.send_msg(can.Message(arbitration_id=txmsg.frame_id, data=data))
    data = txmsg.encode({"cmd": DAQ_BL_CMD_LOG_STATUS, "data": 0})
    canbus.send_msg(can.Message(arbitration_id=txmsg.frame_id, data=data))

    #rxmsg = canbus.db.get_message_by_name(f"daq_response_MAIN_MODULE")
    #msg = canbus.receive_msg(rxmsg)
    #print(msg)
