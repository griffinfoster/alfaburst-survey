#!/usr/local/bin/ruby

# cognizeALFA.rb
# Checks if ALFA is enabled and if it is, trigger data acquisition if it is not
# taking place already. If ALFA is not enabled, and if data acquisition is
# taking place, kill it.
# To be set up as cron job, ideally every 5 minutes.


# for testing
debug = false

# number of ALFA beams
numBeams = 7

# check whether the signal source is the Gregorian dome
# 0 for Gregorian dome
sigSrcGregorian = (%x[redis-cli -h serendip6 hget SCRAM:IF2 IF2SIGSR]).to_i

# check whether the ALFA receiver is enabled
# 1 for ALFA enabled
recALFAEnabled = (%x[redis-cli -h serendip6 hget SCRAM:IF2 IF2ALFON]).to_i

# check that the RX turret is in the correct position for ALFA
# should be 26.64 deg +/- 0.25
recTurretAngle = (%x[redis-cli -h serendip6 hget SCRAM:TT TTTURDEG]).to_f
angPostALFA = 26.64
angleTol = 1.0

# for testing
#sigSrcGregorian = 0
#recALFAEnabled = 1

# TODO: check time tolerance, etc.?

dateTime = Time.now.strftime("%Y-%m-%d %H:%M:%S")
# convert local time to LST
siderealTime = (%x[/home/artemis/Survey/Scripts/localtime2lst.py "#{dateTime}"]).strip()
if debug
    print "#{dateTime}: LST: #{siderealTime}: ALFA status: "
end

# ALFA is enabled
if 0 == sigSrcGregorian and 1 == recALFAEnabled and (recTurretAngle - angPostALFA).abs <= angleTol
    # get the RF centre frequency
    rfCenFreq = (%x[redis-cli -h serendip6 hget SCRAM:IF1 IF1RFFRQ]).to_f

    # for testing
    #rfCenFreq = 1234.5

    # get the pointings of all 7 beams
    curRA = Array.new(numBeams) { |i|
      (%x[redis-cli -h serendip6 hget SCRAM:DERIVED RA#{i}]).to_f
    }
    curDec = Array.new(numBeams) { |i|
      (%x[redis-cli -h serendip6 hget SCRAM:DERIVED DEC#{i}]).to_f
    }

    # check if data acquisition is in progress, if not start it
    idx = %x[ps -ef | grep FRBsearch.sh].index("bash")
    if nil == idx
        if !debug
            print "#{dateTime}: LST: #{siderealTime}: ALFA status: "
        end
        print "ALFA is up. Starting data acquisition.\n"

        # log RF centre frequency
        print "IF1RFFRQ: #{rfCenFreq}\n"
        # log pointings
        for i in 0...numBeams
            print "RA#{i}: #{curRA[i]} DEC#{i}: #{curDec[i]} "
        end
        print "\n"

        # save starting RF centre frequency to file
        %x[echo "#{rfCenFreq}" > /home/artemis/Survey/Log/LastRFCenFreq.tmp]
        %x[echo "Start: #{Time.now.to_i}" >> /home/artemis/Survey/Log/surveytime.log]
        %x[/home/artemis/Survey/Scripts/FRBsearch.sh]
    else
        if !debug
            print "#{dateTime}: LST: #{siderealTime}: ALFA status: "
        end
        print "ALFA is up. Data acquisition in progress.\n"

        # log RF centre frequency
        print "IF1RFFRQ: #{rfCenFreq}\n"
        # log pointings
        for i in 0...numBeams
            print "RA#{i}: #{curRA[i]} DEC#{i}: #{curDec[i]} "
        end
        print "\n"

        # check if RF frequency has changed (by more than the channel
        # bandwidth), if yes, restart observation
        rfCenFreqLast = (%x[cat /home/artemis/Survey/Log/LastRFCenFreq.tmp]).to_f
        if (rfCenFreqLast - rfCenFreq).abs >= 109375.0
            if !debug
                print "#{dateTime}: LST: #{siderealTime}: ALFA status: "
            end
            print "RF centre frequency changed from #{rfCenFreqLast} to #{rfCenFreq}. Restarting data acquisition.\n"
            %x[echo "Stop: #{Time.now.to_i}" >> /home/artemis/Survey/Log/surveytime.log]
            %x[/home/artemis/Survey/Scripts/killobs_SSH]
            # save starting RF centre frequency to file
            %x[echo "#{rfCenFreq}" > /home/artemis/Survey/Log/LastRFCenFreq.tmp]
            %x[echo "Start: #{Time.now.to_i}" >> /home/artemis/Survey/Log/surveytime.log]
            %x[/home/artemis/Survey/Scripts/FRBsearch.sh]
        end
    end
else
    if debug
        print "ALFA is not up. Waiting.\n"
    end
end

if 1 == sigSrcGregorian or 0 == recALFAEnabled or (recTurretAngle - angPostALFA).abs >= angleTol
    idx = %x[ps -ef | grep FRBsearch.sh].index("bash")
    if idx != nil
        if !debug
            print "#{dateTime}: LST: #{siderealTime}: ALFA status: "
        end
        print "ALFA is down. Stopping data acquisition.\n"
        %x[echo "Stop: #{Time.now.to_i}" >> /home/artemis/Survey/Log/surveytime.log]
        %x[/home/artemis/Survey/Scripts/killobs_SSH]
    end
end

