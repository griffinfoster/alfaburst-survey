#!/usr/bin/env python

"""
Plot a filterbank file
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
    o.add_option('--cmap', dest='cmap', default='magma',
        help='plotting colormap, default: magma')
    o.add_option('-s', '--start', dest='start_time', type='float', default=None,
        help='Start time to plot/save in seconds, default: None')
    o.add_option('-w', '--window', dest='time_window', type='float', default=None,
        help='Time window to plot/save, default: None')
    o.add_option('-t', '--time', dest='timeFactor', type='int', default=None,
        help='Average in time by N samples, similar to SIGPROC decimate -t option')
    o.add_option('-f', '--freq', dest='freqFactor', type='int', default=1,
        help='Average in freq by N samples')
    o.add_option('--dark', dest='dark', action='store_true',
        help='Plot with a dark background style')
    opts, args = o.parse_args(sys.argv[1:])

    fil = filterbankio.Filterbank(args[0])

    tInt = fil.header['tsamp'] # get tInt
    freqsHz = fil.freqs * 1e6 # generate array of freqs in Hz

    waterfall = np.reshape(fil.data, (fil.data.shape[0], fil.data.shape[2])) # reshape to (n integrations, n freqs)

    if np.isnan(waterfall).any(): waterfall = np.nan_to_num(waterfall).astype('float64')

    if not opts.timeFactor is None: # average down by N time samples, waterfall.shape[0] must be divisible by N
        if waterfall.shape[0] % opts.timeFactor==0:
            waterfall = waterfall.reshape(waterfall.shape[0]/opts.timeFactor, opts.timeFactor, waterfall.shape[1]).sum(axis=1)
            tInt *= opts.timeFactor
        else:
            print 'WARNING: %i time samples is NOT divisible by %i, zero-padding spectrum to usable size'%(waterfall.shape[0], opts.timeFactor)
            zeros = np.zeros((opts.timeFactor - (waterfall.shape[0] % opts.timeFactor), waterfall.shape[1]))
            waterfall = np.concatenate((waterfall, zeros))
            waterfall = waterfall.reshape(waterfall.shape[0]/opts.timeFactor, opts.timeFactor, waterfall.shape[1]).sum(axis=1)
            tInt *= opts.timeFactor

    if not opts.freqFactor is None: # average down by N frequency channels, waterfall.shape[1] must be divisible by N
        if waterfall.shape[1] % opts.freqFactor==0:
            print waterfall.shape
            waterfall = waterfall.reshape(waterfall.shape[0], waterfall.shape[1]/opts.freqFactor, opts.freqFactor).sum(axis=2)
            freqsHz = freqsHz[::opts.freqFactor]
        else:
            print 'WARNING: %i frequency channels is NOT divisible by %i, ignoring option'%(waterfall.shape[1], opts.freqFactor)

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

    waterfall = waterfall[startIdx:endIdx]

    if not opts.nodisplay or opts.savefig:

        if opts.dark:
            plt.style.use('dark_background')

        fig = plt.figure(figsize=(12,8)) # (width, height)

        imRaw = plt.imshow(np.flipud(waterfall.T), extent=(0, tInt*waterfall.shape[0], fil.freqs[0], fil.freqs[-1]), aspect='auto', cmap=plt.get_cmap(opts.cmap), interpolation='nearest')
        plt.ylabel('MHz')
        plt.title(args[0].split('/')[-1])
        plt.xlabel('seconds')
        #cax = fig.add_axes([0.75, 0.865, 0.15, 0.01])
        cax = fig.add_axes([0.75, .95, 0.15, 0.03])
        cbar = fig.colorbar(imRaw, cax=cax, orientation='horizontal')
        cbar.ax.set_xticklabels(cbar.ax.get_xticklabels(), rotation='vertical', fontsize=8)


    if opts.savefig: plt.savefig(opts.savefig)
    if not opts.nodisplay: plt.show()

