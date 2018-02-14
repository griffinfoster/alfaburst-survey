#!/usr/bin/env python
"""
Convert the output dat files of the ALFABURST FRB detection pipeline to a pandas dataframe
"""

import sys,os
from StringIO import StringIO # Python 2 specific, use io for Python 3
import numpy as np
import pandas as pd

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] ALFABURST_DAT')
    o.set_description(__doc__)
    o.add_option('-b', '--buffer_output', dest='bufferOutput', default=None,
            help='Output buffer filename, if name ends in .pkl save as python pickle, default: do not write out buffer file')
    o.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true',
        help='Verbose output')
    opts, args = o.parse_args(sys.argv[1:])

    concatDf = None

    if os.path.exists(opts.bufferOutput):
        if opts.bufferOutput.endswith('pkl'): bufferDf = pd.read_pickle(opts.bufferOutput)
        else: bufferDf = pd.read_csv(opts.bufferOutput)
    else:
        bufferDf = pd.DataFrame(columns=['datfile', 'Beam', 'TSID', 'Buffer', 'MJDstart', 'bestDM', 'bestSNR', 'BinFactor', 'Events', 'DMmax', 'DMmin', 'DMmean', 'DMmedian', 'DMstd', 'SNRmean', 'SNRmedian', 'SNRstd', 'MJDmax', 'MJDmin', 'MJDstd', 'MJDmean', 'MJDmedian', 'Label'])
    for datFile in args:
        if opts.verbose: print datFile

        beamID = int(datFile.split('/')[-1].split('Beam')[-1][0]) # ASSUMES: file format Beam<BeamID>_...
        tsID = datFile.split('/')[-1].split('_dm_')[-1][:-4] # Timestamp ID, useful for finding the corresponding filterbank file

        # We need to get the buffer IDs for each buffer which is in a comment string at the end of the list of events recorded for the buffer
        content = open(datFile).read()
        content = content.split('# ------')[-1].split('Done')[:-1] # drop header and split at the end of buffer line
        nbuffer = len(content)
        print datFile
        for buf in content:
            events = buf.split('#')
            bufStr = events[-1] # Get the string with the buffer ID
            # ex. ' Written buffer :2 | MJDstart: 57637.763946759 | Best DM: 10039 | Max SNR: 12.042928695679'
            # some times (mainly in 2015) the dat has a corrupt buffer, best just to skip it
            bufferIDStr = bufStr.split(' ')[3][1:]
            try:
                bufferID = int(bufferIDStr)
            except ValueError:
                print 'Found Bad Buffer, skipping'
                continue

            events = events[0] # remove buffer string
            df = pd.read_csv(StringIO(events), sep=',', names=['MJD', 'DM', 'SNR', 'BinFactor']).dropna()
            
            df['Beam'] = beamID # Add Beam ID
            df['Flag'] = 0 # Add flag column
            df['BinFactor'] = df['BinFactor'].astype(int) # Convert bin factor to integer
            df['TSID'] = tsID # Timestamp ID
            df['buffer'] = bufferID # buffer ID, unique only timestamped file
            if concatDf is None: concatDf = df
            else: concatDf = pd.concat([concatDf, df], ignore_index=True) # Concatenate dataframes

            if not(opts.bufferOutput is None):
                MJDstart = float(bufStr.split(' ')[6])
                bestDM = int(float(bufStr.split(' ')[10]))
                bestSNR = float(bufStr.split(' ')[14])
                BinFactor = int(df['BinFactor'].median())
                nEvents = len(df)
                DMmax = df['DM'].max()
                DMmin = df['DM'].min()
                DMmean = df['DM'].mean()
                DMmedian = df['DM'].median()
                DMstd = df['DM'].std()
                SNRmean = df['SNR'].mean()
                SNRmedian = df['SNR'].median()
                SNRstd = df['SNR'].std()
                MJDmax = df['MJD'].max()
                MJDmin = df['MJD'].min()
                MJDstd = df['MJD'].std()
                MJDmean = df['MJD'].mean()
                MJDmedian = df['MJD'].median()
                bufRow = [os.path.basename(datFile), beamID, tsID, bufferID, MJDstart, bestDM, bestSNR, BinFactor, nEvents, DMmax, DMmin, DMmean, DMmedian, DMstd, SNRmean, SNRmedian, SNRstd, MJDmax, MJDmin, MJDstd, MJDmean, MJDmedian, -1]

                # append row to buffer dataframe
                bufferDf.loc[len(bufferDf)] = bufRow

    if not(opts.bufferOutput is None):
        bufferDf['Beam'] = bufferDf['Beam'].astype(int)
        bufferDf['Buffer'] = bufferDf['Buffer'].astype(int)
        bufferDf['BinFactor'] = bufferDf['BinFactor'].astype(int)
        bufferDf['Events'] = bufferDf['Events'].astype(int)
        bufferDf['Label'] = bufferDf['Label'].astype(int)

        if opts.bufferOutput.endswith('.pkl'):
            bufferDf.to_pickle(opts.bufferOutput) # Save to Pickle file
        else: bufferDf.to_csv(opts.bufferOutput) # Save to CSV file

