import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')
import sqlite3
import common

conn = sqlite3.connect(common.DB_PATH)

c = conn.cursor()

#delete all dn_topic
c.execute('delete from dn_topic')

#query
sql = 'select t.title, count(a.id), max(a.url_date)'\
      ' from topic as t'\
      ' join topic_article_rel as tar on t.title = tar.topic_title'\
      ' join article as a on tar.article_id = a.id'\
      ' group by t.title'
rows = list(c.execute(sql))
insert_sql = 'insert into dn_topic (title, amount, last_article) values (?, ?, ?)'
c.executemany(insert_sql, rows)
conn.commit()
