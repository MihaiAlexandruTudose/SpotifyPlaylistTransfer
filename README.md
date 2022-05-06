# SpotifyPlaylistTransfer
Multithreaded Python script to transfer Spotify playlist to Youtube. Uses Spotify API and an un-offical Youtube Music wrapper library.

# Requirements
- Python 3.6+
- ```pip install -r requirements.txt```

# Usage
1. Create an app at https://developer.spotify.com/dashboard/applications.
2. Copy Spotify app id and secret to the -id option, Example: ```-id "<id>:<secret>"```.
3. Copy Spotify playlist uri to the -p option. Click the dropdown, Hover over **Share**, Hold Alt, Click "Copy Spotify URI", Example: (... -> Share -> Hold Alt -> Copy Spotify URI)
4. Copy Youtube Music POST headers as specified at https://ytmusicapi.readthedocs.io/en/latest/setup.html to the -yt command line option,
   Example: ```-yt "POST /youtubei/v1/browse?key=qELvSDvkcRwsAw6X54sdf8dJpC7L-dEYcDNy0w..."```.


# Command line options
```
usage: spotify2youtube.py [-h] -id SPOTIFY_CREDS -p PLAYLIST_URI -yt YOUTUBE_AUTH [--playlist-type {videos,songs}] [-t THREADS] [--disable-youtube-autocorrect]

Multithreaded script to recreate a Spotify playlist on Youtube

options:
  -h, --help            show this help message and exit
  -id SPOTIFY_CREDS, --spotify-creds SPOTIFY_CREDS
                        Spotify client ID and client secret separated by a colon
  -p PLAYLIST_URI, --playlist-uri PLAYLIST_URI
                        URI of Spotify playlist
  -yt YOUTUBE_AUTH, --youtube-auth YOUTUBE_AUTH
                        Youtube auth headers
  --playlist-type {videos,songs}
                        Select whether to create a video or song playlist on Youtube, default=videos
  -t THREADS, --threads THREADS
                        Select number of threads, default=20
  --disable-youtube-autocorrect
                        Disables Youtube's autocorrect while searching

Example: python3 spotify2youtube.py -id "49f96038f20aa062772267b640a18d79:dd02c7c2232759874e1c205587017bed" -p "spotify:playlist:d06dafe4687e579fce76b3"
-yt "POST /youtubei/v1/browse?key=qELvSDvkcRwsAw6X54sdf8dJpC7L-dEYcDNy0w..." -t 40 --playlist-type "songs" --disable-youtube-autocorrect
```

# Libraries
- spotipy: https://github.com/plamere/spotipy
- ytmusicapi: https://github.com/sigma67/ytmusicapi
