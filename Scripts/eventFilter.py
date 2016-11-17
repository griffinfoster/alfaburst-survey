#!/usr/bin/env python
"""
Filter Spurious event (i.e. RFI) from an event CV or pickle file output from datConverter.py
"""

import sys,os
import numpy as np
import pandas as pd

pd.set_option('precision', 10)

def filterNEvents(idf, nThresh=100, tWinInSec=0.5, verbose=False):
    """Flag events if the number of events exceeds nThresh during the time window tWinInSec
    input:
        idf: input dataframe
        nThresh: int, maximum number of events allowed per time window
        tWinInSec: float, time window in seconds
        verbose: boolean
    returns: flagged data frame
    """
    print 'N Events Filter N:%i'%nThresh
    dfList = []
    niter = 0

    #nThresh = 100 # Maximum number of events in a time window before flagging as RFI
    #tWinInSec = 0.5 # time window in seconds
    tWin = tWinInSec * (1./(24.*60.*60.)) # time window in fractions of a Julian Day, first value is in seconds

    while not idf.empty:
        t0 = idf['MJD'].iloc[0] # earliest timestamp

        winDf = idf[idf['MJD'] >= t0][idf['MJD'] < t0+tWin] # dataframe for time window [t0, t0+tWin)

        nEvents = len(winDf.index) # Number of events in the time window
        if verbose: print 'Window %i MJD: %f Events: %i'%(niter, t0, nEvents)
        if nEvents > nThresh:
            winDf['Flag'] = 1

        idf.drop(winDf.index, inplace=True) # drop rows from original df

        dfList.append(winDf) # add filtered df to list

        niter += 1

    return pd.concat(dfList, ignore_index=True) # concate df list and output final df

def filterOnlyOneBeam(idf, tWinInSec=0.5, verbose=False):
    """Flag events if events occur in more than one beam during the time window tWinInSec
    input:
        idf: input dataframe
        tWinInSec: float, time window in seconds
        verbose: boolean
    returns: flagged data frame
    """
    print 'Only One Beam Filter'
    dfList = []
    niter = 0

    #tWinInSec = 0.5 # time window in seconds
    tWin = tWinInSec * (1./(24.*60.*60.)) # time window in fractions of a Julian Day, first value is in seconds

    while not idf.empty:
        t0 = idf['MJD'].iloc[0] # earliest timestamp

        winDf = idf[idf['MJD'] >= t0][idf['MJD'] < t0+tWin] # dataframe for time window [t0, t0+tWin)

        uniqueBeams = winDf['Beam'].unique()
        nBeams = len(uniqueBeams)
        if verbose: print 'Window %i MJD: %f Unique Beams: %i'%(niter, t0, nBeams)
        if nBeams != 1: # flag if events occur in multiple beams
            winDf['Flag'] = 1

        idf.drop(winDf.index, inplace=True) # drop rows from original df

        dfList.append(winDf) # add filtered df to list

        niter += 1

    return pd.concat(dfList, ignore_index=True) # concate df list and output final df

def filterDMRange(idf, normDMrange=0.25, tWinInSec=0.5, verbose=False):
    """Flag events if the normalized DM range of events exceeds normDMrange during the time window tWinInSec
    input:
        idf: input dataframe
        normDMrange: float, minimum range of (DM_max - DM_min)/DM_median to flag
        tWinInSec: float, time window in seconds
        verbose: boolean
    returns: flagged data frame
    """
    print 'Normalized DM Range Filter DM Range:%f'%normDMrange
    dfList = []
    niter = 0

    #normDMrange = 0.25 # normalized DM range (DM_max - DM_min)/DM_median to use as threshold
    #tWinInSec = 0.5 # time window in seconds
    tWin = tWinInSec * (1./(24.*60.*60.)) # time window in fractions of a Julian Day, first value is in seconds

    while not idf.empty:
        t0 = idf['MJD'].iloc[0] # earliest timestamp

        winDf = idf[idf['MJD'] >= t0][idf['MJD'] < t0+tWin] # dataframe for time window [t0, t0+tWin)

        winDMrange = (winDf['DM'].max() - winDf['DM'].min()) / winDf['DM'].median()
        if verbose: print 'Window %i MJD: %f DM Range: %f'%(niter, t0, winDMrange)
        if winDMrange > normDMrange:
            winDf['Flag'] = 1

        idf.drop(winDf.index, inplace=True) # drop rows from original df

        dfList.append(winDf) # add filtered df to list

        niter += 1

    return pd.concat(dfList, ignore_index=True) # concate df list and output final df

def filterMinSNR(idf, minSNR=10.):
    """Flag events if less than a minimum SNR
    input:
        idf: input dataframe
        minSNR: float, minimum SNR
    returns: flagged data frame
    """
    print 'Minimum SNR Threshold:', minSNR
    idx = idf[idf['SNR'] < minSNR].index
    idf.set_value(idx, 'Flag',  1)
    return idf

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] DAT_OR_PKL')
    o.set_description(__doc__)
    o.add_option('-o', '--output', dest='output', default='filtered.dat',
        help='Output filename, if name ends in .pkl save as python pickle, else save as CSV, default: filtered.dat')
    o.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Verbose output')
    opts, args = o.parse_args(sys.argv[1:])

    if args[0].endswith('.pkl'): # Load Pickle file
        df = pd.read_pickle(args[0])
    else: # Assume file is a CSV
        df = pd.read_csv(args[0], index_col=0)

    #df.sort(columns='MJD', inplace=True) # Sort events based on timestamp
    df.sort_values(by='MJD', inplace=True) # Sort events based on timestamp
    df.reset_index(inplace=True, drop=True) # Reindex based on timestamp sort

    ######## N events Threshold Filter ###
    concatDf = filterNEvents(df, nThresh=150, tWinInSec=0.1, verbose=opts.verbose)

    ######## Unique Beam Filter ##########
    df = concatDf
    concatDf = filterOnlyOneBeam(df, tWinInSec=0.5, verbose=opts.verbose)

    ######## DM Range Filter #############
    df = concatDf
    concatDf = filterDMRange(df, normDMrange=0.25, tWinInSec=0.5, verbose=opts.verbose)

    ######## Minimum SNR Filter ##########
    df = concatDf
    concatDf = filterMinSNR(df, minSNR=10.1)

    ######### N events Threshold Filter ###
    ######### Filter Start ################

    #dfList = []
    #niter = 0

    #nThresh = 100 # Maximum number of events in a time window before flagging as RFI
    #tWinInSec = 0.5 # time window in seconds
    #tWin = tWinInSec * (1./(24.*60.*60.)) # time window in fractions of a Julian Day, first value is in seconds

    #while not df.empty:
    #    t0 = df['MJD'].iloc[0] # earliest timestamp


    #    winDf = df[df['MJD'] >= t0][df['MJD'] < t0+tWin] # dataframe for time window [t0, t0+tWin)

    #    nEvents = len(winDf.index) # Number of events in the time window
    #    print 'Window %i MJD: %f Events: %i'%(niter, t0, nEvents)
    #    if nEvents > nThresh:
    #        winDf['Flag'] = 1

    #    df.drop(winDf.index, inplace=True) # drop rows from original df

    #    dfList.append(winDf) # add filtered df to list

    #    niter += 1

    #concatDf = pd.concat(dfList, ignore_index=True) # concate df list and output final df

    ######### Filter End ##################

    ######### Unique Beam Filter ##########
    ######### Filter Start ################

    #df = concatDf
    #dfList = []
    #niter = 0

    #tWinInSec = 0.5 # time window in seconds
    #tWin = tWinInSec * (1./(24.*60.*60.)) # time window in fractions of a Julian Day, first value is in seconds

    #while not df.empty:
    #    t0 = df['MJD'].iloc[0] # earliest timestamp

    #    winDf = df[df['MJD'] >= t0][df['MJD'] < t0+tWin] # dataframe for time window [t0, t0+tWin)

    #    uniqueBeams = winDf['Beam'].unique()
    #    nBeams = len(uniqueBeams)
    #    print 'Window %i MJD: %f Unique Beams: %i'%(niter, t0, nBeams)
    #    if nBeams != 1: # flag if events occur in multiple beams
    #        winDf['Flag'] = 1

    #    df.drop(winDf.index, inplace=True) # drop rows from original df

    #    dfList.append(winDf) # add filtered df to list

    #    niter += 1

    #concatDf = pd.concat(dfList, ignore_index=True) # concate df list and output final df

    ######### Filter End ##################

    ######### DM Range Filter #############
    ######### Filter Start ################

    #df = concatDf
    #dfList = []
    #niter = 0

    #normDMrange = 0.25 # normalized DM range (DM_max - DM_min)/DM_median to use as threshold
    #tWinInSec = 0.5 # time window in seconds
    #tWin = tWinInSec * (1./(24.*60.*60.)) # time window in fractions of a Julian Day, first value is in seconds

    #while not df.empty:
    #    t0 = df['MJD'].iloc[0] # earliest timestamp

    #    winDf = df[df['MJD'] >= t0][df['MJD'] < t0+tWin] # dataframe for time window [t0, t0+tWin)

    #    winDMrange = (winDf['DM'].max() - winDf['DM'].min()) / winDf['DM'].median()
    #    print 'Window %i MJD: %f DM Range: %f'%(niter, t0, winDMrange)
    #    if winDMrange > normDMrange:
    #        winDf['Flag'] = 1

    #    df.drop(winDf.index, inplace=True) # drop rows from original df

    #    dfList.append(winDf) # add filtered df to list

    #    niter += 1

    #concatDf = pd.concat(dfList, ignore_index=True) # concate df list and output final df

    ######### Filter End ##################

    if opts.output.endswith('.pkl'):
        concatDf.to_pickle(opts.output) # Save to Pickle file
    else: concatDf.to_csv(opts.output) # Save to CSV file

    # Save dataframe of all events
    # Save dataframe of unflagged events

