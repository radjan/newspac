# -*- coding: utf-8 -*-
import sqlite3
import atexit
import os
DB_DIR = os.path.dirname(__file__)

import traceback

import common
log = common.get_logger()

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

conn = sqlite3.connect(DB_DIR + '/newspacks.db')
atexit.register(conn.close)
def transaction(fn):
    def new_fn(*args, **kw):
        c = conn.cursor()
        try:
            ret = fn(c, *args, **kw)
        except Exception, e:
            conn.rollback()
            raise
        else:
            conn.commit()
        return ret
    new_fn.__name__ = fn.__name__
    new_fn.__doc__ = fn.__doc__
    new_fn.__dict__.update(fn.__dict__)
    return new_fn

DATES = ('last_modified', 'created')
SOURCE_KEYS = ('name', 'url', 'logo')

@log_entry
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

@log_entry
def _get_topic_title(cursor, title):
    sql = 'select title from topic'\
          ' where title=?'
    cursor.execute(sql, (title,))
    topic = cursor.fetchone()
    return topic[0] if topic else None

@log_entry
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

@log_entry
def _get_source_name(cursor, name):
    sql = 'select name from source'\
          ' where name=?'
    cursor.execute(sql, (name,))
    source = cursor.fetchone()
    return source[0] if source else None

@log_entry
@transaction
def ensure_article_exists(cursor, article):
    article_id = _get_article_id_by_url(cursor, article['url'])
    source_name = _ensure_source_exists(cursor, article.pop('source'))
    log.debug(source_name)
    article['source'] = source_name
    if not article_id:
        sql = 'insert into article (title, url, source, url_date)'\
                     ' values (:title, :url, :source, :url_date)'
    else:
        sql = 'update article set title = :title, source = :source,'\
              ' url_date = :url_date where id = :id'
        article['id'] = article_id
    cursor.execute(sql, article)
    article_id = _get_article_id_by_url(cursor, article['url'])
    return article_id

@log_entry
@transaction
def update_source(cursor, name, url):
    sql = 'update source set url = ? where name = ?'
    cursor.execute(sql, (url, name))

@log_entry
def _get_article_id_by_url(cursor, url):
    sql = 'select id from article'\
          ' where url=?'
    cursor.execute(sql, (url,))
    article_id = cursor.fetchone()
    return article_id[0] if article_id else None

@log_entry
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
@log_entry
@transaction
def list_topics(cursor):
    sql = 'select title from topic'
    cursor.execute(sql)
    fetch = cursor.fetchall()
    results = [record[0] for record in fetch]
    return results

@log_entry
@transaction
def list_articles_by_topic(cursor, topic_title):
    cols = ['id', 'title', 'url', 'url_date', 'url_status', 'created',
            'source', 'source_url', 'brief']
    sql = '''
          select a.id, a.title, a.url, a.url_date, a.url_status, a.created,
                 a.source, s.url, t_a_rel.brief
          from article as a 
                 inner join topic_article_rel as t_a_rel on a.id = t_a_rel.article_id
                 inner join source s on a.source = s.name
          where
                t_a_rel.topic_title = ?
          order by a.created desc
          '''
    cursor.execute(sql, (topic_title,))
    fetch = cursor.fetchall()
    return [dict(zip(cols, record)) for record in fetch]
