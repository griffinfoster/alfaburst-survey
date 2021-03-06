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

echo "$(date) : FRB Search pipeline started" >> /data/Survey/Log/frb_abc0.log

# initialize pipelines
cd /data/Survey/Log/beam0
numactl -C 0-5 -l ABPipeline --config=/home/artemis/Survey/Config/Beam0_client.xml &> /data/Survey/Log/beam0/pipeline0.log &
pidp0=$!

cd /data/Survey/Log/beam1
numactl -C 6-11 -l ABPipeline --config=/home/artemis/Survey/Config/Beam1_client.xml &> /data/Survey/Log/beam1/pipeline1.log &
pidp1=$!

sleep 5

# initialize servers
cd /data/Survey/Log/beam0
numactl -C 12-17 ABServer --config=/home/artemis/Survey/Config/Beam0_server.xml &> /data/Survey/Log/beam0/server0.log &
pids0=$!

cd /data/Survey/Log/beam1
numactl -C 18-23 ABServer --config=/home/artemis/Survey/Config/Beam1_server.xml &> /data/Survey/Log/beam1/server1.log &
pids1=$!

echo $pidp0 $pidp1 $pids0 $pids1

# check if processes have died, if one has, restart it
while true
do
    if ! ps -p $pidp0 > /dev/null; then
        # restart pipeline
        echo "$(date) : ABpipeline Beam 0 process died, restarting" >> /data/Survey/Log/frb_abc0.log
        cd /data/Survey/Log/beam0
        numactl -C 0-5 -l ABPipeline --config=/home/artemis/Survey/Config/Beam0_client.xml &> /data/Survey/Log/beam0/pipeline0.log &
        pidp0=$!
    fi

    if ! ps -p $pidp1 > /dev/null; then
        # restart pipeline
        echo "$(date) : ABpipeline Beam 1 process died, restarting" >> /data/Survey/Log/frb_abc0.log
        cd /data/Survey/Log/beam1
        numactl -C 6-11 -l ABPipeline --config=/home/artemis/Survey/Config/Beam1_client.xml &> /data/Survey/Log/beam1/pipeline1.log &
        pidp1=$!
    fi

    if ! ps -p $pids0 > /dev/null; then
        # restart pipeline and server
        echo "$(date) : ABServer Beam 0 process died, restarting" >> /data/Survey/Log/frb_abc0.log
        kill -9 $pidp0
        cd /data/Survey/Log/beam0
        numactl -C 0-5 -l ABPipeline --config=/home/artemis/Survey/Config/Beam0_client.xml &> /data/Survey/Log/beam0/pipeline0.log &
        pidp0=$!

        sleep 5

        numactl -C 12-17 ABServer --config=/home/artemis/Survey/Config/Beam0_server.xml &> /data/Survey/Log/beam0/server0.log &
        pids0=$!
    fi

    if ! ps -p $pids1 > /dev/null; then
        # restart pipeline and server
        echo "$(date) : ABServer Beam 1 process died, restarting" >> /data/Survey/Log/frb_abc0.log
        kill -9 $pidp1
        cd /data/Survey/Log/beam1
        numactl -C 6-11 -l ABPipeline --config=/home/artemis/Survey/Config/Beam1_client.xml &> /data/Survey/Log/beam1/pipeline1.log &
        pidp1=$!

        sleep 5

        numactl -C 18-23 ABServer --config=/home/artemis/Survey/Config/Beam1_server.xml &> /data/Survey/Log/beam1/server1.log &
        pids1=$!
    fi
    
    echo $pidp0 $pidp1 $pids0 $pids1

    sleep 60
done

