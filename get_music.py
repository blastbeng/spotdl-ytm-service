import os
import sys
import random
import traceback
import time
import datetime as dt
import eyed3
import logging
import requests
import requests_cache
from scheduler import Scheduler
from requests_cache.session import CachedSession
from requests_cache.backends import SQLiteCache
from tqdm import tqdm
from os.path import dirname
from os.path import join
from dotenv import load_dotenv
import ytmusicapi
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials
from ytmusicapi.exceptions import YTMusicServerError
from yt_dlp.utils import _utils as ytdlp_utils
from spotdl.utils.spotify import SpotifyClient
from spotdl.console import download
from spotdl.console import meta
from spotdl.utils import search
from spotdl.utils.config import create_settings
from spotdl.download.downloader import Downloader
from spotdl.utils.logging import init_logging

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

eyed3.log.setLevel("ERROR")


class Arguments:
    def __init__(self):
        self.config = True
        self.cache_path = os.path.dirname(
            os.path.realpath(__file__)) + '/config/.spotipy'
        self.cookie_file = os.path.dirname(
            os.path.realpath(__file__)) + '/config/cookies.txt'


class GetMusic(object):

    def __init__(self):
        requests_cache.install_cache(
            'get_music_cache', backend=SQLiteCache(
                db_path=os.path.dirname(
                    os.path.realpath(__file__)) + '/config/requests_cache.sqlite'))

        self.ytmusic = YTMusic(
            auth=os.path.dirname(
                os.path.realpath(__file__)) + '/config/oauth.json',
            oauth_credentials=OAuthCredentials(
                client_id=os.environ.get("YT_CLIENT_ID"),
                client_secret=os.environ.get("YT_SECRET_ID")))
        self.track_list = []
        self.audio_files = []
        self.spotify_settings, self.downloader_settings, web_settings = create_settings(
            Arguments())

        init_logging(
            self.downloader_settings["log_level"],
            self.downloader_settings["log_format"])
        self.logger = logging.getLogger(__name__)

    def delete_old_m3u(self):
        for item in os.listdir(os.environ.get("SPOTDL_PLAYLIST_PATH")):
            if item.endswith(".m3u"):
                os.remove(os.path.join(m3u_path, item))

    def make_dirs(self):
        if not os.path.exists(os.environ.get("SPOTDL_PLAYLIST_PATH")):
            os.makedirs(os.environ.get("SPOTDL_PLAYLIST_PATH"))

    def get_subscriptions_tracks(self):
        liked_suscriptions = self.ytmusic.get_library_subscriptions(limit=None)
        for subscription in tqdm(liked_suscriptions,
                                 desc="Scanning suscriptions"):
            if subscription['type'] == 'artist':
                artist = self.ytmusic.get_artist(
                    channelId=subscription['browseId'])
                if 'albums' in artist:
                    if 'params' in artist['albums']:
                        artist_albums = self.ytmusic.get_artist_albums(
                            channelId=artist['albums']['browseId'], params=artist['albums']['params'], limit=None)
                        for artist_album in artist_albums:
                            album_multi = self.ytmusic.get_album(
                                browseId=artist_album['browseId'])
                            if 'tracks' in album_multi:
                                for track in album_multi['tracks']:
                                    if self.verify_track(track):
                                        self.track_list.append(
                                            self.append_track(track['videoId']))
                if 'singles' in artist and 'browseId' in artist[
                        'singles'] and 'params' in artist['singles']:
                    singles = self.ytmusic.get_artist_albums(
                        channelId=artist['singles']['browseId'],
                        params=artist['singles']['params'],
                        limit=None)
                    for single in singles:
                        album_single = self.ytmusic.get_album(
                            browseId=single['browseId'])
                        if 'tracks' in album_single:
                            for track in album_single['tracks']:
                                if self.verify_track(track):
                                    self.track_list.append(
                                        self.append_track(track['videoId']))

    def get_library_songs_tracks(self):
        library_songs = self.ytmusic.get_library_songs(limit=None)
        for track in tqdm(library_songs, desc="Scanning library songs"):
            if self.verify_track(track):
                self.track_list.append(self.append_track(track['videoId']))

    def verify_track(self, track):
        if 'videoId' in track and track['videoId'] is not None:
            if (self.append_track(track['videoId'])) in self.track_list:
                return False
            if 'videoType' not in track or (
                    track['videoType'] != 'MUSIC_VIDEO_TYPE_ATV'):
                return False
            if "title" not in track or ("remix" in track["title"].lower() or "live at" in track["title"].lower(
            ) or "live_at" in track["title"].lower() or "live from" in track["title"].lower() or "live_from" in track["title"].lower()):
                return False
            if 'album' in track and 'name' in track['album'] and ("remix" in track['album']["name"].lower() or "live at" in track['album']["name"].lower(
            ) or "live_at" in track['album']["name"].lower() or "live from" in track['album']["name"].lower() or "live_from" in track['album']["name"].lower()):
                return False
            return True
        return False

    def get_history(self):
        history_songs = self.ytmusic.get_history()
        for track in tqdm(history_songs, desc="Scanning history songs"):
            if self.verify_track(track):
                self.track_list.append(self.append_track(track['videoId']))

    def get_liked_songs(self):
        liked_songs = self.ytmusic.get_liked_songs(limit=None)
        if 'tracks' in liked_songs:
            for track in tqdm(
                    liked_songs['tracks'], desc="Scanning liked songs"):
                if self.verify_track(track):
                    self.track_list.append(self.append_track(track['videoId']))

    def get_subscriptions(self):
        self.get_subscriptions_tracks()
        self.get_library_songs_tracks()

    def get_playlists(self):
        library_playlists = self.ytmusic.get_library_playlists(limit=None)
        for library_playlist in tqdm(
                library_playlists, desc="Scanning playlists"):
            playlist = self.ytmusic.get_playlist(
                library_playlist['playlistId'], limit=None)
            if 'tracks' in playlist and 'title' in playlist and (
                    playlist['id'] is None or 'lm' != playlist['id'].lower().strip()):
                for track in playlist['tracks']:
                    if self.verify_track(track):
                        self.track_list.append(
                            self.append_track(track['videoId']))

    def append_track(self, videoId):
        return ("https://music.youtube.com/watch?v=" + videoId).strip()

    def remove_empty_dirs(self, path=os.environ.get("SPOTDL_MUSIC_PATH")):
        if not os.path.isdir(path):
            return

        files = os.listdir(path)
        if len(files):
            for f in files:
                fullpath = os.path.join(path, f)
                if os.path.isdir(fullpath):
                    self.remove_empty_dirs(path=fullpath)

        files = os.listdir(path)
        if len(files) == 0 and path != os.environ.get("SPOTDL_MUSIC_PATH"):
            os.rmdir(path)

    def verify_songs_from_ytm(self, tracks):
        for track in tqdm(list(tracks),
                          desc="Verifying youtube music responses"):
            song_from_ytm = self.ytmusic.get_song(track.split("?v=", 1)[1])
            if 'videoDetails' not in song_from_ytm:
                self.logger.warning(
                    "Skipping " +
                    track +
                    ", youtube music response contains a bad json")
                self.tracks.remove(audio_file_path)
        return tracks

    def verify_mp3_files(self, init=True):
        for subdir, dirs, files in os.walk(
                os.environ.get("SPOTDL_MUSIC_PATH")):
            for file in files:
                if file.endswith('.mp3') or '.mp3.' in file:
                    self.audio_files.append(os.path.join(subdir, file))

        for audio_file_path in tqdm(
                list(self.audio_files), desc="Performing corrupted file check"):
            audio = eyed3.load(audio_file_path)
            if audio is None:
                self.logger.warning(
                    "Deleting " +
                    audio_file_path +
                    ", corrupted audio file")
                os.remove(audio_file_path)
                self.audio_files.remove(audio_file_path)
            if init:
                if audio.tag.comments is None or len(audio.tag.comments) == 0:
                    self.logger.warning(
                        "Deleting " +
                        audio_file_path +
                        ", no download link found for this song")
                    os.remove(audio_file_path)
                    self.audio_files.remove(audio_file_path)
                elif audio.tag.comments[0].text.strip() not in self.track_list:
                    self.logger.debug(
                        "Deleting " +
                        audio_file_path +
                        ", this song is not present inside the requested track list")
                    os.remove(audio_file_path)
                    self.audio_files.remove(audio_file_path)
                elif audio.tag.comments[0].text.strip() in self.track_list:
                    self.logger.debug(
                        "Skipping " +
                        audio_file_path +
                        ", this song was already downloaded")
                    self.track_list.remove(audio.tag.comments[0].text.strip())

    def update_metadata(self):
        if len(self.audio_files) == 0:
            self.logger.info(
                "No existing songs found, skipping metadata update...")
        else:
            random.shuffle(self.audio_files)
            chunks_audio_files = [self.audio_files[x:x + 32]
                                  for x in range(0, len(self.audio_files), 32)]
            for chunk_audio in tqdm(chunks_audio_files,
                                    desc="Updating songs metadata"):
                meta.meta(
                    chunk_audio, Downloader(self.downloader_settings))

    def download_songs(self):
        if len(self.track_list) == 0:
            self.logger.info("No new songs found, skipping download...")
        else:
            random.shuffle(self.track_list)
            cleaned_tracks = self.verify_songs_from_ytm(self.track_list)
            chunks_track_list = [cleaned_tracks[x:x + 32]
                                 for x in range(0, len(cleaned_tracks), 32)]
            for chunk_track in tqdm(chunks_track_list,
                                    desc="Downloadings tracks"):
                download.download(
                    cleaned_tracks, Downloader(self.downloader_settings))

    def get(self):
        exit_code = 0
        try:
            os.chdir(os.environ.get("SPOTDL_MUSIC_PATH"))
            self.make_dirs()
            self.delete_old_m3u()
            self.get_liked_songs()
            #self.get_playlists()
            #self.get_subscriptions()
            #self.verify_mp3_files()
            #self.remove_empty_dirs()

            try:
                if len(self.audio_files) != 0 or len(self.track_list) != 0:
                    SpotifyClient.init(**self.spotify_settings)
                self.update_metadata()
                self.download_songs()
            except Exception as e:
                raise e

        except Exception:
            self.logger.exception(traceback.format_exc())
            exit_code = 1
        finally:
            if len(self.track_list) > 0:
                self.verify_mp3_files(init=False)
                self.remove_empty_dirs()
        return exit_code


def is_int(val):
    try:
        int(val)
        return True
    except (ValueError, TypeError):
        return False


def main():
    if (len(sys.argv) == 2 and str(
            sys.argv[1]) == "script") or len(sys.argv) == 1:
        print('Executing in scripted mode.')
        get_music = GetMusic()
        sys.exit(get_music.get())
    elif (len(sys.argv) == 2 or len(sys.argv) == 3) and str(sys.argv[1]) == "scheduled":
        schedule = Scheduler(max_exec=1)
        minutes = 1440
        if len(sys.argv) == 3 and is_int(sys.argv[2]) and int(sys.argv[2]) > 0:
            minutes = int(sys.argv[2])
        print('Scheduling downloader every ' +
              str(minutes) + (' minute.' if (minutes == 1) else ' minutes.'))
        get_music = GetMusic()
        schedule.cyclic(dt.timedelta(minutes=minutes), get_music.get)
        while True:
            schedule.exec_jobs()
            time.sleep(1)
        print('Done.')
        sys.exit(0)
    else:
        print('Incorrect launch parameters')
        print('     get_music.py             -> launch as script')
        print('     get_music.py scripted    -> launch as script')
        print('     get_music.py scheduled   -> launch as scheduled task every 24 hours')
        print('     get_music.py scheduled x -> launch as scheduled task every x minutes')
        sys.exit(1)


if __name__ == "__main__":
    main()
