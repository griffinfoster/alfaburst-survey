#!/usr/bin/env python
"""
Report the total survey time based on alfaburst:/home/artemis/Survey/Log/surveytime.log
"""

import datetime
import time
import numpy as np

logFile = '/home/artemis/Survey/Log/surveytime.log'

fh = open(logFile, 'r')
ll = fh.read().split('\n')

startTime = None
stopTime = None

t0 = []
tf = []
diffTime = []

for line in ll:
    if startTime is None: # Go through lines until a start time is found
        if line.startswith('Start'):
            startTime = float(line.split(':')[-1])
    else: # we have a start time, now need to find a stop time
        if line.startswith('Start'): # update to new start time
            startTime = float(line.split(':')[-1])
        elif line.startswith('Stop'): # found a start/stop pair
            stopTime = float(line.split(':')[-1])
            t0.append(startTime)
            tf.append(stopTime)
            diffTime.append(stopTime - startTime) # observation length (in seconds)
            startTime = None
            stopTime = None

t0 = np.array(t0)
tf = np.array(tf)
diffTime = np.array(diffTime)

print 'First Obs:', datetime.datetime.fromtimestamp(t0[0])
print 'Last Obs:', datetime.datetime.fromtimestamp(t0[-1])
print 'Obs Statistics (in seconds)'
print 'Mean:', np.mean(diffTime), 'Max:', np.max(diffTime), 'Min:', np.min(diffTime), 'Median:', np.median(diffTime)
print 'Total Obs Time (in hours):', np.sum(diffTime)/(60*60)

