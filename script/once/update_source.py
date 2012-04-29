import common
import database as db
logger = common.get_logger()
topics = db.list_topics()
for t in topics:
    articles = db.list_articles_by_topic(t)
    for a in articles:
        url = a['url']
        source_url = url[:url.find('/', url.find('//') + 2)]
        print a['source'], source_url
        db.update_source(a['source'], source_url)
    
