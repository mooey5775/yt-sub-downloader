## YouTube Subscription Fetcher

This script will download the latest subscriptions up to, but not including, the video ID found in `mostrecent.txt`.

### Usage

```console
$ python3 ytdownload.py
```

### Configuration

The script uses the Youtube V3 API which requires you to create an 
application on the Google developer console before you can make 
requests. After you make the application you must enable
'YouTube Data API v3' access and create a server API key.

This is all explained here:

https://developers.google.com/youtube/registering_an_application

After you get your API key, add it to `ytdownload.py` in the variable `my_key`.

Additionally, add your channel username to `ytdownload.py` in the variable `username`.

By default, this script downloads videos at 720p. If you want a different resolution, change `ydl_opts` on line 148 of `ytdownload.py`.

Finally, to change the most recent video that will not be downloaded, edit `mostrecent.txt` with the video ID.

### Attribution

Thanks to Alistair Buxton, who made much of the code to fetch youtube subscription video IDs. (https://github.com/ali1234/ytsubs)