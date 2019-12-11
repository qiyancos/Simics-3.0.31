#!/bin/sh
# Create links from <simics>/import/ to a global dump directory.
#
# This script should be run to finalize a Simics installation
# where dump files are kept in a separate directory (recommended).
#


DEFAULT_DUMP_PATH=/opt/virtutech/import/

if [ "x$1" = "x" ] ; then
    echo "No dump path specified, using default: $DEFAULT_DUMP_PATH"
    DUMP_PATH=$DEFAULT_DUMP_PATH
else
    DUMP_PATH=$1
fi

if [ "`echo $DUMP_PATH | cut -b1`" != "/" ] ; then
    DUMP_PATH=`pwd`/$DUMP_PATH
fi

if [ ! -d $DUMP_PATH ] ; then
    echo "The directory $DUMP_PATH does not exist."
    echo "Setup failed!"
    echo ""
    exit 1
fi

setup_dir=`pwd`
cd $DUMP_PATH
dirs=`find . -name "*" -type d | sed 's/\.\///g'`
files=`find . -name "*" -type f | sed 's/\.\///g'`
links=`find . -name "*" -type l | sed 's/\.\///g'`

files="$files $links"

for d in $dirs ; do
    if [ ! -d $setup_dir/$d ] ; then
        echo "Creating directory: $setup_dir/$d"
        mkdir -p $setup_dir/$d
    fi
done

for f in $files ; do
    cd $setup_dir
    cd `dirname $f`
    ff=`basename $f`
    # -h works better that -L on Solaris' sh
    if [ -h "$ff" ] ; then
        # remove old links, but not files
        rm -f $ff
    fi
    if [ -f $ff ] ; then
        echo "Keeping file '$f'."
    else
        ln -s $DUMP_PATH/$f .
    fi
done

cd $setup_dir

echo ""
echo "Done!"
echo ""
