#!/usr/bin/env python
"""
Compute a lower limit on the survey time by parsing dat files
"""

import sys,os
import numpy as np
import datetime
import pytz
LOCALTZ = 'America/Puerto_Rico' # Arecibo time zone
local_tz = pytz.timezone(LOCALTZ)

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] ALFABURST_DAT')
    o.set_description(__doc__)
    o.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true',
        help='Verbose output')
    opts, args = o.parse_args(sys.argv[1:])

    totalTime = 0. # seconds

    for datFile in args:
        if opts.verbose: print datFile

        beamID = int(datFile.split('/')[-1].split('Beam')[-1][0]) # ASSUMES: file format Beam<BeamID>_...
        tsID = datFile.split('/')[-1].split('_dm_')[-1][:-4] # Timestamp ID, useful for finding the corresponding filterbank file

        # We need to get the buffer IDs for each buffer which is in a comment string at the end of the list of events recorded for the buffer
        content = open(datFile).read()
        content = content.split('# ------')[-1].split('Done')[:-1] # drop header and split at the end of buffer line
        nbuffer = len(content)
        if nbuffer > 0:

            # start time
            startTs = datetime.datetime.strptime(tsID, 'D%Y%m%dT%H%M%S').replace(tzinfo=local_tz)

            # end time
            bufStr = content[-1].split('#')[-1]
            mjdStart = float(bufStr.split('|')[1].split(':')[1])
            unixTime = (mjdStart + 2400000.5 - 2440587.5) * 86400
            endTs = datetime.datetime.fromtimestamp(unixTime).replace(tzinfo=local_tz)

            # time delta
            #if startTs > endTs: endTs += datetime.timedelta(seconds=60*60)
            delta = endTs - startTs
            if delta < datetime.timedelta(seconds=-1):
                delta = datetime.timedelta(seconds=0)
                print 'time delta is negative' 
            if opts.verbose: print startTs, endTs, delta
            totalTime += delta.total_seconds()

    print 'Total Time: %f s (%f hours)'%(totalTime, totalTime/3600.)

