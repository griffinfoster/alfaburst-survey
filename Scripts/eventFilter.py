#!/usr/bin/env python
"""
Filter Spurious event (i.e. RFI) from an event CV or pickle file output from datConverter.py
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
    o.add_option('-o', '--output', dest='output', default='filtered.dat',
        help='Output filename, if name ends in .pkl save as python pickle, else save as CSV, default: filtered.dat')
    opts, args = o.parse_args(sys.argv[1:])

    if args[0].endswith('.pkl'): # Load Pickle file
        df = pd.read_pickle(args[0])
    else: # Assume file is a CSV
        df = pd.read_csv(args[0], index_col=0)

    df.sort(columns='MJD', inplace=True) # Sort events based on timestamp
    df.reset_index(inplace=True, drop=True) # Reindex based on timestamp sort

    ######## Filter Start ################

    dfList = []
    niter = 0

    nThresh = 50 # Maximum number of events in a time window before flagging as RFI
    tWinInSec = 0.01 # time window in seconds
    tWin = tWinInSec * (1./(24.*60.*60.)) # time window in fractions of a Julian Day, first value is in seconds

    while not df.empty:
        t0 = df['MJD'].iloc[0] # earliest timestamp

        print 'Window %i MJD: %f'%(niter, t0)

        winDf = df[df['MJD'] >= t0][df['MJD'] < t0+tWin] # dataframe for time window [t0, t0+tWin)

        nEvents = len(winDf.index) # Number of events in the time window
        if nEvents > nThresh:
            winDf['Flag'] = 1

        df.drop(winDf.index, inplace=True) # drop rows from original df

        dfList.append(winDf) # add filtered df to list

        niter += 1

    ######## Filter End ##################

    concatDf = pd.concat(dfList, ignore_index=True) # concate df list and output final df

    if opts.output.endswith('.pkl'):
        concatDf.to_pickle(opts.output) # Save to Pickle file
    else: concatDf.to_csv(opts.output) # Save to CSV file

    # Filter: too many events within a time window
    # Filter: events occuring in multiple beams

    # Plot: DM vs time scatter (size based on SNR) of all events
    # Plot: DM vs time scatter (size based on SNR) of unflagged events

    # Save dataframe of all events
    # Save dataframe of unflagged events

