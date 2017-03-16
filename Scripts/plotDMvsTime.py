#!/usr/bin/env python
"""
Plot DM vs Time for an events file (CSV or pickle)
"""

# TODO: convert time to LST
# TODO: label beam colors

import sys,os
import numpy as np
import pandas as pd
import astropy.time
import datetime

# Check if $DISPLAY is set (for handling plotting on remote machines with no X-forwarding)
if os.environ.has_key('DISPLAY'):
    import matplotlib.pyplot as plt
else:
    import matplotlib
    matplotlib.use('Agg')
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
    o.add_option('--utc', dest='utc', action='store_true',
        help='Show UTC on X-axis')
    o.add_option('--utc_start', dest='utc_start', default=None,
        help='Start datetime string in UTC, format: YYYYMMDD_HHMMSS')
    o.add_option('--utc_end', dest='utc_end', default=None,
        help='End datetime string in UTC, format: YYYYMMDD_HHMMSS')
    o.add_option('--log', dest='log', action='store_true',
        help='Plot y-axis in log space')
    opts, args = o.parse_args(sys.argv[1:])

    fig, axes = plt.subplots(figsize=(16,8)) # (width, height)

    if args[0].endswith('.pkl'): # Load Pickle file
        df = pd.read_pickle(args[0])
    else: # Assume file is a CSV
        df = pd.read_csv(args[0], index_col=0)

    if opts.utc:
        df['UTC'] = astropy.time.Time(df['MJD'], format='mjd').utc.datetime
        timeType = 'UTC'
    else:
        timeType = 'MJD'

    scaleFactor = 4. # size scale factor

    ax = plt.subplot(111)

    if opts.ignore:
        print 'Plotting all events', len(df.index)
        plt.scatter(df[timeType].values, df['DM'], s=df['SNR']*scaleFactor, c=df['Beam'], edgecolors='none', alpha=0.5, rasterized=True)
    
    elif opts.unflagged:
        unflaggedDf = df[df['Flag']==0]
        
        print 'Plotting unflagged events', len(unflaggedDf.index)
        plt.scatter(unflaggedDf[timeType].values, unflaggedDf['DM'], s=unflaggedDf['SNR']*scaleFactor, c=unflaggedDf['Beam'], edgecolors='none', alpha=0.5, rasterized=True)

    else:
        flaggedDf = df[df['Flag']!=0]
        
        print 'Plotting flagged events', len(flaggedDf.index)
        plt.scatter(flaggedDf[timeType].values, flaggedDf['DM'], s=flaggedDf['SNR'], c=flaggedDf['Beam'], cmap=plt.get_cmap('gray'), edgecolors='none', alpha=0.15, rasterized=True)
        unflaggedDf = df[df['Flag']==0]
        
        print 'Plotting unflagged events', len(unflaggedDf.index)
        plt.scatter(unflaggedDf[timeType].values, unflaggedDf['DM'], s=unflaggedDf['SNR']*scaleFactor, c=unflaggedDf['Beam'], edgecolors='none', alpha=0.5, rasterized=True)

    mjdRange = df['MJD'].max() - df['MJD'].min()
    if opts.utc:
        if opts.utc_start is None: # if no start/end time use the min/max range
            minUTC = astropy.time.Time(df['MJD'].min() - 0.1*mjdRange, format='mjd').utc.datetime
            maxUTC = astropy.time.Time(df['MJD'].max() + 0.1*mjdRange, format='mjd').utc.datetime
        else:
            minUTC = datetime.datetime.strptime(opts.utc_start, '%Y%m%d_%H%M%S')
            maxUTC = datetime.datetime.strptime(opts.utc_end, '%Y%m%d_%H%M%S')
        plt.xlim(minUTC, maxUTC)
        plt.xlabel('UTC')
    else:
        plt.xlim(df['MJD'].min() - 0.1*mjdRange, df['MJD'].max() + 0.1*mjdRange) # add a bit of buffer
        plt.xlabel('Modified Julian Date')

    if opts.log:
        plt.ylim(1., max(df['DM'].max(), 10100.))
        ax.set_yscale('log')
    else:
        plt.ylim(0., max(df['DM'].max(), 10100.))

    plt.ylabel('Dispersion Measure')
    plt.title('ALFABURST Events')

    if not (opts.savefig is None): 
        print 'Saving figure to', opts.savefig
        plt.savefig(opts.savefig)
    if not opts.nodisplay: plt.show()

