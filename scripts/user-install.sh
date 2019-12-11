#!/bin/sh

install_error()
{
    echo
    echo $1
    echo
    echo "Simics was NOT installed"
    echo
    exit 1
}

query_user2()
{
    def=$1
    shift 1
    reps="["$def"]"
    for rep in $@ ; do
        reps="$reps / $rep"
    done
    printf "$reps : " >&2
    read ans
    if [ "x$ans" = "x" ] ; then
        ans=$def
    fi
}

query_user()
{
    chk=$@
    while true ; do
        query_user2 $chk
        for a in $chk ; do
            if [ "x$a" = "x$ans" ] ; then
                echo $ans
                return 0
            fi
        done
    done
}

mkdir_f()
{
    d="$1"
    if [ ! -d "$d" ]; then
	# echo "Creating directory \"$d\""
	mkdir "$d"
    fi
}


usage ()
{
     echo
     echo
     echo "This script will install a local copy of Simics from"
     echo "a specified master installation. If no destination"
     echo "directory is set, a directory will be created in the"
     echo "current directory, with the same name as the master."
     echo
     echo "Usage:"
     echo
     echo "  `basename $0` [OPTIONS] <master-directory> [<destination-directory>]"
     echo
     echo "Options:"
     echo "   -b   specifies batch-mode where no user interaction"
     echo "        is needed for the script to complete."
     echo "   -f   forced installation, replace any existing files when"
     echo "        installing."
     echo "   -h   display this help test"
     echo
     exit 0
}

# first check for options
while getopts fbh var
do
    case $var in
    b)
	BATCH=b
	;;
    f)
	FORCE=f
	;;
    ? | h) 
	usage
        exit 2;;
    esac
done

#remove options
shift `expr $OPTIND - 1`

if [ x$1 = x ] ; then
    usage
fi

if [ ! -d "$1" ] ; then
    install_error "Specified argument is not a directory."
fi

if [ xb != x$BATCH ] ; then
    clear
fi

echo
echo "Simics user-install script"
echo "========================================="
echo
echo "This script will install a local copy of Simics from"
echo "a specified master installation. If no destination"
echo "directory is set, a directory will be created in the"
echo "current directory, with the same name as the master."
echo
echo "Default alternatives are enclosed in square brackets ([ ])."
echo
echo "*** WARNING: This script is deprecated, and replaced by"
echo "              The 'workspace-setup' script."
echo

#expand the source path. tar doesn't like . or .. paths
work_dir=`pwd`
cd "$1"
src_dir=`pwd`
cd "$work_dir"

if [ "x$2" = "x" ] ; then
    dst_dir=`basename "$src_dir"`
else
    dst_dir="$2"
fi

if [ -d "$dst_dir" ] ; then
    work_dir="`pwd`"
    cd "$dst_dir"
    dst_path="`pwd`"
    cd "$work_dir"
    if [ "$src_dir" = "$dst_path" ] ; then
        install_error "Same directory set for both source and destination."
        exit 1
    fi
    echo
    echo
    echo "A directory already exists with the name '$dst_dir'."
    echo
    if [ xf = x$FORCE ] ; then
	echo "Overwriting"
	echo
	ans=yes
    else
	if [ xb != x$BATCH ] ; then
	    echo "Do you want to remove it?"
	    echo
	    ans=`query_user no yes`
	else
	    ans=no
	fi
    fi
    if [ "x$ans" = "xno" ] ; then
        install_error "Installation interrupted"
    fi
    rm -rf "$dst_dir"
fi

mkdir_f "$dst_dir"

if [ ! -d "$dst_dir" ] ; then
    install_error "Could not create Simics directory."
fi


cd "$dst_dir"

###########################################

echo
echo
echo "Starting user installation of Simics."
echo
echo "Installing from: $src_dir"
echo "             to: `pwd`"
echo
if [ xb = x$BATCH ] ; then
    and=yes
else
    echo "Do you want to continue ?"
    ans=`query_user yes no`
fi
if [ "x$ans" = "xno" ] ; then
    install_error "Installation interrupted"
fi

# link everything
ln -s "$src_dir"/* .

# TODO: make sure this host list is in sync
hostsQ="v9-sol8-64 x86-linux amd64-linux x86-win32"
for h in $hostsQ ; do
    if [ -d "$src_dir/$h" ] ; then
        all_hosts="$all_hosts $h"
    fi
done

echo
echo
if [ xb = x$BATCH ] ; then
    ans=all
else
    echo "What host types do you want to install support for?"
    echo
    num=1
    for h in $all_hosts ; do
	echo "$num    $h"
	num_str="$num_str $num"
	num=`echo $num | awk "{print int(\\$1)+1}"`
    done
    echo
    ans=`query_user all $num_str`
fi

num=1
if [ "x$ans" = "xall" ] ; then
    hosts=$all_hosts
else
    for h in $all_hosts ; do
        if [ "x$ans" = "x$num" ] ; then
            hosts=$h
            break
        fi
	num=`echo $num | awk "{print int(\\$1)+1}"`
    done
fi


echo
echo "Setting up links..."

# remove links to directories that will be copied (or not used)
rm -f config
rm -f home
rm -f scripts
rm -f src
rm -f import
for h in $all_hosts ; do
    rm -f $h
done

mkdir_f config
confs=`ls "$src_dir/config"`
for c in $confs ; do
    if [ "x$c" = "xmodules.list.local" ] ; then
	# copy the local modules.list
	cp "$src_dir/config/$c" config/$c
    else
        # link everything else
	ln -s "$src_dir/config/$c" config/$c
    fi
done

# create an import directory. Copy all directories, but link files
mkdir_f import
imlist=`ls "$src_dir/import"`
for i in $imlist ; do
    if [ -d "$src_dir/import/$i" ] ; then
        mkdir_f import/$i
        sublist=`ls "$src_dir/import/$i"`
        for j in $sublist ; do
            ln -s "$src_dir/import/$i/$j" import/$i/$j
        done
    else
        ln -s "$src_dir/import/$i" import/`basename $i`
    fi
done

echo
echo "Copying files..."

# copy some common files (use tar to preserve links)
tar cf - -C "$src_dir" home -C "$src_dir" scripts | tar xf -

mkdir_f src
mkdir_f src/devices
mkdir_f src/extensions
ln -s $src_dir/src/devices/common src/devices/
ln -s $src_dir/src/devices/microwire-eeprom src/devices/
ln -s $src_dir/src/extensions/common src/extensions/
ln -s $src_dir/src/include src/include

echo
echo "Patching local configuration files..."

for h in $hosts ; do
    # Make sure that this host is configured

    if [ ! -f "$src_dir/$h/config/host-config" ]; then
	echo "*WARNING*: $src_dir/$h is not configured properly. Skipping." >&2
	continue
    fi

    mkdir_f $h
    mkdir_f $h/bin
    mkdir_f $h/lib
    mkdir_f $h/obj
    ln -s $src_dir/$h/sys $h/sys
    cp -r "$src_dir/$h/config" $h
    # check if relative path
    if [ x`echo $dst_dir | grep "^/"` = x ] ; then
        DSTPATH=$work_dir/$dst_dir
    else
        DSTPATH=$dst_dir
    fi
    # remove in case it was write-protected
    rm -f $h/config/host-config
    cat "$src_dir/$h/config/host-config" |\
	sed -e "s|^SIMICS_BASE.*|SIMICS_BASE=$DSTPATH/|" \
	    -e "s|^BUILD_DIR.*|BUILD_DIR=$DSTPATH/$h|" \
	    -e "s|^top_srcdir.*|top_srcdir=$DSTPATH/$h|" \
            -e "s|^.*DISABLE_SIMICS_LICENSE.*|DISABLE_SIMICS_LICENSE=yes|" \
	> $h/config/host-config	
    bins=`ls "$src_dir/$h/bin"`

    for b in $bins ; do
        ln -s "$src_dir/$h/bin/$b" $h/bin/$b
    done
    ln -s "$src_dir/$h/lib/Makefile" $h/lib/Makefile

    # This assumes that we are using Python 2.*, but it should work
    # even if we upgrade to Python 2.3 and beyond
    ln -s $src_dir/$h/lib/python2* $h/lib/
done

# now create a link to the master installation

ln -s "$src_dir" master-install


cat - <<EOF

Completed setup of local Simics installation directory

    $dst_dir

For documentation on how to proceed from here, refer to the Simics User Guide.

EOF
