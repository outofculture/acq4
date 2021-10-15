import numpy
import scipy.signal

from acq4.devices.Device import Device


class BaseDAQ(Device):
    @staticmethod
    def downsample(data, ds, method, **kargs):
        if method == 'subsample':
            data = data[::ds].copy()

        # MC: this code is broke: no `res`
        # elif method == 'mean':
        #     # decimate by averaging points together (does not remove HF noise, just folds it down.)
        #     if res['info']['type'] in ['di', 'do']:
        #         data = NiDAQ.meanResample(data, ds, binary=True)
        #     else:
        #         data = NiDAQ.meanResample(data, ds)

        elif method == 'fourier':
            # Decimate using fourier resampling -- causes ringing artifacts, very slow to compute (possibly uses butterworth filter?)
            newLen = int(data.shape[0] / ds)
            data = scipy.signal.resample(data, newLen, window=8)  # Use a kaiser window with beta=8

        elif method == 'bessel_mean':
            # Lowpass, then average. Bessel filter has less efficient lowpass characteristics and filters some of the passband as well.
            data = BaseDAQ.lowpass(data, 2.0 / ds, filter='bessel', order=4, bidir=True)
            data = BaseDAQ.meanResample(data, ds)

        elif method == 'butterworth_mean':
            # Lowpass, then average. Butterworth filter causes ringing artifacts.
            data = BaseDAQ.lowpass(data, 1.0 / ds, bidir=True, filter='butterworth')
            data = BaseDAQ.meanResample(data, ds)

        elif method == 'lowpass_mean':
            # Lowpass, then average. (for testing)
            data = BaseDAQ.lowpass(data, **kargs)
            data = BaseDAQ.meanResample(data, ds)

        return data

    @staticmethod
    def meanResample(data, ds, binary=False):
        """Resample data by taking mean of ds samples at a time"""
        newLen = int(data.shape[0] / ds) * ds
        data = data[:newLen]
        data.shape = (int(data.shape[0] / ds), ds)
        if binary:
            data = data.mean(axis=1).round().astype(numpy.byte)
        else:
            data = data.mean(axis=1)
        return data

    @staticmethod
    def lowpass(data, cutoff, order=4, bidir=True, filter='bessel', stopCutoff=None, gpass=2., gstop=20.,
                samplerate=None):
        """Bi-directional bessel/butterworth lowpass filter"""
        if samplerate is not None:
            cutoff /= 0.5 * samplerate
            if stopCutoff is not None:
                stopCutoff /= 0.5 * samplerate

        if filter == 'bessel':
            ## How do we compute Wn?
            ### function determining magnitude transfer of 4th-order bessel filter
            # from scipy.optimize import fsolve

            # def m(w):
            # return 105. / (w**8 + 10*w**6 + 135*w**4 + 1575*w**2 + 11025.)**0.5
            # v = fsolve(lambda x: m(x)-limit, 1.0)
            # Wn = cutoff / (sampr*v)
            b, a = scipy.signal.bessel(order, cutoff, btype='low')
        elif filter == 'butterworth':
            if stopCutoff is None:
                stopCutoff = cutoff * 2.0
            ord, Wn = scipy.signal.buttord(cutoff, stopCutoff, gpass, gstop)
            # print "butterworth ord %f   Wn %f   c %f   sc %f" % (ord, Wn, cutoff, stopCutoff)
            b, a = scipy.signal.butter(ord, Wn, btype='low')
        else:
            raise Exception('Unknown filter type "%s"' % filter)

        padded = numpy.hstack(
            [data[:100], data, data[-100:]])  ## can we intelligently decide how many samples to pad with?

        if bidir:
            data = scipy.signal.lfilter(b, a, scipy.signal.lfilter(b, a, padded)[::-1])[::-1][
                   100:-100]  ## filter twice; once forward, once reversed. (This eliminates phase changes)
        else:
            data = scipy.signal.lfilter(b, a, padded)[100:-100]
        return data

    @staticmethod
    def denoise(data, radius=2, threshold=4):
        """Very simple noise removal function. Compares a point to surrounding points,
        replaces with nearby values if the difference is too large."""

        r2 = radius * 2
        d2 = data[radius:] - data[:-radius]  # a derivative
        stdev = d2.std()
        mask1 = d2 > stdev * threshold  # where derivative is large and positive
        mask2 = d2 < -stdev * threshold  # where derivative is large and negative
        maskpos = mask1[:-radius] * mask2[radius:]  # both need to be true
        maskneg = mask1[radius:] * mask2[:-radius]
        mask = maskpos + maskneg
        d5 = numpy.where(mask, data[:-r2], data[
                                           radius:-radius])  # where both are true replace the value with the value from 2 points before
        d6 = numpy.empty(data.shape, dtype=data.dtype)  # add points back to the ends
        d6[radius:-radius] = d5
        d6[:radius] = data[:radius]
        d6[-radius:] = data[-radius:]
        return d6