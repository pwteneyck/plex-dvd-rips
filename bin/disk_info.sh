#! /usr/bin/bash

# arg: an integer (I have two disk drives, so either 0 or 1 for me) denoting
# which drive to rip a title from (aka /dev/sr1, arg would be '1')
drive_id=$1
test_input_file=$2

if [ -z "$test_input_file" ]
then 
	disk_id=$(makemkvcon -r info disc --debug | grep -P "/dev/sr$drive_id" | cut -d ',' -f 1 | cut -d ':' -f 2)
	echo "disk:$disk_id"
	makemkvcon -r info disc:$disk_id | tee resources/"dev_sr$1.info"
else 
	disk_id=0
	cat $test_input_file
fi