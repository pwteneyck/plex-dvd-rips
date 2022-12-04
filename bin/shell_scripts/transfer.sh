#! /usr/bin/bash

plex_user=$1
plex_ip=$2
plex_media_dir=$3
dest_dir=$4
filename=$5
encoded_dir=$6

plex_ssh_dest="$plex_user"@"$plex_ip"

ssh -i ~/.ssh/id_rsa "$plex_ssh_dest" "mkdir -p \"$plex_media_dir/$dest_dir\""
rsync -vrd --protect-args --progress -e ssh "$encoded_dir/$dest_dir/$filename" "$plex_ssh_dest:$plex_media_dir/$dest_dir/$filename"