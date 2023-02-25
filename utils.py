import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import numpy as np
import sys

# Global Variables
def initGlobals():
    global signals
    signals = {}
    global plot_x_range_sec
    plot_x_range_sec = 10
    global events
    events = []
    global b_str
    b_str = "Main"
    global data_types
    data_types = {
        'uint8_t':np.dtype('<u1'),
        'uint16_t':np.dtype('<u2'),
        'uint32_t':np.dtype('<u4'),
        'uint64_t':np.dtype('<u8'),
        'int8_t':np.dtype('<i1'),
        'int16_t':np.dtype('<i2'),
        'int32_t':np.dtype('<i4'),
        'int64_t':np.dtype('<i8'),
        'float':np.dtype('<f4') # 32 bit
    }
    global data_type_length
    data_type_length = {'uint8_t':8, 'uint16_t':16, 'uint32_t':32, 'uint64_t':64,
                    'int8_t':8, 'int16_t':16, 'int32_t':32, 'int64_t':64,
                    'float':32}
    global debug_mode
    debug_mode = False
    global dark_mode
    dark_mode = False
    global daqProt
    daqProt = None
    global logging_paused
    logging_paused = True

# Logging helper functions
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log_error(phrase):
    print(f"{bcolors.FAIL}ERROR: {phrase}{bcolors.ENDC}")

def log_warning(phrase):
    log(f"{bcolors.WARNING}WARNING: {phrase}{bcolors.ENDC}")

def log_success(phrase):
    log(f"{bcolors.OKGREEN}{phrase}{bcolors.ENDC}")

def log(phrase):
    global debug_mode
    if debug_mode: print(phrase)

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

def clearDictItems(dictionary:dict):
    """ recursively calls clear on items in multidimensional dict"""
    for key, value in dictionary.items():
        if type(value) is dict:
            clearDictItems(value)
        else:
            value.clear()

def logEvent(time, msg):
    global events
    events.append([time, msg])
    print(events)

def clearEvents():
    global events
    events = []
