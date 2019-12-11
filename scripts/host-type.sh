#!/bin/sh

OS=`uname -s`
HOST_ARCH=`uname -m`

SCRIPTSDIR="`dirname "$0"`"
HOSTSDIR="`cd "$SCRIPTSDIR"/.. ; pwd`"

case $OS in
    Linux)
        OS_PART=linux
	;;
    SunOS)
        OS_PART=sol8-64
	;;
    CYGWIN_NT*)
        OS_PART=win32
	;;
    *)
        echo "Unsupported OS: $OS" >&2
	exit 1
	;;
esac

case $HOST_ARCH in
    i*86) 
        ARCH=x86
	;;
    x86_64)
        ARCH="amd64 x86"
	;;
    amd64)
        ARCH="amd64 x86"
	;;
    sun4u|sun4v)
        ARCH=v9
	;;
    *)	
        echo "Unsupported architecture: $HOST_ARCH" >&2
	exit 1
	;;
esac

if [ -n "$SIMICS_HOST" ]; then
    if [ -d "$HOSTSDIR/$SIMICS_HOST/bin"  ]; then
	echo $SIMICS_HOST
	exit 0
    else
	echo "Non-existing host $SIMICS_HOST." >&2
	exit 1
    fi
else
    for arch in $ARCH; do
	host=$arch-$OS_PART
	if [ -d "$HOSTSDIR/$host/bin" ]; then
	    echo $host
	    exit 0
	fi
    done
    echo "No matching host found." >&2
    exit 1
fi
