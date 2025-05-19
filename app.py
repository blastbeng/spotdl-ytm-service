import os
import logging
from get_music import GetMusic
from config import Config
import eyed3
import logging
import requests_cache
from requests_cache.backends import SQLiteCache
from logging.handlers import RotatingFileHandler
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
from flask import Flask, request, send_file, Response, jsonify, make_response, after_this_request, g, render_template
from flask_restx import Api, Resource, reqparse


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

scheduler.add_job(
    func=downloader_ytm.get,
    trigger="interval",
    minutes=int(os.environ.get("SCHEDULER_MINUTES", 1440)),
    id="download_music",
    replace_existing=True,
    max_instances=1
)

scheduler.start()

scheduler.run_job("download_music")