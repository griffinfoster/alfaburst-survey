#! /bin/bash

DATADIR=/data/Survey/Data

# make the data directory if it doesn't all ready exist
if [ ! -d "$DATADIR" ]; then
    mkdir /data/Survey/Data
fi

# clear out any previous pipeline/server processes
for i in {1..3}
do
    # from killobs script:
    top -b -n1 >> /data/Survey/Log/killlog
    killall -9 ABServer
    killall -9 ABPipeline
    sleep 2
done

echo "$(date) : FRB Search pipeline started" >> /data/Survey/Log/frb_abc3.log

# initialize pipelines
cd /data/Survey/Log/beam6
numactl -C 0-5 -l ABPipeline --config=/home/artemis/Survey/Config/Beam6_client.xml &> /data/Survey/Log/beam6/pipeline0.log &
pidp0=$!

sleep 5

# initialize servers
cd /data/Survey/Log/beam6
numactl -C 12-17 ABServer --config=/home/artemis/Survey/Config/Beam6_server.xml &> /data/Survey/Log/beam6/server0.log &
pids0=$!

echo $pidp0 $pids0

# check if processes have died, if one has, restart it
while true
do
    if ! ps -p $pidp0 > /dev/null; then
        # restart pipeline
        echo "$(date) : ABpipeline Beam 0 process died, restarting" >> /data/Survey/Log/frb_abc3.log
        cd /data/Survey/Log/beam6
        numactl -C 0-5 -l ABPipeline --config=/home/artemis/Survey/Config/Beam6_client.xml &> /data/Survey/Log/beam6/pipeline0.log &
        pidp0=$!
    fi

    if ! ps -p $pids0 > /dev/null; then
        # restart pipeline and server
        echo "$(date) : ABServer Beam 0 process died, restarting" >> /data/Survey/Log/frb_abc3.log
        cd /data/Survey/Log/beam6
        kill -9 $pidp0
        numactl -C 0-5 -l ABPipeline --config=/home/artemis/Survey/Config/Beam6_client.xml &> /data/Survey/Log/beam6/pipeline0.log &
        pidp0=$!

        sleep 5

        numactl -C 12-17 ABServer --config=/home/artemis/Survey/Config/Beam6_server.xml &> /data/Survey/Log/beam6/server0.log &
        pids0=$!
    fi
    
    echo $pidp0 $pids0

    sleep 60
done

