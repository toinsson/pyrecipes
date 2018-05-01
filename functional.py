import time

import numpy as np
import pandas as pd


class AxisFilter(object):
    """Filter an axis with given time step, fits a polynomial of given order and returns
    approximate derivatives up to deriv order.

    Args:
        stepsize (int): time step in ms, should be an integer, minimum value is 1.
        window_length (int): length of the window over which to fit the polynom, odd number.
        polyorder (int): order of the polynomial to fit.
        derivative_number (int): number of derivatives of the signals to return.
    """
    def __init__(self, stepsize=10, window_length=11, polyorder=3, derivative_number=1, **kwargs):
        super(AxisFilter, self).__init__()

        self.stepsize = stepsize
        self.window_length = window_length
        self.polyorder = polyorder
        self.derivative_number = derivative_number

        # perform constant time sampling through linear interpolation
        self.si = StepInterpolator(stepsize)

        # low-pass filter
        self.lpf = LowPassFilter(**kwargs)

        # we do not compensate for h in sgf
        self.sgf = SavitskyGolayFitter(window_length, polyorder, derivative_number)


    def new_sample(self, time, value):
        """Filter a new sample.

        Args:
            time (): timestamp in ms
            value (): value at the timestamp

        Returns:

        """
        interp = self.si.new_sample(time, value)

        ns = np.zeros((0,self.derivative_number + 2)) # 0th order is 1 sample, and add time stamp

        for t, point in interp:
            point = self.lpf.new_sample(point)
            ns = np.vstack([ns, np.r_[t, self.sgf.new_sample(point)]])

        return ns


class StepInterpolator(object):
    """Interpolate linearly between 2 sample at constant step size.

    The step size is an integer with smallest value 1.
    If the new sample is further than stepsize, then return empty.
    """
    def __init__(self, stepsize):
        self.stepsize = stepsize
        self.firstpoint = True

        self.last_time = 0
        self.last_value = 0
        self.time_steps = np.zeros(1)
        self.value_steps = np.zeros(1)

    def new_sample(self, time, value):

        starttime = self.last_time + (self.stepsize - self.last_time)%self.stepsize
        endtime = time

        self.time_steps = np.arange(starttime, endtime, self.stepsize)
        self.value_steps = np.interp(self.time_steps, [self.last_time, time], [self.last_value, value])

        self.last_time = time
        self.last_value = value

        return np.c_[self.time_steps, self.value_steps]


import scipy.signal
class LowPassFilter(object):
    """docstring for ClassName"""
    def __init__(self, lowcut=15, sampling_frequency=50, order=5):
        super(LowPassFilter, self).__init__()

        def _butter_lowpass(lowcut, sampling_frequency, order=5):
            order = order
            fs = sampling_frequency
            nyq = 0.5 * fs
            low = lowcut / nyq
            b, a = scipy.signal.butter(order, low, btype='low')
            return b,a

        b,a = _butter_lowpass(lowcut, sampling_frequency, order)
        self.iir = IIRFilter(b,a)

    def new_sample(self, x):
        return self.iir.new_sample(x)


class IIRFilter(object):
    def __init__(self, B, A):
        """Create an IIR filter, given the B and A coefficient vectors.
        """
        self.B = B
        self.A = A
        self.prev_outputs = RingBuffer(len(A)-1)
        self.prev_inputs = RingBuffer(len(B))

    def filter(self, x):
        """Take one sample and filter it. Return the output.
        """
        y = 0
        self.prev_inputs.new_sample(x)

        prev_inputs = self.prev_inputs.samples.reshape(-1)
        prev_outputs = self.prev_outputs.samples.reshape(-1)

        num = self.B * prev_inputs[::-1]
        den = self.A[1:] * prev_outputs[::-1]

        y = (num.sum() - den.sum()) / self.A[0]
        self.prev_outputs.new_sample(y)

        return y

    def new_sample(self, x):
        return self.filter(x)


class SavitskyGolayFitter(object):
    """Fit a polynome of order polyorder on a window of length window_length and returns
    the derivatives deriv of the polynome at the middle point.

    https://en.wikipedia.org/wiki/Savitzky%E2%80%93Golay_filter

    Let us have n points (xi, yi) equally spaced with distance h. We define z as:
    z = (x - x.mean()) / h

    We want to fit a polynome of polyorder k onto m points, such that:
    Y = a0 + a1.z + a2.z**2 + ... + ak.z**k

    The coefficents ak solves:
    a = J-1 * y

    where J is defined as:
    J.shape = window_length, polyorder+1
    Ji = 1, zi, zi**2, ..., zi**k

    and gives:
    Y = J-1 * z

    then:
    Y(z=0)    = a0
    Y'(z=0)   = a1/h
    Y''(z=0)  = 2a2/h**2
    Y'''(z=0) = 6a3/h**3

    Note that we just return the coefficient ax, and note the multiplying constant.

    example:
    k = 3, m = 5
    z = -2, -1, 0, 1, 2
    J = [[1, -2, 4, 8
          1, -1, 1, -1
          1, 0, 0, 0
          1, 1, 1, 1
          1, 2, 4, 8
        ]]

    """
    def __init__(self, window_length, polyorder, deriv=0, stepsize=None):
        super(SavitskyGolayFitter, self).__init__()

        assert ((window_length % 2) != 0), "window_length must be odd"
        assert (window_length >= (polyorder + 2)), \
        "window_length too small for polyorder: {} >= ({} + 2)".format(window_length, polyorder)
        assert (deriv <= polyorder), "the polynom order has to be greater than the derivative order."


        self.window_length = window_length
        self.polyorder = polyorder
        self.deriv = deriv

        self.rb = RingBuffer(window_length)

        # compute and store the convolution coefficients
        number_coeffs = polyorder + 1
        half_window = (window_length-1)//2
        J = np.array([
            [k**i for i in range(number_coeffs)]
            for k in range(-half_window, half_window+1)
            ])
        J_1 = np.linalg.pinv(J)
        self.conv_coeffs = J_1[:deriv+1]

        # # compute the derivative multiplying constants
        # if stepsize:
        #     deriv_constant = np.array([1, 1./stepsize, 2./stepsize**2, 6./stepsize**3])
        #     deriv_constant = np.hstack([deriv_constant, np.ones(window_length)])
        #     deriv_constant = deriv_constant[:deriv+1]
        # else:
        # deriv_constant = np.ones(deriv+1)
        # self.deriv_constant = deriv_constant

    def new_sample(self, x):
        """Add a new sample to the ring buffer and returns the derivatives up to deriv order.
        Note that the derivatives are computed on a window which implements a time delay of
        window_length/2 samples.
        """
        _ = self.rb.write(x)
        derivs = np.dot(self.conv_coeffs, self.rb.samples.reshape(-1)) # * self.deriv_constant
        return derivs[:self.deriv+1]



class RingBuffer(object):
    """Implements a ring buffer of size (n,m).

    dtype can contain named columns.
    """
    def __init__(self, size, init=0, columns=None):

        if type(size) == int:
            size = (size,1)

        self.n_samples = size[0]

        self.columns = columns

        # if (dtype is not None):
        #     self._samples = np.zeros(size[0], dtype=dtype)
        # else:
        self._samples = np.zeros(size)

        self.read_head = 1
        self.write_head = 0
        self.sum = 0

    def write(self, x):
        self.new_sample(x)
    def new_sample(self, x):
        """Write x at write position and return previous sample in place.
        """
        s = self._samples[self.write_head]
        self._samples[self.write_head] = x

        self.read_head += 1
        self.write_head += 1
        self.read_head %= self.n_samples
        self.write_head %= self.n_samples

        return s

    def __getitem__(self, value):
        # could implement slice
        return self._forward_index(value-1)

    def _reverse_index(self, i):
        new_index = self.write_head-i-1
        while new_index<0:
            new_index+=self.n_samples
        return self.samples[new_index]

    def _forward_index(self, i):
        new_index = self.read_head+i-1
        new_index = new_index % self.n_samples
        return self._samples[new_index]

    @property
    def last(self):
        return self._samples[self.write_head-1]

    @property
    def samples(self):
        """Returns the samples as a numpy array."""
        return np.vstack((self._samples[self.read_head-1:],self._samples[0:self.read_head-1]))

    @property
    def samples_df(self):
        """Returns the samples as a pandas dataframes with named columns."""
        return pd.DataFrame(np.vstack((self._samples[self.read_head-1:],self._samples[0:self.read_head-1])), columns=self.columns)

    @property
    def size(self):
        return self.n_samples


