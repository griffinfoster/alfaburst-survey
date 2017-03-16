#!/usr/bin/env python

"""
Dedisperse a filterbank file. Generate figures and/or time series (.tim) file

TODO: output tim
"""

import sys,os
import numpy as np

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
    o.add_option('-d', '--dm', dest='dm', default=0., type='float',
        help='Despersion Measure to correct, default: 0.')
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
    opts, args = o.parse_args(sys.argv[1:])

    dm = opts.dm

    fil = filterbankio.Filterbank(args[0])

    tInt = fil.header['tsamp'] # get tInt
    freqsHz = fil.freqs * 1e6 # generate array of freqs in Hz
    
    waterfall = np.reshape(fil.data, (fil.data.shape[0], fil.data.shape[2])) # reshape to (n integrations, n freqs)
    ddwaterfall = dedispersion.incoherent(freqsHz, waterfall, tInt, dm, boundary='wrap') # apply dedispersion

    timeSeries = np.sum(ddwaterfall, axis=1)

    normTimeSeries = (timeSeries - np.mean(timeSeries))/np.std(timeSeries)

    # Select time subsets to plot and save to file
    if opts.start_time is None:
        startIdx = 0
    else:
        startIdx = int(opts.start_time / tInt)
        if startIdx > timeSeries.shape[0]:
            print 'Error: start time (-s) is beyond the maximum time (%f s) of the filterbank, exiting'%(timeSeries.shape[0] * tInt)
            exit()

    if opts.time_window is None:
        endIdx = timeSeries.shape[0]
    else:
        endIdx = startIdx + int(opts.time_window / tInt)
        if endIdx > timeSeries.shape[0]:
            print 'Warning: time window (-w) in conjunction with start time (-s) results in a window extending beyond the filterbank file, clipping to maximum size'
            endIdx = timeSeries.shape[0]

    timeSeries = timeSeries[startIdx:endIdx]
    waterfall = waterfall[startIdx:endIdx,:]
    ddwaterfall = ddwaterfall[startIdx:endIdx,:]

    if not opts.nodisplay or opts.savefig:

        fig = plt.figure(figsize=(12,8)) # (width, height)

        plt.subplot(3,1,1)
        imRaw = plt.imshow(np.flipud(waterfall.T), extent=(0, tInt*waterfall.shape[0], fil.freqs[0], fil.freqs[-1]), aspect='auto', cmap=plt.get_cmap(opts.cmap))
        plt.title('Raw')
        plt.ylabel('MHz')
        cax = fig.add_axes([0.75, 0.865, 0.15, 0.01])
        fig.colorbar(imRaw, cax=cax, orientation='horizontal')

        plt.subplot(3,1,2)
        imDedisp = plt.imshow(np.flipud(ddwaterfall.T), extent=(0, tInt*waterfall.shape[0], fil.freqs[0], fil.freqs[-1]), aspect='auto', cmap=plt.get_cmap(opts.cmap))
        plt.title('Dedispersed DM: %.0f'%dm)
        plt.ylabel('MHz')
        cax = fig.add_axes([0.75, 0.58, 0.15, 0.01])
        fig.colorbar(imDedisp, cax=cax, orientation='horizontal')
        
        plt.subplot(3,1,3)
        plt.plot(tInt*np.arange(waterfall.shape[0]), timeSeries)
        #plt.plot(tInt*np.arange(waterfall.shape[0]), normTimeSeries)
        plt.xlim(0, tInt*timeSeries.shape[0])
        plt.title('Time Series')
        plt.xlabel('seconds')
        plt.ylabel('Amp')

        plt.suptitle(args[0].split('/')[-1])

        plt.subplots_adjust(hspace=0.4)

    if opts.savefig: plt.savefig(opts.savefig)
    if not opts.nodisplay: plt.show()

