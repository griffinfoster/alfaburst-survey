#!/usr/bin/env python
"""
Daily status reporting script run on abc3 node as user artemis
Find dat files in input directory, generate reports on 24 hour time windows, generate a DM vs Time plot containing all beams (plotDMvsTime.py), and a combined event dataframe (datConverter.py)
"""

import os,sys
import shutil
import subprocess
import glob
import datetime
import pytz

LOCALTZ = 'America/Puerto_Rico' # Arecibo time zone
tz = pytz.timezone(LOCALTZ)
SCRIPT_DIR = '/home/artemis/Survey/Scripts/' # HARDCODE, see --script_dir option
DMPLOT_SCRIPT = 'plotDMvsTime.py'
DATCONVERT_SCRIPT = 'datConverter.py'
BUFFER_FILE = '/databk/datProcessing/output/ALFAbuffers.pkl'

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] INPUT_DIR PROC_DIR OUTPUT_DIR')
    o.add_option('-S', '--script_dir', dest='scriptDir', default=SCRIPT_DIR,
        help='Directory of scripts (generateDedispFigures.py), default: %s'%SCRIPT_DIR)
    o.add_option('--run', dest='run', action='store_true',
        help='Run commands, default is to only print commands as a dry run')
    o.set_description(__doc__)
    opts, args = o.parse_args(sys.argv[1:])

    # assume input directory and output directory in script call
    inputDir = args[0]
    procDir = args[1]
    outputDir = args[2]
    scriptDir = opts.scriptDir

    print datetime.datetime.now(), 'Starting ALFABURST Status Report Generation'

    if os.path.exists(inputDir):
        if not inputDir.endswith('/'): inputDir += '/'
        print 'INPUT DIRECTORY:', inputDir
    else:
        print 'ERROR: INPUT DIRECTORY MISSING'
        exit()
        
    # PROCESSED DIRECTORY: move dat files once processed
    if os.path.exists(procDir):
        if not procDir.endswith('/'): procDir += '/'
        print 'PROCESSED DIRECTORY:', procDir
    else:
        print 'ERROR: PROCESSED DIRECTORY MISSING'
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
    if len(datFiles) > 0: datFiles = sorted(datFiles, key=lambda x: x.split('_')[-1])
    while len(datFiles) > 0:

        # Parse the first dat file to find a time window
        refDatFile = os.path.split(datFiles[0])[1]
        refDateTime = datetime.datetime.strptime(refDatFile.split('_dm_')[-1], 'D%Y%m%dT%H%M%S.dat') # reference datetime in AST local time
        ## Define a time window: 12:59 DAY N-1 to 13:00 DAY N
        #if refDateTime.hour < 13:
        #    startDateTime = refDateTime - datetime.timedelta(hours = refDateTime.hour, minutes = refDateTime.minute, seconds=refDateTime.second) - datetime.timedelta(hours = 11)
        #else:
        #    startDateTime = refDateTime - datetime.timedelta(hours = refDateTime.hour, minutes = refDateTime.minute, seconds=refDateTime.second) + datetime.timedelta(hours = 13)
        #endDateTime = startDateTime + datetime.timedelta(days = 2)

        startDateTime = datetime.datetime(*refDateTime.timetuple()[:3])
        endDateTime = datetime.datetime(*refDateTime.timetuple()[:3]) + datetime.timedelta(days = 1)
        # Define a time window: 12:59 DAY N-1 to 13:00 DAY N
        if refDateTime.hour < 13:
            startDateTime -= datetime.timedelta(hours = 11)
            endDateTime -= datetime.timedelta(hours = 11)
        else:
            startDateTime += datetime.timedelta(hours = 13)
            endDateTime += datetime.timedelta(hours = 13)
        print 'Time Window:', startDateTime, '---', endDateTime
        
        # Find all DAT files in the time window
        datsInWindow = []
        for fullDatFile in datFiles:
            datFile = os.path.split(fullDatFile)[1]
            datDateTime = datetime.datetime.strptime(datFile.split('_dm_')[-1], 'D%Y%m%dT%H%M%S.dat') # datetime in AST local time
            if startDateTime <= datDateTime and datDateTime < endDateTime: # if DAT file in time window
                datsInWindow.append(fullDatFile)
        # remove datsInWindow from datFiles list
        datFiles = [dfn for dfn in datFiles if dfn not in datsInWindow]
        
        # Convert DAT files in the time window into a dataframe (datConverter.py)
        outFileBase = startDateTime.strftime('comb_D%Y%m%dT%H%M%S_AST')
        csvFile = outFileBase + '.csv'
        cmd = scriptDir + DATCONVERT_SCRIPT + ' --buffer_output=' + BUFFER_FILE + ' --output=' + outputDir + csvFile +  ' ' + ' '.join(datsInWindow)
        if opts.run:
            print cmd
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
            print stderrdata
        else:
            print cmd

        # Generate DM vs Time Plot (plotDMvsTime.py)
        utcStart = tz.localize(startDateTime).astimezone(pytz.utc)
        utcEnd = tz.localize(endDateTime).astimezone(pytz.utc)
        outFigure = outFileBase + '.png'
        cmd = scriptDir + DMPLOT_SCRIPT + ' --ignore' + ' --nodisplay' + ' --utc' + ' --utc_start=' + utcStart.strftime('%Y%m%d_%H%M%S') + ' --utc_end=' + utcEnd.strftime('%Y%m%d_%H%M%S')  + ' --savefig=' + outputDir + outFigure + ' ' + outputDir + csvFile
        if opts.run:
            print cmd
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
            print stderrdata
        else:
            print cmd

    # Move DAT file to _DIR   
    cmd = 'mv ' + inputDir + '*.dat ' + procDir
    if opts.run:
        print cmd
        proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
        print stderrdata
    else:
        print cmd

    print datetime.datetime.now(), 'Finished ALFABURST DAT Processing'

