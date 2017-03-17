#!/usr/bin/env python
"""
Daily post-processing script to be run on each abcX node as user artemis
Find .dat/.fil file pairs in an input directory, generate a dedispersion plot for each filterbank buffer, transfer to finished products to an output directory
"""

import os,sys
import shutil
import subprocess
import glob
import datetime

SCRIPT_DIR = '/home/artemis/Survey/Scripts/' # HARDCODE, see --script_dir option
ABC3_DIR = '/databk/datProcessing/' # HARDCODE, see --abc3 option
GENERATOR_SCRIPT = 'generateDedispFigures.py'

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] INPUT_DIR OUTPUT_DIR')
    o.add_option('-S', '--script_dir', dest='scriptDir', default=SCRIPT_DIR,
        help='Directory of scripts (generateDedispFigures.py), default: %s'%SCRIPT_DIR)
    o.add_option('--abc3', dest='abc3Dir', default=ABC3_DIR,
        help='Directory on ABC3 to store DAT files, default: %s'%ABC3_DIR)
    o.add_option('--run', dest='run', action='store_true',
        help='Run commands, default is to only print commands as a dry run')
    o.set_description(__doc__)
    opts, args = o.parse_args(sys.argv[1:])

    # assume input directory and output directory in script call
    inputDir = args[0]
    outputDir = args[1]
    scriptDir = opts.scriptDir
    abc3Dir = opts.abc3Dir

    print datetime.datetime.now(), 'Starting ALFABURST Post-Processing'

    if os.path.exists(inputDir):
        if not inputDir.endswith('/'): inputDir += '/'
        print 'INPUT DIRECTORY:', inputDir
    else:
        print 'ERROR: INPUT DIRECTORY MISSING'
        exit()

    if os.path.exists(outputDir):
        if not outputDir.endswith('/'): outputDir += '/'
        print 'OUTPUT DIRECTORY:', outputDir
    else:
        print 'ERROR: OUTPUT DIRECTORY MISSING'
        exit()

    if not scriptDir.endswith('/'): scriptDir += '/'
    print 'SCRIPT DIRECTORY:', scriptDir

    # Check for dat files in INPUT_DIR
    datFiles = glob.glob(inputDir+'*.dat')
    if len(datFiles) > 0:
        for fid, fullDatFile in enumerate(datFiles):
            print fullDatFile + ' (%i of %i)'%(fid+1, len(datFiles))

            # Get base filenames for the DAT file and corresponding FILTERBANK file
            datFileName = os.path.split(fullDatFile)[1]
            beamStr, tsID = datFileName[:-4].split('_dm_')
            beamID = int(beamStr[-1])

            # Sometimes the DAT and FIL files are off by a second, check for this
            #fbFileName = beamStr + '_fb_' + tsID + '.fil'
            fbFileNameGlob = beamStr + '_fb_' + tsID[:-2] + '*.fil'
            fbFileName = os.path.split(glob.glob(inputDir + fbFileNameGlob)[0])[1]

            # Generate a dedispersed plot for all buffers in a fil file based on the dat file using generateDedispFigures.py
            cmd = scriptDir + GENERATOR_SCRIPT + ' --out_dir=' + outputDir + ' ' + inputDir + fbFileName + ' ' + inputDir + datFileName + ' --run'
            if opts.run:
                proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
                print stdoutdata, stderrdata
            else:
                print cmd

            # Move FILTERBANK file to OUTPUT_DIR
            if opts.run: shutil.move(inputDir + fbFileName, outputDir + fbFileName)
            else: print 'mv ' + inputDir + fbFileName + ' ' + outputDir + fbFileName

            # SCP DAT file to abc3
            cmd = 'scp ' + inputDir + datFileName + ' artemis@abc3:' + abc3Dir
            if opts.run:
                proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
            else:
                print cmd

            # Move DAT file to OUTPUT_DIR
            if opts.run:
                shutil.move(inputDir + datFileName, outputDir + datFileName)
            else:
                print 'mv ' + inputDir + datFileName + ' ' + outputDir + datFileName

    print datetime.datetime.now(), 'Finished ALFABURST Post-Processing'

