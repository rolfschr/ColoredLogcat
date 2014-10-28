#!/bin/bash

PID=$$
PACKAGE=$1

function finish () {
    echo "Restarting ..."
    echo "PID=$PID"
    sleep 1
}

trap finish SIGINT SIGTERM

while :
do
    PACKAGE_PID=`adb shell ps | grep $1 | cut -c 10-15`
    clear
    adb logcat -v time | grep --color --line-buffered $PACKAGE_PID | coloredlogcat.py
done
