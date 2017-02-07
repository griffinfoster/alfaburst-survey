#! /bin/bash
mkdir /data/Survey/Data
/home/artemis/Survey/Scripts/killobs
/home/artemis/Survey/Scripts/killobs
/home/artemis/Survey/Scripts/killobs
cd /data/Survey/Log/beam4
numactl -C 0-5 -l ABPipeline --config=/home/artemis/Survey/Config/Beam4_client.xml &> /data/Survey/Log/beam4/pipeline0.log &
pidp0=$!
cd /data/Survey/Log/beam5
numactl -C 6-11 -l ABPipeline --config=/home/artemis/Survey/Config/Beam5_client.xml &> /data/Survey/Log/beam5/pipeline1.log &
pidp1=$!
sleep 5
cd /data/Survey/Log/beam4
numactl -C 12-17 ABServer --config=/home/artemis/Survey/Config/Beam4_server.xml &> /data/Survey/Log/beam4/server0.log &
pids0=$!
cd /data/Survey/Log/beam5
numactl -C 18-23 ABServer --config=/home/artemis/Survey/Config/Beam5_server.xml &> /data/Survey/Log/beam5/server1.log &
pids1=$!
echo $pidp0 $pidp1 $pids0 $pids1
wait $pidp0
wait $pidp1
wait $pids0
wait $pids1
