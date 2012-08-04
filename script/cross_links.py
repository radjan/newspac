import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')
import sqlite3
import common
import database as db
import datetime
TS_FORMAT = '%Y-%m-%d %H:%M:%S'
ONE_DAY = datetime.timedelta(days=1)
ONE_HOUR = datetime.timedelta(hours=1)
#now the script runs every 3 hour, given it two chances
PROCESS_WINDOW = ONE_HOUR * 7

log = common.get_logger()

conn = sqlite3.connect(common.DB_PATH)
c = conn.cursor()

latest_topic_sql = 'select max(created) from topic'
c.execute(latest_topic_sql)
latest = c.fetchone()[0]
latest_dt = datetime.datetime.strptime(latest, TS_FORMAT)
now = datetime.datetime.now()

sql = 'select a.id, a.title, tar.brief, tar.topic_title'\
      ' from article as a join topic_article_rel as tar'\
      ' on a.id = tar.article_id'
if (now - latest_dt) > PROCESS_WINDOW:
    #no new topic, do the latest only
    c.execute(sql + ' where a.created > ?', (now - PROCESS_WINDOW,))
else:
    c.execute(sql)

fetch = c.fetchall()
articles = {}
for row in fetch:
    a = articles.setdefault(row[0], {'topics': set()})
    a['id'] = row[0]
    a['title'] = unicode(row[1])
    a['brief'] = unicode(row[2])
    a['topics'].add(row[3])

print len(articles)

topics = db.list_topics()
count = 0
for t in topics:
    for aid, a in articles.items():
        if t not in a['topics']:
            if t.lower() in a['title'].lower() or t.lower() in a['brief'].lower():
                db.insert_or_update_t_a_rel(t, aid, a['brief'])
                count += 1
conn.commit()
print 'add %s links' % count
