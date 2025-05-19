class Config(object):
    """All application configurations"""

    SCHEDULER_API_ENABLED = True
    SCHEDULER_API_PREFIX = "/api/v1/scheduler"
    SCHEDULER_EXECUTORS = {
        "default": {
            "type": "threadpool",
            "max_workers": 1}}
