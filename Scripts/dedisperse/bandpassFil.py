#!/usr/bin/env python

"""
Plot the bandpass of a filterbank file
"""

import sys,os
import numpy as np

import filterbankio # extracted from https://github.com/UCBerkeleySETI/filterbank

# Check if $DISPLAY is set (for handling plotting on remote machines with no X-forwarding)
if os.environ.has_key('DISPLAY'):
    import matplotlib.pyplot as plt
else:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] FIL')
    o.set_description(__doc__)
    o.add_option('--nodisplay', dest='nodisplay', action='store_true',
        help='Do not display figures')
    o.add_option('-S', '--savefig', dest='savefig', default=None,
        help='Save figure to filename')
    o.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Verbose output')
    o.add_option('-s', '--start', dest='start_time', type='float', default=None,
        help='Start time to plot/save in seconds, default: None')
    o.add_option('-w', '--window', dest='time_window', type='float', default=None,
        help='Time window to plot/save, default: None')
    o.add_option('--write', dest='write', action='store_true',
        help='Write bandpass to text file with prefix set by --prefix option')
    o.add_option('--prefix', dest='prefix', default='bandpass',
        help='Prefix of files to write bandpass to, default: bandpass')
    o.add_option('--minmax', dest='minmax', action='store_true',
        help='Plot the min/max bounds')
    opts, args = o.parse_args(sys.argv[1:])
    
    if not opts.nodisplay or opts.savefig:
        fig = plt.figure(figsize=(12,6)) # (width, height)

    for fbIdx, fbFn in enumerate(args):
        fil = filterbankio.Filterbank(fbFn)

        tInt = fil.header['tsamp'] # get tInt
        freqsHz = fil.freqs * 1e6 # generate array of freqs in Hz

        waterfall = np.reshape(fil.data, (fil.data.shape[0], fil.data.shape[2])) # reshape to (n integrations, n freqs)

        # Select time subsets to plot and save to file
        if opts.start_time is None:
            startIdx = 0
        else:
            startIdx = int(opts.start_time / tInt)
            if startIdx > waterfall.shape[0]:
                print 'Error: start time (-s) is beyond the maximum time (%f s) of the filterbank, exiting'%(waterfall.shape[0] * tInt)
                exit()

        if opts.time_window is None:
            endIdx = waterfall.shape[0]
        else:
            endIdx = startIdx + int(opts.time_window / tInt)
            if endIdx > waterfall.shape[0]:
                print 'Warning: time window (-w) in conjunction with start time (-s) results in a window extending beyond the filterbank file, clipping to maximum size'
                endIdx = waterfall.shape[0]

        waterfall = waterfall[startIdx:endIdx,:]
        meanBandpass = np.mean(waterfall, axis=0)
        maxBandpass = np.min(waterfall, axis=0)
        minBandpass = np.max(waterfall, axis=0)

        if not opts.nodisplay or opts.savefig:

            if opts.minmax: plt.fill_between(fil.freqs, minBandpass, maxBandpass, alpha=0.1, edgecolor='none')
            plt.plot(fil.freqs, meanBandpass)
            plt.xlim(fil.freqs[0], fil.freqs[-1])

        if opts.write:
            # write bandpass to a text file
            outFn = opts.prefix + str(fbIdx) + '.dat'
            print 'Writing bandpass of %s to %s'%(fbFn, outFn)
            np.savetxt(outFn, bandpass, fmt='%.10f')
    
    if not opts.nodisplay or opts.savefig:
        plt.title('Bandpass')
        plt.xlabel('Freq. (MHz)')
        plt.ylabel('Amp')

    if opts.savefig: plt.savefig(opts.savefig)
    if not opts.nodisplay: plt.show()

