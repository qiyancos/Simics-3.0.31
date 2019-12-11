#!/bin/sh

COMPILER="$1"

if "$COMPILER" -v 2>&1 | grep 'gcc version' >/dev/null; then
    "$COMPILER" --version | head -n 1 | sed 's/\r//g'
    exit

elif "$COMPILER" -v 2>&1 | head -n 1 | grep "Microsoft" >/dev/null; then
    version=`"$COMPILER" 2>&1 | head -1 | sed -ne 's/.*Version \(.*\) for.*/\1/p'`
    echo "Microsoft Visual C++ Version $version"
    exit

elif "$COMPILER" -V 2>&1 | head -n 1 | grep "Intel" >/dev/null; then
    version=`"$COMPILER" -V 2>&1 | head -1 | sed -ne 's/.*\Version \(.*\) Build.*/\1/p'`
    echo "Intel C++ Compiler Version $version"
    exit

elif "$COMPILER" -V 2>&1 | head -n 1 | grep "WorkShop" >/dev/null; then
    "$COMPILER" -V 2>&1 | head -n 1 | sed -ne 's/.*\(Sun WorkShop.*\)Patch.*/\1/p'
    exit

elif "$COMPILER" -V 2>&1 | head -n 1 | grep "Forte" >/dev/null; then
    "$COMPILER" -V 2>&1 | head -n 1 | sed -ne 's/.*\(Forte Developer.*\)200.*/\1/p'
    exit

elif "$COMPILER" -V 2>&1 | head -n 1 | grep "Sun C" >/dev/null; then
    "$COMPILER" -V 2>&1 | head -n 1 | sed -ne 's/.*\(Sun C.*\)200.*/\1/p'
    exit
fi

echo "Unknown"
