#!/bin/bash
# Rotate nginx logs if log size is more than 10Mb.

LOGS=`find . -type f -name nginx-\*.log -size +10M`
DO_RESTART=0
for log in $LOGS; do
    DO_RESTART=1
    mv $log $log.1
done

if [[ $DO_RESTART == 1 ]]
then
    kill -USR1 `cat $OPENSHIFT_DATA_DIR/pid/nginx.pid`
fi
