# -*- coding: utf-8 -*-
import sqlite3
import atexit
import datetime
import traceback
import threading

import common
log = common.get_logger()

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def log_entry(fn):
    def new_fn(*args, **kw):
        try:
            log.debug('<== entering %s' % fn.__name__)
            log.debug((u'    args: (' + u' %s,'*len(args) + u'), kw: %s') % (args + (kw,)))
            return fn(*args, **kw)
        except Exception, e:
            log.error(traceback.format_exc())
            raise
        finally:
            log.debug('==> leaving %s' % fn.__name__)
    new_fn.__name__ = fn.__name__
    new_fn.__doc__ = fn.__doc__
    new_fn.__dict__.update(fn.__dict__)
    return new_fn


THREAD_LOCAL = False
def transaction(fn):
    def new_fn(*args, **kw):
        if THREAD_LOCAL:
            try:
                conn = threading.local().conn
            except Exception:
                conn = sqlite3.connect(common.DB_PATH)
                threading.local().conn = conn
                atexit.register(conn.close)
        else:
            conn = sqlite3.connect(common.DB_PATH)
        c = conn.cursor()
        try:
            ret = fn(c, *args, **kw)
        except Exception, e:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            c.close()
            if not THREAD_LOCAL:
                conn.close()
        return ret
    new_fn.__name__ = fn.__name__
    new_fn.__doc__ = fn.__doc__
    new_fn.__dict__.update(fn.__dict__)
    return new_fn

DATES = ('last_modified', 'created')
SOURCE_KEYS = ('name', 'url', 'logo')

#@log_entry
@transaction
def ensure_topic_exists(cursor, title):
    topic_title = _get_topic_title(cursor, title)
    
    if topic_title:
        return topic_title
    log.debug('insert title %s' % title)
    insert_sql = 'insert into topic (title)'\
                 ' values (?);'
    # XXX 0 for type not null hack
    cursor.execute(insert_sql, (title,))
    return _get_topic_title(cursor, title)

#@log_entry
def _get_topic_title(cursor, title):
    sql = 'select title from topic'\
          ' where title=?'
    cursor.execute(sql, (title,))
    topic = cursor.fetchone()
    return topic[0] if topic else None

#@log_entry
def _ensure_source_exists(cursor, name):
    source_name = _get_source_name(cursor, name)
    if source_name:
        return source_name
    log.debug('insert source %s' % name)
    insert_sql = 'insert into source (name, url)'\
                 ' values (?, ?);'
    # XXX '' for url not null hack
    cursor.execute(insert_sql, (name, ''))
    return _get_source_name(cursor, name)

#@log_entry
def _get_source_name(cursor, name):
    sql = 'select name from source'\
          ' where name=?'
    cursor.execute(sql, (name,))
    source = cursor.fetchone()
    return source[0] if source else None

#@log_entry
@transaction
def ensure_article_exists(cursor, article, overwrite=False):
    if 'cached' not in article:
        article['cached'] = None
    if 'url_status' not in article:
        article['url_status'] = -1

    if 'id' in article:
        article_id = article['id']
    else:
        article_id = _get_article_id_by_url(cursor, article['url'])

    if article_id and not overwrite:
        return article_id
    elif not article_id:
        sql = 'insert into article (title, url, source, url_date, cached, url_status)'\
                     ' values (:title, :url, :source, :url_date, :cached, :url_status)'
    else:
        sql = 'update article set title = :title, source = :source,'\
              ' url = :url, url_date = :url_date, cached = :cached, url_status = :url_status'\
              ' where id = :id'
        article['id'] = article_id
    source_name = _ensure_source_exists(cursor, article.pop('source'))
    article['source'] = source_name
    cursor.execute(sql, article)
    article_id = _get_article_id_by_url(cursor, article['url'])
    return article_id

#@log_entry
@transaction
def update_source(cursor, name, url):
    sql = 'update source set url = ? where name = ?'
    cursor.execute(sql, (url, name))

#@log_entry
def _get_article_id_by_url(cursor, url):
    sql = 'select id from article'\
          ' where url=?'
    cursor.execute(sql, (url,))
    article_id = cursor.fetchone()
    return article_id[0] if article_id else None

#@log_entry
@transaction
def insert_or_update_t_a_rel(cursor, topic_title, article_id, brief):
    sql = 'select topic_title, article_id from topic_article_rel'\
          ' where topic_title = ? and article_id = ?'
    cursor.execute(sql, (topic_title, article_id))
    t_a_rel = cursor.fetchone()
    if t_a_rel:
        sql = 'update topic_article_rel set brief=:brief'\
              ' where topic_title=:topic_title and article_id=:article_id'
    else:
        sql = 'insert into topic_article_rel (topic_title, article_id, brief)'\
              ' values (:topic_title, :article_id, :brief)'
    cursor.execute(sql, dict(topic_title=topic_title,
                             article_id=article_id,
                             brief=brief))

@transaction
def get_topic(cursor, topic):
    cols = ('title', 'brief', 'last_modified', 'created')
    sql = 'select %s, %s, %s, %s from topic'\
          ' where title = ?' % cols
    cursor.execute(sql, (topic,))
    t = cursor.fetchone()
    if t:
        return dict(zip(cols, t))
    return None

#@log_entry
@transaction
def list_topics(cursor):
    sql = 'select title from topic'
    cursor.execute(sql)
    fetch = cursor.fetchall()
    results = [record[0] for record in fetch]
    return results

#@log_entry
@transaction
def homepage_topics(cursor):
    sql = 'select t.title, dnt.amount, dnt.last_article from topic as t'\
          ' join dn_topic dnt on t.title = dnt.title order by dnt.last_article desc'
    cursor.execute(sql)
    fetch = cursor.fetchall()
    keys = ['title', 'amount', 'last_article']
    results = [dict(zip(keys, row)) for row in fetch]
    return results

#@log_entry
@transaction
def list_articles_by_topic(cursor, topic_title, start=None, end=None, limit=0):
    start_clause = end_clause = limit_clause = ''
    if start:
        start_clause = ' AND a.url_date >= \'%s\'' % start.strftime(DATE_FORMAT)
    if end:
        end_clause = ' AND a.url_date <= \'%s\'' % end.strftime(DATE_FORMAT)
    if limit > 0:
        limit_clause = ' limit %s' % limit
    cols = ['id', 'title', 'url', 'url_date', 'url_status', 'created',
            'source', 'source_url', 'brief']
    sql = '''
          select a.id, a.title, a.url, a.url_date, a.url_status, a.created,
                 a.source, s.url, t_a_rel.brief
          from article as a 
                 inner join topic_article_rel as t_a_rel on a.id = t_a_rel.article_id
                 inner join source s on a.source = s.name
          where
                t_a_rel.topic_title = ?'''\
          + start_clause + end_clause + \
          'order by a.created desc' \
          + limit_clause
    cursor.execute(sql, (topic_title,))
    fetch = cursor.fetchall()
    return [dict(zip(cols, record)) for record in fetch]

#@log_entry
@transaction
def list_articles_by_topics(cursor, topics, limit=0):
    if not topics:
        return []
    limit_clause = ''
    if limit > 0:
        limit_clause = ' LIMIT %s' % limit
    cols = ['id', 'title', 'url', 'url_date', 'url_status', 'created',
            'source', 'source_url', 'brief']
    sql = '''
          SELECT a.id, a.title, a.url, a.url_date, a.url_status, a.created,
                 a.source, s.url, t_a_rel.brief
          FROM article AS a 
                 INNER JOIN topic_article_rel AS t_a_rel ON a.id = t_a_rel.article_id
                 INNER JOIN source s ON a.source = s.name,
                 (
                    SELECT t_a_r.article_id AS aid, COUNT(1) AS amount
                    FROM topic_article_rel As t_a_r
                    WHERE t_a_r.topic_title IN (%s)
                    GROUP BY aid
                 ) AS aid_table 
          WHERE
                aid_table.aid = a.id
                AND aid_table.amount = ?
                AND t_a_rel.topic_title = ?
          ORDER BY a.url_date DESC
          ''' + limit_clause
    sql = sql % ','.join(['?']*len(topics))
    cursor.execute(sql, tuple(topics) + (len(topics), topics[0]))
    fetch = cursor.fetchall()
    return [dict(zip(cols, record)) for record in fetch]
     
#@log_entry
@transaction
def list_articles_by_source(cursor, source, start=None, end=None, limit=0, addition_cols=None):
    start_clause = end_clause = limit_clause = ''
    if start:
        start_clause = ' AND a.url_date >= \'%s\'' % start.strftime(DATE_FORMAT)
    if end:
        end_clause = ' AND a.url_date <= \'%s\'' % end.strftime(DATE_FORMAT)
    if limit > 0:
        limit_clause = ' limit %s' % limit
    cols_clause = ''
    if addition_cols is None:
        addition_cols = []
    if addition_cols:
        cols_clause = reduce(lambda x, y: x + y, (', a.%s' % col for col in addition_cols))
    cols = ['id', 'title', 'url', 'url_date', 'url_status', 'created',
            'source', 'source_url'] + addition_cols
    sql = '''
          select a.id, a.title, a.url, a.url_date, a.url_status, a.created,
                 a.source, s.url%s
          from article as a 
                 inner join source s on a.source = s.name
          where
                a.source = ?
                %s %s
          order by a.created desc %s
          '''
    sql = sql % (cols_clause, start_clause, end_clause, limit_clause)
    cursor.execute(sql, (source,))
    fetch = cursor.fetchall()
    return [dict(zip(cols, record)) for record in fetch]


#@log_entry
@transaction
def get_article(cursor, aid):
    cols = ('id', 'title', 'url', 'source', 'url_date', 'url_status', 'cached')
    sql = 'select %s, %s, %s, %s, %s, %s, %s from article where id = ?' % cols 
    cursor.execute(sql, (aid,))
    article = cursor.fetchone()
    return dict(zip(cols, article)) if article else None

@transaction
def get_article_by_url(cursor, url):
    cols = ('id', 'title', 'url', 'source', 'url_date', 'url_status', 'cached')
    sql = 'select %s, %s, %s, %s, %s, %s, %s from article where url = ?' % cols 
    cursor.execute(sql, (url,))
    article = cursor.fetchone()
    return dict(zip(cols, article)) if article else None

#@log_entry
@transaction
def get_source(cursor, name):
    cols = ['name', 'url', 'logo']
    sql = 'select name, url, logo from source'\
          ' where name=?'
    cursor.execute(sql, (name,))
    source = cursor.fetchone()
    return dict(zip(cols, source)) if source else None

@transaction
def list_sources(cursor):
    #XXX mail parser produces garbage
    cols = ('name', 'url')
    sql = 'select %s, %s from'\
          ' (select name, s.url, count(a.id) as amount'\
          '  from source s inner join article a on s.name = a.source'\
          '  group by name)'\
          ' where amount > 1' % cols
    cursor.execute(sql)
    fetch = cursor.fetchall()
    return [dict(zip(cols, record)) for record in fetch]

#@log_entry
@transaction
def get_topics_by_article(cursor, aid):
    cols = ('topic_title', 'brief')
    sql = 'select %s, %s from topic_article_rel where article_id = ?' % cols
    cursor.execute(sql, (aid,))
    fetch = cursor.fetchall()
    return [dict(zip(cols, row)) for row in fetch]

#@log_entry
@transaction
def get_related_topics(cursor, topics, start=None, end=None, limit=0):
    start_clause = end_clause = limit_clause = ''
    if start:
        start_clause = ' AND a.url_date >= \'%s\'' % start.strftime(DATE_FORMAT)
    if end:
        end_clause = ' AND a.url_date <= \'%s\'' % end.strftime(DATE_FORMAT)
    if limit > 0:
        limit_clause = ' limit %s' % limit
    if len(topics) > 1:
        sql = '''
               SELECT t_a_r2.topic_title, COUNT(DISTINCT t_a_r1.article_id) as count
               FROM 
                topic_article_rel AS t_a_r1 
               INNER JOIN article AS a ON
                   t_a_r1.article_id = a.id
               INNER JOIN topic_article_rel AS t_a_r2 ON
                   t_a_r1.article_id = t_a_r2.article_id,
               (
                   SELECT t_a_r.article_id AS aid, COUNT(1) AS amount
                   FROM topic_article_rel As t_a_r
                   WHERE t_a_r.topic_title IN (%s)
                   GROUP BY aid
               ) AS aid_table 
               WHERE 
                   aid_table.amount = ?
                   AND t_a_r1.article_id = aid_table.aid
                   AND t_a_r1.topic_title IN (%s)
                   AND t_a_r2.topic_title NOT IN (%s)
             '''\
             + start_clause + end_clause + \
             '''
               GROUP BY t_a_r2.topic_title
               ORDER BY count DESC
             '''\
             + limit_clause
        sql = sql % ((','.join(['?'] * len(topics)),) * 3)
        topics_tuple = tuple(topics)
        cursor.execute(sql, topics_tuple + (len(topics_tuple),) + topics_tuple + topics_tuple)
    else:
        topic = topics[0]
        sql = '''
              SELECT t_a_r2.topic_title, COUNT(1) as count
               FROM 
               topic_article_rel AS t_a_r1 
               INNER JOIN topic_article_rel AS t_a_r2 ON
                   t_a_r1.article_id = t_a_r2.article_id
               INNER JOIN article AS a ON
                   t_a_r1.article_id = a.id
               WHERE 
                   t_a_r1.topic_title = ?
                   AND t_a_r2.topic_title != ?
              '''\
              + start_clause + end_clause + \
              '''
               GROUP BY t_a_r2.topic_title
               ORDER BY count DESC
              '''\
              + limit_clause
        cursor.execute(sql, (topic, topic))
    cols = ['title', 'amount']
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

#@log_entry
@transaction
def get_articles_amount_by_topics(cursor, topics, start=None, end=None, limit=0):
    start_clause = end_clause = limit_clause = ''
    if start:
        start_clause = ' AND a.url_date >= \'%s\'' % start.strftime(DATE_FORMAT)
    if end:
        end_clause = ' AND a.url_date <= \'%s\'' % end.strftime(DATE_FORMAT)
    if limit > 0:
        limit_clause = ' limit %s' % limit
    if len(topics) > 1:
        sql = '''
               SELECT COUNT(DISTINCT t_a_r1.article_id) as count
               FROM 
                topic_article_rel AS t_a_r1 
               INNER JOIN article AS a ON
                   t_a_r1.article_id = a.id
               INNER JOIN topic_article_rel AS t_a_r2 ON
                   t_a_r1.article_id = t_a_r2.article_id,
               (
                   SELECT t_a_r.article_id AS aid, COUNT(1) AS amount
                   FROM topic_article_rel As t_a_r
                   WHERE t_a_r.topic_title IN (%s)
                   GROUP BY aid
               ) AS aid_table 
               WHERE 
                   aid_table.amount = ?
                   AND t_a_r1.article_id = aid_table.aid
                   AND t_a_r1.topic_title = ?
             '''\
             + start_clause + end_clause + limit_clause
        sql = sql % (','.join(['?'] * len(topics)),)
        topics_tuple = tuple(topics)
        cursor.execute(sql, topics_tuple + (len(topics_tuple), topics_tuple[0]))
    else:
        topic = topics[0]
        sql = '''
              SELECT COUNT(1) as count
               FROM 
               topic_article_rel AS t_a_r 
               INNER JOIN article AS a ON
                   t_a_r.article_id = a.id
               WHERE 
                   t_a_r.topic_title = ?
              '''\
              + start_clause + end_clause + limit_clause
        cursor.execute(sql, (topic,))
    return cursor.fetchone()[0]

#@log_entry
@transaction
def get_new_artitcles(cursor, limit=10):
   sql = '''
        SELECT id, title, url
        FROM article
        ORDER BY url_date DESC
        LIMIT ?
   '''
   cursor.execute(sql, (limit,)) 
   cols = ['id', 'title', 'url']
   return [dict(zip(cols, item)) for item in cursor.fetchall()] 
