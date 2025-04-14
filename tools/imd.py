import numpy as np
from scipy import signal
from scipy.fftpack import fft, ifft

def autocorrelation(x):
    xp = ifftshift((x - np.average(x))/np.std(x))
    n, = xp.shape
    xp = np.r_[xp[:n//2], np.zeros_like(xp), xp[n//2:]]
    f = fft(xp)
    p = np.absolute(f)**2
    pi = ifft(p)
    return np.real(pi)[:n//2]/(np.arange(n//2)[::-1]+n//2)

t = np.linspace(0, 1, 256, endpoint=False)
sig = np.sin(2 * np.pi * t)
pwm = signal.square(2 * np.pi * t * 5, duty=(sig + 1)/2)
print(pwm)
x = np.fft.fft(pwm)
auto = autocorrelation(x)
print(auto)

