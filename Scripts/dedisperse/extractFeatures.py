#!/usr/bin/env python

"""
Feature Extraction Script
"""

import sys,os
import numpy as np
import cPickle as pickle

import dedispersion # https://fornax.phys.unm.edu/lwa/trac/browser/trunk/lsl/lsl/misc/dedispersion.py
import filterbankio # extracted from https://github.com/UCBerkeleySETI/filterbank

## Check if $DISPLAY is set (for handling plotting on remote machines with no X-forwarding)
#if os.environ.has_key('DISPLAY'):
#    import matplotlib.pyplot as plt
#else:
#    import matplotlib
#    matplotlib.use('Agg')
#    import matplotlib.pyplot as plt

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] FIL')
    o.set_description(__doc__)
    o.add_option('-d', '--dm', dest='dm', default=0., type='float',
        help='Despersion Measure to correct, default: 0.')
    #o.add_option('--nodisplay', dest='nodisplay', action='store_true',
    #    help='Do not display figures')
    #o.add_option('-S', '--savefig', dest='savefig', default=None,
    #    help='Save figure to filename')
    o.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Verbose output')
    #o.add_option('--cmap', dest='cmap', default='magma',
    #    help='plotting colormap, default: magma')
    #o.add_option('-s', '--start', dest='start_time', type='float', default=None,
    #    help='Start time to plot/save in seconds, default: None')
    #o.add_option('-w', '--window', dest='time_window', type='float', default=None,
    #    help='Time window to plot/save, default: None')
    o.add_option('-t', '--time', dest='timeFactor', type='int', default=2,
        help='Average in time by N samples, similar to SIGPROC decimate -t option')
    o.add_option('-M', '--meta', dest='meta', default=None,
        help='Metadata pickle file used to print buffer stats, generated in generateDedispFigures.py')
    #o.add_option('--write', dest='write', action='store_true',
    #    help='Write dedispersed time series to text file')
    opts, args = o.parse_args(sys.argv[1:])

    dm = opts.dm

    fil = filterbankio.Filterbank(args[0])

    tInt = fil.header['tsamp'] # get tInt
    freqsHz = fil.freqs * 1e6 # generate array of freqs in Hz

    waterfall = np.reshape(fil.data, (fil.data.shape[0], fil.data.shape[2])) # reshape to (n integrations, n freqs)

    if waterfall.shape[0] != 32768: # expand array to be full size
        zeros = np.zeros((32768 - waterfall.shape[0], waterfall.shape[1]))
        waterfall = np.concatenate((waterfall, zeros))

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

    ddwaterfall = dedispersion.incoherent(freqsHz, waterfall, tInt, dm, boundary='wrap') # apply dedispersion

    ## Select time subsets to plot and save to file
    #if opts.start_time is None:
    #    startIdx = 0
    #else:
    #    startIdx = int(opts.start_time / tInt)
    #    if startIdx > waterfall.shape[0]:
    #        print 'Error: start time (-s) is beyond the maximum time (%f s) of the filterbank, exiting'%(waterfall.shape[0] * tInt)
    #        exit()

    #if opts.time_window is None:
    #    endIdx = waterfall.shape[0]
    #else:
    #    endIdx = startIdx + int(opts.time_window / tInt)
    #    if endIdx > waterfall.shape[0]:
    #        print 'Warning: time window (-w) in conjunction with start time (-s) results in a window extending beyond the filterbank file, clipping to maximum size'
    #        endIdx = waterfall.shape[0]

    ddTimeSeries = np.sum(ddwaterfall, axis=1)
    timeSeries = np.sum(waterfall, axis=1)
    #timeSeries = timeSeries[startIdx:endIdx]

    if not (opts.meta is None):
        metaData = pickle.load(open(opts.meta, "rb"))
    else:
        metaData = {}

    #######################
    # Feature Extraction

    def globalStats(arr):
        """Global Statistics of an array"""
        arrMedian = np.median(arr)
        arrMean = arr.mean()
        nPosCount = arr[arr > arrMedian].size
        nNegCount = arr[arr < arrMedian].size
        nPosPct = nPosCount / float(arr.size)
        nNegPct = nNegCount / float(arr.size)
        return { 'mean': arrMean, 'median': arrMedian, 'std': arr.std(), 'min': arr.min(), 'max': arr.max(),
                 'meanMedianRatio': np.abs(arrMean / arrMedian), 'maxMinRatio': np.abs(arr.max() / arr.min()),
                 'posCount': nPosCount, 'negCount': nNegCount, 'posPct': nPosPct, 'negPct': nNegPct }

    metaData['globalTimeStats'] = globalStats(timeSeries)
    metaData['globalDedispTimeStats'] = globalStats(ddTimeSeries)

    def windowedStats(arr, nseg=16):
        """Statistics on segments of an array"""
        segSize = arr.shape[0] / nseg
        minVals = np.zeros(nseg)
        maxVals = np.zeros(nseg)
        meanVals = np.zeros(nseg)
        stdVals = np.zeros(nseg)

        for sid in np.arange(nseg):
            minVals[sid] = arr[segSize*sid:segSize*(sid+1)].min()
            maxVals[sid] = arr[segSize*sid:segSize*(sid+1)].max()
            meanVals[sid] = arr[segSize*sid:segSize*(sid+1)].mean()
            stdVals[sid] = np.std(arr[segSize*sid:segSize*(sid+1)])
        
        return { 'min': minVals, 'max': maxVals, 'mean': meanVals, 'std': stdVals, 'snr': maxVals / stdVals }

    metaData['windTimeStats'] = windowedStats(timeSeries)
    metaData['windDedispTimeStats'] = windowedStats(ddTimeSeries)

    def percentZero(arr):
        """Percent of an array which is 0"""
        pctZero = (timeSeries.size - np.count_nonzero(timeSeries)) / float(timeSeries.size)
        return pctZero

    metaData['pctZero'] = percentZero(timeSeries)

    def percentZeroDeriv(arr):
        """take the 0-dm time series derivative, calculate the percent of time series with derivative=0"""
        arrDer = arr[:-1] - arr[1:]
        pctZeroDer = (arrDer.size - np.count_nonzero(arrDer)) / float(arrDer.size)
        return pctZeroDer

    metaData['pctZeroDeriv'] = percentZeroDeriv(timeSeries)

    def longestRun(arr):
        """Longest run of a constant value in a 1-D array"""
        maxRun = 1
        maxVal = -1.
        currentRun = 1
        for idx in np.arange(arr.size - 1):
            if arr[idx-1]==arr[idx]: currentRun += 1
            else:
                if currentRun > maxRun:
                    maxRun = currentRun
                    maxVal = arr[idx-1]
                else:
                    currentRun = 1

        return maxRun, maxVal, maxRun / float(arr.size)

    metaData['longestRun'] = longestRun(timeSeries)

    def countValOverflows(arr, threshold=1e20):
        """Return a count of the number of values which are above a given threshold"""
        nCount = arr[np.abs(arr)>threshold].size
        return { 'ncount': nCount, 'pct': nCount / float(arr.size) }

    metaData['overflows'] = countValOverflows(waterfall)

    def pixelizeSpectrogram(arr, nTime=16, nChan=4):
        """Coarsely pixelize a spectrogram"""
        timeSize = arr.shape[0] / nTime
        chanSize = arr.shape[1] / nChan
        minVals = np.zeros((nTime, nChan))
        maxVals = np.zeros((nTime, nChan))
        meanVals = np.zeros((nTime, nChan))

        for tid in np.arange(nTime):
            for cid in np.arange(nChan):
                minVals[tid,cid] = arr[timeSize*tid:timeSize*(tid+1), chanSize*cid:chanSize*(cid+1)].min()
                maxVals[tid,cid] = arr[timeSize*tid:timeSize*(tid+1), chanSize*cid:chanSize*(cid+1)].max()
                meanVals[tid,cid] = arr[timeSize*tid:timeSize*(tid+1), chanSize*cid:chanSize*(cid+1)].mean()
        
        return { 'min': minVals, 'max': maxVals, 'mean': meanVals}

    metaData['pixels'] = pixelizeSpectrogram(waterfall)

    #######################
    print metaData.keys()

    if not (opts.meta is None):
        pickle.dump(metaData, open(opts.meta, "wb"))

    #######################
    #waterfall = waterfall[startIdx:endIdx,:]
    #ddwaterfall = ddwaterfall[startIdx:endIdx,:]

    ##normTimeSeries = (timeSeries - np.mean(timeSeries))/np.std(timeSeries)
    #normTimeSeries = timeSeries / (waterfall.shape[1] * opts.timeFactor)
    ##normTimeSeries = ddTimeSeries / (waterfall.shape[1] * opts.timeFactor)

    #if opts.write:
    #    # write time series to text file
    #    timFn = os.path.basename(args[0]).split('.fil')[0] + '.dm%i'%(int(dm)) + '.dat'
    #    print 'Writing dedispered time series to %s'%(timFn)
    #    np.savetxt(timFn, timeSeries, fmt='%f')

    #if not opts.nodisplay or opts.savefig:

    #    fig = plt.figure(figsize=(12,8)) # (width, height)

    #    plt.subplot(3,1,1)
    #    imRaw = plt.imshow(np.flipud(waterfall.T), extent=(0, tInt*waterfall.shape[0], fil.freqs[0], fil.freqs[-1]), aspect='auto', cmap=plt.get_cmap(opts.cmap), interpolation='nearest')
    #    plt.title('Raw')
    #    plt.ylabel('MHz')
    #    #cax = fig.add_axes([0.75, 0.865, 0.15, 0.01])
    #    cax = fig.add_axes([0.75, .95, 0.15, 0.03])
    #    cbar = fig.colorbar(imRaw, cax=cax, orientation='horizontal')
    #    cbar.ax.set_xticklabels(cbar.ax.get_xticklabels(), rotation='vertical', fontsize=8)

    #    plt.subplot(3,1,2)
    #    imDedisp = plt.imshow(np.flipud(ddwaterfall.T), extent=(0, tInt*waterfall.shape[0], fil.freqs[0], fil.freqs[-1]), aspect='auto', cmap=plt.get_cmap(opts.cmap), interpolation='nearest')
    #    plt.title('Dedispersed DM: %.0f'%dm)
    #    plt.ylabel('MHz')
    #    #cax = fig.add_axes([0.75, 0.58, 0.15, 0.01])
    #    #cbar = fig.colorbar(imDedisp, cax=cax, orientation='horizontal')
    #    #cbar.ax.set_xticklabels(cbar.ax.get_xticklabels(), rotation='vertical', fontsize=8)
    #    
    #    plt.subplot(3,1,3)
    #    #plt.plot(tInt*np.arange(waterfall.shape[0]), timeSeries)
    #    plt.plot(tInt*np.arange(waterfall.shape[0]), normTimeSeries)
    #    plt.xlim(0, tInt*timeSeries.shape[0])
    #    plt.title('Time Series')
    #    plt.xlabel('seconds')
    #    plt.ylabel('Amp')

    #    plt.suptitle(args[0].split('/')[-1])

    #    plt.subplots_adjust(hspace=0.4)

    #    if not (opts.meta is None):
    #        metaData = pickle.load(open(opts.meta, "rb"))
    #        tOffset = (float(metaData['maxMJD']) - float(metaData['MJD0'])) * 24. * 60. *60.
    #        metaStr = 'Events: %i     DM: (min: %.0f  max: %.0f  mean: %.0f  median: %.0f)     MJD Start: %s\n'%(metaData['nEvents'], metaData['DMmin'], metaData['DMmax'], metaData['DMmean'], metaData['DMmedian'], metaData['MJD0'])
    #        metaStr += 'Max SNR: %.2f     MJD: %s    t_offset: %.3f'%(metaData['maxSNR'], metaData['maxMJD'], tOffset)
    #        plt.text(0.1, 0.92, metaStr, fontsize=10, transform=fig.transFigure)

    #if opts.savefig: plt.savefig(opts.savefig)
    #if not opts.nodisplay: plt.show()

