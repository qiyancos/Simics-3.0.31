#!/bin/bash
# Win32: Print filename with no spaces in them and no backward slashes.

# Remove anything resembling options. This to allow checking things like
# "cpp -E".
PROG=$(echo "$1" | sed -e 's/ \-.*//g')

# workaround for bug(?) in cygpath -d
if [ -f "$PROG" ]; then
    PROG0=$(dirname "$PROG")/$(basename "$PROG" .exe).exe
else
    PROG0="$PROG"
fi

if echo "$PROG0" | grep ' ' >/dev/null; then
    PROG0=$(cygpath -u $(cygpath -m $(cygpath -d "$PROG0")) | sed -e 's/\.exe$//')
else
    PROG0=$(cygpath -u $(cygpath -m "$PROG0") | sed -e 's/\.exe$//')
fi

echo $1 | sed -e "s:$PROG:$PROG0:"
