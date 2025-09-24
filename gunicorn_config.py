import multiprocessing

# Nombre de workers = (2 x CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1
bind = "0.0.0.0:10000"
worker_class = "sync"
timeout = 120
max_requests = 1000
max_requests_jitter = 100
preload_app = True