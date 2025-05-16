## spotdl-ytm-service

Python script to be used as a service or launched manually to download your personal library from youtube music

## Configuration

        * You need to generate your own API Keys on google cloud console if you want to download music in 256kbps
        * copy .env.sample to .env
        * edit .env and you're good to go

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