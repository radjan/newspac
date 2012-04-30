import sqlite3
import common
import database as db

log = common.get_logger()

conn = sqlite3.connect(common.DB_PATH)
c = conn.cursor()

topics = db.list_topics()

sql = 'select a.id, a.title, tar.brief, tar.topic_title'\
      ' from article as a join topic_article_rel as tar'\
      ' on a.id = tar.article_id '
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

count = 0
for t in topics:
    for aid, a in articles.items():
        if t not in a['topics']:
            if t in a['title'] or t in a['brief']:
                db.insert_or_update_t_a_rel(t, aid, a['brief'])
                count += 1
conn.commit()
print 'add %s links' % count
