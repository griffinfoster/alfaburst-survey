#!/usr/bin/env python
"""
Report statistics of unflagged event clusters
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
    o.add_option('-t', '--time', dest='tWinInSec', type='float', default=0.5,
        help='Time window to cluster events in seconds, default: 0.5')
    o.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Verbose output')
    opts, args = o.parse_args(sys.argv[1:])

    if args[0].endswith('.pkl'): # Load Pickle file
        df = pd.read_pickle(args[0])
    else: # Assume file is a CSV
        df = pd.read_csv(args[0], index_col=0)

    unflaggedDf = df[df['Flag']==0].copy() # drop all flagged data

    #unflaggedDf.sort(columns='MJD', inplace=True) # Sort events based on timestamp
    unflaggedDf.sort_values(by='MJD', inplace=True) # Sort events based on timestamp
    unflaggedDf.reset_index(inplace=True, drop=True) # Reindex based on timestamp sort

    tWin = opts.tWinInSec * (1./(24.*60.*60.)) # time window in fractions of a Julian Day, first value is in seconds

    print 'Unflagged Events:'
    print '--------------------------------------'

    niter = 0
    while not unflaggedDf.empty:
        t0 = unflaggedDf['MJD'].iloc[0] # earliest timestamp

        winDf = unflaggedDf[unflaggedDf['MJD'] >= t0][unflaggedDf['MJD'] < t0+tWin] # dataframe for time window [t0, t0+tWin)
        print 'Cluster:', niter, 'MJD:', t0, 'DM Range: (%i %i)'%(winDf['DM'].min(), winDf['DM'].max()), 'Event Count:', len(winDf.index), 'Max SNR:', winDf['SNR'].max(), 'Beams:', winDf['Beam'].unique()

        unflaggedDf.drop(winDf.index, inplace=True) # drop rows from original df
        niter += 1

