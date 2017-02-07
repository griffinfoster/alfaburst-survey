#!/usr/bin/env python
"""
"""

import datetime
import time
import numpy as np
import pandas as pd

#logFile = '/home/griffin/testCognize.log'
logFile = '/home/artemis/Survey/Log/cognizeALFA.log' # 2015-08-17 to present

# dataframe row:
# datetime, LST, Status, IF, RA0, DEC0, RA1, DEC1, RA2, DEC2, RA3, DEC3, RA4, DEC4, RA5, DEC5, RA6, DEC6
tempDf = pd.DataFrame(columns=['datetime', 'LST', 'status', 'tint', 'IF', 'RA0', 'DEC0', 'RA1', 'DEC1', 'RA2', 'DEC2', 'RA3', 'DEC3', 'RA4', 'DEC4', 'RA5', 'DEC5', 'RA6', 'DEC6'])
df = tempDf.copy()
dt = None
lst = None
status = None
ifFreq = None
ras = None
decs = None
tint = 60. # integration time in seconds

finalDf = None

print 'Reading', logFile
fh = open(logFile, 'r')
ll = fh.read().split('\n')

lid = 0
for line in ll:
    if line.startswith('IF1RFFRQ'): # IF frequency line
        ifFreq = float(line.split(': ')[-1]) # IF freq in Hz
    elif line.startswith('RA0:'): # RA/DEC pointing line
        raDecStrs = line.split(' ')
        ras = map(float, [raDecStrs[1], raDecStrs[5], raDecStrs[9], raDecStrs[13], raDecStrs[17], raDecStrs[21], raDecStrs[25]])
        decs = map(float, [raDecStrs[3], raDecStrs[7], raDecStrs[11], raDecStrs[15], raDecStrs[19], raDecStrs[23], raDecStrs[27]])

        # At this point, we should have all we need to add an observation entry
        df = df.append(pd.DataFrame({'datetime': dt, 'LST': lst, 'status': status, 'tint':tint, 'IF': ifFreq, 'RA0': ras[0], 'DEC0': decs[0], 'RA1': ras[1], 'DEC1': decs[1], 'RA2': ras[2], 'DEC2': decs[2],'RA3': ras[3], 'DEC3': decs[3],'RA4': ras[4], 'DEC4': decs[4],'RA5': ras[5], 'DEC5': decs[5],'RA6': ras[6], 'DEC6': decs[6]}, index=[0]), ignore_index=True)
        dt = None
        lst = None
        status = None
        ifFreq = None
        ras = None
        decs = None

    elif line.startswith('20'): # Status line
        statusStrs = line.split(' ')
        dt = pd.Timestamp(statusStrs[0] + ' ' + statusStrs[1][:-1])
        lst = statusStrs[3][:-1]
        if statusStrs[8].startswith('down'): status = 0 # 0: ALFA is down, 1: ALFA is up
        else: status = 1

        # Every 1000 active observation entries, append the contents of the df to a final df and reset the df to empty
        lid +=1
        if lid%1000==0:
            print lid
            if finalDf is None: finalDf = df.copy()
            else:
                finalDf = finalDf.append(df)
                df = tempDf.copy()

    # Entry for not observing
    if status == 0:
        df = df.append(pd.DataFrame({'datetime': dt, 'LST': lst, 'status': status, 'tint': None, 'IF': None, 'RA0': None, 'DEC0': None, 'RA1': None, 'DEC1': None, 'RA2': None, 'DEC2': None,'RA3': None, 'DEC3': None,'RA4': None, 'DEC4': None,'RA5': None, 'DEC5': None,'RA6': None, 'DEC6': None}, index=[0]), ignore_index=True)
        dt = None
        lst = None
        status = None
        ifFreq = None
        ras = None
        decs = None

# append remaning entries to the final dataframe
if finalDf is None: finalDf = df.copy()
else: finalDf = finalDf.append(df)

# compute the total observing time
obsTimeSec = finalDf[finalDf['status'] == 1]['tint'].sum()
print 'Total observation time: %s (%.2f seconds)'%(str(datetime.timedelta(seconds=obsTimeSec)), obsTimeSec)

finalDf.to_pickle('cognize.pkl') # save to fast read pickle file
#finalDf.to_csv('cognize.csv') # save to readable CSV file

# TODO:
# option: load dataframe
# plot pointing data to healpix map, compute sky coverage

