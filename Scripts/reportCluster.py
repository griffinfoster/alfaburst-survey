#!/usr/bin/env python
"""
Report statistics of filtered events

Run after eventFilter.py to produce a useful report of possible events
"""

import sys,os
import numpy as np
import pandas as pd

pd.set_option('precision', 10)

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] DAT_OR_PKL')
    o.set_description(__doc__)
    o.add_option('-t', '--time', dest='tWinInSec', type='float', default=10.,
        help='Time window to cluster events in seconds, default: 10.')
    o.add_option('-n', '--nevents', dest='nevents', default=None, type='int',
        help='Report on the top N scoring clusters, default: report all')
    o.add_option('-m', '--max', dest='maxscore', default=None, type='float',
        help='Only report clusters with scores below a maximum, default: report all')
    o.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Verbose output')
    opts, args = o.parse_args(sys.argv[1:])

    if args[0].endswith('.pkl'): # Load Pickle file
        df = pd.read_pickle(args[0])
    else: # Assume file is a CSV
        df = pd.read_csv(args[0], index_col=0)

    df.sort_values(by='MJD', inplace=True) # Sort events based on timestamp
    df.reset_index(inplace=True, drop=True) # Reindex based on timestamp sort

    tWin = opts.tWinInSec * (1./(24.*60.*60.)) # time window in fractions of a Julian Day, first value is in seconds
    
    print 'Events Report:'
    print '--------------------------------------'

    clusterMetric = []
    reportStrs = []
    while not df.empty:
        t0 = df['MJD'].iloc[0] # earliest timestamp
        winDf = df[df['MJD'] >= t0][df['MJD'] < t0+tWin] # dataframe for time window [t0, t0+tWin)

        metric = float(winDf['Flag'].sum()) / winDf.size

        rStr = 'MJD: %f Metric: %f Events: %i'%(t0, metric, winDf.size)

        uniBeams = winDf['Beam'].unique()
        for uBeam in uniBeams:
            idxmax = winDf[winDf['Beam']==uBeam]['SNR'].idxmax()
            rStr += '\n\tBeam: %i %s Buffer: %i Max SNR: %f DM: %f BinFactor: %i'%(uBeam, winDf['TSID'].ix[idxmax], winDf['buffer'].ix[idxmax], winDf['SNR'].ix[idxmax], winDf['DM'].ix[idxmax], winDf['BinFactor'].ix[idxmax])

        if opts.maxscore is None:
            clusterMetric.append(metric) # use to report clusters based on sorted metric
            reportStrs.append(rStr)
        elif metric <= opts.maxscore:
            clusterMetric.append(metric) # use to report clusters based on sorted metric
            reportStrs.append(rStr)

        df.drop(winDf.index, inplace=True) # drop rows from original df

    sortedMetricIdx = np.argsort(clusterMetric)
    if not(opts.nevents is None): sortedMetricIdx = sortedMetricIdx[:opts.nevents]

    for idx in sortedMetricIdx: print reportStrs[idx]
