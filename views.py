#! /bin/env python
# -*- coding: utf-8 -*-
import urllib
import os
import csv
import codecs
import cStringIO
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django import forms
from django.core.context_processors import csrf
from django.core.servers.basehttp import FileWrapper

import datetime

import database as db
import common
log = common.get_logger()

import power_price as p_p

bm = common.get_benchmark()
import time
import settings

BENCHMARK_VERSION = 1
def benchmark(fn):
    def new_fn(*args, **kw):
        t1 = time.time()
        is_log = True
        try:
            req =  args[0]
            ip = req.META['REMOTE_ADDR']
            query =  req.REQUEST
            path_info = req.META['PATH_INFO']
            agent = req.META['HTTP_USER_AGENT']
            if 'Baiduspider' in agent or 'Sogou web spider' in agent:
                is_log = False
                return HttpResponse('')
            return fn(*args, **kw)
        except Exception, e:
            log.error(e)
            raise
        finally:
            if is_log:
                t2 = time.time()
                entries = (BENCHMARK_VERSION, t1, t2-t1, ip, path_info,
                           fn.__name__, query, agent)
                bm.info('\t'.join(['%s'] * len(entries)) % entries)
    new_fn.__name__ = fn.__name__
    new_fn.__doc__ = fn.__doc__
    new_fn.__dict__.update(fn.__dict__)
    return new_fn

def empty(request):
    return HttpResponse('')

def maintenance(request):
    return HttpResponse(u'''
    <html>
    <head><title>新聞面面觀</title></head>
    <body style="text-align: center">
    <div>網站維護中，馬上回來！</div>
    <div>Site during maintenance, be right back!</div>
    </body>
    </html>
    ''')

@benchmark
def robot(request):
    return HttpResponse('''User-agent: *
Disallow: /*
''', content_type="text/plain")

@benchmark
def index(request):
    topics = db.homepage_topics()
    topics = _add_level(topics)
    #new_articles = db.get_new_artitcles(limit=30)
    return render_to_response('index.html',
                              dict(topics=topics,))
                                   #new_articles=new_articles))

def _add_level(datalist):
    def value_fn(item):
        return item['amount']
    def set_level(item, lv):
        item['level'] = lv
    cand_list = [value_fn(item) for item in datalist]
    cand_list = sorted(cand_list)
    idxs = _get_indexes(cand_list)
    for item in datalist:
        is_set = False
        for i in range(len(idxs)):
            if value_fn(item) <= idxs[i]:
                set_level(item, i + 1)
                is_set = True
                break
        if not is_set:
            set_level(item, len(idxs) + 1)
    return datalist

def _get_indexes(clist):
    l = len(clist)
    seg_10 = int(l * 0.1)
    seg_35 = int(l * 0.35)
    return [clist[seg_10], clist[seg_35], clist[-seg_35], clist[-seg_10]]

@benchmark
def topic(request):
    topics_str = _get(request, 'topic')
    if not topics_str:
        return HttpResponseRedirect('/')

    limit = _get(request, 'limit')
    if limit is None:
        limit = 100
    elif limit == 'all':
        limit = 0
    else:
        try:
            limit = int(limit)
        except Exception:
            limit = 100

    topics = topics_str.split(common.TOPIC_SEPARATOR)
    topic_dicts = [dict(topic=t, rm_q='') for t in topics]
    if len(topics) == 1:
        articles = db.list_articles_by_topic(topics[0], limit=limit)
    else:
        articles = db.list_articles_by_topics(topics, limit=limit)
        for topic_dict in topic_dicts:
            tmp_topics = topics[:]
            tmp_topics.remove(topic_dict['topic'])
            topic_dict['rm_q'] = _join_topic_str(tmp_topics,
                                                 common.TOPIC_SEPARATOR)
    def _process_row(a):
        a['created_date'] = a['created'][:10] #.timepstr('%Y-%M-%D')
        a['url'] = urllib.unquote(a['url'])
        a['source_url'] = urllib.unquote(a['source_url'])
        return a
    articles = [_process_row(a) for a in articles]
    limit = limit if len(articles) == limit else 0

    related_topics = db.get_related_topics(topics, limit=10)
    for item in related_topics:
        item['q'] = topics_str + common.TOPIC_SEPARATOR + item['title']
    highlight_pattern=_join_topic_str(topics, common.DISPLAY_SEPARATOR)
    return render_to_response('topic.html',
                              dict(topics=topic_dicts,
                                   topic=topics_str,
                                   highlight_pattern=highlight_pattern,
                                   articles=articles,
                                   limit=limit,
                                   related_topics=related_topics))

@benchmark
def article(request):
    aid = _get(request, 'id')
    if not aid:
        return HttpResponseRedirect('/')
    aid = int(aid)
    article = db.get_article(aid)
    if not article:
        return HttpResponseRedirect('/')
    article['source'] = db.get_source(article['source'])
    article['topics'] = db.get_topics_by_article(aid)
    article['url'] = urllib.unquote(article['url'])
    article['source']['url'] = urllib.unquote(article['source']['url'])
    if article['cached'] and len(article['cached']) > 100:
        article['cached'] = article['cached'][:100] + '...'
    return render_to_response('article.html', article)

@benchmark
def topic_ana(request):
    topics_str = _get(request, 'topic')
    if not topics_str:
        return HttpResponseRedirect('/')
    topics = topics_str.split(common.TOPIC_SEPARATOR)
    topic_dicts = [dict(topic=t, rm_q='') for t in topics]
    if len(topics) > 1:
        for topic_dict in topic_dicts:
            tmp_topics = topics[:]
            tmp_topics.remove(topic_dict['topic'])
            topic_dict['rm_q'] = _join_topic_str(tmp_topics,
                                                 common.TOPIC_SEPARATOR)
    related_topics = db.get_related_topics(topics)
    all_amount = db.get_articles_amount_by_topics(topics)
    for item in related_topics:
        item['q'] = topics_str + common.TOPIC_SEPARATOR + item['title']
        item['percentage'] = 100* item['amount'] / all_amount
        if item['percentage'] ==0:
            item['percentage'] = 1

    start = _shift_datetime(_truncate_day(datetime.datetime.now()), days=-7)
    all_7d_amount = db.get_articles_amount_by_topics(topics, start=start)
    related_7d_topics = db.get_related_topics(topics, start=start)
    for item in related_7d_topics:
        item['q'] = topics_str + common.TOPIC_SEPARATOR + item['title']
        item['percentage'] = 100* item['amount'] / all_7d_amount
        if item['percentage'] ==0:
            item['percentage'] = 1

    return render_to_response('topic_analytics.html',
                              dict(topics=topic_dicts,
                                   topic=topics_str,
                                   all_7d_amount=all_7d_amount,
                                   related_7d_topics=related_7d_topics,
                                   all_amount=all_amount,
                                   related_topics=related_topics))

def _get(r, key):
    return r.REQUEST[key] if key in r.REQUEST else None

def _truncate_day(dt):
    return datetime.datetime(dt.year, dt.month, dt.day)

def _shift_datetime(dt, days=0, hours=0, minutes=0, seconds=0):
    return dt + datetime.timedelta(days=days,
                                   hours=hours,
                                   minutes=minutes,
                                   seconds=seconds)

def _join_topic_str(topics, separator):
   return separator.join(topics) if len(topics) > 1 else topics[0] 

class PowerForm(forms.Form):
    num = forms.DecimalField(label = u'用電度數或是帳單金額（雙月）')
    deg_or_price = forms.ChoiceField([('price', u'帳單金額'), ('deg', u'用電度數')], label = u'選擇用電度數或是帳單金額')
    charge_type = forms.ChoiceField([(p_p.HOME, u'住家'), (p_p.BUSSINESS, u'營業')], label=u'用電類型')
    season = forms.ChoiceField([(p_p.NORMAL, u'非夏月用電'), (p_p.SUMMER, u'夏月用電')], label=u'用電季節')
    phase = forms.ChoiceField([(p_p.ORI, u'漲價前電價'), (p_p.PH1, u'第一階段調漲'), (p_p.PH2, u'第二階段調漲')], label = u'電價')
    
@benchmark
def power_price(request):
    deg = price = 0
    formula = results = []
    selected = {}
    if request.method == 'POST':
        form = PowerForm(request.POST, request.FILES)
        if form.is_valid():
            deg_or_price = form.cleaned_data['deg_or_price']
            charge_type = int(form.cleaned_data['charge_type'])
            season = str(form.cleaned_data['season'])
            phase = int(form.cleaned_data['phase'])
            num= form.cleaned_data['num']
            if deg_or_price == 'deg':
                deg = num
                price, formula = p_p.deg2price(deg, charge_type, season, phase)
            else:
                price = num 
                deg, formula = p_p.price2deg(price, charge_type, season, phase)
                deg = int(deg)
            for p in [p_p.ORI, p_p.PH1, p_p.PH2]:
                for s in [p_p.NORMAL, p_p.SUMMER]:
                    results.append(p_p.deg2price(deg, charge_type, s, p))
            selected['season'] = dict(form.fields['season'].choices)[season]
            selected['phase'] = dict(form.fields['phase'].choices)[phase]
            selected['charge_type'] = dict(form.fields['charge_type'].choices)[charge_type]
        else:
            form = PowerForm()
    else:
        form = PowerForm(initial={
                            'season': p_p.NORMAL,
                            'phase': p_p.PH1,})
    power = dict(form=form,
                 selected=selected,
                 deg=deg,
                 price=price,
                 formula=formula,
                 results=results)
    power.update(csrf(request))
    return render_to_response('power.html', power)

@benchmark
def source(request):
    s = _get(request, 's')
    if not s:
        return HttpResponseRedirect('/')
    articles = db.list_articles_by_source(s)
    if not articles:
        return HttpResponseRedirect('/')
    for article in articles:
        article['url'] = urllib.unquote(article['url'])
    source = db.get_source(s)
    return render_to_response('source.html', dict(articles=articles,
                                                  source=source))

DATA_ROOT = os.path.join(settings.ROOT_DIR, 'd')

@benchmark
def dtopic(request):
    t = _get(request, 't')
    if not t:
        return HttpResponseRedirect('/')
    filename = os.path.join(DATA_ROOT, 'topic', t)
    #if not os.path.exists(filename) or True:
    if True:
        with open(filename, 'wb') as f:
            writer = UnicodeWriter(f)
            topics = t.split(common.TOPIC_SEPARATOR)
            related_topics = db.get_related_topics(topics, limit=10)
            writer.writerow(['topic', 'articles'])
            writer.writerows([[d['title'], str(d['amount'])] for d in related_topics])
    wrapper = FileWrapper(file(filename))
    response = HttpResponse(wrapper, content_type='text/plain')
    response['Content-Length'] = os.path.getsize(filename)
    return response

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row) 
