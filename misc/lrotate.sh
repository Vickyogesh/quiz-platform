#!/bin/bash
# Rotate nginx logs if log size is more than 10Mb.
# We rotate only nginx loga because uwsgi and dbupdate.py
# rotates their logs by itself.
cd $OPENSHIFT_DIY_LOG_DIR

# Rotate nginx logs
do_nginx_logrotate() {
    echo "Rotating nginx logs..."
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
}

# Archive logs
do_archive() {
    echo "Archivin logs..."
    date +"%d.%m.%Y %T %Z %:::z" > timestamp
    tar -cvjf logs-snapshot.tar.bz2 timestamp *.log*

    # Remove old logs (like app.log.1)
    sleep 1
    echo "Cleanup..."
    rm timestamp *.log.* 2>/dev/null
}


case $1 in
    -h)
    echo "Log rotate tool."
    echo "Usage: lrotate.sh [-h] [-arch] [-checkarch]"
    echo
    echo "-h            Prin this help."
    echo "-arch         Create archive only (logs-snapshot.tar.bz2)."
    echo "-checkarch    Create archive if not exist."
    echo
    echo "Examples:"
    echo "      Rotate nginx logs and create logs archive:"
    echo "          lrotate.sh"
    echo "      Only create logs archive:"
    echo "          lrotate.sh -arch"
    echo "      Only create logs archive if not exist:"
    echo "          lrotate.sh -checkarch"
    ;;

    -arch)
    do_archive
    ;;

    -checkarch)
    if [[ ! -f logs-snapshot.tar.bz2 ]]; then
        do_archive
    fi
    ;;

    *)
    do_nginx_logrotate
    sleep 1
    do_archive
    ;;
esac
