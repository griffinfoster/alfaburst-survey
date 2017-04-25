#!/usr/bin/env python
"""
Apply the label outputs from labelImg.py to the buffer database generated in datConverter.py
"""

import sys,os
import cPickle as pickle
import pandas as pd

idxLabelMap = ['interesting',   # 0
                'rfi',          # 1
                'systematics']  # 2

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] LABEL_PKL_FILES')
    o.set_description(__doc__)
    o.add_option('-d', '--dbfile', dest='dbfile', default=None,
        help='REQUIRED: buffer database output from datConverter.py')
    opts, args = o.parse_args(sys.argv[1:])

    if opts.dbfile is None:
        print 'ERROR: --dbfile option not supplied'
        exit(1)

    bufDf = pd.read_pickle(opts.dbfile)
    bufDf = bufDf.set_index(['TSID', 'Beam', 'Buffer'])

    nFiles = len(args)
    for fid, lfn in enumerate(args):
        print 'Working on %s (%i of %i)'%(lfn, fid+1, nFiles)
        
        labelDict = pickle.load(open(lfn, 'rb'))

        for key, val in labelDict.iteritems():
            # ex. 'Beam5_fb_D20160129T195403.buffer6.d64.png': 1
            TSID = key.split('fb_')[1].split('.')[0]
            beamID = int(key[4])
            bufferID = int(key.split('buffer')[1].split('.')[0])
            if (TSID, beamID, bufferID) in bufDf.index:
                bufDf = bufDf.set_value((TSID, beamID, bufferID), 'Label', val)
            else:
                print 'WARNING: (%s, %i, %i) not in the buffer database'%(TSID, beamID, bufferID)

    print 'Writing updated labels back to database file'
    bufDf = bufDf.reset_index()
    bufDf.to_pickle(opts.dbfile)

