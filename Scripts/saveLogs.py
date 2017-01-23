#!/usr/bin/env python
"""
Save the server, pipeline, and RFI bandpass diagonistics after stopping the
pipeline on the acbX compute nodes
"""

import glob, os
import shutil
import datetime

LOGBASEDIR = '/data/Survey/Log/'
BEAMDIRS = ['beam0/', 'beam1/', 'beam2/', 'beam3/', 'beam4/', 'beam5/', 'beam6/']

for bd in BEAMDIRS: # generic script to work on any node

    LOGDIR = LOGBASEDIR + bd
    ARCHIVEDIR = LOGDIR + 'Archive/'

    if os.path.exists(LOGDIR): # check that this beam directory is on this node

        # check if archive directory exists, if not create one
        if not os.path.exists(ARCHIVEDIR):
            os.makedirs(ARCHIVEDIR)
        
        # get a single datetime for all files
        timeStr = datetime.datetime.now().strftime('D%Y%m%dT%H%M%S')
        
        # for bandpass files: rename with datetime, move to archive
        fList = glob.glob(LOGDIR + 'bandpass*.dat')
        for fn in fList:
            prefix = os.path.split(fn)[-1].split('.dat')[0]
            archiveFn = ARCHIVEDIR + prefix + '_' + timeStr + '.dat'
            #shutil.move(fn, archiveFn)
            shutil.copy(fn, archiveFn)
        
        # for log files: rename with datetime, move to archive
        fList = glob.glob(LOGDIR + 'pipeline*.log')
        for fn in fList:
            prefix = os.path.split(fn)[-1].split('.log')[0]
            archiveFn = ARCHIVEDIR + prefix + '_' + timeStr + '.log'
            #shutil.move(fn, archiveFn)
            shutil.copy(fn, archiveFn)
        
        fList = glob.glob(LOGDIR + 'server*.log')
        for fn in fList:
            prefix = os.path.split(fn)[-1].split('.log')[0]
            archiveFn = ARCHIVEDIR + prefix + '_' + timeStr + '.log'
            #shutil.move(fn, archiveFn)
            shutil.copy(fn, archiveFn)

