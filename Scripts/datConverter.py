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
    o.add_option('-o', '--output', dest='output', default='concat.dat',
        help='Output filename, if name ends in .pkl save as python pickle, else save as CSV, default: concat.dat')
    o.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true',
        help='Verbose output')
    opts, args = o.parse_args(sys.argv[1:])

    concatDf = None
    for datFile in args:
        if opts.verbose: print datFile

        beamID = int(datFile.split('/')[-1].split('Beam')[-1][0]) # ASSUMES: file format Beam<BeamID>_...
        tsID = datFile.split('/')[-1].split('_dm_')[-1][:-4] # Timestamp ID, useful for finding the corresponding filterbank file

        # We need to get the buffer IDs for each buffer which is in a comment string at the end of the list of events recorded for the buffer
        content = open(datFile).read()
        content = content.split('# ------')[-1].split('Done')[:-1] # drop header and split at the end of buffer line
        nbuffer = len(content)
        for buf in content:
            events = buf.split('#')
            bufStr = events[-1] # Get the string with the buffer ID
            bufferID = int(bufStr.split(' ')[3][1:]) # ex: ' Written buffer :2 | MJDstart: 57637.763946759 | Best DM: 10039 | Max SNR: 12.042928695679'
            events = events[0] # remove buffer string
            df = pd.read_csv(StringIO(events), sep=',', names=['MJD', 'DM', 'SNR', 'BinFactor']).dropna()
            
            df['Beam'] = beamID # Add Beam ID
            df['Flag'] = 0 # Add flag column
            df['BinFactor'] = df['BinFactor'].astype(int) # Convert bin factor to integer
            df['TSID'] = tsID # Timestamp ID
            df['buffer'] = bufferID # buffer ID, unique only timestamped file
            if concatDf is None: concatDf = df
            else: concatDf = pd.concat([concatDf, df], ignore_index=True) # Concatenate dataframes

    if opts.output.endswith('.pkl'):
        concatDf.to_pickle(opts.output) # Save to Pickle file
    else: concatDf.to_csv(opts.output) # Save to CSV file

