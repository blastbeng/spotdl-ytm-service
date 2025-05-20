import os
import re
import random
import traceback
import eyed3
import logging
import emoji
from tqdm import tqdm
from os.path import dirname
from os.path import join
from pathlib import Path
from dotenv import load_dotenv
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials
from spotdl.utils.spotify import SpotifyClient
from spotdl.console import download
from spotdl.console import meta
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

        self.ytmusic = YTMusic(
            auth=os.path.dirname(
                os.path.realpath(__file__)) + '/config/oauth.json',
            oauth_credentials=OAuthCredentials(
                client_id=os.environ.get("YT_CLIENT_ID"),
                client_secret=os.environ.get("YT_SECRET_ID")))
        self.spotify_settings, self.downloader_settings, web_settings = create_settings(
            Arguments())

        init_logging(
            self.downloader_settings["log_level"],
            self.downloader_settings["log_format"])

        self.logger = logging.getLogger('werkzeug')

    def delete_old_m3u(self):
        for item in os.listdir(os.environ.get("SPOTDL_PLAYLIST_PATH")):
            if item.endswith(".m3u"):
                os.remove(os.path.join(os.environ.get("SPOTDL_PLAYLIST_PATH"), item))

    def make_dirs(self):
        if not os.path.exists(os.environ.get("SPOTDL_PLAYLIST_PATH")):
            os.makedirs(os.environ.get("SPOTDL_PLAYLIST_PATH"))

    def get_subscriptions_tracks(self, track_list):
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
                                    if self.verify_track(track, track_list):
                                        track_list.append(
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
                                if self.verify_track(track, track_list):
                                    track_list.append(
                                        self.append_track(track['videoId']))
        return track_list

    def get_library_songs_tracks(self, track_list):
        library_songs = self.ytmusic.get_library_songs(limit=None)
        for track in tqdm(library_songs, desc="Scanning library songs"):
            if self.verify_track(track, track_list):
                track_list.append(self.append_track(track['videoId']))
        return track_list

    def verify_track(self, track, track_list):
        if 'videoId' in track and track['videoId'] is not None:
            if (self.append_track(track['videoId'])) in track_list:
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

    def get_history(self, track_list):
        history_songs = self.ytmusic.get_history()
        for track in tqdm(history_songs, desc="Scanning history songs"):
            if self.verify_track(track, track_list):
                track_list.append(self.append_track(track['videoId']))

    def get_liked_songs(self, track_list):
        liked_songs = self.ytmusic.get_liked_songs(limit=None)
        if 'tracks' in liked_songs:
            for track in tqdm(
                    liked_songs['tracks'], desc="Scanning liked songs"):
                if self.verify_track(track, track_list):
                    track_list.append(self.append_track(track['videoId']))
        return track_list

    def get_subscriptions(self):
        track_list = self.get_subscriptions_tracks(track_list)
        track_list = self.get_library_songs_tracks(track_list)

    def get_playlists(self, track_list, generate_m3u=False):
        library_playlists = self.ytmusic.get_library_playlists(limit=None)
        audio_objects = []
        if generate_m3u and len(library_playlists) > 0:
            audio_objects = self.get_audio_objects()

        if generate_m3u and len(audio_objects) == 0:
            logger.warning("No existing audio files found, Skipping playlist import procedure")
        else:
            for library_playlist in tqdm(library_playlists, desc='Importing playlists' if generate_m3u else 'Scanning playlists'):
                playlist = self.ytmusic.get_playlist(
                    library_playlist['playlistId'], limit=None)
                if 'tracks' in playlist and 'title' in playlist and (
                        playlist['id'] is None or 'lm' != playlist['id'].lower().strip()):
                    m3u_path = None
                    if generate_m3u:
                        m3u_path = os.environ.get("SPOTDL_PLAYLIST_PATH") + emoji.replace_emoji(playlist['title'], '').replace("/", " ").replace("\\"," ").strip() + ".m3u"
                        with open(m3u_path, "w") as m3u_file:
                            m3u_file.write("#EXTM3U\n")
                    for track in playlist['tracks']:
                        if self.verify_track(track, track_list):
                            track = self.append_track(track['videoId'])
                            if generate_m3u and m3u_path is not None:
                                audio_dict = self.search_for_track(track, audio_objects)
                                if audio_dict is not None:
                                    with open(m3u_path, "a") as m3u_file:
                                        record = f"#EXTINF:{audio_dict['duration']},{audio_dict['artist']}-{audio_dict['album']}-{audio_dict['title']}.{Path(audio_dict['path']).suffix}"
                                        m3u_file.write("\n"+record+"\n")
                                        m3u_file.write(audio_dict['path'].replace(os.environ.get("SPOTDL_MUSIC_PATH"),"./")+"\n")
                            else:
                                track_list.append(track)
        return track_list

    def search_for_track(self, track, audio_objects):
        for audio_dict in audio_objects:
            if audio_dict["url"] == track:
                return audio_dict
        return None
               

    def get_audio_files(self):
        audio_files = []
        for subdir, dirs, files in tqdm(os.walk(
                os.environ.get("SPOTDL_MUSIC_PATH")), desc="Reading existing files"):
            for file in files:
                if file.endswith('.mp3'):
                    audio_files.append(os.path.join(subdir, file))
        return audio_files

    def get_audio_objects(self):
        audio_objects = []
        audio_files = self.get_audio_files()
        for audio_file_path in tqdm(audio_files, desc="Reading audio tags"):
            if audio_file_path.endswith('.mp3'):
                audio = eyed3.load(audio_file_path)
                if audio is None:
                    self.delete_audio_file(audio_file_path)
                elif audio.tag.comments is not None and len(audio.tag.comments) != 0:
                    audio_dict = {}
                    audio_dict["url"] = audio.tag.comments[0].text.strip()
                    audio_dict["path"] = audio.path
                    audio_dict["duration"] = audio.info.time_secs
                    audio_dict["artist"] = audio.tag.artist
                    audio_dict["title"] = audio.tag.title
                    audio_dict["album"] = audio.tag.album
                    audio_objects.append(audio_dict)
        return audio_objects

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
        if len(files) == 0 and path != os.environ.get("SPOTDL_MUSIC_PATH") and path != os.environ.get("SPOTDL_PLAYLIST_PATH"):
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

    def delete_audio_file(self, audio_file_path, audio_files):
        self.logger.warning(
            "Deleting " +
            audio_file_path +
            ", corrupted audio file")
        os.remove(audio_file_path)
        audio_files.remove(audio_file_path)
        return audio_files

    def verify_mp3_files(self, track_list, init=True):
        audio_files = self.get_audio_files()
        for audio_file_path in tqdm(
                list(audio_files), desc="Performing corrupted file check"):
            audio = eyed3.load(audio_file_path)
            if audio is None:
                audio_files = self.delete_audio_file(audio_file_path, audio_files)
            elif init:
                if audio.tag.comments is None or len(audio.tag.comments) == 0:
                    self.logger.warning(
                        "Deleting " +
                        audio_file_path +
                        ", no download link found for this song")
                    os.remove(audio_file_path)
                    audio_files.remove(audio_file_path)
                elif audio.tag.comments[0].text.strip() not in track_list:
                    self.logger.debug(
                        "Deleting " +
                        audio_file_path +
                        ", this song is not present inside the requested track list")
                    os.remove(audio_file_path)
                    audio_files.remove(audio_file_path)
                elif audio.tag.comments[0].text.strip() in track_list:
                    self.logger.debug(
                        "Skipping " +
                        audio_file_path +
                        ", this song was already downloaded")
                    track_list.remove(audio.tag.comments[0].text.strip())
        return audio_files, track_list

    def update_metadata(self, audio_files, chunks_len=32):
        if len(audio_files) == 0:
            self.logger.info(
                "No existing songs found, skipping metadata update...")
        else:
            SpotifyClient.init(**self.spotify_settings)
            random.shuffle(audio_files)
            chunks_audio_files = [audio_files[x:x + chunks_len]
                                  for x in range(0, len(audio_files), chunks_len)]
            with tqdm(total=len(audio_files), desc="Updating songs metadata") as ubar:
                for chunk_audio in chunks_audio_files:
                    meta.meta(
                        chunk_audio, Downloader(self.downloader_settings))
                    ubar.update(chunks_len)

    def download_songs(self, track_list, chunks_len=32):
        if len(track_list) == 0:
            self.logger.info("No new songs found, skipping download...")
        else:
            SpotifyClient.init(**self.spotify_settings)
            random.shuffle(track_list)
            cleaned_tracks = self.verify_songs_from_ytm(track_list)
            chunks_track_list = [cleaned_tracks[x:x + chunks_len]
                                 for x in range(0, len(cleaned_tracks), chunks_len)]
            with tqdm(total=len(track_list), desc="Downloadings tracks") as dbar:
                for chunk_track in chunks_track_list:
                    download.download(
                        chunk_track, Downloader(self.downloader_settings))
                    dbar.update(chunks_len)

    def meta(self):
        try:
            self.logger.info("START - get_music.meta")
            self.update_metadata(self.get_audio_files())
        except Exception:
            self.logger.error(traceback.format_exc())
            self.logger.info("DONE - get_music.meta")

    def playlist(self):
        try:
            self.logger.info("START - get_music.playlist")
            self.delete_old_m3u()
            self.get_playlists([], generate_m3u=True)
        except Exception:
            self.logger.error(traceback.format_exc())
            self.logger.info("DONE - get_music.playlist")

    def get(self):
        try:
            self.logger.info("START - get_music.get")
            os.chdir(os.environ.get("SPOTDL_MUSIC_PATH"))

            track_list = []
            audio_files = []

            self.make_dirs()
            track_list = self.get_liked_songs(track_list)
            track_list = self.get_playlists(track_list)
            track_list = self.get_subscriptions(track_list)

            audio_files, track_list = self.verify_mp3_files(track_list)
            if len(audio_files) != 0:
                self.remove_empty_dirs()

            download_songs(track_list)

        except Exception:
            self.logger.error(traceback.format_exc())
        finally:
            self.verify_mp3_files([], init=False)
            self.remove_empty_dirs()
            self.logger.info("DONE - get_music.get")
