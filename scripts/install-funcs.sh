# help functions for installation/tfkey handling

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

query_user_any()
{
    chk=$@
    query_user2 $chk
    echo $ans
    return 0
}

get_key_name()
{
    num=$1
    sep=_
    ver=`echo $2 | sed "s/\./_/"`
    echo "tfkey$num$sep$ver"
}

get_key_value()
{
    key=`get_key_name $1 $2`
    echo `eval echo "\\$$key"`
}

set_key_value()
{
    key=`get_key_name $1 $2`
    eval $key=\"$3\"
    export $key
}

get_key()
{
    key_return=`get_key_value $1 $2`
    if [ -z "$key_return" ] ; then
        echo
	echo "No key cached for package $1 version $2"
        echo
        printf "Enter decryption key: "
	read key_return
        set_key_value $1 $2 "$key_return"
    fi
    export key_return
}

# create list of variables, echo one at a time
save_keys()
{
    dotfile=$1
    rm -f $dotfile
    keys=`set | grep "^tfkey" | awk -F= '{print $1}'`
    for tf in $keys ; do
	echo "$tf="\"`eval echo \\$$tf`\" >> $dotfile
    done
    if [ -f $dotfile ] ; then
	chmod go-rw $dotfile
    fi
}
