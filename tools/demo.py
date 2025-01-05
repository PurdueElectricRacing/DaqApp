"""
Course Number: ENGR 13300
Semester: Fall 2024

Description:
    Download the audio of a youtube video given a user-provided URL. Open the input audio WAV file as a numpy array and perform a FFT to analyze in the frequency domain. Using FFT and other DSP routines, determine whether the 6 LEDs should be turned on or off for the current audio sample interval. Send the states to the hardware device so the microcontroller can toggle the LEDs in sync with the music playing in the background thread.

Assignment Information:
    Assignment:     16. Individual Project
    Team ID:        LC11 - 26
    Author:         Eileen Yoon, eyn@purdue.edu
    Date:           12/05/2024

Contributors:

    My contributor(s) helped me:
    [ ] understand the assignment expectations without
        telling me how they will approach it.
    [ ] understand different ways to think about a solution
        without helping me plan my solution.
    [ ] think through the meaning of a specific error or
        bug present in my code without looking at my code.
    Note that if you helped somebody else with their code, you
    have to list that person as a contributor here as well.

Academic Integrity Statement:
    I have not used source code obtained from any unauthorized
    source, either modified or unmodified; nor have I provided
    another student access to my code.  The project I am
    submitting is my own original work.
"""

import argparse
import time
import numpy as np  # DSP library imports
from scipy.io import wavfile
import playsound
np.set_printoptions(suppress=True) # no scientific repr
import yt_dlp  # I/O library imports
import os
from tqdm import tqdm

# import UART hardware module
#from uart_gateway import UARTGateway
from canbus import CANBus

UART_COMMAND_LED = 0x1

# download_youtube_audio(link, outfile="out.wav")
#   Download audio of a YouTube video as a WAV file given the URL using youtube-dlp.
#   The youtube-dlp call is configured to fetch a 16 kHz WAV file containing only the audio portion of the YouTube video.
#
# Arguments:
# 1. link: URL to YouTube video you want to play, e.g. https://www.youtube.com/watch?v=dQw4w9WgXcQ
# 2. outfile: name of output WAV file (default "out.wav")
#
# Return:
# 1. outfile: name of the output WAV file it was downloaded to
#
def download_youtube_audio(link, outfile="out"):
    ydl_opts = {
        'outtmpl': outfile,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192'
        }],
        'postprocessor_args': [
            '-ar', '16000'
        ],
        'prefer_ffmpeg': True,
        'keepvideo': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
    return outfile + ".wav"

# open_audio_wav(filename)
#   Read input WAV file as a numpy array using scipy.io.wavfile. Return the input sample rate in Hz and the audio data as a numpy array.
#
# Arguments:
# 1. filename: path to input WAV file
#
# Return:
# 1. fs: sample rate of the audio file in Hz
# 2. audio_data: numpy array of the audio data
#
def open_audio_wav(filename):
    fs, data = wavfile.read(filename)
    return fs, data

# calc_rms_avg(fft, step)
#   Calculate the Root Mean Square (RMS) average of the given FFT data (indicates energy of the sample).
#
# Arguments:
# 1. fft: DFT of current audio sample
# 2. step: audio sample size, e.g. 2048
#
# Return:
# 1. rms_avg: RMS average of the FFT coefficients
#
def calc_rms_avg(fft, step):
    # Calculate root mean squared energy of the real component of the FFT to detect the power of the current audio sample
    fft_re = 2 / step * np.abs(fft)
    rms_avg = np.sqrt(np.mean(fft_re ** 2))
    return rms_avg

# calc_led_state_b0(fft, fs, step)
#   Determine whether to turn on LED0.
#   LED0: Small blue LED. Maps to bass guitar.
#
# Arguments:
#   1. fft: DFT of current audio sample
#   2. fs: sample rate of input audio, e.g. 16000 kHz
#   3. step: audio sample size, e.g. 2048
# Return:
#   1. b0: boolean state of LED0. 1 if bass guitar presence, else 0.
#
def calc_led_state_b0(fft, fs, step):
    # Midrange cut: 800 Hz–2.5 kHz, important for standing out in the mix
    # Presence and sparkle: 2.5 kHz–8 kHz, critical for articulation and note definition
	# Extract FFT bins containing 2 kHz - 4 kHz frequencies
    bin_low = int(1 / (fs / step / 2000))  # 2 kHz bin
    bin_high = int(1 / (fs / step / 4000)) # 4 kHz bin

    midrange = fft[bin_low:bin_high] # extract midrange
    # test if there is a significant energy of midrange frequencies
    b0 = np.sum(np.sqrt(np.abs(midrange))) > 100000
    return b0

# calc_led_state_b1(fft)
#   Determine whether to turn on LED1.
#   LED1: Small yellow LED. Maps to mid-high tones guitar.
#
# Arguments:
#   1. fft: DFT of the current audio sample
# Return:
#   1. b1: boolean state of LED1. 1 if mid-high tones guitar presence, else 0.
#
def calc_led_state_b1(fft):
    # Calculate bins of FFT to see frequency distribution
    hist, bin_edges = np.histogram(np.abs(fft), bins=7)
    # Since presence and sparkle is 2.5 kHz–8 kHz
    # If the first bin is between 40-100 MHz, i.e. mid tone guitar is a dominant frequency, turn on LED1
    b1 = (bin_edges[1] > 400000) and (bin_edges[1] < 1000000) # guitar frequency
    return b1

# calc_led_state_b2(sample, rms_avg, rms_last)
#   Determine whether to turn on LED2.
#   LED2: Small red LED. Maps to rhythm guitar.
#
# Arguments:
#   1. sample: audio sample
#   2. rms_avg: root mean square average (energy) of the current sample
#   3. rms_last: RMS energy of the last sample
# Return:
#   1. b2: boolean state of LED2. 1 if rhythm guitar is present, else 0.
#
def calc_led_state_b2(sample, rms_avg, rms_last):
    # General energy delta detection / guitar strum
    # If the RMS energy of the current sample is greater than the last sample, turn on red LED (indicates rhythm)
    b2 = (rms_last) and ((rms_avg - rms_last) > 10)
    b2 = int(b2)
    return b2

# calc_led_state_b3(sample, rms_avg, rms_last)
#   Determine whether to turn on LED3.
#   LED3: Large red LED. Maps to mid percussion.
#
# Arguments:
#   1. sample: audio sample
#   2. rms_avg: root mean square average (energy) of the current sample
#   3. rms_last: RMS energy of the last sample
# Return:
#   1. b3: boolean state of LED3. 1 if mid-low tone percussion is present, else 0.
#
def calc_led_state_b3(sample, rms_avg, rms_last):
    # General energy delta detection / guitar strum
    # If the RMS energy of the current sample is greater than the last sample, turn on red LED (indicates rhythm)
    b3 = (rms_last) and ((rms_avg - rms_last) > 10)
    b3 = int(b3)
    # check that the volume is above some threshold for dramatic effect
    b3 = b3 and np.median(np.abs(sample)) > 4000
    return b3

# calc_led_state_b4(sample, rms_avg, rms_last)
#   Determine whether to turn on LED4.
#   LED4: Large green LED. Maps to snare drum.
#
# Arguments:
#   1. sample: audio sample
#   2. rms_avg: root mean square average (energy) of the current sample
#   3. rms_last: RMS energy of the last sample
# Return:
#   1. b4: boolean state of LED4. 1 if snare drum or large energy delta is detected, else 0.
#
def calc_led_state_b4(sample, rms_avg, rms_last):
    # If delta in energy is above some threshold,
    # there was a spike in energy, e.g. snare drum
    b4 = (rms_last) and ((rms_avg - rms_last) > 70)
    # check if audio volume is above some threshold
    b4 = b4 or (np.max(sample) > 20000 and ((rms_avg - rms_last) > 30))
    return b4

# calc_led_state_b5(sample, fft, rms_avg, rms_last)
#   Determine whether to turn on LED5.
#   LED5: Large blue LED. Maps to bass drum.
#
# Arguments:
#   1. sample: audio sample
#   2. fft: DFT of the current audio sample
#   3. rms_avg: root mean square average (energy) of the current sample
#   4. rms_last: RMS energy of the last sample
# Return:
#   1. b5: boolean state of LED5. 1 if bass drum is detected, else 0.
#
def calc_led_state_b5(sample, fft, rms_avg, rms_last):
    # Extract the lower 4 FFT coefficients which represent bass frequencies (20-60 hz)
    bass = fft[2:4]
    # Extract energy of bass coefficients
    bass = np.sum(np.sqrt(np.abs(bass)))
    # Test if there is significant bass presence in sample, and also whether volume is above some threshold
    b5 = (bass > 1000) and ((rms_avg - rms_last) > 0) and np.median(np.abs(sample)) > 4000
    return b5

#  main(ug, fs, data, step)
#   1. ug: UART device class
#   2. fs: sample rate of input audio data in Hz
#   2. data: numpy array of input audio data
#   3. step: user-defined audio sample size
def main(ug, fs, data, step):
    audio = data[:,1] # force mono stereo by only extracting right side

    #ug.send_frame(UART_COMMAND_LED, 0) # turn all LEDs off
    ug.send_frame(node="daq", cmd=0x30, data=0)
    playsound.playsound(filename, False) # start playing music in background

    # initialize loop counter variables
    rms_last = 0
    # main loop iterating over audio in sample size intervals
    for n in tqdm(range(len(audio) // step)): # iterate over audio
        # start counter to calculate time delta
        start = time.time()
        sample = audio[(n)*step:(n+1)*step] # extract audio sample

        # perform DFT over audio sample
        fft = np.fft.fft(sample)
        # calculate RMS energy
        rms_avg = calc_rms_avg(fft, step)

        # calculate the LED states for each LED
        b0 = calc_led_state_b0(fft, fs, step)
        b1 = calc_led_state_b1(fft)
        b2 = calc_led_state_b2(sample, rms_avg, rms_last)
        b3 = calc_led_state_b3(sample, rms_avg, rms_last)
        b4 = calc_led_state_b4(sample, rms_avg, rms_last)
        b5 = calc_led_state_b5(sample, fft, rms_avg, rms_last)
        rms_last = rms_avg # store value to use in next frame

        # pack the 6 LED states into a single command to the MCU
        data = b5 << 5 | b4 << 4 | b3 << 3 | b2 << 2 | b1 << 1 | b0 << 0
        ug.send_frame(node="daq", cmd=0x30, data=int(data))

        # end counter to calculate time delta
        end = time.time()
        # sleep for the length of the sample - time it took to calculate/send to the device
        # so we are in sync with music playing in the background
        # duration of calculation must be > sample length else time.sleep() is negative and errors
        time.sleep((1 / (fs / step)) - (end - start))

    ug.send_frame(node="daq", cmd=0x30, data=0) # turn all LEDs off again

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", default='',
        help="path to device e.g. /dev/ttyUSB0, COM7",)
    parser.add_argument("-b", "--baud", default=115200, type=int,
        help="UART baud rate (default 115200)",)
    parser.add_argument("-l", "--link", default='',
        help="Link to youtube video",)
    parser.add_argument("-s", "--step", default=2048, type=int,
        help="FFT sample rate (default 2048)",)
    parser.add_argument('-v', "--verbose", action='store_true',
        help="verbose",
    )

    args = parser.parse_args()
    #ug = UARTGateway()
    #ug.connect(args.device, args.baud)
    ug = CANBus(verbose=args.verbose)
    ug.connect("tcp")

    # error checking
    if (not ug.is_connected()):
        raise ValueError("Failed to find UART device, hardware noy set up correctly")
    if (args.baud <= 0):
        raise ValueError("Baud rate must be a positive integer")
    if (args.step <= 0 or args.step & 1):
        raise ValueError("FFT size must be a positive integer divisible by 2")

    if (args.link):
        filename = download_youtube_audio(args.link, "out")
    else: # dry run
        filename = "out.wav"
    fs, data = open_audio_wav(filename)
    main(ug, fs, data, args.step)
