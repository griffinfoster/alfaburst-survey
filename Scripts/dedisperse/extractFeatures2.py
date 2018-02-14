#!/usr/bin/env python

"""
Feature Extraction Script
"""

import sys,os
import numpy as np
import cPickle as pickle
import scipy
from scipy import stats
from scipy.stats import kstest
import statsmodels
from statsmodels import stats
from statsmodels.stats import diagnostic


import dedispersion # https://fornax.phys.unm.edu/lwa/trac/browser/trunk/lsl/lsl/misc/dedispersion.py
import filterbankio # extracted from https://github.com/UCBerkeleySETI/filterbank
#SOURCE_PATH = '/home/inigo/pulseClassifier/src/'
#import imp
#dedispersion = imp.load_source('dedispersion', SOURCE_PATH + 'dedispersion.py')
#filterbankio = imp.load_source('filterbankio', SOURCE_PATH + 'filterbankio.py')


if __name__ == '__main__': #if this is being run as the main program (ie. not called in another program)
    from optparse import OptionParser #allows you to input commands
    o = OptionParser()
    o.set_usage('%prog [options] FIL') #tells you the syntax for running the script
    o.set_description(__doc__)
    o.add_option('-d', '--dm', dest='dm', default=0., type='float',
        help='Despersion Measure to correct, default: 0.')
    o.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Verbose output')
    o.add_option('-t', '--time', dest='timeFactor', type='int', default=2,
        help='Average in time by N samples, similar to SIGPROC decimate -t option')
    o.add_option('-M', '--meta', dest='meta', default=None,
        help='Metadata pickle file used to print buffer stats, generated in generateDedispFigures.py')
    opts, args = o.parse_args(sys.argv[1:]) #sys.argv[0] is the name of the program being executed

    dm = opts.dm #set dm as input

    fil = filterbankio.Filterbank(args[0]) #args[] is list full of declared arguments

    tInt = fil.header['tsamp'] # get tInt
    freqsHz = fil.freqs * 1e6 # generate array of freqs in Hz

    waterfall = np.reshape(fil.data, (fil.data.shape[0], fil.data.shape[2])) # reshape to (n integrations, n freqs)

    #create max size array with fil.data values and zeros
    if waterfall.shape[0] != 32768: # expand array to be full size
        zeros = np.zeros((32768 - waterfall.shape[0], waterfall.shape[1]))
        waterfall = np.concatenate((waterfall, zeros))

    if np.isnan(waterfall).any(): waterfall = np.nan_to_num(waterfall).astype('float64') #some sort of data cleaning thing

    if not opts.timeFactor is None: # average down by N time samples, waterfall.shape[0] must be divisible by N
        if waterfall.shape[0] % opts.timeFactor==0:
            waterfall = waterfall.reshape(waterfall.shape[0]/opts.timeFactor, opts.timeFactor, waterfall.shape[1]).mean(axis=1)
            tInt *= opts.timeFactor
        else:
            print 'WARNING: %i time samples is NOT divisible by %i, zero-padding spectrum to usable size'%(waterfall.shape[0], opts.timeFactor)
            zeros = np.zeros((opts.timeFactor - (waterfall.shape[0] % opts.timeFactor), waterfall.shape[1])) #add extra dimensions so that waterfall shape is divisible by timeFactor
            waterfall = np.concatenate((waterfall, zeros))
            waterfall = waterfall.reshape(waterfall.shape[0]/opts.timeFactor, opts.timeFactor, waterfall.shape[1]).mean(axis=1) #sum elements in 1st dimension
            tInt *= opts.timeFactor

    ddwaterfall = dedispersion.incoherent(freqsHz, waterfall, tInt, dm, boundary='wrap') # apply dedispersion

    ddTimeSeries = np.sum(ddwaterfall, axis=1)
    timeSeries = np.sum(waterfall, axis=1)

    if not (opts.meta is None):
        if os.path.isfile(opts.meta) == True:
            metaData = pickle.load(open(opts.meta, "rb"))
        else:
            metaData = {}
            pickle.dump(metaData, open(opts.meta, "wb"))
    else:
            metaData = {}

    #######################
    # Feature Extraction
    #time series gives an intensity at each time BIN, they are NOT sorted by ascending order
    
    #how many values are above/below the mean
    def globalStats(arr):
        """Global Statistics of an array"""
        arrMedian = np.median(arr)
        arrMean = arr.mean()
        nPosCount = arr[arr > arrMean].size
        nNegCount = arr[arr < arrMean].size #useful as some RFI have a lot of values below the 'baseline'
        nPosPct = nPosCount / float(arr.size)
        nNegPct = nNegCount / float(arr.size)
        std = arr.std()
        if np.isclose(arrMedian, 0.): meanMedianRatio = 0.
        else: meanMedianRatio = np.abs(arrMean / arrMedian)
        #return a dictionary full of statistics
        return { 'mean': arrMean, 'median': arrMedian, 'std': std, 'min': arr.min(), 'max': arr.max(),
                 'meanMedianRatio': meanMedianRatio, 'maxMinRatio': np.abs(arr.max() / arr.min()),
                 'posCount': nPosCount, 'negCount': nNegCount, 'posPct': nPosPct, 'negPct': nNegPct}

    metaData['globalTimeStats'] = globalStats(timeSeries)
    metaData['globalDedispTimeStats'] = globalStats(ddTimeSeries)

    def GaussianTests(arr):
        """Test for values that indicate how Gaussian the data is"""
        kurtosis = scipy.stats.kurtosis(arr)
        skew = scipy.stats.skew(arr)
        dpearson = scipy.stats.normaltest(arr) #dagostino-pearson
        dpearsonomni = dpearson[0]
        dpearsonp = dpearson[1]
        
        lilliefors = statsmodels.stats.diagnostic.kstest_normal(arr, pvalmethod='approx') #Lilliefors test (KS test but with estimated mean and variance, only useful for p<0.2 or boolean for p>0.2
        lsD = lilliefors[0]
        lsp = lilliefors[1]
     
        #KS test uses 0 mean and 1 variance, data is already roughly centered around 0, so need to recenter distribution and make variance 1. Is this not using a circular argument as i must assume normal dist to calculate variance??
        arrnorm = (arr-arr.mean())/arr.std()
        ks = scipy.stats.kstest(arrnorm,'norm')
                                
        return { 'kurtosis': kurtosis, 'skew': skew, 'dpearsonomni': dpearsonomni, 'dpearsonp': dpearsonp, 'lsD': lsD, 'lsp': lsp, 'ks': ks }
    
    metaData['GaussianTests'] = GaussianTests(timeSeries)
    
    def segGaussianTests(arr):
        #splits segments into ~max pulsar pulse width (not sure what this actually is? related to dm but how, intrinsic width must also play a part?)
        nseg = 8 #guessed based on pulsar width in example
        segSize = arr.shape[0] / nseg #how many elements in each segment
        dpearson = np.empty([nseg,2])

        #takes sidth segment and assigns value for that segment to sidth element of value array
        #put KS testing in here too?
        lfpsum = 0
        lfpmax = 0
        lfDmax = 0
        lfDmin = 1
        for sid in np.arange(nseg):
            segarr = arr[segSize*sid:segSize*(sid+1)]
            dpearson[sid] = np.asarray(scipy.stats.normaltest(segarr))
            lilliefors = np.asarray(statsmodels.stats.diagnostic.kstest_normal(segarr, pvalmethod='approx')) #can you store arrays inside arrays?
            if lilliefors[1] > 0.1:
                lfpsum += 1
            if lilliefors[1] > lfpmax:
                lfpmax= lilliefors[1]
            if lilliefors[0] > lfDmax:
                lfDmax = lilliefors[0]
            if lilliefors[0] < lfDmin:
                lfDmin = lilliefors[0]
                                
        dpearsonsum = np.sum(dpearson, axis=0)
        dpearsonomnisum = dpearsonsum[0]
        dpearsonpsum = dpearsonsum[1]
    
        return { 'lillieforsmaxp': lfpmax, 'lillieforsmaxD': lfDmax, 'lfDmin': lfDmin, 'lillieforssum': lfpsum, 'dpearson': dpearson, 'dpearsonomnisum': dpearsonomnisum, 'dpearsonpsum': dpearsonpsum}
    
    metaData['segGaussianTests'] = segGaussianTests(timeSeries)
    
    def windowedStats(arr, nseg=16):
        """Statistics on segments of an array"""
        #splits array into nseg segments and creates empty arrays for each value, each array has nseg elements
        segSize = arr.shape[0] / nseg #how many elements in each segment
        minVals = np.zeros(nseg)
        maxVals = np.zeros(nseg)
        meanVals = np.zeros(nseg)
        stdVals = np.zeros(nseg)
        snrVals = np.zeros(nseg)

        #takes sidth segment and assigns value for that segment to sidth element of value array
        #put KS testing in here too?
        for sid in np.arange(nseg):
            minVals[sid] = arr[segSize*sid:segSize*(sid+1)].min()
            maxVals[sid] = arr[segSize*sid:segSize*(sid+1)].max()
            meanVals[sid] = arr[segSize*sid:segSize*(sid+1)].mean()
            stdVals[sid] = np.std(arr[segSize*sid:segSize*(sid+1)])
            if np.isclose(stdVals[sid], 0): snrVals[sid] = 0.
            else: snrVals[sid] = maxVals[sid] / stdVals[sid]

        return { 'min': minVals, 'max': maxVals, 'mean': meanVals, 'std': stdVals, 'snr': snrVals }

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

    def longestRun(arr, ddarr):
        """Longest run of a constant value in a 1-D array, check for a phantom peak and return its indices"""
        maxRun = 1
        maxVal = -1.
        currentRun = 1
        for idx in np.arange(arr.size - 1): #np.arrange(size) returns evenly spaced values
            if  arr[idx] == arr[idx-1]:
                currentRun += 1 #if previous value of array ~ as next value then add +1 to 'currentRun' and go to next value
            else:
                if currentRun > maxRun: 
                    maxRun = int(currentRun) #save new value to maxrun if the total run is greater than a previous one
                    maxVal = int(arr[idx-1])
                else:
                    currentRun = 1
           
        ddmaxRun = 1
        ddmaxVal = -1
        currentRun =1
        
        for idx in np.arange(ddarr.size - 1): #np.arrange(size) returns evenly spaced values
            if  ddarr[idx] == ddarr[idx-1]:
                currentRun += 1 #if previous value of array ~ as next value then add +1 to 'currentRun' and go to next value
            else:
                if currentRun > maxRun: 
                    ddmaxRun = int(currentRun) #save new value to maxrun if the total run is greater than a previous one
                    ddmaxVal = int(ddarr[idx-1])
                else:
                    currentRun = 1
         
        """if ddmaxRun == maxRun:
            phpeak = True
        else:
            phpeak = False"""
        
     
        return { 'maxRun': maxRun, 'maxVal': maxVal, 'maxRunpct': maxRun / float(arr.size), 'ddmaxRun': ddmaxRun, 'ddmaxVal': ddmaxVal}
    
    metaData['longestRun'] = longestRun(timeSeries, ddTimeSeries)

    
    def countValOverflows(arr, threshold=1e20):
        """Return a count of the number of values which are above a given threshold"""
        nCount = arr[np.abs(arr)>threshold].size
        return { 'ncount': nCount, 'pct': nCount / float(arr.size) }

    metaData['overflows'] = countValOverflows(waterfall)

    def pixelizeSpectrogram(arr, nTime=16, nChan=4):
        """Coarsely pixelize a spectrogram"""
        timeSize = arr.shape[0] / nTime
        chanSize = arr.shape[1] / nChan
        #empty value arrays
        minVals = np.zeros((nTime, nChan))
        maxVals = np.zeros((nTime, nChan))
        meanVals = np.zeros((nTime, nChan))

        #cycles over different nTime x nChan segments of arr and saves max/min/mean in tidth element of value arrays
        for tid in np.arange(nTime):
            for cid in np.arange(nChan):
                minVals[tid,cid] = arr[timeSize*tid:timeSize*(tid+1), chanSize*cid:chanSize*(cid+1)].min()
                maxVals[tid,cid] = arr[timeSize*tid:timeSize*(tid+1), chanSize*cid:chanSize*(cid+1)].max()
                meanVals[tid,cid] = arr[timeSize*tid:timeSize*(tid+1), chanSize*cid:chanSize*(cid+1)].mean()
        
        return { 'min': minVals, 'max': maxVals, 'mean': meanVals}

    metaData['pixels'] = pixelizeSpectrogram(waterfall)

    if not (opts.meta is None):
        pickle.dump(metaData, open(opts.meta, "wb")) #saves the metadata dictionary file as .pkl
    else:
        print metaData

