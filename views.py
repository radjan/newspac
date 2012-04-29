import urllib
import database as db
from django.shortcuts import render_to_response
import common
log = common.get_logger()

def index(request):
    topics = db.homepage_topics()
    topics = _add_level(topics)
    return render_to_response('index.html',
                              dict(topics=topics))

def _add_level(datalist):
    def value_fn(item):
        return item['amount']
    def set_level(item, lv):
        item['level'] = lv
    cand_list = [value_fn(item) for item in datalist]
    cand_list = sorted(cand_list)
    log.debug(cand_list)
    idxs = _get_indexes(cand_list)
    log.debug(idxs)
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


def topic(request):
    def _process_row(a):
        a['created_date'] = a['created'][:10] #.timepstr('%Y-%M-%D')
        a['url'] = urllib.unquote(a['url'])
        a['source_url'] = urllib.unquote(a['source_url'])
        return a
        
    topic = request.REQUEST['topic']
    articles = db.list_articles_by_topic(topic)
    articles = [_process_row(a) for a in articles]
    return render_to_response('topic.html',
                              dict(topic=topic,
                                   articles=articles))
