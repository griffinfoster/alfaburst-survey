#!/usr/bin/env python
"""
Return the ALFA pointing based on a MJD or Unix timestamp
"""

import sys,os
import numpy as np
import pandas as pd
from astropy import units
from astropy.coordinates import Angle

def printPointing(pointingSeries, raType='str', decType='str'):
    print '(RA: %s, DEC: %s)'%(raType, decType)
    for key, val in pointingSeries.iteritems():
        if key.startswith('RA'):
            ra = Angle(val, unit=units.hour)
            if raType=='str':
                print key, ra.to_string(sep=':'),
            elif raType=='hours':
                print key, ra.hour,
            elif raType=='deg':
                print key, ra.degree,
            elif raType=='rad':
                print key, ra.radian,
            else:
                print 'RA type unknown'
        if key.startswith('DEC'):
            dec = Angle(val, unit=units.deg)
            if decType=='str':
                print key, dec.to_string(sep=':')
            elif decType=='deg':
                print key, dec.degree
            elif decType=='rad':
                print key, dec.radian
            else:
                print 'Dec type unknown'

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] MJD/Unix time')
    o.set_description(__doc__)
    o.add_option('-d', '--dbfile', dest='dbfile', default='areciboPointing.h5',
        help='HDF5-based pandas dataframe containing pointing, default: areciboPointing.h5')
    o.add_option('-u', '--unix', dest='unix', action='store_true',
        help='Interpet time as a Unix timestamp')
    o.add_option('-w', '--window', dest='window', default=4, type='int',
        help='Time window to search for closest pointing, default: +/-4 seconds')
    o.add_option('--ra', dest='ra', default='str',
        help='RA print mode: \'str\': HH:MM:SS.SSSS, \'hours\': decimal hours, \'deg\': decimal degrees, \'rad\': decimal radians, default: str')
    o.add_option('--dec', dest='dec', default='str',
        help='RA print mode: \'str\': DD:MM:SS.SSSS, \'deg\': decimal degrees, \'rad\': decimal radians, default: str')
    opts, args = o.parse_args(sys.argv[1:])

    dbfile = opts.dbfile

    if opts.unix:
        unixTime = int(args[0])
    else:
        # convert to unix time
        mjd = float(args[0])
        jd = mjd + 2400000.5
        unixTime = int((jd - 2440587.5) * 86400)

    df = pd.read_hdf(opts.dbfile, 'pointing')
    # RAx stored as decimal Hours
    # Decx stored as decimal degrees

    # search in window for closest time stamp
    if unixTime in df.index:
        print 'Pointing at Unix Time:', unixTime
        printPointing(df.loc[unixTime], raType=opts.ra, decType=opts.dec)
    else:
        deltat = 1
        nearestTime = None
        while deltat < opts.window and nearestTime is None:
            if (unixTime + deltat in df.index): nearestTime = unixTime + deltat
            elif (unixTime - deltat in df.index): nearestTime = unixTime - deltat
            deltat += 1

        if nearestTime is None:
            print 'No timestamp found within time window of +/-%i seconds of Unix Time %i'%(opts.window, unixTime)
        else:
            print 'Nearest timestamp to Unix Time %i found at Unix Time %i'%(unixTime, nearestTime)
            printPointing(df.loc[nearestTime], raType=opts.ra, decType=opts.dec)

