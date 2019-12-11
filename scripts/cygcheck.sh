#!/bin/bash
# Check if a program depends on cygwin1.dll

# Remove anything which looks like flags
PROG=$(echo "$1" | sed -e 's/ \-.*//g')

case "$PROG" in
    *.exe)
	PROG="$PROG"
	;;
    *)
	PROG="$PROG.exe"
esac

[ -f "$PROG" ] || PROG=$(type -p "$1")
DIR=$(dirname "$PROG")
if (cd "$DIR"; cygcheck ./$(cygpath -w -p $(basename "$PROG" .exe).exe)) \
    | grep cygwin1.dll >/dev/null; then
    #echo "$PROG is a cygwin executable" >&2
    exit 0
else
    #echo "$PROG is not a cygwin executable" >&2
    exit 1
fi

