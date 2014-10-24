#!/bin/bash

host="${COLLECTD_HOSTNAME}"
pause="${COLLECTD_INTERVAL:-10}"

# old way:
#while sleep "$pause"
#do
#    time="$(date +%s)"
#    items=(`du -sb --exclude=.* $OPENSHIFT_HOMEDIR`)
#    echo "PUTVAL $host/disk/total_usage ${time}:${items[0]}"
#done

# gear data https://forums.openshift.com/how-to-check-actual-physical-parameters-of-your-gear
# https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Resource_Management_Guide/sec-cpu.html
# https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Resource_Management_Guide/sec-cpuacct.html

while sleep "$pause"
do
    time="$(date +%s)"
    data=(`quota -w|egrep -v '(quotas|Filesystem)'`)
    mem=(`echo "$(oo-cgroup-read memory.usage_in_bytes)/$(oo-cgroup-read memory.limit_in_bytes)*100;$(oo-cgroup-read memory.max_usage_in_bytes)/$(oo-cgroup-read memory.limit_in_bytes)*100"|bc -l|sed 's/^\./0./'`)
    usage=${data[1]}
    limit=${data[3]}
    percentage=$(echo "(${usage}/${limit})*100" |bc -l|sed 's/^\./0./')
    current_usage=${percentage/\.*}
    echo "PUTVAL $host/disk/usage ${time}:${usage}"
    echo "PUTVAL $host/disk/limit ${time}:${limit}"
    echo "PUTVAL $host/disk/percentage ${time}:${percentage}"
    echo "PUTVAL $host/memory/usage ${time}:${mem[0]}"
    echo "PUTVAL $host/memory/usage_max ${time}:${mem[1]}"
done
