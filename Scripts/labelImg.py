#!/usr/bin/env python
"""
Load images from a directory and provide a simple interface to label the images, write labels to a pickle file
"""

import sys,os
import glob
import tty, termios
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import cPickle as pickle

idxLabelMap = ['interesting',   # 0
                'rfi',          # 1
                'systematics']  # 2

def getchar():
    # https://gist.github.com/jasonrdsouza/1901709
    # Returns a single character from standard input, does not support special keys like arrows
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] IMAGE_DIRECTORY')
    o.set_description(__doc__)
    o.add_option('--dbfile', dest='dbfile', default='imgLabel.pkl',
        help='CSV file of image labels, default: imgLabel.pkl')
    o.add_option('-e', '--ext', dest='ext', default='png',
        help='Image extension to label, default: png')
    o.add_option('-i', '--index', dest='index', default=0, type='int',
        help='Starting index, default: 0')
    opts, args = o.parse_args(sys.argv[1:])

    imgDir = os.path.join(args[0], '')

    # load dbfile if exists, else create an empty dict
    if os.path.exists(opts.dbfile):
        print 'Loading', opts.dbfile
        labelDict = pickle.load(open(opts.dbfile, 'rb'))
    else:
        labelDict = {}

    # get list of images in directory
    print 'Labels for images in directory:', imgDir
    print 'Keys:\n' + \
            '\tq: quit\n' + \
            '\ti: interesting event\n' + \
            '\tr: RFI event\n' + \
            '\ts: System variability\n' + \
            '\tb: back one image\n' + \
            '\tn: next one image\n'
    imgFiles = sorted(glob.glob(imgDir + '*.' + opts.ext))
    nfiles = len(imgFiles)
    if len(imgFiles) == 0:
        inLoop = False
        print 'WARNING: no files with extension %s found in directory'%opts.ext
    else:
        inLoop = True
        idx = opts.index
        print idx, imgFiles[idx]

    plt.ion()
    fig = plt.figure(frameon=False, figsize=(12,8))
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    
    img = mpimg.imread(imgFiles[idx])
    plt.imshow(img)
    plt.pause(0.01)

    while inLoop:
        currentImg = imgFiles[idx]
        baseName = os.path.basename(currentImg)
        if baseName in labelDict:
            print 'Current Label:', idxLabelMap[labelDict[baseName]]
        else:
            print 'Unlabelled'

        ch = getchar()
        if ch=='q':
            inLoop = False
            print 'Quiting, writing labels to', opts.dbfile
            pickle.dump(labelDict, open(opts.dbfile, 'wb')) # write dict to file
        elif ch=='n': # go to next image
            if idx+1==nfiles: idx = 0 
            else: idx += 1
            print idx, imgFiles[idx]
            img = mpimg.imread(imgFiles[idx])
            plt.cla()
            plt.imshow(img)
            plt.pause(0.01)

        elif ch=='b': # go to previous image
            if idx==0: idx = nfiles - 1
            else: idx -= 1
            print idx, imgFiles[idx]
            img = mpimg.imread(imgFiles[idx])
            plt.cla()
            plt.imshow(img)
            plt.pause(0.01)

        elif ch=='i': # label: interesting
            print 'Label: interesting'
            labelDict[baseName] = 0

        elif ch=='r': # label: RFI
            print 'Label: RFI'
            labelDict[baseName] = 1

        elif ch=='s': # label: system variability
            print 'Label: system variability'
            labelDict[baseName] = 2

