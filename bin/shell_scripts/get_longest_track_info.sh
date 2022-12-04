#! /usr/bin/bash

# arg: an integer (I have two disk drives, so either 0 or 1 for me) denoting
# which drive to rip a title from (aka /dev/sr1, arg would be '1')
drive_id=$1
test_input_file=$2



if [ -z "$test_input_file" ]
then 
	disk_id=$(makemkvcon -r info disc | grep -P "/dev/sr$drive_id" | cut -d ',' -f 1 | cut -d ':' -f 2)
	all_info=$(makemkvcon -r info disc:$disk_id)
else 
	disk_id=0
	all_info=$(cat $test_input_file)
fi

longest_title=$(echo "$all_info" | grep -P 'TINFO:\d,9,\d,".*"' | sort -t , -k 4 | tail -1 | awk -F '[:,]' '{print $2}')
title_info=$(echo "$all_info" | grep "TINFO:$longest_title")
source_info=$(echo "$all_info" | grep "SINFO:$longest_title" )

title_length=$(echo "$title_info" | grep -P "TINFO:$longest_title,9,\d,\".*\"" | cut -d '"' -f 2)
title_size=$(echo "$title_info" | grep -P "TINFO:$longest_title,10,\d,\".*\"" | cut -d '"' -f 2)
source_res=$(echo "$source_info" | grep -P "SINFO:$longest_title,\d,19,\d,\".*\"" | cut -d '"' -f 2)

title_name=$(echo "$title_info" | grep -P "TINFO:$longest_title,27,\d,\".*\"" | cut -d '"' -f 2)
disk_name=$(echo "$all_info" | grep -P "CINFO:2,0,\".*\"" | cut -d '"' -f 2) 

echo "disk_id:$disk_id"
echo "disk_name:$disk_name"
echo "title_id:$longest_title"
echo "title_name:$title_name"
echo "title_length:$title_length"
echo "title_size:$title_size"
echo "source_res:$source_res"