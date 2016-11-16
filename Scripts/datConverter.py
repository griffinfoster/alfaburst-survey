#!/usr/bin/env python
"""
Convert the output dat files of the ALFABURST FRB detection pipeline to a pandas dataframe
"""

import sys,os
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

    dfList = []
    for datFile in args:
        if opts.verbose: print datFile

        beamID = int(datFile.split('/')[-1].split('Beam')[-1][0]) # ASSUMES: file format Beam<BeamID>_...
        #df = pd.read_csv(datFile, sep=',', names=['MJD', 'DM', 'SNR', 'BinFactor'], comment='#', skip_blank_lines=True)
        df = pd.read_csv(datFile, sep=',', names=['MJD', 'DM', 'SNR', 'BinFactor'], comment='#').dropna()

        df['Beam'] = beamID # Add Beam ID
        df['Flag'] = 0 # Add flag column
        df['BinFactor'] = df['BinFactor'].astype(int) # Convert bin factor to integer
        dfList.append(df)

    concatDf = pd.concat(dfList, ignore_index=True) # Concatenate dataframes

    if opts.output.endswith('.pkl'):
        concatDf.to_pickle(opts.output) # Save to Pickle file
    else: concatDf.to_csv(opts.output) # Save to CSV file

