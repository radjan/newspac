#! /bin.env python
# -*- coding: utf-8 -*-

import database as db
#import simplejson as json
#import json
from django.utils import simplejson as json

from views import benchmark
from django.http import HttpResponse

CONTENT_TYPE_JSON = 'application/json; charset=utf-8'

def json_response(res):
    return HttpResponse(json.dumps(res, ensure_ascii=False, encoding='utf-8'),
                        content_type=CONTENT_TYPE_JSON)

@benchmark
def topics(request):
    return json_response(db.list_topics())

@benchmark
def sources(request):
    return json_response(db.list_sources())

