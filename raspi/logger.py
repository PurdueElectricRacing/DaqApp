import RPi.GPIO as GPIO
import time
import subprocess
import os
import datetime

INPUT_PIN = 26
LED_PIN = 19
LOG_DURATION = 15 #minutes
USB = "/media/usb"
LOG_LOCATION = os.path.join(USB, 'logs')
DEBUG_PATH="/home/ubuntu/DAQ/logger.log"

GPIO.setmode(GPIO.BCM)
GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)

logging = False
start_time = 0
curr_proc = None

def log_debug(phrase):
    global DEBUG_PATH
    with open(DEBUG_PATH, 'a') as f:
        f.write(f"{datetime.datetime.now()}> {phrase}")


def mountUsb():
    with open('/proc/partitions') as partitions:
        lines = partitions.readlines()[2:] # skip header lines
    for line in lines:
        words = [x.strip() for x in line.split()]
        minor = int(words[1])
        device = words[3]
        #if minor % 16 ==0:
        path = "/sys/class/block/" + device
        if os.path.islink(path):
            if os.path.realpath(path).find('/usb') > 0:
                print(f"/dev/{device} -> {USB}")
                os.system(f"sudo mkdir {USB} 2>/dev/null")
                os.system(f"sudo chown -R ubuntu:ubuntu {USB} 2>/dev/null")
                os.system(f"mount /dev/{device} {USB} -o uid=ubuntu,gid=ubuntu 2>/dev/null")
    if len(os.listdir(USB)) > 0:
        print("USB connected")
        return False
    else:
        print("USB not connected")
        return True

def logProcessCreate():
    return subprocess.Popen(["candump", "-tA", "-l", "can0"], cwd=LOG_LOCATION)

def startLog():
    global start_time
    global curr_proc
    if curr_proc: stopLog()
    start_time = time.time()
    GPIO.output(LED_PIN, GPIO.HIGH)
    curr_proc = logProcessCreate()

def stopLog():
    global curr_proc
    curr_proc.terminate()
    GPIO.output(LED_PIN, GPIO.LOW)

def switchLogFile():
    # creates overlap, ensures no missed frames
    global start_time
    global curr_proc
    start_time = time.time()
    new_proc = logProcessCreate()
    stopLog()
    curr_proc = new_proc

def mountLoop():
    #while mountUsb():
    while not os.path.isdir(LOG_LOCATION):
        print("USB drive not mounted, trying again in 30 seconds")
        log_debug("USB drive not mounted, trying again in 30 seconds\n")
        time.sleep(30)
    print("USB drive mounted")
    log_debug("USB drive mounted\n")

log_debug("Starting DAQ Logger")
mountLoop()

try:
    while True:
        log_pin_on = GPIO.input(INPUT_PIN)
        if not os.path.isdir(LOG_LOCATION):
            if logging: stopLog()
            logging = False
            print("usb disconnected")
            log_debug("usb disconnected\n")
            mountLoop()

        if log_pin_on and not logging:
            logging = True
            print("starting log")
            log_debug("starting log\n")
            startLog()

        if not log_pin_on and logging:
            logging = False
            print("stopping log")
            log_debug("stopping log\n")
            stopLog()

        if logging and (time.time() - start_time) / 60.0 > LOG_DURATION:
            switchLogFile()

        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("closing logger")
    log_debug("closing logger\n")
