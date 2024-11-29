
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt

from canbus import CANBus
import can
import time
import librosa

def window_rms(a, window_size):
  a2 = np.power(a, 2)
  window = np.ones(window_size)/float(window_size)
  return np.sqrt(np.convolve(a2, window, 'valid'))

def get_b0(x):
    m = np.abs(np.median(x))
    b0 = int(m > 400 and np.max(x) > 5000)
    b1 = int(m > 60)

    fourier = np.fft.fft(x)
    FFT_data_real = 2/step*np.abs(fourier)
    rms_averaged = np.sqrt(np.mean(FFT_data_real**2))
    #print(rms_averaged)
    b2 = int(rms_averaged > 100)
    fourier = np.fft.fft(x)
    hist, bin_edges = np.histogram(np.abs(fourier), bins=6)
    x = (hist > 4).astype(np.uint8)
    data = x[5] << 5 | b0 << 4 | x[3] << 3 | x[2] << 2 | x[1] << 1 | b1 << 0
    return data

if 1:
    filename = "/home/eileen/Downloads/College/ENGR_133/project/Metallica-Master Of Puppets (Lyrics) [xnKhsTXoKCI].wav"
    samplerate, data = wavfile.read("/home/eileen/Downloads/College/ENGR_133/project/Metallica-Master Of Puppets (Lyrics) [xnKhsTXoKCI].wav")

    signal = data[:,1]

    step = 2048
    out = []
    for n in range(20):
        x = signal[(n)*step:(n+1)*step]
        fft = np.fft.fft(x)
        plt.plot(np.abs(fft)[:(fft.size//2 - 1)])
        plt.show()

        #print(hist)
        #print(bin_edges)
        #plt.plot(np.abs(fourier))
        #plt.show()
        #data = txmsg.encode({"cmd": 0x30, "data": b})
        #canbus.send_msg(can.Message(arbitration_id=txmsg.frame_id, data=data))
        #if (np.median(x) > 20000):
        #    out.append(x)
        #fourier = np.fft.fft(x)
        #fourier = np.abs(fourier)
        #
        #time.sleep(0.064) # 0.064
        #break
