import argparse
import spotipy
import time
from concurrent.futures import ThreadPoolExecutor
from queue import SimpleQueue
from spotipy.oauth2 import SpotifyClientCredentials
from threading import Event
from ytmusicapi import YTMusic


def get_sp_playlist(sp_creds, sp_playlist_uri, queue, qstop):
    sp_id_secret = sp_creds.split(":")
    client_credentials_manager = SpotifyClientCredentials(sp_id_secret[0], sp_id_secret[1])
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
   
    sp_playlist_info = sp.playlist(sp_playlist_uri, fields="name,tracks.total") 
    sp_playlist_name = sp_playlist_info["name"]
    sp_playlist_total = sp_playlist_info["tracks"]["total"]

    offset = 0
    while True:
        response = sp.playlist_items(sp_playlist_uri, offset=offset, fields='items.track.name,items.track.artists')
        if not len(response["items"]):
            break

        # send a list containing song name and a list of artists to queue
        for song in response["items"]:
            artists = []
            for artist in song["track"]["artists"]:
                artists.append(artist["name"])
            queue.put([song["track"]["name"], artists])

        offset += len(response["items"])
        if offset == sp_playlist_total:
            qstop.set()
        print(f"[*] {offset}/{sp_playlist_total} Spotify songs retrieved...", end="\r")
    print(f"[*] {offset}/{sp_playlist_total} Spotify songs retrieved...")

    return sp_playlist_name, sp_playlist_total


def search_yt_playlist(ytmusic, queue, qstop, playlist_type, autocorrect):
    unadded_songs = []
    yt_song_ids = []
    while not qstop.is_set() or not queue.empty():
        search_term = queue.get()
        search_results = ytmusic.search(search_term[0] + " " + " ".join(search_term[1]), filter=playlist_type, ignore_spelling=autocorrect)
        if search_results:
            yt_song_ids.append(search_results[0]["videoId"])
        elif not search_results and len(search_term[1]) > 1:  # try searching for song only listing the main artist
            search_results = ytmusic.search(search_term[0] + " " + search_term[1][0], filter=playlist_type, ignore_spelling=autocorrect)
            if search_results:
                yt_song_ids.append(search_results[0]["videoId"])
            else:
                unadded_songs.append(search_term[0])
                print(f"[!] Skipping song: '{search_term[0]}'...")
        else:
            unadded_songs.append(search_term[0])
            print(f"[!] Skipping song: '{search_term[0]}'...")

    return unadded_songs, yt_song_ids


def create_yt_playlist(ytmusic, playlist_name, yt_song_ids):
    print(f"[*] Creating Youtube playlist named '{playlist_name}'...")
    yt_playlist_id = ytmusic.create_playlist(playlist_name, "Spotify playlist")

    # Add a list of Youtube song IDs to a playlist
    try:
        print("[*] Adding songs to Youtube playlist...")
        r = ytmusic.add_playlist_items(yt_playlist_id, yt_song_ids, duplicates=True)
        if r["status"] != "STATUS_SUCCEEDED":
            for _ in range(5):
                try:
                    print("[!] Failed adding songs to Youtube, trying again in 5 seconds...")
                    time.sleep(5)
                    ytmusic.add_playlist_items(yt_playlist_id, yt_song_ids, duplicates=True) 
                    break
                except Exception as e:
                    print(e)
                    continue
    except Exception as e:
        print("[!]", e)


def main():
    parser = argparse.ArgumentParser(description="Multithreaded script to recreate a Spotify playlist on Youtube",
                                    epilog='''
                                    Example: python3 spotify2youtube.py -id "49f96038f20aa062772267b640a18d79:dd02c7c2232759874e1c205587017bed" 
                                    -p "spotify:playlist:d06dafe4687e579fce76b3" -yt "POST /youtubei/v1/browse?key=qELvSDvkcRwsAw6X54sdf8dJpC7L-dEYcDNy0w..." -t 40 
                                    --playlist-type "songs" --disable-youtube-autocorrect''')
    parser.add_argument("-id", "--spotify-creds", required=True, help="Spotify client ID and client secret separated by a colon")
    parser.add_argument("-p", "--playlist-uri", required=True, help="URI of Spotify playlist")
    parser.add_argument("-yt", "--youtube-auth", required=True, help="Youtube auth headers")
    parser.add_argument("--playlist-type", choices=["videos", "songs"], default="videos", help="Select whether to create a video or song playlist on Youtube, default=videos")
    parser.add_argument("-t", "--threads", default=20, type=int, help="Select number of threads, default=20")
    parser.add_argument("--disable-youtube-autocorrect", action='store_true', help="Disables Youtube's autocorrect while searching")
    args = parser.parse_args()
    
    # Create ytmusicapi authenticated object used to add to a user's playlist and an unauthenticated object used for searching
    ytauth = YTMusic.setup(headers_raw=args.youtube_auth)
    ytmusic = YTMusic(str(ytauth))
    ytmusic_searching = YTMusic()

    q = SimpleQueue()
    qstop = Event()

    unadded_songs = []
    yt_song_ids = []

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        print(f"[*] Retrieving songs from Spotify...")
        info = executor.submit(get_sp_playlist, args.spotify_creds, args.playlist_uri, q, qstop)     

        print("[*] Thread pool searching Spotify songs on Youtube...")
        futures = [executor.submit(search_yt_playlist, ytmusic_searching, q, qstop, args.playlist_type, args.disable_youtube_autocorrect) for _ in range(executor._max_workers)]

        # Aggregate thread results
        for f in futures:
            unadded_songs += f.result()[0]
            yt_song_ids += f.result()[1]

        # Add the list of song IDs to Youtube playlist
        create_yt_playlist(ytmusic, info.result()[0], yt_song_ids) 

    if unadded_songs:
        print("[!] Songs that need to be manually added:", unadded_songs)

    print("[*] Finished!")

if __name__ == '__main__':
    main()

