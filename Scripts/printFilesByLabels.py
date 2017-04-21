#!/usr/bin/env python
"""
Print a list of files names based on the output pickle from labelImg.py
"""

import sys,os
import cPickle as pickle

idxLabelMap = ['interesting',   # 0
                'rfi',          # 1
                'systematics']  # 2

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] PKL_FILE')
    o.set_description(__doc__)
    o.add_option('-l', '--label', dest='label', default='0',
        help='Labels to print: 0:interesting, 1:rfi, 2:systematics , default: 0')
    opts, args = o.parse_args(sys.argv[1:])

    labelList = map(int, opts.label.split(','))

    #print 'Loading', args[0]
    labelDict = pickle.load(open(args[0], 'rb'))

    validKeys = []

    for key, val in labelDict.iteritems():
        if val in labelList: validKeys.append(key)
    
    validKeys.sort(key=lambda x:x.split('_')[2])
    for key in validKeys: print key

