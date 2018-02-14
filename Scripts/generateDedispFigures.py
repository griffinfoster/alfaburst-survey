#!/usr/bin/env python
"""
Generate a dedispersion plot for each filterbank buffer based on a corresponding DAT file

Requires:
ALFABURST extractBuffer.rb, dedisperseFil.py script
*REMOVED SIGPROC (decimate)
"""

import os,sys
import shutil
import subprocess
import datetime
import pandas as pd
import cPickle as pickle
from StringIO import StringIO # Python 2 specific, use io for Python 3

SCRIPT_DIR = '/home/artemis/Survey/Scripts/' # HARDCODE, see --script_dir option
EXTRACT_SCRIPT = 'extractBuffer.rb' # HARDCODE
PLOTTING_SCRIPT = 'dedisperse/dedisperseFil.py' # HARDCODE
FEATURE_SCRIPT = 'dedisperse/extractFeatures.py' # HARDCODE
#FEATURE_SCRIPT = 'dedisperse/extractFeatures2.py' # HARDCODE

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] FILTERBANK DAT')
    o.add_option('-S', '--script_dir', dest='scriptDir', default=SCRIPT_DIR,
        help='Directory of scripts (generateDedispFigures.py), default: %s'%SCRIPT_DIR)
    o.add_option('-o', '--out_dir', dest='outputDir', default=None,
        help='Output directory to write figures to, default: directory in which the script is called')
    o.add_option('--run', dest='run', action='store_true',
        help='Run commands, default is to only print commands as a dry run')
    o.set_description(__doc__)
    opts, args = o.parse_args(sys.argv[1:])

    # assume input directory and output directory in script call
    fullFilFileName = args[0]
    fullDatFileName = args[1]
    scriptDir = opts.scriptDir
    if opts.outputDir is None: outputDir = os.getcwd()
    else: outputDir = opts.outputDir

    print datetime.datetime.now(), 'Starting dedispersion plot generation'

    if os.path.exists(outputDir):
        if not outputDir.endswith('/'): outputDir += '/'
        print 'OUTPUT DIRECTORY:', outputDir
    else:
        print 'ERROR: OUTPUT DIRECTORY MISSING'
        exit()

    if not scriptDir.endswith('/'): scriptDir += '/'
    print 'SCRIPT DIRECTORY:', scriptDir

    # Get base filenames for the DAT file and corresponding FILTERBANK file
    datFileDir, datFileName = os.path.split(fullDatFileName)
    filFileDir, fbFileName = os.path.split(fullFilFileName)
    if datFileDir=='': datFileDir = '.'
    if filFileDir=='': filFileDir = '.'
    beamID = int(datFileName.split('Beam')[-1][0]) # ASSUMES: file format Beam<BeamID>_...
    tsID = datFileName.split('_dm_')[-1][:-4] # Timestamp ID, useful for finding the corresponding filterbank file
    datFileDir += '/'
    filFileDir += '/'

    # We need to get the buffer IDs for each buffer which is in a comment string at the end of the list of events recorded for the buffer
    content = open(datFileDir + datFileName).read()
    content = content.split('# ------')[-1].split('Done')[:-1] # drop header and split at the end of buffer line
    nbuffer = len(content)
    for buf in content:
        events = buf.split('#')
        bufStr = events[-1] # Get the string with the buffer ID
        bufferID = int(bufStr.split(' ')[3][1:]) # ex: ' Written buffer :2 | MJDstart: 57637.763946759 | Best DM: 10039 | Max SNR: 12.042928695679'
        events = events[0] # remove buffer string
        df = pd.read_csv(StringIO(events), sep=',', names=['MJD', 'DM', 'SNR', 'BinFactor']).dropna()

        df['Beam'] = beamID # Add Beam ID
        df['Flag'] = 0 # Add flag column
        df['BinFactor'] = df['BinFactor'].astype(int) # Convert bin factor to integer
        df['TSID'] = tsID # Timestamp ID
        df['buffer'] = bufferID # buffer ID, unique only timestamped file

        binFactor = df['BinFactor'].median() # take the median as the 'typical' bin factor
        bufMaxSNR = float(bufStr.split(':')[-1])
        bufBestDM = float(bufStr.split('|')[2].split(' ')[-2])

        # Write some buffer meta data to a pickle file to be printed in the dedispersion figure
        mjdStart = bufStr.split(' ')[6]
        metaData =      {'filterbank': fbFileName,
                         'dat': datFileName,
                         'nEvents': len(df.index),
                         'MJD0': mjdStart,
                         'DMmin': df['DM'].min(),
                         'DMmax': df['DM'].max(),
                         'DMmean': df['DM'].mean(),
                         'DMmedian': df['DM'].median(),
                         'maxSNR': bufMaxSNR,
                         'maxMJD': df.ix[df['DM'].idxmax()]['MJD'],
                         'RA': None,
                         'Dec': None
                        }
        metaFileName = fbFileName.split('.fil')[0] + '.buffer%i'%bufferID + '.meta.pkl'
        if opts.run:
            pickle.dump(metaData, open(filFileDir + metaFileName, 'wb'))
        else:
            print 'writing pickle:', filFileDir + metaFileName

        # Extract buffer from FILTERBANK
        # this produces a new filterbank file named with the buffer, e.g. EXTRACT_SCRIPT -b 9 Beam2_fb_D20161030T154704.fil outputs Beam2_fb_D20161030T154704.buffer9.fil in directory script is run from
        cmd = scriptDir + EXTRACT_SCRIPT + ' ' + '-b %i'%bufferID + ' ' + filFileDir + fbFileName
        if opts.run:
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
        else:
            print cmd
        bufFileName = fbFileName.split('.fil')[0] + '.buffer%i'%bufferID + '.fil'

        # Move single buffer filterbank to INPUT_DIR
        if opts.run:
            shutil.move('./' + bufFileName, filFileDir + bufFileName)
        else:
            print 'mv ' + './' + bufFileName + ' ' + filFileDir + bufFileName

        ## Decimate the buffer by the binFactor using SIGPROC
        #decBufFileName = bufFileName.split('.fil')[0] + '.d%i'%binFactor + '.fil'
        #cmd = 'decimate ' + filFileDir + bufFileName + ' -c 1 -t %i > '%binFactor + filFileDir + decBufFileName
        #if opts.run:
        #    proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #    #print proc.communicate() # (stdoutdata, stderrdata)
        #else:
        #    print cmd

        ## Generate dedispersion plot
        #dedispFig = decBufFileName.split('.fil')[0] + '.png'
        #cmd =  scriptDir + PLOTTING_SCRIPT + ' -d %f'%bufBestDM + ' --nodisplay' + ' -S ' + dedispFig + ' ' + filFileDir + decBufFileName
        #if opts.run:
        #    proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #    #print proc.communicate() # (stdoutdata, stderrdata)
        #else:
        #    print cmd

        # Generate dedispersion plot
        dedispFig = bufFileName.split('.fil')[0] + '.d%i'%binFactor + '.png'
        cmd =  scriptDir + PLOTTING_SCRIPT + ' -d %f'%bufBestDM + ' --nodisplay' + ' -M ' + filFileDir + metaFileName + ' -S ' + dedispFig + ' -t %i '%binFactor + ' --zerodm ' + filFileDir + bufFileName
        if opts.run:
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
        else:
            print cmd

        # Extract Features, write to buffer pickle file
        cmd =  scriptDir + FEATURE_SCRIPT + ' -d %f'%bufBestDM + ' -M ' + filFileDir + metaFileName + ' -t %i '%binFactor + filFileDir + bufFileName
        if opts.run:
            print cmd
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
            print stdoutdata, stderrdata
        else:
            print cmd

        # Clean up intermediate data products
        print 'Removing intermediate files'
        if opts.run:
            os.remove(filFileDir + bufFileName)
            #os.remove(filFileDir + 'metadata.pkl')
        else:
            print 'rm ' + filFileDir + bufFileName
            #print 'rm ' + filFileDir + 'metadata.pkl'

        # Move figure to OUTPUT_DIR
        if opts.run:
            shutil.move('./' + dedispFig, outputDir + dedispFig)
            shutil.move(filFileDir + metaFileName, outputDir + metaFileName)
        else:
            print 'mv ' + filFileDir + dedispFig + ' ' + outputDir + dedispFig
            print 'mv ' + filFileDir + metaFileName + ' ' + outputDir + metaFileName

    print datetime.datetime.now(), 'Finished dedispersion plot generation'

