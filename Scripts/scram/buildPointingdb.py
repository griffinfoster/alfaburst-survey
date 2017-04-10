#!/usr/bin/env python
"""
Build a pandas-based dataframe of time and pointing from the output files of extractPointing.rb
"""

import sys,os
import numpy as np
import pandas as pd
import datetime

pd.set_option('precision', 10)

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] POINTING_OUTPUT')
    o.set_description(__doc__)
    o.add_option('-d', '--dbfile', dest='dbfile', default='areciboPointing.h5',
        help='HDF5-based pandas dataframe containing pointing, if exists then the input files will be appended to the dataframe, default: areciboPointing.h5')
    o.add_option('-o', '--overwrite', dest='overwrite', action='store_true',
        help='Overwrite the dbfile if it exists')
    opts, args = o.parse_args(sys.argv[1:])

    if os.path.exists(opts.dbfile) and opts.overwrite:
        print 'Removing existing database file:', opts.dbfile
        os.remove(opts.dbfile)

    if os.path.exists(opts.dbfile):
        print 'Using existing database file:', opts.dbfile
    else:
        print 'Creating new database file:', opts.dbfile
    dbfile = opts.dbfile

    nFiles = len(args)

    with pd.get_store(dbfile) as store:

        # TODO: check if file all ready written to database file

        for fid, outFile in enumerate(args):
            print 'Processing %s (%i of %i)'%(outFile, fid+1, nFiles), datetime.datetime.now()

            # Create empty dataframe
            df = pd.DataFrame(columns=('unixtime', 'RA0', 'DEC0', 'RA1', 'DEC1', 'RA2', 'DEC2', 'RA3', 'DEC3', 'RA4', 'DEC4', 'RA5', 'DEC5', 'RA6', 'DEC6'))
            blockDf = pd.DataFrame(columns=('unixtime', 'RA0', 'DEC0', 'RA1', 'DEC1', 'RA2', 'DEC2', 'RA3', 'DEC3', 'RA4', 'DEC4', 'RA5', 'DEC5', 'RA6', 'DEC6'))
            lastUnixTime = None
            dfIdx = 0 # dataframe location index

            with open(outFile) as fh:
                for line in fh:
                    """SCRAM:DERIVED DERTIME 1408398075 RA0 14.7545542292 DEC0 9.9765359889 RA1 14.7496071722 DEC1 10.0323946532 RA2 14.7485893975 DEC2 9.9282495515 RA3 14.7535438265 DEC3 9.8726639060 RA4 14.7595245599 DEC4 9.9214336024 RA5 14.7605314714 DEC5 10.0251277561 RA6 14.7555682899 DEC6 10.0805006174"""
                    # Parse line
                    lineList = line.split(' ')
                    unixTime = int(lineList[2])
                    # if unique timestamp append pointing to dataframe
                    if unixTime != lastUnixTime:
                        pointing = map(float, lineList[4:32:2])
                        row = [unixTime]
                        row.extend(pointing)
                        blockDf.loc[dfIdx] = row
                        dfIdx += 1
                        if dfIdx % 5000 == 0: # append blocks to file dataframe
                            print dfIdx
                            df = df.append(blockDf)
                            blockDf = pd.DataFrame(columns=('unixtime', 'RA0', 'DEC0', 'RA1', 'DEC1', 'RA2', 'DEC2', 'RA3', 'DEC3', 'RA4', 'DEC4', 'RA5', 'DEC5', 'RA6', 'DEC6'))

                    lastUnixTime = unixTime

            df = df.append(blockDf)

            df['unixtime'] = df['unixtime'].astype('int') # set unixtime to type integer
            df = df.set_index('unixtime') # set the index to the unixtime

            store.append('pointing', df)
            store.append('files', pd.Series(outFile))

        print 'Closing dbfile'

