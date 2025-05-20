from gevent import monkey
monkey.patch_all(thread=False, select=False)
bind = '0.0.0.0:5484'
backlog = 2048

workers = 4
worker_class = 'gthread'
worker_connections = 1000
timeout = 43200
keepalive = 2
spew = False
capture_output = True
threads = 4

daemon = False

errorlog = '-'
accesslog = '-'
