#! /bin/env python
# -*- coding: utf-8 -*-
import sys
idx = int(sys.argv[1]) if len(sys.argv) > 1 else None
import traceback

from imapclient import imapclient
from imapclient.imapclient import IMAPClient
import email
import base64
#from HTMLParser import HTMLParser
#from htmlentitydefs import name2codepoint
from datetime import datetime

import database as db
import common

log = common.get_logger()

HOST = 'imap.gmail.com'
USERNAME = 'news.packs@gmail.com'
PASSWORD = 'news0987!'
ssl = True

TOPIC_TITLE = 'title'
RECEIVE_TIME = 'receive_time'
DATE_FORMAT = '%a, %d %b %Y %H:%M:%S +0000'

MAX_BATCH_AMOUNT = 300

def main():
    server = IMAPClient(HOST, use_uid=True, ssl=ssl)
    server.login(USERNAME, PASSWORD)

    select_info = server.select_folder('INBOX')
    log.info('%d messages in INBOX' % select_info['EXISTS'])

    messages = server.search(['NOT DELETED'])
    #messages = server.search(['UNSEEN'])
    log.info("%d messages that aren't deleted" % len(messages))
    if idx is not None:
        messages = [messages[idx],]
    elif len(messages) > MAX_BATCH_AMOUNT:
        messages = messages[0-MAX_BATCH_AMOUNT:]

    done_msgs = []
    for msg_id in messages:
        try:
            process_email(server, msg_id)
            done_msgs.append(msg_id)
        except Exception:
            if idx is None:
                with open('email_backup/error/id_%s' % msg_id, 'w') as f:
                    traceback.print_exc(file=f)
            else:
                raise

    log.info('processed %s mails' % len(done_msgs))
    if idx is None and done_msgs:
        #mark as deleted
        server.set_flags(done_msgs, imapclient.DELETED)
        #tell server to delete deleted email
        server.expunge()
        log.info('delete %s mails from server' % len(done_msgs))

def process_email(server, msg_id):
    #print
    #log.debug("Messages:")
    #datalist = ['FLAGS', 'RFC822', 'BODY']
    datalist = ['RFC822']
    response = server.fetch(msg_id, datalist)

    for msgid, data in response.iteritems():
        email_info, plain = parse_message(msgid, data)
        if not email_info:
            continue
        topic_title, result = parse_plain(plain)
        #for data in result:
        #    for k, v in data.items():
        #        log.debug(k, v)
        with open('email_backup/%s_%s.txt' % (msgid, topic_title), 'w') as f:
            f.write(plain.encode('utf8'))
        log.info('parsing topic: %s' % topic_title)
        topic_title = db.ensure_topic_exists(topic_title)
        for data in result:
            article = dict(url=data['url'],
                           title=data['title'],
                           source=data['source'],
                           url_date=email_info[RECEIVE_TIME])
            article_id = db.ensure_article_exists(article)
            brief = data['brief']
            db.insert_or_update_t_a_rel(topic_title, article_id, brief)

def get_email_info(part):
    items = dict(part.items())
    return items['From'], items['Date']

def is_google_alert(sender):
    return sender.find('googlealerts-noreply@google.com') >= 0

def parse_message(msgid, data):
    plain = sender = sent_time = ''
    #print
    #log.debug('   ID %d: FLAGS=%s' % (msgid, data['FLAGS']))
    msg =  email.message_from_string(data['RFC822'])
    
    #log.debug(dir(msg))
    #log.debug(msg.is_multipart())
    #log.debug(msg.get_content_subtype())
    #log.debug('-' * 60)
    #log.debug(base64.b64decode(msg.get_payload().replace('\r\n\r\n', '||||').replace('\r\n', '||||').replace(',||||','||||')))

    from_google_alert = True
    for part in msg.walk():
        if not from_google_alert:
            break
        content_type = part.get_content_type()
        #log.debug('-'*60)
        #log.debug(content_type)
        #log.debug(dict(part.get_params()))
        #log.debug(dict(part.items()))
        if msg.is_multipart() and content_type == 'multipart/alternative':
            sender, sent_time = get_email_info(part)
            from_google_alert = is_google_alert(sender)
            if not from_google_alert:
                continue
        if content_type == 'text/plain':
            if not msg.is_multipart():
                sender, sent_time = get_email_info(part)
                from_google_alert = is_google_alert(sender)
                if not from_google_alert:
                    continue
            params =  dict(part.get_params())
            charset = params['charset']

            items = dict(part.items())
            transfer_encoding = items['Content-Transfer-Encoding']

            payload = part.get_payload()
            plain = unicode(base64.b64decode(payload).decode(charset))
        elif content_type == 'text/html':
            #html = base64.b64decode(payload)
            pass

    if from_google_alert:
        email_info = {RECEIVE_TIME: datetime.strptime(sent_time, DATE_FORMAT)}
        return email_info, plain
    return None, None

def _decode_str(line_str, charset):
    try:
        return unicode(line_str.decode(charset))
    except Exception, e:
        for c in CHAR_SETS:
            try:
                return unicode(line_str.decode(c))
            except:
                pass
        raise e

def parse_plain(plain):
    l = plain.splitlines()
    title = l[0]
    title = title[title.index('[')+1:title.rindex(']')]    
    del l[0]

    result = []
    obj = None
    skip = False
    more_title = False
    for line in l:
        #log.debug(len(line.encode('utf8')), line)
        if skip:
            skip = False
            continue
        if not line:
            if not obj:
                continue
            else:
                result.append(obj)
                obj = None
        else:
            if not obj:
                obj = {'brief':''}
            if 'title' not in obj:
                obj['title'] = line
                more_title = (len(line.encode('utf8')) >= 111)
            elif more_title:
                obj['title'] += line
                more_title = (len(line.encode('utf8')) >= 111)
            elif 'source' not in obj:
                obj['source'] = line
            elif line.startswith(u'查看此主題下的所有報導'):
                skip = True
            elif line.startswith('<http'):
                if line.startswith('<http://www.google.com/url?'):
                    start = line.index('q=') + 2
                    end = line.index('&', start)
                else:
                    start = 1
                    end = -1
                obj['url'] = line[start:end]
            #elif '\xe5\xbf\xab\xe8\xa8\x8a\xe6\x8f\x90\xe4\xbe\x9b\xe3\x80\x82' in line:
            #    break
            elif line.startswith('http'):
                break
            else:
                obj['brief'] += line
    return title, result

if __name__ == '__main__':
    main()
