# -*- coding: utf-8 -*

import logging
import os
from logging import handlers
import shutil
import atexit
log = None

DB_DIR = os.path.dirname(__file__)
DB_PATH = DB_DIR + '/newspacks.db'

MB = 1024 * 1024
LOG_ROOT = '/var/log/newspack/'

TOPIC_SEPARATOR = '_-_'
DISPLAY_SEPARATOR = '|'

def mv_log(*log_fns):
    fn = log_fns[1]
    if os.path.exists(fn) and os.path.getsize(fn) == 0:
        for fn in log_fns:
            os.remove(fn)
    for fn in log_fns:
        if os.path.exists(fn):
            shutil.move(fn, LOG_ROOT + '/old/')

def get_logger():
    global log
    if not log:
        formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        pid = os.getpid()
        debug_fn = LOG_ROOT + str(pid) + '-news-debug.log'
        log_fn = LOG_ROOT + str(pid) + '-news.log'
        log = logging.getLogger(__name__)
        log.setLevel(logging.DEBUG)
        
        debug_fh = _init_handler(debug_fn, formatter, logging.INFO)
        fh = _init_handler(log_fn, formatter, logging.WARN)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)

        log.addHandler(debug_fh)
        log.addHandler(fh)
        log.addHandler(ch)
        atexit.register(mv_log, debug_fn, log_fn) 
        
    return log        

def _init_handler(fn, formatter, level=logging.DEBUG, maxBytes=30*MB, backupCount=10):
    fh = handlers.RotatingFileHandler(fn, maxBytes=maxBytes, backupCount=backupCount) 
    #fh = handlers.RotatingFileHandler(fn)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    return fh
