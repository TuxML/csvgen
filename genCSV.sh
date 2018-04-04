#!/bin/bash

if [ -s "$1" ] ; then
    echo "Usage : $0 file_output"
    exit 1
fi

echo "V1 : "
python3 "./genCSV_v1.py" "${1}_v1.tmp"
echo "V2 : "
python3 "./genCSV_v2.py" "${1}_v2.tmp"

echo "Merging..."
./merge.sh "${1}_v1.tmp" "${1}_v2.tmp" "$1"

rm "${1}_v1.tmp"
rm "${1}_v2.tmp"

echo "Done"