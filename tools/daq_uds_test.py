#!/usr/bin/env python3
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import can
from datetime import datetime
from communication.canbus_backend import CANBusTCP, CANBusUSB

DAQ_BL_CMD_RST        = 0x55

DAQ_BL_CMD_NTP_DATE   = 0x30
DAQ_BL_CMD_NTP_TIME   = 0x31
DAQ_BL_CMD_NTP_GET    = 0x32

DAQ_BL_CMD_HANDSHAKE  = 0x40
DAQ_BL_CMD_LOG_ENABLE = 0x41
DAQ_BL_CMD_LOG_STATUS = 0x42
DAQ_BL_CMD_LED_DISCO  = 0x43


def daq_uds_ntp(canbus):
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

    canbus.send_uds_frame(node="daq", cmd=DAQ_BL_CMD_NTP_DATE, data=date_data)
    canbus.send_uds_frame(node="daq", cmd=DAQ_BL_CMD_NTP_TIME, data=time_data)
    canbus.send_uds_frame(node="daq", cmd=DAQ_BL_CMD_NTP_GET, data=0)

def daq_uds_logging(canbus):
    canbus.send_uds_frame(node="daq", cmd=DAQ_BL_CMD_LOG_ENABLE, data=0)
    canbus.send_uds_frame(node="daq", cmd=DAQ_BL_CMD_LOG_STATUS, data=0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--node", default="daq",
        help="node name to flash, e.g. main_module",
    )
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )

    args = parser.parse_args()
    node = args.node
    cb = CANBusTCP(verbose=args.verbose)
    cb.connect()
    cb.start_thread()
    cb.send_uds_frame(node="daq", cmd=0x50, data=0)
    cb.stop_thread()

    #raise ValueError("exit")

    #daq_uds_ntp(canbus)
    #daq_uds_logging(canbus)
