#!/bin/bash

# Test if files are same

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] ; then 
    echo "Usage : $0 file1 file2 file_output"
    exit 1
fi

head -n 1 $1 > ${1}_header.tmp
head -n 1 $2 > ${2}_header.tmp

if cmp "${1}_header.tmp" "${2}_header.tmp" > /dev/null ; then
    cat $1 > $3
    tail $2 -n +2 >> $3
    echo "Files were merged to $3"
else
    echo "Files can't be merged - check your files or contact the TuxML team"
fi

rm ${1}_header.tmp
rm ${2}_header.tmp