import urllib
import database as db
from django.shortcuts import render_to_response

def index(request):
    topics = db.list_topics()
    return render_to_response('index.html',
                              dict(topics=topics))


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
