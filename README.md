## spotdl-ytm-service

Python script to be used as a service or launched manually to download your personal library from youtube music

## Configuration

As metadata are provided using [spotdl](https://github.com/spotDL/spotify-downloader) you will need spotify developer API Keys from here https://developer.spotify.com/

For youtube music premium users:
    you need to generate your own API Keys on google cloud console if you want to download music in 256kbps

* copy .env.sample to .env
* edit .env

## Install as docker scheduled service

* Run 'docker compose up'

## Run as script

* Run './installdeps.sh
* Run python get_music.py <args>

## Environment

* YT_CLIENT_ID="get this from google cloud console"
* YT_SECRET_ID="get this from google cloud console"
* SPOTIFY_CLIENT_ID="get this from spotify developer console"
* SPOTIFY_CLIENT_SECRET="get this from spotify developer console"
* SPOTDL_PLAYLIST_PATH="/media/playlist -> placeholder, will be implemented in future"
* SPOTDL_MUSIC_PATH="/media/musica/ -> where you want to download your music(if any)"

## Usage
* get_music.py             -> launch as script
* get_music.py scripted    -> launch as script
* get_music.py scheduled   -> launch as scheduled task every 24 hours
* get_music.py scheduled x -> launch as scheduled task every x minutes

A big thanks to the developers and maintaners of these libraries\softwares:
* [ytmusicapi](https://github.com/sigma67/ytmusicapi)
* [spotdl](https://github.com/spotDL/spotify-downloader) 