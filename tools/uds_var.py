#!/usr/bin/env python3
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from construct import *
from communication.canbus_backend import CANBusUSB, CANBusTCP
from communication.common import DAQAppObject
import argparse
import can
import struct

import json
import os

UDSVarMessage = Struct(
    "cmd" / Hex(Int8ul),
    "id"  / Hex(Int8ul),
    "value" / Hex(Int32ul),
    "pad" / Default(Hex(Int16ul), 0xAAAA),
)
assert(UDSVarMessage.sizeof() == 8)

class UDSVarWriter(DAQAppObject):
    UDS_CMD_VAR_READ  = 0x20
    UDS_CMD_VAR_WRITE = 0x21
    UDS_CMD_PIN_READ  = 0x22

    def __init__(self, canbus, daq_config, node, verbose=False):
        super(UDSVarWriter, self).__init__(verbose)
        self.canbus = canbus
        self.daq_config = daq_config
        #assert(canbus.is_connected())

        self.active_node = ""
        self.txmsg = None
        self.rxmsg = None
        self.variables = []
        self.var_id_mapping = {}
        if (node):
            self.set_active_node(node)

    def set_active_node(self, node):
        self.active_node = node
        self.txmsg = self.canbus.db.get_message_by_name(f"uds_command_{node.lower()}")
        self.rxmsg = self.canbus.db.get_message_by_name(f"uds_response_{node.lower()}")
        self.load_variables(node)

    def uds_handshake(self, uds_request, **kwargs):
        tx_data = UDSVarMessage.build(uds_request)
        self.canbus.send_uds_frame(node=self.active_node.lower(), cmd=uds_request.cmd, data=tx_data)
        rxmsg = self.canbus.receive_uds_frame(node=self.active_node.lower(), cmd=uds_request.cmd, raw=True, timeout=1)
        uds_response = UDSVarMessage.parse(rxmsg.data)
        return uds_response

    def var_read(self, var_id, **kwargs):
        var_id = self.convert_id(var_id)
        uds_request = Container(dict(cmd=self.UDS_CMD_VAR_READ, id=var_id, value=0))
        uds_response = self.uds_handshake(uds_request, **kwargs)
        return uds_response

    def var_write(self, var_id, value, **kwargs):
        var_id = self.convert_id(var_id)
        uds_request = Container(dict(cmd=self.UDS_CMD_VAR_WRITE, id=var_id, value=value))
        uds_response = self.uds_handshake(uds_request, **kwargs)
        return uds_response

    def load_variables(self, active_node):
        var_id_mapping = {} # "name": id
        variables = []  # list in id order
        for bus in self.daq_config["busses"]:
            for node in bus["nodes"]:
                if (node["node_name"].lower() == active_node):
                    for i,var in enumerate(node["variables"]):
                        var["id"] = i
                        variables.append(var)
                        var_id_mapping[var["var_name"]] = i
                    break
        if (not len(variables)):
            raise RuntimeError(f"Failed to retreive variables for node {active_node}")
        self.variables = variables
        self.var_id_mapping = var_id_mapping

    def varname2id(self, name):
        if (name not in self.var_id_mapping):
            raise ValueError("Invalid variable name %s" % (name))
        var_id = self.var_id_mapping[name]
        # print(self.variables[var_id])
        return var_id

    def varname2var(self, name):
        return self.variables[self.varname2id(name)]

    def convert_id(self, id):
        if (isinstance(id, str)):
            id = self.varname2id(id)
        return id

import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError

def load_json_config(config_path, schema_path):
    """ loads config from json and validates with schema """
    config = json.load(open(config_path))
    schema = json.load(open(schema_path))

    # compare with schema
    try:
        validate(config, schema)
    except ValidationError as e:
        log_error("Invalid JSON!")
        print(e)
        sys.exit(1)

    return config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--node", default="main_module",
        help="node name to flash, e.g. main_module",
    )
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )
    parser.add_argument('-m', "--mode", default='usb',
        help="mode",
    )

    args = parser.parse_args()
    active_node = args.node

    CONFIG_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'dashboard.json'))
    firmware_base = ""
    if (not firmware_base):
        config = json.load(open(CONFIG_FILE_PATH))
        firmware_base = config['firmware_path']
    daq_config = load_json_config(os.path.join(firmware_base, 'common/daq/daq_config.json'), os.path.join(firmware_base, 'common/daq/daq_schema.json'))

    bus = CANBusUSB if (args.mode == "usb") else CANBusTCP

    cb = bus(verbose=args.verbose)
    cb.connect()
    cb.start_thread()

    uw = UDSVarWriter(cb, daq_config, node=active_node, verbose=args.verbose)

    if (active_node == "main_module"):
        var_name = "dummy_test_uds"
        x = uw.var_write(var_name, 0x11111111)
        x = uw.var_read(var_name)
        print(f"old: {x}")
        assert(x.value == 0x11111111)
        x = uw.var_write(var_name, 0x22222222)
        x = uw.var_read(var_name)
        print(f"new: {x}")
        assert(x.value == 0x22222222)
    elif (active_node == "daq"):
        var_name = 0
        x = uw.var_read(var_name)
        print(f"old: {x}")

    cb.stop_thread()
