
import numpy as np

import scipy
def plot_fft(signal, sampling_period, ax):
    # Number of samplepoints
    N = signal.shape[0]
    # sample spacing
    T = sampling_period

    x = np.linspace(0.0, N*T, N)
    y = signal

    yf = scipy.fftpack.fft(y)
    xf = np.linspace(0.0, 1.0/(2.0*T), N/2)

    ax.plot(xf, 2.0/N * np.abs(yf[:N//2]))


def autocorr(x):
    result = np.correlate(x, x, mode='full')
    return result[int(result.size/2):] / result[int(result.size/2)]