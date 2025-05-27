import os

class Arguments:
    def __init__(self):
        self.config = True
        self.cache_path = os.path.dirname(
            os.path.realpath(__file__)) + '/config/.spotipy'
        self.cookie_file = os.path.dirname(
            os.path.realpath(__file__)) + '/config/cookies.txt'
        self.yt_dlp_args = " --proxy " + os.environ.get("SQUID_PROXY_URL")
        self.proxy = os.environ.get("SQUID_PROXY_URL")