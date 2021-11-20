import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import sys

# Global Variables
def initGlobals():
    global signals
    signals = {}
    global plot_x_range_sec
    plot_x_range_sec = 10

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
    print(f"{bcolors.WARNING}WARNING: {phrase}{bcolors.ENDC}")

def log_success(phrase):
    print(f"{bcolors.OKGREEN}{phrase}{bcolors.ENDC}")

def log(phrase):
    print(phrase)

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
