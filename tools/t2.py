
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--node", default="main_module",
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
    data = txmsg.encode({"cmd": 0x20, "data": 50})
    canbus.send_msg(can.Message(arbitration_id=txmsg.frame_id, data=data))
