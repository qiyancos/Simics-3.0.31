#!/bin/sh

COMPILER="$1"

if "$COMPILER" -v 2>&1 | grep 'gcc version' >/dev/null; then
    if uname | grep CYGWIN >/dev/null; then
	if $COMPILER -dumpmachine | grep cygwin >/dev/null; then
	    echo "Only MingW/GCC supported on Windows hosts." >&2
	    echo "unsupported"
	    exit
	fi
    fi

    $COMPILER -dumpversion 2>&1 |  egrep "^[A-Za-z-]*2\." >/dev/null
    if [ "$?" = "0" ] ; then
        echo "unsupported" ; exit
    fi

    $COMPILER -dumpversion 2>&1 |  egrep "^[A-Za-z-]*3\." >/dev/null
    if [ "$?" = "0" ] ; then
        echo "gcc3" ; exit
    fi

    # treat gcc4 as gcc3 for now
    $COMPILER -dumpversion 2>&1 |  egrep "^[A-Za-z-]*4\." >/dev/null
    if [ "$?" = "0" ] ; then
        echo "gcc3" ; exit
    fi
    
    $COMPILER -dumpversion 2>&1 |  egrep "^[A-Za-z-]*5\." >/dev/null
    if [ "$?" = "0" ] ; then
        echo "gcc3" ; exit
    fi

elif "$COMPILER" -v 2>&1 | head -1 | grep "Microsoft" >/dev/null; then

    echo "msvc" ; exit

elif "$COMPILER" -V 2>&1 | head -1 | grep "Intel" >/dev/null; then

    echo "icc" ; exit

elif "$COMPILER" -V 2>&1 | head -1 | grep "WorkShop" >/dev/null; then

    $COMPILER -V 2>&1 | grep "WorkShop Compilers 5" >/dev/null
    if [ "$?" = "0" ] ; then
        echo "ws5" ; exit
    fi

    $COMPILER -V 2>&1 | grep "WorkShop 6" >/dev/null
    if [ "$?" = "0" ] ; then
        echo "ws6" ; exit
    fi

elif "$COMPILER" -V 2>&1 | head -1 | grep "Forte" >/dev/null; then

    $COMPILER -V 2>&1 | grep "Developer 7" >/dev/null
    if [ "$?" = "0" ] ; then
        echo "ws7" ; exit
    fi

elif "$COMPILER" -V 2>&1 | head -1 | grep "Sun C" >/dev/null; then
    $COMPILER -V 2>&1 | grep "5\.5" >/dev/null
    if [ "$?" = "0" ] ; then
        echo "sone8" ; exit
    fi
    $COMPILER -V 2>&1 | grep "5\.6" >/dev/null
    if [ "$?" = "0" ] ; then
        echo "sone9" ; exit
    fi
    $COMPILER -V 2>&1 | grep "5\.7" >/dev/null
    if [ "$?" = "0" ] ; then
        echo "sun10" ; exit
    fi
    $COMPILER -V 2>&1 | grep "5\.8" >/dev/null
    if [ "$?" = "0" ] ; then
        echo "sun11" ; exit
    fi

else
    # Intel C++ for windows does not seem to have any option to
    # to display version number, so we try to compile a small program.
    tmpfile=tmp$$.c
    cat >$tmpfile <<EOF
int main() {
#ifdef __INTEL_COMPILER
	return 0;
#else
	return 1;
#endif
}
EOF
    if $COMPILER $tmpfile >/dev/null 2>&1; then
	echo "icc"
	rm -f $tmpfile
	exit
    fi
    
    rm -f $tmpfile
fi

echo "unknown"
