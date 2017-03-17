#!/usr/bin/env python
"""
Plot the bandpass output of the RFI Clipper
"""

import sys,os
import numpy as np

# Check if $DISPLAY is set (for handling plotting on remote machines with no X-forwarding)
if os.environ.has_key('DISPLAY'):
    import matplotlib.pyplot as plt
else:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] BANDPASS_DAT')
    o.add_option('-S', '--savefig', default=None,
        help='Save figure to file, file type determined based on extension.')
    o.add_option('--nodisplay', action='store_true',
        help='Do not display the figure')
    o.add_option('--log', dest='log', action='store_true',
        help='Plot y-axis in log space')
    o.set_description(__doc__)
    opts, args = o.parse_args(sys.argv[1:])

    fig, axes = plt.subplots(figsize=(10,5)) # (width, height)

    for fn in args:
        bp = np.loadtxt(fn) # Bandpass file is a simple list of floats separated by carriage returns
        plt.plot(bp)
    
    plt.xlabel('Frequency Index')
    plt.ylabel('Amplitude')
    plt.title('Derived Bandpass')

    if opts.log:
        axes.set_yscale('log')
    
    if not (opts.savefig is None): 
        print 'Saving figure to', opts.savefig
        plt.savefig(opts.savefig)
    if not opts.nodisplay: plt.show()

