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

idxLabelDict = { 0 : 'Interesting, follow up',
                 9 : 'Known Pulsar',
                 1 : 'Unclipped RFI/Noise',
                 2 : 'Wide-band, long-duration in time clipped RFI (2016+)',
                 3 : 'Wide-band, short-duration in time clipped RFI (2016+)',
                 4 : 'Wide-band, short duration clipped RFI (2015)',
                 5 : 'Sharp bandpass transition',
                 6 : 'Wide-band, bursty clipped RFI (2015)',
                 7 : 'Error in spectra captue or replacement',
                 8 : 'Systematic int/float overflow'}

labelStrList = map(str, idxLabelDict)

def keyInformationStr(idxLabelDict):
    
    oStr = 'Keys:\n' + \
            '\tq: quit\n' + \
            '\tb: back one image\n' + \
            '\tn: next one image\n' + \
            '\tu OR r: remove label\n' + \
            '\th: re-print this information\n'

    for key,val in idxLabelDict.iteritems():
        oStr += '\t%s: %s\n'%(str(key), val)

    return oStr

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
    o.add_option('--dbfile', dest='dbfile', default='imgLabel2.pkl',
        help='CSV file of image labels, default: imgLabel2.pkl')
    o.add_option('-e', '--ext', dest='ext', default='png',
        help='Image extension to label, default: png')
    o.add_option('-i', '--index', dest='index', default=0, type='int',
        help='Starting index, default: 0')
    o.add_option('--subset', dest='subset', default=None,
        help='Only show a subset of figures, use key value, can be comma separated. Example: u,9,0 only shows unlabelled, interesting, and known pulsar figures ')
    o.add_option('-a', '--auto', dest='auto', default=None,
        help='Auto assign a label to unlabelled images, use key value, e.g. 1 is wideband clipped RFI')
    opts, args = o.parse_args(sys.argv[1:])

    if os.path.isdir(args[0]):
        imgDir = os.path.join(args[0], '')
        # get list of images in directory
        print 'Labels for images in directory:', imgDir
        imgFiles = sorted(glob.glob(imgDir + '*.' + opts.ext))
    else:
        imgFiles = args

    # load dbfile if exists, else create an empty dict
    """ labelDict format:
            {string of image filename (no path) : integer of label, ... }
    """
    if os.path.exists(opts.dbfile):
        print 'Loading', opts.dbfile
        labelDict = pickle.load(open(opts.dbfile, 'rb'))
    else:
        labelDict = {}

    print keyInformationStr(idxLabelDict)

    if opts.auto is None:
        autoLabel = None
    else:
        if int(opts.auto) in idxLabelDict.keys():
            autoLabel = int(opts.auto)
            print 'Auto Assign (%i):'%autoLabel, idxLabelDict[autoLabel]
        else: autoLabel = None

    if not(opts.subset is None):
        subsetList = opts.subset.split(',')
        unlabelStatus = 'u' in subsetList or 'r' in subsetList

        subImgFiles = []
        for ifn in imgFiles:
            baseName = os.path.basename(ifn)
            if baseName in labelDict:
                if str(labelDict[baseName]) in subsetList: subImgFiles.append(ifn)
            elif unlabelStatus: subImgFiles.append(ifn) # added unlabelled figures to subset list

        imgFiles = subImgFiles

    nfiles = len(imgFiles)
    print 'Found %i figures which fit the criteria'%nfiles
    
    if len(imgFiles) == 0:
        inLoop = False
        print 'WARNING: no files matching the option parameters found in directory/in the subset catergory'
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
            print 'Current Label (%s):'%str(labelDict[baseName]), idxLabelDict[labelDict[baseName]]
        else:
            if autoLabel is None:
                print 'Unlabelled'
            else:
                print 'Auto Label (%i):'%autoLabel, idxLabelDict[autoLabel]
                labelDict[baseName] = autoLabel

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

        elif ch in labelStrList:
            print 'Label (%i):'%int(ch), idxLabelDict[int(ch)]
            labelDict[baseName] = int(ch)

        elif ch=='u' or ch=='r': # remove label
            del labelDict[baseName]

        elif ch=='h':
            print keyInformationStr(idxLabelDict)

        else: print 'Key does not map to known label'

