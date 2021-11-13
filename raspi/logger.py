import RPi.GPIO as GPIO
import time
import subprocess

INPUT_PIN = 26
LOG_DURATION = 15 #minutes
LOG_LOCATION = './logs'

GPIO.setmode(GPIO.BCM)
GPIO.setup(INPUT_PIN, GPIO.IN)

logging = False
start_time = 0
curr_proc = None

def logProcessCreate():
    return subprocess.Popen(["candump", "-tA", "-l", "can0"], cwd=LOG_LOCATION)

def startLog():
    global start_time
    global curr_proc
    if curr_proc: stopLog()
    start_time = time.time()
    curr_proc = logProcessCreate()

def stopLog():
    global curr_proc
    curr_proc.terminate()

def switchLogFile():
    # creates overlap, ensures no missed frames
    global start_time
    global curr_proc
    start_time = time.time()
    new_proc = logProcessCreate()
    stopLog()
    curr_proc = new_proc

try:
    while True:
        log_pin_on = GPIO.input(INPUT_PIN)

        if log_pin_on and not logging:
            logging = True
            print("starting log")
            startLog()

        if not log_pin_on and logging:
            logging = False
            print("stopping log")
            stopLog()

        if logging and (time.time() - start_time) / 60.0 > LOG_DURATION:
            switchLogFile()

        time.sleep(1)

except KeyboardInterrupt:
    print("closing logger")
