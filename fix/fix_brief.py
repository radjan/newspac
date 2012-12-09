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

log = common.get_logger()

conn = sqlite3.connect(common.DB_PATH)
c = conn.cursor()

sql = 'select article_id, topic_title, brief'\
      ' from topic_article_rel'

c.execute(sql)
fetch = c.fetchall()

count = 0
t_count = 0
try:
  for aid, t, brief in fetch:
    if len(brief) > 200:
        lt = t.lower()
        l_cached = brief.lower()
        if lt in l_cached:
            idx = l_cached.find(lt)
            s = idx - 75
            e = idx + 75
            if s < 0:
                s = 0
                e += 75
            brief = brief[s:e]
        else:
            biref = brief[:150]
        db.insert_or_update_t_a_rel(t, aid, brief)
        count += 1
    t_count += 1
    #conn.commit()
finally:
  print 'total', t_count
  print 'do', count
