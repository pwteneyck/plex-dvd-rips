#! /usr/bin/bash

remote_user=$3
remote_ip=$4
available=$(ssh "$remote_user"@"$remote_ip" df | grep $1 | awk '{print $4}')
need=$(ls -l "$2" | awk '{print $5}')
if [ "$need" -ge "$available" ]; then
	echo "Insufficient disk space on remote; exiting"
	exit 1
fi
