#!/usr/bin/python

# makeFil.py
# Makes a filterbank file from raw ALFABURST data
#
# KR@AO 6Jul2014
# Modified by Jayanth Chennamangalam on 2015.02.21

import os
import sys
import struct
import numpy as np


def prep_string(string):
    return struct.pack('i', len(string))+string

def prep_double(name, value):
    return prep_string(name)+struct.pack('d', float(value))

def prep_int(name, value):
    return prep_string(name)+struct.pack('i', int(value))

hdr = prep_string("HEADER_START")
hdr += prep_int("telescope_id", 1)
hdr += prep_int("machine_id", 0)
hdr += prep_int("data_type", 1) # 1 = filterbank, 2 = timeseries
hdr += prep_string("source_name")
hdr += prep_string("test")
hdr += prep_double("src_raj", 0.0)
hdr += prep_double("src_dej", 0.0)
hdr += prep_int("nbits", 16)
hdr += prep_int("nifs", 1)
#hdr += prep_int("nchans", 1024)
#hdr += prep_double("fch1", 1541)
hdr += prep_int("nchans", 512)
hdr += prep_double("fch1", 1513)
#hdr += prep_int("nchans",4096)
#hdr += prep_double("fch1", 1625)
hdr += prep_double("foff", -0.109375)
hdr += prep_double("tstart", 50000)
hdr += prep_double("tsamp", 0.000128)
hdr += prep_string("HEADER_END")

# open filterbank file for writing
fid = open("test.fil", "wb")
fid.write(hdr)

ABHeaderLen = 8
ABPayloadLen = 8192
ABFooterLen = 8
# length of AB section in packet, in bytes
PktSize = ABHeaderLen + ABPayloadLen + ABFooterLen
PCAPFileHeaderLen = 24              # bytes
PCAPPacketHeaderLen = 58            # bytes

NChans = 4096
NChansPerPkt = NChans / 4

f = open(sys.argv[1], "rb")
f.seek(PCAPFileHeaderLen, 0)        # skip pcap file header

nPkts = int(sys.argv[2])

# read in the packets from the .pcap file
i = 0
while True:
    f.seek(PCAPPacketHeaderLen,1)   # skip pcap packet header
    data = f.read(PktSize)
    header = struct.unpack(">Q", data[0:8])[0]
    integCount = header >> 16
    # get the spectral quarter
    sq = struct.unpack(">B", data[6:7])[0]
    # get the beam ID
    b = struct.unpack(">B", data[7:8])[0]
    # start from spectral quarter 0
    if sq != 3:
        i += 1
        continue
    else:
        prevSq = sq
        prevIntegCount = integCount
        break
skip = i + 1
print "Skipping", skip, "packets..."

# NOTE: assuming that there are no missing packets

numMissPkts = 0

# initialize accumulators
XXacc = np.zeros(NChans, dtype=np.uint16)
YYacc = np.zeros(NChans, dtype=np.uint16)
for i in range(nPkts - skip):
    f.seek(PCAPPacketHeaderLen, 1)   # skip pcap packet header
    data = f.read(PktSize)
    header = struct.unpack(">Q", data[0:8])[0]
    integCount = header >> 16
    # get the spectral quarter
    sq = struct.unpack(">B", data[6:7])[0]

    if (prevSq + 1) % 4 != sq:
        icDiff = integCount - prevIntegCount
        if 0 == icDiff:     # same integration, different spectral quarter
            sqDiff = sq - prevSq
            numMissPkts += (sqDiff - 1)
            print prevSq, sq, prevIntegCount, integCount, numMissPkts
        else:               # different integration
            numMissPkts += ((3 - prevSq) + sq + 4 * (icDiff - 1))
            print prevSq, sq, prevIntegCount, integCount, numMissPkts

    if 0 == sq:
        icDiff = integCount - prevIntegCount
        if icDiff != 1:
            numMissPkts += ((3 - prevSq) + sq + 4 * (icDiff - 1))
            print prevSq, sq, prevIntegCount, integCount, numMissPkts

    prevSq = sq
    prevIntegCount = integCount

    # read in data, skipping first 8 bytes (header) and ignoring last
    # 8 bytes (footer)
    data = np.array((struct.unpack(">4096H", data[8:8200])), dtype=np.uint16)

    # extract the pseudo-Stokes components
    XXacc[sq*NChansPerPkt:sq*NChansPerPkt+NChansPerPkt] = data[0::4]
    YYacc[sq*NChansPerPkt:sq*NChansPerPkt+NChansPerPkt] = data[1::4]

    if 3 == sq:
        # compute Stokes I
        #(XXacc + YYacc).tofile(fid, sep="")
        #(XXacc + YYacc)[768:1792].astype(np.float32).tofile(fid, sep="")

        #(XXacc + YYacc)[3584:4096].astype(np.uint16).tofile(fid, sep="")
        #(XXacc + YYacc)[3072:3584].astype(np.uint16).tofile(fid, sep="")
        #(XXacc + YYacc)[2560:3072].astype(np.uint16).tofile(fid, sep="")
        #(XXacc + YYacc)[2048:2560].astype(np.uint16).tofile(fid, sep="")
        #(XXacc + YYacc)[1536:2048].astype(np.uint16).tofile(fid, sep="")
        (XXacc + YYacc)[1024:1536].astype(np.uint16).tofile(fid, sep="")
        #(XXacc + YYacc)[512:1024].astype(np.uint16).tofile(fid, sep="")
        #(XXacc + YYacc)[0:512].astype(np.uint16).tofile(fid, sep="")
        
        #(XXacc + YYacc).astype(np.float32).tofile(fid, sep="")

## remove the weird high values in channel 0
## TODO: check what causes this
#XXacc[0] = XXacc[1]
#YYacc[0] = YYacc[1]

fid.close()

