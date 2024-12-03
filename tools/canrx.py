import argparse
import can
from datetime import datetime
from canbus import CANBus

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )
    parser.add_argument('-s', "--socket", action='store_true',
        help="use linux socket backend instead of gs_usb (linux only)",
    )
    parser.add_argument('-r', "--receive", action='store_true',
        help="use linux socket backend instead of gs_usb (linux only)",
    )

    args = parser.parse_args()
    node = args.node
    canbus = CANBus(verbose=args.verbose, use_socket=args.socket)
    canbus.connect()

    if (args.receive):
        rxmsg = canbus.db.get_message_by_name(f"daq_response_MAIN_MODULE")
        msg = canbus.receive_msg(rxmsg)
        print(msg)
    else:
        txmsg = canbus.db.get_message_by_name(f"daq_response_MAIN_MODULE")
        data = txmsg.encode({"data": 0})
        canbus.send_msg(can.Message(arbitration_id=txmsg.frame_id, data=data))

        rxmsg = canbus.db.get_message_by_name(f"daq_response_MAIN_MODULE")
        msg = canbus.receive_msg(rxmsg)
        print(msg)
