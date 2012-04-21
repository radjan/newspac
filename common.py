# -*- coding: utf-8 -*

import logging
import os
from logging import handlers
import shutil
import atexit
log = None

MB = 1024 * 1024
LOG_ROOT = '/var/log/newspack/'

def mv_log(*log_fns):
    for fn in log_fns:
        if os.path.exists(fn):
            shutil.move(fn, LOG_ROOT + '/old/')

def get_logger():
    global log
    if not log:
        pid = os.getpid()
        debug_fn = LOG_ROOT + str(pid) + '-news-debug.log'
        log_fn = LOG_ROOT + str(pid) + '-news.log'
        log = logging.getLogger(__name__)
        log.setLevel(logging.DEBUG)
        debug_fh = _init_handler(debug_fn)
        fh = _init_handler(log_fn, logging.WARN)
        log.addHandler(debug_fh)
        log.addHandler(fh)
        atexit.register(mv_log, debug_fn, log_fn) 
        
    return log        

def _init_handler(fn, level=logging.DEBUG, maxBytes=30*MB, backupCount=10):
    #fh = handlers.RotatingFileHandler(fn, maxBytes, backupCount) 
    fh = logging.FileHandler(fn, maxBytes, backupCount) 
    fh.setLevel(level)
    return fh
