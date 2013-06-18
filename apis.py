#! /bin.env python
# -*- coding: utf-8 -*-

import datetime
import urllib

import database as db
import views

from django.http import HttpResponse
from django.utils import simplejson as json

CONTENT_TYPE_JSON = 'application/json; charset=utf-8'
MAX_LIMIT = 1000
ONE_DAY = datetime.timedelta(days=1)
DATE_FORMAT = '%Y-%m-%d'

def json_response(res):
    return HttpResponse(json.dumps(res, ensure_ascii=False, encoding='utf-8'),
                        content_type=CONTENT_TYPE_JSON)

@views.benchmark
def topics(request):
    return json_response(db.list_topics())

@views.benchmark
def sources(request):
    return json_response(db.list_sources())

def _parse_params(request):
    start = views._get(request, 'start')
    end = views._get(request, 'end')
    limit = views._get(request, 'limit')
    if start:
        start = datetime.datetime.strptime(start, DATE_FORMAT)
    if end:
        end = datetime.datetime.strptime(end, DATE_FORMAT) + ONE_DAY
    if limit:
        limit = int(limit)
        limit = limit if limit < MAX_LIMIT else MAX_LIMIT
    else:
        limit = MAX_LIMIT
    return start, end, limit

def _404_response():
    r = HttpResponse(json.dumps({"error_code": 404,
                                 "error": "Resource Not Found"}))
    r.status_code = 404
    return r

@views.benchmark
def topic(request, topic=''):
    t = db.get_topic(topic)
    if t is None:
        return _404_response()
    start, end, limit = _parse_params(request)
    articles = db.list_articles_by_topic(topic, start=start, end=end, limit=limit)
    t['articles'] = articles
    return json_response(t)

@views.benchmark
def source(request, source=''):
    s = db.get_source(source)
    if s is None:
        return _404_response()
    start, end, limit = _parse_params(request)
    articles = db.list_articles_by_source(source, start=start, end=end, limit=limit)
    s['articles'] = articles
    return json_response(s)

@views.benchmark
def article(request, aid=''):
    if not aid:
        return _404_response()
    aid = int(aid)
    article = db.get_article(aid)
    if not article:
        return _404_response()
    article['source'] = db.get_source(article['source'])
    article['topics'] = db.get_topics_by_article(aid)
    article['url'] = urllib.unquote(article['url'])
    article['source']['url'] = urllib.unquote(article['source']['url'])
    #if article['cached'] and len(article['cached']) > 100:
    #    article['cached'] = article['cached'][:100] + '...'
    return json_response(article)

@views.benchmark
def article_by_url(request):
    url = views._get(request, 'url')
    if not url:
        return _404_response()
    article = db.get_article_by_url(url)
    if not article:
        return _404_response()
    article['source'] = db.get_source(article['source'])
    #article['topics'] = db.get_topics_by_article(aid)
    article['url'] = urllib.unquote(article['url'])
    article['source']['url'] = urllib.unquote(article['source']['url'])
    #if article['cached'] and len(article['cached']) > 100:
    #    article['cached'] = article['cached'][:100] + '...'
    return json_response(article)
    
