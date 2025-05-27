import eventlet
eventlet.monkey_patch()
bind = '0.0.0.0:5484'
backlog = 2048

workers = 1
worker_class = 'gthread'
worker_connections = 1000
timeout = 43200
keepalive = 2
spew = False
capture_output = True
threads = 1

daemon = False

errorlog = '-'
accesslog = '-'
