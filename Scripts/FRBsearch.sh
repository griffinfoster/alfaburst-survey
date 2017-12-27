#!/bin/bash

# for cron
source /home/artemis/.bashrc

function observe {
    ssh -o ConnectTimeout=20 -o BatchMode=yes artemis@abc0 "/home/artemis/Survey/Scripts/frb_abc0.sh" & 
    pidabc0=$!
    ssh -o ConnectTimeout=20 -o BatchMode=yes artemis@abc1 "/home/artemis/Survey/Scripts/frb_abc1.sh" & 
    pidabc1=$!
    ssh -o ConnectTimeout=20 -o BatchMode=yes artemis@abc2 "/home/artemis/Survey/Scripts/frb_abc2.sh" & 
    pidabc2=$!
    ssh -o ConnectTimeout=20 -o BatchMode=yes artemis@abc3 "/home/artemis/Survey/Scripts/frb_abc3.sh" & 
    pidabc3=$!
    echo Waiting for $pidabc0 $pidabc1 $pidabc2 $pidabc3
    wait $pidabc0
    wait $pidabc1
    wait $pidabc2
    wait $pidabc3
}

echo "Starting observation on:" `date`>> /home/artemis/Survey/Log/Obs.log
observe
echo "Stopping observation on:" `date`>> /home/artemis/Survey/Log/Obs.log
echo "--" >> /home/artemis/Survey/Log/Obs.log

