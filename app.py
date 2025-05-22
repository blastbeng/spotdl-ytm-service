import os
import logging
from get_music import GetMusic
from config import Config
import eyed3
import logging
from time import strftime
from tqdm import tqdm
from os.path import dirname
from os.path import join
from dotenv import load_dotenv
from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials
from spotdl.utils.spotify import SpotifyClient
from spotdl.console import download
from spotdl.console import meta
from spotdl.utils.config import create_settings
from spotdl.download.downloader import Downloader
from spotdl.utils.logging import init_logging
from flask_apscheduler import APScheduler
from flask import Flask
from flask import request
from flask import send_file
from flask import Response
from flask_restx import Api
from flask_restx import Resource
import threading

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=int(
        os.environ.get("LOG_LEVEL", 40)),
    datefmt='%Y-%m-%d %H:%M:%S')


log = logging.getLogger('werkzeug')
log.setLevel(int(os.environ.get("LOG_LEVEL",
             40)))

app = Flask(__name__)
app.config.from_object(Config)

scheduler = APScheduler()
scheduler.init_app(app)
api = Api(app)
downloader_ytm = GetMusic()


@app.after_request
def after_request(response):
    """Excluding healthcheck endpoint from logging"""
    if not request.path.startswith('/api/v1/utils/healthcheck'):
        timestamp = strftime('[%Y-%b-%d %H:%M]')
        logging.info('%s %s %s %s %s %s',
                     timestamp,
                     request.remote_addr,
                     request.method,
                     request.scheme,
                     request.full_path,
                     response.status)
    return response


nsutils = api.namespace('utils', 'Utils APIs')


@nsutils.route('/healthcheck')
class Healthcheck(Resource):
    """Healthcheck class"""

    def get(self):
        """Healthcheck endpoint"""
        return "Ok!"


nsdownload = api.namespace('download', 'Downloader APIs')


@nsdownload.route('/run')
class RunDownload(Resource):
    """Run Download class"""

    def get(self):
        """Run Download endpoint"""
        threading.Thread(
            target=lambda: scheduler
            .run_job("download_music")).start()
        return "Starting download_music job!"


@nsdownload.route('/pause')
class PauseDownload(Resource):
    """Pause Download class"""

    def get(self):
        """Pause Download endpoint"""
        threading.Thread(
            target=lambda: scheduler
            .pause_job("download_music")).start()
        return "Pausing download_music job!"


@nsdownload.route('/resume')
class ResumeDownload(Resource):
    """Resume Download class"""

    def get(self):
        """Resume Download endpoint"""
        threading.Thread(
            target=lambda: scheduler
            .resume_job("download_music")).start()
        return "Resume download_music Job!"


nsmetadata = api.namespace('metadata', 'Metadata APIs')


@nsmetadata.route('/run')
class RunMetadata(Resource):
    """Run Metadata class"""

    def get(self):
        """Run Metadata endpoint"""
        threading.Thread(
            target=lambda: scheduler
            .run_job("update_metadata")).start()
        return "Starting update_metadata job!"


@nsmetadata.route('/pause')
class PauseMetadata(Resource):
    """Pause Metadata class"""

    def get(self):
        """Pause Metadata endpoint"""
        threading.Thread(
            target=lambda: scheduler
            .pause_job("update_metadata")).start()
        return "Pausing update_metadata job!"


@nsmetadata.route('/resume')
class ResumeMetadata(Resource):
    """Resume Metadata class"""

    def get(self):
        """Resume Metadata endpoint"""
        threading.Thread(
            target=lambda: scheduler
            .resume_job("update_metadata")).start()
        return "Resume update_metadata Job!"


nsplaylist = api.namespace('playlist', 'Playlist APIs')


@nsplaylist.route('/import')
class Import(Resource):
    """Import Playlist class"""

    def get(self):
        """Import Playlist endpoint"""
        threading.Thread(
            target=lambda: downloader_ytm.playlist).start()
        return "Starting import_playlists job!"

scheduler.add_job(
    func=downloader_ytm.get,
    trigger="interval",
    minutes=int(os.environ.get("SCHEDULER_MINUTES", 1440)),
    id="download_music",
    replace_existing=True,
    max_instances=1
)

scheduler.add_job(
    func=downloader_ytm.meta,
    trigger="interval",
    minutes=int(os.environ.get("SCHEDULER_MINUTES", 7200)),
    id="update_metadata",
    replace_existing=True,
    max_instances=1
)

#scheduler.add_job(
#    func=downloader_ytm.playlist,
#    trigger="interval",
#    minutes=int(os.environ.get("SCHEDULER_MINUTES", 4320)),
#    id="import_playlists",
#    replace_existing=True,
#    max_instances=1
#)

scheduler.start()

if __name__ == '__main__':
    app.run()
