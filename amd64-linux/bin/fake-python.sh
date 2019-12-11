#!/bin/sh

DIR="$0"

case `uname` in
    CYGWIN*)
	DIR=`cygpath "$0"`
	;;
esac

DIR=`dirname "$DIR"`

LD_LIBRARY_PATH="$DIR:$DIR/../sys/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH

if [ $# -eq 0 ] ; then
    echo "Usage: $0 -c command | script"
    exit 1
elif [ $# -eq 2 -a "$1" = "-c" ] ; then
    "$DIR/simics-common" -quiet -no-copyright -batch-mode -e "@$2"
else
    "$DIR/simics-common" -quiet -no-copyright -batch-mode -python "$@"
fi
