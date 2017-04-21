#!/usr/bin/env python
"""
Return Arecibo status based on a MJD or Unix timestamp, and HDF5 directory output of buildHDF5.py
"""

import sys,os
import numpy as np
import pandas as pd
import glob
from astropy.time import Time
from astropy import units
from astropy.coordinates import Angle
from astropy.coordinates import SkyCoord

H5_DIR = '/home/griffin/data/serendip6/sandbox/'

def printPointing(pointingSeries, raType='str', decType='str'):
    print '(RA: %s, DEC: %s)'%(raType, decType)
    #for key, val in pointingSeries.iteritems():
    for beamId in range(7):
        ra = Angle(pointingSeries['RA%i'%beamId], unit=units.hour)
        dec = Angle(pointingSeries['DEC%i'%beamId], unit=units.deg)
        pnt = SkyCoord(ra=ra, dec=dec)

        pntStr = 'Beam %i: '%beamId
        if raType=='str':
            pntStr += 'RA: %s '%ra.to_string(sep=':')
        elif raType=='hours':
            pntStr += 'RA: %f '%ra.hour
        elif raType=='deg':
            pntStr += 'RA: %f '%ra.deg
        elif raType=='rad':
            pntStr += 'RA: %f '%ra.radian

        if decType=='str':
            pntStr += 'DEC: %s '%dec.to_string(sep=':')
        elif decType=='deg':
            pntStr += 'DEC: %f '%dec.deg
        elif decType=='rad':
            pntStr += 'DEC: %f '%dec.radian

        pntStr += '(l=%f, b=%f)'%(pnt.galactic.l.deg, pnt.galactic.b.deg)

        print pntStr

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] MJD/Unix time')
    o.set_description(__doc__)
    o.add_option('-d', '--h5dir', dest='h5dir', default=H5_DIR,
        help='Directory which contains HDF5-based pandas dataframes, default: %s'%H5_DIR)
    o.add_option('-u', '--unix', dest='unix', action='store_true',
        help='Interpret time as a Unix timestamp')
    o.add_option('--ra', dest='ra', default='str',
        help='RA print mode: \'str\': HH:MM:SS.SSSS, \'hours\': decimal hours, \'deg\': decimal degrees, \'rad\': decimal radians, default: str')
    o.add_option('--dec', dest='dec', default='str',
        help='RA print mode: \'str\': DD:MM:SS.SSSS, \'deg\': decimal degrees, \'rad\': decimal radians, default: str')
    opts, args = o.parse_args(sys.argv[1:])

    if opts.unix:
        unixTime = int(args[0])
    else:
        # convert to unix time
        mjd = Time(float(args[0]), format='mjd')
        print 'UNIX TIME:', mjd.unix
        unixTime = int(mjd.unix) 
        # simple conversion, should be equivalent to astropy.time conversion as leap seconds are not important when converting between MJD and unix time
        #jd = mjd + 2400000.5
        #unixTime = int((jd - 2440587.5) * 86400)

    # find the correct file ID based on unixtime
    derH5files = glob.glob(opts.h5dir + '*derived.h5')
    fnPrefix = None
    for h5fn in derH5files:
        baseH5fn = os.path.basename(h5fn)
        fnUnixTime = int(baseH5fn.split('.')[1])
        timeDiff = fnUnixTime - unixTime
        if timeDiff > 0 and  timeDiff < 86400: # each file contains at most 24*60*60 seconds
            print 'Timestamp in', h5fn
            fnPrefix = baseH5fn.split('derived')[0]
            break

    if fnPrefix is None:
        print 'No file found which contains this Unix timestamp'
        exit(1)

    print '\nUnix Time:', unixTime

    validH5fn = fnPrefix + 'derived.h5'
    if os.path.exists(validH5fn):
        df = pd.read_hdf(validH5fn)
        # RAx stored as decimal Hours
        # Decx stored as decimal degrees
        printPointing(df.loc[unixTime], raType=opts.ra, decType=opts.dec)
    else:
        print 'WARN: no derived pointing HDF5 file %s found, skipping'%validH5fn

    validH5fn = fnPrefix + 'if1.h5'
    if os.path.exists(validH5fn):
        df = pd.read_hdf(validH5fn)
        print '\nIF1SYNHZ: %f GHz IF1RFFRQ: %f GHz'%(df.loc[unixTime]['IF1SYNHZ']/1e9, df.loc[unixTime]['IF1RFFRQ']/1e9)
    else:
        print 'WARN: no IF1 HDF5 file %s found, skipping'%validH5fn

    validH5fn = fnPrefix + 'if2.h5'
    if os.path.exists(validH5fn):
        df = pd.read_hdf(validH5fn)
        print '\nIF2SYNHZ: %f GHz IF2ALFON: %i\n'%(df.loc[unixTime]['IF2SYNHZ']/1e9, int(df.loc[unixTime]['IF2ALFON']))
        #print df.loc[unixTime]
    else:
        print 'WARN: no IF2 HDF5 file %s found, skipping'%validH5fn

