# Plex DVD Ripper

## Requirements

* **Python >= 3.10** - dataclasses aren't available before 3.10
* **makemkvcon**
  * this tool calls MakeMKV via the `makemkvcon` command, so that needs to be available in your `PATH`
  * [install guide](https://forum.makemkv.com/forum/viewtopic.php?f=3&t=224)
    * (Debian) [unofficial apt repository](https://unixcop.com/how-to-install-makemkv-on-ubuntu-20-04/)
    * (Arch) [aur](https://aur.archlinux.org/packages/makemkv-cli) 
* **HandBrakeCLI**
  * this tool calls HandBrakeCLI via the `HandBrakeCLI` command, so that needs to be available in your `PATH`
  * (Debian) [unofficial apt repository](https://handbrake.fr/docs/en/1.2.0/get-handbrake/download-and-install.html)
  * (Arch) [aur](https://archlinux.org/packages/community/x86_64/handbrake-cli/)
* **TMDB API Key**
  * Used to apply correct names to movies and episodes
  * See https://developers.themoviedb.org/3/getting-started/authentication
  * Put your API key into the `TMDBToken` field in `bin/config.ini`

## Setup

The following values need to be provided in `bin/config.ini`:

* **InstallDir -** The directory that you place this tool into. For example, I've installed in `~/rips/`:

```bash
tree ~/rips -L 1
/home/pwt/rips
├── bin
├── done_queue
├── encoded
├── encode_queue
├── raw
└── transfer_queue
```

* **PlexUser -** The user login for your Plex server. Consider setting up passwordless `ssh`, otherwise the transfer process will prompt you to provide your password to establish the ssh connection for each file transfer.
* **DestinationIP -** The IPv4 address of your Plex server, e.g. `127.0.0.1`
* **PlexMediaDir -** The path to the `Media` directory Plex will find your content under. See [Nameing and Organizing Your TV Show Files](https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/)
* **TMDBToken -** An API key the tool can use to make requests to The Movie Database in order to provide well-formatted titles for media. See https://developers.themoviedb.org/3/getting-started/authentication

## Use

This tool separates the different steps of transferring a DVD to a media server via queues, allowing each process to proceed at its own rate. The three steps are:

1. **Ripping** - pulling raw files from the DVD onto the local drive. These files are typically ~1.5GB / hour for 480p or ~8GB / hour for 720p
1. **Encoding** - converting those raw files into a more efficient video format such as `.mkv` or `.m4v`. The main goal here is significant space savings: encoding can reduce the size of a raw DVD rip by up to 80%
1. **Transferring** - moving the encoded files from the local drive to the media server itself. This includes placing the media in the correct place in the remote's directory structure for Plex to recognize it; this tool follows [standard Plex organizational recommendations](https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/)

Ideally, each of these tasks is handled by a separate process, so that the `encode` process can be working through a backlog of newly-ripped files while the `rip` process is struggling to get through your Blu-Ray copy of _Avatar_. This might look like:

```bash
$ pwd
path/to/install/dir

# start the encoding process
$ python bin/encode.py 
No encode work found; polling for new items...(\)

# in a separate session
# start the transfer process
$ python bin/transfer.py 
No encode work found; polling for new items...(\)

# in a separate session
# rip a movie from a DVD in /dev/sr0 
$ python bin/rip.py movie -d 0
Waiting for ready status from /dev/sr0......
```

### Rip CLI Reference

```
$ python bin/rip.py --help

usage: rip.py [-h] [-d DRIVE] [-hq] [-n SHOWNAME] [-id SHOWID] [-s SEASON]
              [-o OFFSET] [--reverse] [--notify]
              {movie,show}

positional arguments:
  {movie,show}

options:
  -h, --help            show this help message and exit
  -d DRIVE, --drive DRIVE
                        drive number to rip from - e.g. "/dev/sr0" would be
                        drive 0
  -hq, --highquality    prioritize encoding compression/quality over speed
  -n SHOWNAME, --showname SHOWNAME
                        (show only) - the name of the show - used to search
                        TMDB for episode names
  -id SHOWID, --showid SHOWID
                        (show only) - shownames can be ambiguous or overloaded
                        - instead, this argument provides the unambiguous show
                        ID used by tmdb.com to identify a specific show, e.g.
                        Parks and Recreation is ID 8592:
                        https://www.themoviedb.org/tv/8592-parks-and-
                        recreation
  -s SEASON, --season SEASON
                        the season of the show, one-indexed like you'd expect
  -o OFFSET, --offset OFFSET
                        (show only) - the zero-indexed offset of the first
                        episode on the disk - e.g. if the first episode on a
                        disk is episode 5, the correct offset for that disk is
                        4. Maybe the easier way to think about this is that
                        "offset" should correspond to the last episode number
                        on the previous disk.
  --reverse             some DVDs store episodes in reverse order - use this
                        flag to correctly apply episode names in reverse order
  --notify              adds a post-complete action to the rip process - use
                        this flag to have the rip process execute the
                        "notify.sh" script under
                        install_dir/bin/shell_scripts.
```

MakeMKV will occasionally time out while reading from a disk - usually retrying will resolve the issue. If not, the logging output for the initial MakeMKV `info` call is written to `bin/resources/dev_sr{X}.info`. This output follows the `--robot` or "automation mode" formatting as described in [MakeMKV's usage.txt](https://www.makemkv.com/developers/usage.txt).

### Encode CLI Reference

`encode.py` takes no arguments and parses no arguments. It takes any configuration needed from `config.ini` instead.

You can **pause** work on the encode queue by creating a file named `pause` in the queue directory - for example:

```
touch encode_queue/pause
```

While **paused**, the encode process will complete its current task but will not start any new ones until the `pause` file is removed from the queue. This can be useful for "backgrounding" the encode process, which consumes pretty much all the CPU capacity on your system.

### Transfer CLI Reference

`transfer.py` takes no arguments and parses no arguments. It takes any configuration needed from `config.ini` instead.

You can **pause** work on the transfer queue by creating a file named `pause` in the queue directory - for example:

```
touch transfer_queue/pause
```

While **paused**, the transfer process will complete its current task but will not start any new ones until the `pause` file is removed from the queue. This can be useful for ensuring the safety of file-system operations on the remote host, such as [SnapRAID](https://www.snapraid.it/manual) executions that will fail if performed while another process is writing to the relevant drives.