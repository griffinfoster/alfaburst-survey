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

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] INPUT_DIR OUTPUT_DIR')
    o.add_option('-S', '--script_dir', dest='scriptDir', default=SCRIPT_DIR,
        help='Directory of scripts (generateDedispFigures.py), default: %s'%SCRIPT_DIR)
    o.add_option('--run', dest='run', action='store_true',
        help='Run commands, default is to only print commands as a dry run')
    o.set_description(__doc__)
    opts, args = o.parse_args(sys.argv[1:])

    # assume input directory and output directory in script call
    inputDir = args[0]
    outputDir = args[1]
    scriptDir = opts.scriptDir

    print datetime.datetime.now(), 'Starting ALFABURST Status Report Generation'

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
    while len(datFiles) > 0:

        # Parse the first dat file to find a time window
        refDatFile = os.path.split(datFiles[0])[1]
        refDateTime = datetime.datetime.strptime(refDatFile.split('_dm_')[-1], 'D%Y%m%dT%H%M%S.dat') # reference datetime in AST local time
        # Define a time window: 12:59 DAY N-1 to 13:00 DAY N
        if refDateTime.hour < 13:
            startDateTime = refDateTime - datetime.timedelta(hours = refDateTime.hour, minutes = refDateTime.minute, seconds=refDateTime.second) - datetime.timedelta(hours = 11)
        else:
            startDateTime = refDateTime - datetime.timedelta(hours = refDateTime.hour, minutes = refDateTime.minute, seconds=refDateTime.second) + datetime.timedelta(hours = 13)
        endDateTime = startDateTime + datetime.timedelta(days = 1)
        print 'Time Window:', startDateTime, '---', endDateTime
        
        # Find all DAT files in the time window
        datsInWindow = [datFiles[0]]
        datFiles.remove(datFiles[0])
        for fullDatFile in datFiles:
            datFile = os.path.split(fullDatFile)[1]
            datDateTime = datetime.datetime.strptime(datFile.split('_dm_')[-1], 'D%Y%m%dT%H%M%S.dat') # datetime in AST local time
            if startDateTime < datDateTime and datDateTime < endDateTime:
                datsInWindow.append(fullDatFile)
                datFiles.remove(fullDatFile)
        
        # Convert DAT files in the time window into a dataframe (datConverter.py)
        outFileBase = startDateTime.strftime('comb_D%Y%m%dT%H%M%S_AST')
        csvFile = outFileBase + '.csv'
        cmd = scriptDir + DATCONVERT_SCRIPT + ' --output=' + outputDir + csvFile +  ' ' + ' '.join(datsInWindow)
        if opts.run:
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
        else:
            print cmd

        # Generate DM vs Time Plot (plotDMvsTime.py)
        utcStart = tz.localize(startDateTime).astimezone(pytz.utc)
        utcEnd = tz.localize(endDateTime).astimezone(pytz.utc)
        outFigure = outFileBase + '.png'
        cmd = scriptDir + DMPLOT_SCRIPT + ' --ignore' + ' --nodisplay' + ' --utc' + ' --utc_start=' + utcStart.strftime('%Y%m%d_%H%M%S') + ' --utc_end=' + utcEnd.strftime('%Y%m%d_%H%M%S')  + ' --savefig=' + outputDir + outFigure + ' ' + outputDir + csvFile
        if opts.run:
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
        else:
            print cmd

    # Move DAT file to OUTPUT_DIR   
    cmd = 'mv ' + inputDir + '*.dat ' + outputDir
    if opts.run:
        proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
    else:
        print cmd

    print datetime.datetime.now(), 'Finished ALFABURST Status Report Generation'

"""
dailyStatusGen.py: (on abc3)
     check if new .dat files in DIR
     if new files:
         select all dat files in 24 hour window
         for each time window:
             datConverter.py: combine all .dat files in an observing night into a dataframe, save dataframe
             plotDMvsTime.py: generate figure
             move plot, dataframe to processed directory
        * move dat files
        * generate static webpage
        * scp figures and html to webserver
        * run and send statusReport.py
"""
