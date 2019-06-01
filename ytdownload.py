#!/usr/bin/env python

# Copyright (C) 2014 Alistair Buxton <a.j.buxton@gmail.com>
# Copyright (C) 2019 Edward Li <edwardyaoli@gmail.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import urllib
import youtube_dl
import json
import itertools
import os
import sys

baseurl = 'https://www.googleapis.com/youtube/v3'
my_key = 'INSERT API KEY HERE'
username = 'INSERT USERNAME HERE'

with open("mostrecent.txt", "r") as recent:
    mostRecentId = recent.readline().strip()

# check for missing inputs
if not my_key:
  print("YOUTUBE_SERVER_API_KEY variable missing.")
  sys.exit(-1)

def get_channel_for_user(user):
    print("Getting channel ID for "+user)
    url = baseurl + '/channels?part=id&forUsername='+ user + '&key=' + my_key
    response = urllib.request.urlopen(url)
    data = json.load(response)
    return data['items'][0]['id']

def get_playlists(channel):
    playlists = []
    # we have to get the full snippet here, because there is no other way to get the channelId
    # of the channels you're subscribed to. 'id' returns a subscription id, which can only be
    # used to subsequently get the full snippet, so we may as well just get the whole lot up front.
    url = baseurl + '/subscriptions?part=snippet&channelId='+ channel + '&maxResults=50&key=' + my_key

    next_page = ''
    while True:
        print("Getting subscribed channels (50 at a time)")
        # we are limited to 50 results. if the user subscribed to more than 50 channels
        # we have to make multiple requests here.
        response = urllib.request.urlopen(url+next_page)
        data = json.load(response)
        subs = []
        for i in data['items']:
            if i['kind'] == 'youtube#subscription':
                subs.append(i['snippet']['resourceId']['channelId'])

        # actually getting the channel uploads requires knowing the upload playlist ID, which means
        # another request. luckily we can bulk these 50 at a time.
        print("Getting subscribed channel playlist IDs (50 at a time)")
        purl = baseurl + '/channels?part=contentDetails&id='+ '%2C'.join(subs) + '&maxResults=50&key=' + my_key
        response = urllib.request.urlopen(purl)
        data2 = json.load(response)
        for i in data2['items']:
            try:
                playlists.append(i['contentDetails']['relatedPlaylists']['uploads'])
            except KeyError:
                pass

        try: # loop until there are no more pages
            next_page = '&pageToken='+data['nextPageToken']
        except KeyError:
            break

    return playlists

def get_playlist_items(playlist):
    videos = []

    if playlist:
        print("Getting last 25 items for playlist "+playlist)
        # get the last 5 videos uploaded to the playlist
        url = baseurl + '/playlistItems?part=contentDetails&playlistId='+ playlist + '&maxResults=25&key=' + my_key
        response = urllib.request.urlopen(url)
        data = json.load(response)
        for i in data['items']:
            if i['kind'] == 'youtube#playlistItem':
                videos.append(i['contentDetails']['videoId'])

    return videos

def get_real_videos(video_ids):
    print("Getting real video metadata (50 at a time)")
    videos = []
    purl = baseurl + '/videos?part=snippet&id='+ '%2C'.join(video_ids) + '&maxResults=50&key=' + my_key
    response = urllib.request.urlopen(purl)
    data = json.load(response)

    return data['items']

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]

def do_it():
    # get all upload playlists of subbed channels
    playlists = get_playlists(get_channel_for_user(username))

    # get the last 5 items from every playlist
    allitems = []
    for p in playlists:
        allitems.extend(get_playlist_items(p))

    # the playlist items don't contain the correct published date, so now
    # we have to fetch every video in batches of 50.
    allvids = []
    for chunk in chunks(allitems, 50):
        allvids.extend(get_real_videos(chunk))

    # sort them by date
    sortedvids = sorted(allvids, key=lambda k: k['snippet']['publishedAt'], reverse=True)
    sortedvids = sortedvids[:20]

    try:
        index = [v['id'] for v in sortedvids].index(mostRecentId)
        sortedvids = sortedvids[:index]
    except ValueError:
        pass

    sortedvids.reverse()
    print(f"Downloading {len(sortedvids)} videos")

    ydl_opts = {'format': '22'}

    if not os.path.exists("videos"):
        os.makedirs("videos")

    os.chdir("videos")

    # add the most recent 20
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        for v in sortedvids:
            ydl.download(["https://www.youtube.com/watch?v="+v['id']])
            with open('../mostrecent.txt', 'w') as recent:
                recent.write(v['id'])

if __name__ == '__main__':
    for i in range(3):
        try:
            do_it()
        except urllib.request.HTTPError as error:
            if error.code == 500:
                continue
            raise error
        break

