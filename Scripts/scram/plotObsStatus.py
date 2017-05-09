#!/usr/bin/env python
"""
Return Arecibo status based on a MJD or Unix timestamp, and HDF5 directory output of buildHDF5.py
"""

import sys,os
import numpy as np
import pandas as pd
import glob
#from astropy.time import Time
from astropy import units
from astropy.coordinates import Angle
from astropy.coordinates import SkyCoord
import matplotlib.pyplot as plt

import datetime
import pytz
LOCALTZ = 'America/Puerto_Rico' # Arecibo time zone

H5_DIR = '/home/griffin/data/serendip6/h5/'

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
    o.add_option('-w', '--window', dest='window', default=60, type='int',
        help='Window in seconds to plot around event')
    opts, args = o.parse_args(sys.argv[1:])

    if opts.unix:
        unixTime = int(args[0])
        jd = (float(unixTime) / 86400.) + 2440587.5
        mjd = jd - 2400000.5
    else:
        # convert to unix time
        #mjd = Time(float(args[0]), format='mjd')
        #print 'UNIX TIME:', mjd.unix
        #unixTime = int(mjd.unix) 
    
        # simple conversion, should be equivalent to astropy.time conversion as leap seconds are not important when converting between MJD and unix time
        mjd = float(args[0])
        jd = mjd + 2400000.5
        unixTime = int((jd - 2440587.5) * 86400)

    print 'UNIX TIME:', unixTime
    print 'MJD:', mjd

    utc = pytz.utc.localize(datetime.datetime.fromtimestamp(int(unixTime)))
    print 'UTC:', utc.strftime('%Y-%m-%d %H:%M:%S')
    local = utc.astimezone(pytz.timezone(LOCALTZ))
    print 'ARECIBO:', local.strftime('%Y-%m-%d %H:%M:%S')

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

    fig = plt.figure(figsize=(16,12)) # (width, height)

    validH5fn = opts.h5dir + fnPrefix + 'derived.h5'
    if os.path.exists(validH5fn):
        df = pd.read_hdf(validH5fn)
        derivedDf = df.loc[unixTime-opts.window:unixTime+opts.window]
        # RAx stored as decimal Hours
        # Decx stored as decimal degrees
        
        # Plot: RA vs Dec
        plt.subplot(3,3,1)
        for bid in range(7): plt.plot(derivedDf['RA%i'%bid], derivedDf['DEC%i'%bid], label='Beam%i'%bid)
        plt.axvline(df.loc[unixTime]['RA0'])
        plt.xlabel('RA')
        plt.ylabel('DEC')
        plt.legend(fontsize='x-small')

        # Plot: RA vs time
        plt.subplot(3,3,2)
        for bid in range(7): plt.plot(derivedDf.index, derivedDf['RA%i'%bid], label='Beam%i'%bid)
        plt.axvline(unixTime)
        plt.ylabel('RA')
        plt.xlabel('Unix Time')
        plt.legend(fontsize='x-small')
        plt.xlim(derivedDf.index[0], derivedDf.index[-1])

        # Plot: DEC vs time
        plt.subplot(3,3,3)
        for bid in range(7): plt.plot(derivedDf.index, derivedDf['DEC%i'%bid], label='Beam%i'%bid)
        plt.axvline(unixTime)
        plt.ylabel('DEC')
        plt.xlabel('Unix Time')
        plt.legend(fontsize='x-small')
        plt.xlim(derivedDf.index[0], derivedDf.index[-1])

    validH5fn = opts.h5dir + fnPrefix + 'if1.h5'
    if os.path.exists(validH5fn):
        df = pd.read_hdf(validH5fn)
        if1Df = df.loc[unixTime-opts.window:unixTime+opts.window]
        #print if1Df
    else:
        print 'WARN: no IF1 HDF5 file %s found, skipping'%validH5fn

    validH5fn = opts.h5dir + fnPrefix + 'if2.h5'
    if os.path.exists(validH5fn):
        df = pd.read_hdf(validH5fn)
        if2Df = df.loc[unixTime-opts.window:unixTime+opts.window]
        #print if2Df

        # Plot: Synth vs time
        plt.subplot(3,3,4)
        plt.plot(if1Df.index, if1Df['IF1SYNHZ']/1e6, label='IF1SYNHZ')
        plt.plot(if1Df.index, if1Df['IF1RFFRQ']/1e6, label='IF1RFFRQ')
        plt.plot(if2Df.index, if2Df['IF2SYNHZ']/1e6, label='IF2SYNHZ')
        plt.axvline(unixTime)
        plt.ylabel('Freq. (MHz)')
        plt.xlabel('Unix Time')
        plt.legend(fontsize='x-small')
        plt.xlim(if1Df.index[0], if1Df.index[-1])

        # Plot: ALFA IF status
        plt.subplot(3,3,5)
        plt.plot(if1Df.index, if1Df['IF1ALFFB'], label='IF1ALFFB')
        plt.plot(if2Df.index, if2Df['IF2ALFON'], label='IF2ALFON')
        plt.axvline(unixTime)
        plt.ylabel('Status')
        plt.xlabel('Unix Time')
        plt.legend(fontsize='x-small')
        plt.xlim(if1Df.index[0], if1Df.index[-1])
        plt.ylim(-0.1, 1.1)

    else:
        print 'WARN: no IF2 HDF5 file %s found, skipping'%validH5fn

    validH5fn = opts.h5dir + fnPrefix + 'pnt.h5'
    if os.path.exists(validH5fn):
        df = pd.read_hdf(validH5fn)
        pntDf = df.loc[unixTime-opts.window:unixTime+opts.window]
        #print pntDf
    else:
        print 'WARN: no PNT HDF5 file %s found, skipping'%validH5fn

    validH5fn = opts.h5dir + fnPrefix + 'tt.h5'
    if os.path.exists(validH5fn):
        df = pd.read_hdf(validH5fn)
        ttDf = df.loc[unixTime-opts.window:unixTime+opts.window]
        #print ttDf
        # Plot: Encoding vs time
        plt.subplot(3,3,6)
        plt.plot(ttDf.index, ttDf['TTTURENC'], label='TTTURENC')
        plt.axvline(unixTime)
        plt.xlabel('Unix Time')
        plt.ylabel('Encoding Index')
        plt.legend(fontsize='x-small')
        plt.xlim(ttDf.index[0], ttDf.index[-1])

        # Plot: Turret angle vs time
        plt.subplot(3,3,7)
        plt.plot(ttDf.index, ttDf['TTTURDEG'], label='TTTURDEG')
        plt.axvline(unixTime)
        plt.xlabel('Unix Time')
        plt.ylabel('Turret Angle')
        plt.legend(fontsize='x-small')
        plt.xlim(ttDf.index[0], ttDf.index[-1])

    else:
        print 'WARN: no TT HDF5 file %s found, skipping'%validH5fn

    validH5fn = opts.h5dir + fnPrefix + 'agc.h5'
    if os.path.exists(validH5fn):
        df = pd.read_hdf(validH5fn)
        agcDf = df.loc[unixTime-opts.window:unixTime+opts.window]
        #print agcDf
    else:
        print 'WARN: no AGC HDF5 file %s found, skipping'%validH5fn

    validH5fn = opts.h5dir + fnPrefix + 'alfashm.h5'
    if os.path.exists(validH5fn):
        df = pd.read_hdf(validH5fn)
        alfashmDf = df.loc[unixTime-opts.window:unixTime+opts.window]
        #print alfashmDf
        # Plot: Encoding vs time
        plt.subplot(3,3,8)
        plt.plot(alfashmDf.index, alfashmDf['ALFBIAS1'], label='ALFBIAS1')
        plt.plot(alfashmDf.index, alfashmDf['ALFBIAS2'], label='ALFBIAS2')
        plt.axvline(unixTime)
        plt.xlabel('Unix Time')
        plt.ylabel('Bias')
        plt.xlim(alfashmDf.index[0], alfashmDf.index[-1])
        plt.legend(fontsize='x-small')

        # Plot: Turret angle vs time
        plt.subplot(3,3,9)
        plt.plot(alfashmDf.index, alfashmDf['ALFMOPOS'], label='ALFMOPOS')
        plt.axvline(unixTime)
        plt.xlabel('Unix Time')
        plt.ylabel('ALFMOPOS')
        plt.xlim(alfashmDf.index[0], alfashmDf.index[-1])
        plt.legend(fontsize='x-small')

    else:
        print 'WARN: no ALFASHM HDF5 file %s found, skipping'%validH5fn

    plt.show()
    
