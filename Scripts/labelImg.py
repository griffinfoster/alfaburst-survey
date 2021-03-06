#!/usr/bin/env python
"""
Load images with wildcards or from a directory and provide a simple interface to label the images, write labels to a pickle file
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

idxLabelDict = {'interesting' : 0,  # 0
                'rfi' : 1,          # 1
                'systematics' : 2}  # 2

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
    o.set_usage('%prog [options] IMAGE_DIRECTORY/IMAGE')
    o.set_description(__doc__)
    o.add_option('--dbfile', dest='dbfile', default='imgLabel.pkl',
        help='CSV file of image labels, default: imgLabel.pkl')
    o.add_option('-e', '--ext', dest='ext', default='png',
        help='Image extension to label, default: png')
    o.add_option('-i', '--index', dest='index', default=0, type='int',
        help='Starting index, default: 0')
    o.add_option('--subset', dest='subset', default=None,
        help='Only show a subset of figures, can be comma separated: unlabel, rfi, sys, interest')
    o.add_option('-a', '--auto', dest='auto', default=None,
        help='Auto assign a label to unlabelled images')
    opts, args = o.parse_args(sys.argv[1:])

    if os.path.isdir(args[0]):
        imgDir = os.path.join(args[0], '')
        # get list of images in directory
        print 'Labels for images in directory:', imgDir
        imgFiles = sorted(glob.glob(imgDir + '*.' + opts.ext))
    else:
        imgFiles = args

    # load dbfile if exists, else create an empty dict
    if os.path.exists(opts.dbfile):
        print 'Loading', opts.dbfile
        labelDict = pickle.load(open(opts.dbfile, 'rb'))
    else:
        labelDict = {}

    print 'Keys:\n' + \
            '\tq: quit\n' + \
            '\ti: interesting event\n' + \
            '\tr: RFI event\n' + \
            '\ts: System variability\n' + \
            '\tu: Unlabel\n' + \
            '\tb: back one image\n' + \
            '\tn: next one image\n'

    if opts.auto in idxLabelMap: autoLabel = opts.auto
    else: autoLabel = None
    print 'Auto Assign:', autoLabel

    if not(opts.subset is None):
        subsetList = opts.subset.split(',')
        unlabelStatus = 'unlabel' in subsetList
        rfiStatus = 'rfi' in subsetList
        sysStatus = 'sys' in subsetList
        interestStatus = 'interest' in subsetList

        subImgFiles = []
        for ifn in imgFiles:
            baseName = os.path.basename(ifn)
            if baseName in labelDict:
                if interestStatus and labelDict[baseName] == 0: subImgFiles.append(ifn)
                elif rfiStatus and labelDict[baseName] == 1: subImgFiles.append(ifn)
                elif sysStatus and labelDict[baseName] == 2: subImgFiles.append(ifn)
            elif unlabelStatus: subImgFiles.append(ifn) # added unlabelled figures to subset list

        imgFiles = subImgFiles

    nfiles = len(imgFiles)
    print 'Found %i figures which fit the criteria'%nfiles
    
    if len(imgFiles) == 0:
        inLoop = False
        print 'WARNING: no files with extension %s found in directory/in the subset catergory'%opts.ext
        exit()
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
            if autoLabel is None:
                print 'Unlabelled'
            else:
                print 'Auto Label:', autoLabel
                labelDict[baseName] = idxLabelDict[autoLabel]

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
            labelDict[baseName] = idxLabelDict['interesting']

        elif ch=='r': # label: RFI
            print 'Label: RFI'
            labelDict[baseName] = idxLabelDict['rfi']

        elif ch=='s': # label: system variability
            print 'Label: system variability'
            labelDict[baseName] = idxLabelDict['systematics']

        elif ch=='u': # remove label
            del labelDict[baseName]

