#!/usr/bin/env python
"""
Build a pandas-based dataframe of time and pointing from the output files extractScram.py

Parses: *.agc, *.derived, *.alfashm, *.if1, *.if2, *.tt, *.pnt 
"""

import sys,os
import numpy as np
import pandas as pd
import datetime

#pd.set_option('precision', 10)

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] SCRAM_TXT_FILE')
    o.set_description(__doc__)
    opts, args = o.parse_args(sys.argv[1:])

    nFiles = len(args)

    for fid, txtFile in enumerate(args):
        print 'Processing %s (%i of %i)'%(txtFile, fid+1, nFiles), datetime.datetime.now()

        baseFileName = os.path.basename(txtFile)
        fileType = baseFileName.split('.')[-1]
        outFileName = baseFileName + '.h5'

        if fileType=='agc':
            """SCRAM:AGC AGCSTIME 1438445168 AGCTIME 43568016 AGCAZ 300.0003000000 AGCZA 11.9999000000"""
            df = pd.read_csv(txtFile, sep=' ', usecols=[2,4,6,8], names=['unixtime', 'AGCTIME', 'AGCAZ', 'AGCZA'])
            df = df.drop_duplicates(subset='unixtime')
            df = df.set_index('unixtime')
            df.to_hdf(outFileName, 'w', format='t')

        elif fileType=='alfashm':
            """SCRAM:ALFASHM ALFSTIME 1438445242 ALFBIAS1 255 ALFBIAS2 63 ALFMOPOS 71.3234405518"""
            df = pd.read_csv(txtFile, sep=' ', usecols=[2,4,6,8], names=['unixtime', 'ALFBIAS1', 'ALFBIAS2', 'ALFMOPOS'])
            df = df.drop_duplicates(subset='unixtime')
            df = df.set_index('unixtime')
            df.to_hdf(outFileName, 'w', format='t')

        elif fileType=='derived':
            """SCRAM:DERIVED DERTIME 1408398075 RA0 14.7545542292 DEC0 9.9765359889 RA1 14.7496071722 DEC1 10.0323946532 RA2 14.7485893975 DEC2 9.9282495515 RA3 14.7535438265 DEC3 9.8726639060 RA4 14.7595245599 DEC4 9.9214336024 RA5 14.7605314714 DEC5 10.0251277561 RA6 14.7555682899 DEC6 10.0805006174"""
            df = pd.read_csv(txtFile, sep=' ', usecols=np.arange(2, 32, 2), names=['unixtime', 'RA0', 'DEC0', 'RA1', 'DEC1', 'RA2', 'DEC2', 'RA3', 'DEC3', 'RA4', 'DEC4', 'RA5', 'DEC5', 'RA6', 'DEC6'])
            df = df.drop_duplicates(subset='unixtime')
            df = df.set_index('unixtime')
            df.to_hdf(outFileName, 'w', format='t')

        elif fileType=='if1':
            """SCRAM:IF1 IF1STIME 1438445177 IF1SYNHZ 15376000000.0000000000 IF1SYNDB 1300 IF1RFFRQ 5376000000.0000000000 IF1IFFRQ 0.0000000000 IF1ALFFB 0"""
            df = pd.read_csv(txtFile, sep=' ', usecols=np.arange(2, 14, 2), names=['unixtime', 'IF1SYNHZ', 'IF1SYNDB', 'IF1RFFRQ', 'IF1IFFRQ', 'IF1ALFFB'])
            df = df.drop_duplicates(subset='unixtime')
            df = df.set_index('unixtime')
            df.to_hdf(outFileName, 'w', format='t')

        elif fileType=='if2':
            """SCRAM:IF2 IF2STIME 1438445188 IF2SYNHZ 1780000000.0000000000 IF2ALFON 0 IF2SIGSR 0"""
            df = pd.read_csv(txtFile, sep=' ', usecols=np.arange(2, 10, 2), names=['unixtime', 'IF2SYNHZ', 'IF2ALFON', 'IF2SIGSR'])
            df = df.drop_duplicates(subset='unixtime')
            df = df.set_index('unixtime')
            df.to_hdf(outFileName, 'w', format='t')

        elif fileType=='pnt':
            """SCRAM:PNT PNTSTIME 1438445169 PNTRA 7.1523333451 PNTDEC 4.9809721801 PNTMJD 57235.6709411332 PNTAZCOR -0.4048119966 PNTZACOR -0.0243512419"""
            df = pd.read_csv(txtFile, sep=' ', usecols=np.arange(2, 14, 2), names=['unixtime', 'PNTRA', 'PNTDEC', 'PNTMJD', 'PNTAZCOR', 'PNTZACOR'])
            df = df.drop_duplicates(subset='unixtime')
            df = df.set_index('unixtime')
            df.to_hdf(outFileName, 'w', format='t')

        elif fileType=='tt':
            """SCRAM:TT TTSTIME 1438445196 TTTURENC 98807 TTTURDEG 206.7668805804"""
            df = pd.read_csv(txtFile, sep=' ', usecols=np.arange(2, 8, 2), names=['unixtime', 'TTTURENC', 'TTTURDEG'])
            df = df.drop_duplicates(subset='unixtime')
            df = df.set_index('unixtime')
            df.to_hdf(outFileName, 'w', format='t')

    print 'Finished', datetime.datetime.now()

