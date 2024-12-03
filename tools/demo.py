import numpy as np
from scipy.io import wavfile
import playsound
np.set_printoptions(suppress=True)
import yt_dlp
import os
import tqdm
import argparse

from uart import UARTGateway

UART_COMMAND_LED = 0x1

def download_wav(link, outfile="out"):
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

def calc_rms_avg(fft, step):
    fft_re = 2 / step * np.abs(fft)
    rms_avg = np.sqrt(np.mean(fft_re ** 2))
    return rms_avg

def calc_b0(fft):
    # bin_width = rate / fft.size
    # Midrange cut: 800 Hz–2.5 kHz, important for standing out in the mix
    # Presence and sparkle: 2.5 kHz–8 kHz, critical for articulation and note definition
    # 7.8125*250 = 1953.125
    midrange = fft[250:500] # 400Hz
    b0 = np.sum(np.sqrt(np.abs(midrange))) > 100000
    return b0

def calc_b1(fft):
    hist, bin_edges = np.histogram(np.abs(fft), bins=7)
    b1 = bin_edges[1] > 400000 and bin_edges[1] < 1000000 # guitar frequency
    return b1

def calc_b3(rms_avg, rms_last):
    # general energy delta detection / guitar strum
    b3 = (rms_last) and ((rms_avg - rms_last) > 10)
    return b3

def calc_b4(sample, rms_avg, rms_last):
    # b4: snare drum / large energy delta
    b4 = (rms_last) and ((rms_avg - rms_last) > 70)
    b4 = b4 or (np.max(sample) > 20000 and ((rms_avg - rms_last) > 30))
    return b4

def calc_b5(fft, rms_avg, rms_last, sample):
    bass = fft[2:4] # rate 16000, bass 20-60 hz
    bass = np.sum(np.sqrt(np.abs(bass))) # get energy
    b5 = (bass > 1000) and ((rms_avg - rms_last) > 0) and np.median(np.abs(sample)) > 4000
    return b5

def main(ug, filename, step):
    fs, data = wavfile.read(filename)
    signal = data[:,1] # force mono

    ug.send_frame(UART_COMMAND_LED, 0) # turn LEDs off
    playsound.playsound(filename, False) # play sound

    rms_last = 0
    for n in tqdm(range(len(signal) // step)): # iterate over audio
        start = time.time()
        sample = signal[(n)*step:(n+1)*step] # extract audio sample

        # perform DFT over audio sample
        fft = np.fft.fft(sample)
        # calculate RMS energy
        rms_avg = calc_rms_avg(fft, step)

        # calculate the LED states for each LED
        b0 = calc_b0(fft)
        b1 = calc_b1(fft)
        b2 = calc_b3(rms_avg, rms_last)
        b3 = calc_b3(rms_avg, rms_last)
        b4 = calc_b4(sample, rms_avg, rms_last)
        b5 = calc_b5(fft, rms_avg, rms_last, sample)
        rms_last = rms_avg # set value for next frame

        # pack the 6 LED states into a single command to the MCU
        data = b5 << 5 | b4 << 4 | b3 << 3 | b2 << 2 | b1 << 1 | b0 << 0
        ug.send_frame(UART_COMMAND_LED, data)

        end = time.time()
        # sleep for the length of the sample - time it took to calculate/send to sync with music playing in the background
        # duration of calculation must be > sample length else time.sleep() is negative and errors
        time.sleep((1 / (fs / step)) - (end - start))

    ug.send_frame(UART_COMMAND_LED, 0) # turn LEDs off again

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

    args = parser.parse_args()
    ug = UARTGateway()
    ug.connect(args.device, args.baud)
    assert(ug.is_connected())

    if (args.link):
        path = "https://www.youtube.com/watch?v=J5o8Daw1ZsY" # megadeth holy wars 1900
        path = "https://www.youtube.com/watch?v=Lt4UALOsxNY" # brainstew
        path = "https://www.youtube.com/watch?v=o3WdLtpWM_c" # fisher losing it 3600
        path = "https://www.youtube.com/watch?v=E0ozmU9cJDg" # master of puppets 1900
        path = "https://www.youtube.com/watch?v=r7cWi41XGCM" # slayer angel of death 1600
        path = "https://www.youtube.com/watch?v=jqnC54vbUbU" # slayer 1600
        path = "https://www.youtube.com/watch?v=3mbvWn1EY6g"
        path = "https://www.youtube.com/watch?v=pxuYPE84u_E" # acdc thunderstruck 1900
        path = "https://www.youtube.com/watch?v=NjCzxjLLc3g" # darude sandstorm
        path = "https://www.youtube.com/watch?v=K3o6qWXd8qQ" # sweet escape
        path = args.link
        filename = download_wav(path, "out")
    else:
        filename = "out.wav"
    main(ug, filename, args.step)
