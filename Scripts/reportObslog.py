#!/usr/bin/env python
"""
Report the total survey time based on alfaburst:/home/artemis/Survey/Log/Obs.log
"""

import datetime
import time
import numpy as np
import sys

OBSLOG = '/home/artemis/Survey/Log/Obs.log'

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options]')
    o.add_option('-l', '--log', dest='log', default=OBSLOG,
        help='Observation log file')
    o.add_option('-s', '--start', dest='start', default=None,
        help='Start date, DD_MM_YYYY format, default: start from beginning of log')
    o.set_description(__doc__)
    opts, args = o.parse_args(sys.argv[1:])

    logFile = opts.log

    if opts.start is None: globalStartTime = None
    else:
        globalStartTime = datetime.datetime.strptime(opts.start, '%d_%m_%Y') 
        print 'Start time:', globalStartTime
    
    fh = open(logFile, 'r')
    ll = fh.read().split('\n')
    
    startTime = None
    stopTime = None
    
    t0 = []
    tf = []
    
    for line in ll:
        if line.startswith('-') or line.startswith('Clear'): continue
    
        if line.startswith('Start'):
            tStr = line.split('on')[-1]
            tList = tStr.split(' ')
            if len(tList)==7:
                if len(tList[3])==1: tList[3] = '0'+tList[3] # zero pad
                newtStr = tList[1] + ' ' + tList[2] + ' ' + tList[3] + ' ' + tList[4] + ' ' + tList[5] + ' ' + tList[6]
                startTime = datetime.datetime.strptime(newtStr, '%a %b %d %H:%M:%S %Z %Y')
            else:
                if len(tList[2])==1: tList[2] = '0'+tList[2] # zero pad
                newtStr = tList[1] + ' ' + tList[2] + ' ' + tList[3] + ' ' + tList[4] + ' ' + tList[5]
                startTime = datetime.datetime.strptime(newtStr, '%b %d %H:%M:%S %Z %Y')
        elif line.startswith('Stop') and not (startTime is None): # found a start/stop pair
            tStr = line.split('on:')[-1]
            tList = tStr.split(' ')
            if len(tList[3])==1: tList[3] = '0'+tList[3] # zero pad
            newtStr = tList[1] + ' ' + tList[2] + ' ' + tList[3] + ' ' + tList[4] + ' ' + tList[5] + ' ' + tList[6]
            stopTime = datetime.datetime.strptime(newtStr, '%a %b %d %H:%M:%S %Z %Y')
            if (globalStartTime is None) or (startTime > globalStartTime):
                t0.append(time.mktime(startTime.timetuple()))
                tf.append(time.mktime(stopTime.timetuple()))
    
            startTime = None
            stopTime = None
    
    t0 = np.array(t0)
    tf = np.array(tf)
    diffTime = tf - t0
    
    print 'First Obs:', datetime.datetime.fromtimestamp(t0[0])
    print 'Last Obs:', datetime.datetime.fromtimestamp(t0[-1])
    print 'Obs Statistics (in seconds)'
    print 'Mean:', np.mean(diffTime), 'Max:', np.max(diffTime), 'Min:', np.min(diffTime), 'Median:', np.median(diffTime)
    print 'Total Obs Time (in hours):', np.sum(diffTime)/(60*60)

