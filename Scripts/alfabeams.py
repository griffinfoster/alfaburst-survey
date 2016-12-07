#!/usr/bin/python

# Plots the ALFA centre beam using the given co-ordinates, a circle denoting
# the centres of the six outer beams, and the locations of souces provided in
# the file 'sources'

import sys
import math
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


def texInit(fontsize):
    # set plotting font properties
    font = {"family" : "serif",
            "weight" : "regular",
            "size"   : fontsize}
    plt.rc("font", **font)
    # force matplotlib to use Type 1 fonts instead of Type 3
    matplotlib.rcParams["ps.useafm"] = True
    matplotlib.rcParams["pdf.use14corefonts"] = True
    matplotlib.rcParams["text.usetex"] = True


def hhmm2deg(hh, mm):
    return int(hh) * degPerHour + ((float(mm) / 60) * degPerHour)


def ddmm2deg(ddmm):
    fDec = float(ddmm)
    return math.modf(fDec / 100)[1]                                           \
            + ((math.modf(fDec / 100)[0] * 100) / 60.0)


#texInit(16)

# constants
# HWHM of the centre beam
hwhm = 1.775        # arcmin
# distance between the beam centre of the ALFA centre beam and the beam centre
# of an outer beam
r = 5.92            # arcmin
# degrees per hour
degPerHour = 15
# arcmin in degrees
arcmin2degFactor = 1.0 / 60
# convert arcmin values to degrees
hwhm *= arcmin2degFactor
r *= arcmin2degFactor

# read the pointings
pointings = np.loadtxt("pointings", delimiter=",")
i = 0
for pointing in pointings:
    pntRA = pointing[0] * degPerHour
    pntDec = pointing[1]
    # plot the beam centre
    plt.plot(pntRA, pntDec, "rx")
    # plot the beam number
    plt.text(pntRA + 0.005, pntDec + 0.005, str(i), color="black", fontsize=12)
    # plot the extent of the beam, up to HWHM on all sides
    beam = plt.Circle((pntRA, pntDec), hwhm, color="r", fill=False)
    fig = plt.gcf()
    fig.gca().add_artist(beam)
    i += 1

#20:04:52.286
srcRA = 20.0811905556 * degPerHour
#+31:37:10.01
srcDec = 31.6194472222 
plt.plot(srcRA, srcDec, "bo")
plt.text(srcRA + 0.005, srcDec + 0.005, "B2002+31", color="black", fontsize=12)

'''
#19:13:21.061
srcRA = 19.22251694444444444443 * degPerHour
#+09:04:45.4
srcDec = 9.07927777777777777777
plt.plot(srcRA, srcDec, "bo")
plt.text(srcRA + 0.005, srcDec + 0.005, "J1913+0904", color="black", fontsize=12)
'''

'''
#19:15:29.984
srcRA = 19.25832888888888888888 * degPerHour
#+10:09:43.67  
srcDec = 10.16213055555555555555
plt.plot(srcRA, srcDec, "bo")
plt.text(srcRA + 0.005, srcDec + 0.005, "B1913+10", color="black", fontsize=12)

#19:03:29.981
srcRA = 19.0583280556 * degPerHour
#01:35:38.33  
srcDec = 1.5939805556
plt.plot(srcRA, srcDec, "bo")
plt.text(srcRA + 0.005, srcDec + 0.005, "B1900+01", color="black", fontsize=12)
'''

'''
# read the source list
sources = np.loadtxt("sources", dtype=str)

#delimIdx = 9
RA = np.zeros(len(sources))
dec = np.zeros(len(sources))
for i in range(len(sources)):
    source = sources[i]
    # convert the hhmm right ascension to degrees
    RA[i] = hhmm2deg(source[0:2], source[2:4])
    # convert the ddmm declination to degrees
    if source[4] != "+" and source[4] != "-":
        print "ERROR: Incorrect co-ordinate format."
        continue
    dec[i] = ddmm2deg(source[4:9])
    #if i >= delimIdx:
    #    plt.plot(RA[i], dec[i], "mo")
    #else:
    #    plt.plot(RA[i], dec[i], "bo")
    plt.plot(RA[i], dec[i], "bo")
    # plot the pulsar name
    plt.text(RA[i] + 0.005, dec[i] + 0.005, "J" + source, color="black", fontsize=12)
'''

plt.xlabel("RA (deg.)")
plt.ylabel("Dec. (deg.)")

plt.show()

