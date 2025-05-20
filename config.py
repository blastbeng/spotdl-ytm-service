class Config(object):
    """All application configurations"""

    SCHEDULER_API_ENABLED = False
    SCHEDULER_API_PREFIX = "/api/v1/scheduler"
    SCHEDULER_EXECUTORS = {
        "default": {
            "type": "processpool",
            "max_workers": 4}}
