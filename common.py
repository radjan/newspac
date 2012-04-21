# -*- coding: utf-8 -*

import logging
import os
from logging import handlers

_log = None

MB = 1024 * 1024
LOG_ROOT = '/var/log/newspack/'

def get_logger():
    global _log
    if not _log:
        pid = os.getpid()
        _log = logging.getLogger(__name__)
        _log.setLevel(logging.DEBUG)
        debug_fh = _init_handler(LOG_ROOT + str(pid) + '-news-debug.log')
        fh = _init_handler(LOG_ROOT + str(pid) + '-news.log', logging.WARN)
        _log.addHandler(debug_fh)
        _log.addHandler(fh)
    return _log        

def _init_handler(fn, level=logging.DEBUG, maxBytes=30*MB, backupCount=10):
    fh = handlers.RotatingFileHandler(fn, maxBytes, backupCount) 
    fh.setLevel(level)
    return fh
