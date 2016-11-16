#!/usr/bin/env python
"""
Plot DM vs Time for an events file (CSV or pickle)
"""

import sys,os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

pd.set_option('precision', 10)

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] DAT_OR_PKL')
    o.set_description(__doc__)
    o.add_option('-i', '--ignore', action='store_true',
        help='Ignore all flags and plot all')
    o.add_option('-u', '--unflagged', action='store_true',
        help='Only plot unflagged events')
    o.add_option('-S', '--savefig', default=None,
        help='Save figure to file, file type determined based on extension.')
    o.add_option('--nodisplay', action='store_true',
        help='Do not display the figure')
    opts, args = o.parse_args(sys.argv[1:])

    fig, axes = plt.subplots(figsize=(16,8)) # (width, height)

    if args[0].endswith('.pkl'): # Load Pickle file
        df = pd.read_pickle(args[0])
    else: # Assume file is a CSV
        df = pd.read_csv(args[0], index_col=0)

    scaleFactor = 4. # size scale factor

    if opts.ignore:
        print 'Plotting all events', len(df.index)
        plt.scatter(df['MJD'], df['DM'], s=df['SNR']*scaleFactor, c=df['SNR'], edgecolors='none', alpha=0.7, rasterized=True)
    elif opts.unflagged:
        unflaggedDf = df[df['Flag']==0]
        print 'Plotting unflagged events', len(unflaggedDf.index)
        plt.scatter(unflaggedDf['MJD'], unflaggedDf['DM'], s=unflaggedDf['SNR']*scaleFactor, c=unflaggedDf['SNR'], edgecolors='none', alpha=0.7, rasterized=True)
    else:
        flaggedDf = df[df['Flag']!=0]
        print 'Plotting flagged events', len(flaggedDf.index)
        plt.scatter(flaggedDf['MJD'], flaggedDf['DM'], s=flaggedDf['SNR'], c=flaggedDf['SNR'], cmap=plt.get_cmap('gray'), edgecolors='none', alpha=0.15, rasterized=True)
        unflaggedDf = df[df['Flag']==0]
        print 'Plotting unflagged events', len(unflaggedDf.index)
        plt.scatter(unflaggedDf['MJD'], unflaggedDf['DM'], s=unflaggedDf['SNR']*scaleFactor, c=unflaggedDf['SNR'], edgecolors='none', alpha=0.7, rasterized=True)

    mjdRange = df['MJD'].max() - df['MJD'].min()
    plt.xlim(df['MJD'].min() - 0.1*mjdRange, df['MJD'].max() + 0.1*mjdRange) # add a bit of buffer
    plt.ylim(0., max(df['DM'].max(), 12000.))

    plt.colorbar()
    plt.xlabel('Modified Julian Date')
    plt.ylabel('Dispersion Measure')
    plt.title('ALFABURST Events')

    if not (opts.savefig is None): 
        print 'Saving figure to', opts.savefig
        plt.savefig(opts.savefig)
    if not opts.nodisplay: plt.show()

