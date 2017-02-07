#!/usr/bin/env python
"""
Plot the ALFABURST sky coverage and sampling based on cognizeALFA.log (converted with parseCognizeALFALog.py)

ex:

plotSuveryCoverage.py cognize.pkl --NSIDE=128 --gal_cut=10 --sampling --gsm=gsm2016/output/gsm2016_1.400e+00ghz_MJysr_healpyRING.txt --gsm_max=0.4 -s alfaburst_sampling.png
plotSuveryCoverage.py cognize.pkl --NSIDE=128 --gal_cut=10 --max=200 -s alfaburst_coverage.png

"""

import numpy as np
import matplotlib.pyplot as plt
import astropy.units
from astropy.coordinates import SkyCoord
import healpy as hp
import pandas as pd
import sys,os

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] LOG_PKL_FILE')
    o.add_option('--NSIDE', dest='nside', default=256, type='int',
        help='Healpix NSIDE, default: 256')
    o.add_option('--max', dest='max', default=None, type='float',
        help='maximum observation time to clip, default: None')
    o.add_option('--gal_cut', dest='gal_cut', default=None, type='int',
        help='Cut points +/- degrees around the galactic plane, default: None')
    o.add_option('--cmap', dest='cmap', default='Blues',
        help='plotting colormap, default: Blues')
    o.add_option('-s', '--savefig', dest='savefig', default=None,
        help='Save figure to file')
    o.add_option('--coord', dest='coord', default='G',
        help='Coordinate system to plot in, G (Galactic), C (Celestial), default: G (Galactic)')
    o.add_option('--sampling', dest='sampling', action='store_true',
        help='Plot sampling of the sky instead of the coverage')
    o.add_option('--gsm', dest='gsm', default=None,
        help='Global Sky Model to plot')
    o.add_option('--gsm_max', dest='gsm_max', default=None, type='float',
        help='If plotting a GSM, set maximum, default: None')
    o.add_option('--gsm_min', dest='gsm_min', default=None, type='float',
        help='If plotting a GSM, set minimum, default: None')
    o.set_description(__doc__)
    opts, args = o.parse_args(sys.argv[1:])

    print 'Reading', args[0]

    df = pd.read_pickle(args[0])
    activeObs = df[df.status==1] # select log of active observations

    # NOTE:only using the central beam
    # RA in hours, DEC in degrees and flipped
    ra0 = activeObs['RA0'].values * (15. * np.pi / 180.) # Hours to radians
    #dec0 = -1. * (activeObs['DEC0'].values * (np.pi / 180.) - (np.pi / 2.)) # Degrees to radians, Dec needs to be flipped
    dec0 = (activeObs['DEC0'].values * (np.pi / 180.) ) # Degrees to radians
    tint = activeObs['tint'].values # integration time in seconds

    print 'Total observation time: %i seconds'%(np.sum(tint))

    # Convert (RA, Dec) to Galactic (lat, long)
    coords = SkyCoord(ra=ra0 * astropy.units.rad, dec=dec0 * astropy.units.rad, frame='icrs')

    # NOTE: nsides=256, this is the approxomate sky coverage of the ALFA FWHM of the 7 combined beams
    hpMap = np.zeros(hp.nside2npix(opts.nside))
    hpMask = np.zeros(hp.nside2npix(opts.nside))

    gall = coords.galactic.l.degree
    galb = coords.galactic.b.degree

    # cut out a galactic plane strip
    if opts.gal_cut is not None:
        idx = np.argwhere(np.abs(galb) > opts.gal_cut)
        gall = gall[idx].flatten()
        galb = galb[idx].flatten()
        tint = tint[idx].flatten()

        print 'Galaxy Cut Observation time: %i seconds'%(np.sum(tint))

    for pid in np.arange(gall.shape[0]): # NOTE: dumb and slow, but the call to hp.ang2pix() with dec/ra arrays doesn't seem to work
        pixVal = hp.ang2pix(opts.nside, gall[pid], galb[pid], lonlat=True)
        hpMap[pixVal] += tint[pid]
        hpMask[pixVal] = True

    if opts.max is not None: # Clip max values
        print 'Max integration time %f clipped to %f'%(hpMap.max(), opts.max)
        hpMap = np.clip(hpMap, 0., opts.max)

    if opts.gsm is not None: # plot the output to GSM
        print 'Load GSM'
        gsm = np.loadtxt(opts.gsm)
        gsmNside = hp.npix2nside(gsm.shape[0])
        if gsmNside != opts.nside: # downgrade or upgrade the GSM to the number of pixels of the survey resolution
            gsm = hp.ud_grade(gsm, nside_out=opts.nside, order_in='RING', order_out='RING')
        print 'GSM (Min, Max):', np.min(gsm), np.max(gsm)
        if opts.gsm_min is None: gsm_min = np.min(gsm)
        else: gsm_min = opts.gsm_min
        if opts.gsm_max is None: gsm_max = np.max(gsm)
        else: gsm_max = opts.gsm_max
        gsm = np.clip(gsm, gsm_min, gsm_max)


    fig = plt.figure(figsize=(12,7)) # (width, height)

    if opts.coord.upper() == 'C':
        coord = 'GC'
        gradCoord = 'C'
    else:
        coord = 'G'
        gradCoord = 'G'

    if opts.sampling is not None: # plot the sampling function
        if opts.gsm is not None:
            sampIdx = np.argwhere(hpMask == 1)
            gsm[sampIdx] = np.max(gsm)
            hp.mollview(gsm, fig=fig.number, coord=coord, cmap=plt.get_cmap(opts.cmap), unit='MJy/sr', title='ALFABURST Sky Sampling')
        else: hp.mollview(hpMask, fig=fig.number, coord=coord, cmap=plt.get_cmap(opts.cmap), cbar=False, title='ALFABURST Sky Sampling')
    else: # plot sky integrated coverage
        hp.mollview(hpMap, fig=fig.number, coord=coord, cmap=plt.get_cmap(opts.cmap), unit='seconds', title='ALFABURST Sky Coverage')
    
    hp.graticule(coord=gradCoord)

    if opts.savefig is not None: # save figure
        plt.savefig(opts.savefig, bbox_inches='tight')
    else:
        plt.show()

