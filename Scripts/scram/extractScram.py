#!/usr/bin/env python
"""
Extract the status information from (compressed) SCRAM files to local text files
"""

import os,sys
import shutil
import subprocess
import glob
import datetime

S6_OBS_BIN = 's6_observatory_readonly'
S6_OBS_DIR = '/home/griffin/projects/serendip6/src/' # HARDCODE, see --bin_dir option

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] SCRAM_FILES')
    o.add_option('-b', '--bin_dir', dest='binDir', default=S6_OBS_DIR,
        help='Directory location on %s binary, default: %s'%(S6_OBS_BIN, S6_OBS_DIR))
    o.add_option('--run', dest='run', action='store_true',
        help='Run commands, default is to only print commands as a dry run')
    o.set_description(__doc__)
    opts, args = o.parse_args(sys.argv[1:])

    # assume input directory and output directory in script call
    binDir = opts.binDir

    print datetime.datetime.now(), 'Starting ALFABURST Post-Processing'

    if not binDir.endswith('/'): binDir += '/'
    print 'S6 BINARY DIRECTORY:', binDir

    # Check for dat files in INPUT_DIR
    scramFiles = sorted(args)
    if len(scramFiles) > 0:
        for fid, scramFn in enumerate(scramFiles):
            print scramFn + ' (%i of %i)'%(fid+1, len(scramFiles)), datetime.datetime.now()

            tarFn = os.path.split(scramFn)[1]
            baseFnList = tarFn.split('.')
            baseFn = baseFnList[0] + '.' + baseFnList[1]

            # Copy compressed SCRAM file to working directory
            cmd = 'cp %s %s'%(scramFn, './' + tarFn)
            if opts.run:
                shutil.copy(scramFn, './' + tarFn)
            else:
                print cmd

            # gunzip working directory copy
            cmd = 'gunzip --force --name --suffix .at_ucb ' + tarFn
            if opts.run:
                proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
                print stdoutdata, stderrdata
            else:
                print cmd

            # run scram extraction binary
            cmd = '%s -nodb -stdout -infile %s'%(S6_OBS_DIR + S6_OBS_BIN, baseFn)
            if opts.run:
                proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (stdoutdata, stderrdata) = proc.communicate() # (stdoutdata, stderrdata)
                print stdoutdata, stderrdata
            else:
                print cmd

            # remove SCRAM file copy
            cmd = 'rm %s'%(baseFn)
            if opts.run:
                os.remove(baseFn)
            else:
                print cmd

    print datetime.datetime.now(), 'Finished SCRAM packet extraction'

