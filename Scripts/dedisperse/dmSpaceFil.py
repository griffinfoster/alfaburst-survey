#!/usr/bin/env python

"""
Generate a DM-space plot by dedispersing a filterbank file over a range of test DMs
"""

import sys,os
import numpy as np
import cPickle as pickle

import dedispersion # https://fornax.phys.unm.edu/lwa/trac/browser/trunk/lsl/lsl/misc/dedispersion.py
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
    o.add_option('-d', '--dm', dest='dm', default='0_100',
        help='Despersion Measure test range, default: 0_100')
    o.add_option('--nodisplay', dest='nodisplay', action='store_true',
        help='Do not display figures')
    o.add_option('-S', '--savefig', dest='savefig', default=None,
        help='Save figure to filename')
    o.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Verbose output')
    o.add_option('--cmap', dest='cmap', default='viridis',
        help='plotting colormap, default: viridis')
    o.add_option('-s', '--start', dest='start_time', type='float', default=None,
        help='Start time to plot/save in seconds, default: None')
    o.add_option('-w', '--window', dest='time_window', type='float', default=None,
        help='Time window to plot/save, default: None')
    o.add_option('-t', '--time', dest='timeFactor', type='int', default=1,
        help='Average in time by N samples, similar to SIGPROC decimate -t option')
    o.add_option('--dark', dest='dark', action='store_true',
        help='Plot with a dark background style')
    opts, args = o.parse_args(sys.argv[1:])

    fil = filterbankio.Filterbank(args[0])

    tInt = fil.header['tsamp'] # get tInt
    freqsHz = fil.freqs * 1e6 # generate array of freqs in Hz

    waterfall = np.reshape(fil.data, (fil.data.shape[0], fil.data.shape[2])) # reshape to (n integrations, n freqs)

    if np.isnan(waterfall).any(): waterfall = np.nan_to_num(waterfall).astype('float64')

    if not opts.timeFactor is None: # average down by N time samples
        if waterfall.shape[0] % opts.timeFactor==0:
            waterfall = waterfall.reshape(waterfall.shape[0]/opts.timeFactor, opts.timeFactor, waterfall.shape[1]).sum(axis=1)
            tInt *= opts.timeFactor
        else:
            print 'WARNING: %i time samples is NOT divisible by %i, zero-padding spectrum to usable size'%(waterfall.shape[0], opts.timeFactor)
            zeros = np.zeros((opts.timeFactor - (waterfall.shape[0] % opts.timeFactor), waterfall.shape[1]))
            waterfall = np.concatenate((waterfall, zeros))
            waterfall = waterfall.reshape(waterfall.shape[0]/opts.timeFactor, opts.timeFactor, waterfall.shape[1]).sum(axis=1)
            tInt *= opts.timeFactor

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

    dmRange = opts.dm.split('_')
    minDM = float(dmRange[0])
    maxDM = float(dmRange[1])
    if len(dmRange) == 3:
        testDMs = np.arange(minDM, maxDM, int(dmRange[2]))
    else:
        testDMs = np.arange(minDM, maxDM)

    dmSpace = np.zeros((testDMs.shape[0], waterfall.shape[0]))
    print dmSpace.shape
    for dmid, dm in enumerate(testDMs):
        dmSpace[dmid, :] = np.sum(dedispersion.incoherent(freqsHz, waterfall, tInt, dm, boundary='wrap'), axis=1)

    if not opts.nodisplay or opts.savefig:
        if opts.dark: plt.style.use('dark_background')
        fig = plt.figure(figsize=(12,8)) # (width, height)

        plt.imshow(np.flipud(dmSpace), aspect='auto', extent=(0, tInt*waterfall.shape[0], testDMs[0], testDMs[-1]), cmap=plt.get_cmap(opts.cmap), interpolation='nearest')
        plt.ylabel('DM')
        plt.xlabel('t (s)')
        plt.title(args[0])
        plt.colorbar(fraction=0.025)

    if opts.savefig: plt.savefig(opts.savefig)
    if not opts.nodisplay: plt.show()

