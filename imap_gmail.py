#! /bin/env python
# -*- coding: utf-8 -*-
import sys
idx = int(sys.argv[1]) if len(sys.argv) > 1 else None
#print sys.version_info
import pprint
import traceback

from imapclient import imapclient
from imapclient.imapclient import IMAPClient
import email
import base64
#from HTMLParser import HTMLParser
#from htmlentitydefs import name2codepoint
from datetime import datetime

import database as db

HOST = 'imap.gmail.com'
USERNAME = 'news.packs@gmail.com'
PASSWORD = 'news0987!'
ssl = True

TOPIC_TITLE = 'title'
RECEIVE_TIME = 'receive_time'
DATE_FORMAT = '%a, %d %b %Y %H:%M:%S +0000'

def main():
    server = IMAPClient(HOST, use_uid=True, ssl=ssl)
    server.login(USERNAME, PASSWORD)

    select_info = server.select_folder('INBOX')
    print '%d messages in INBOX' % select_info['EXISTS']

    messages = server.search(['NOT DELETED'])
    #messages = server.search(['UNSEEN'])
    print "%d messages that aren't deleted" % len(messages)
    if idx is not None:
        messages = [messages[idx],]
    for msg_id in messages:
        try:
            process_email(server, msg_id)
        except Exception:
            if idx is None:
                with open('email_backup/error/id_%s' % msg_id, 'w') as f:
                    traceback.print_exc(file=f)
            else:
                raise

def process_email(server, msg_id):
    #print
    #print "Messages:"
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
        #        print k, v
        with open('email_backup/%s_%s.txt' % (msgid, topic_title), 'w') as f:
            f.write(plain.encode('utf8'))
        #mark as deleted
        #server.set_flags(msgid, imapclient.DELETED)
        print topic_title
        topic_title = db.ensure_topic_exists(topic_title)
        for data in result:
            article = dict(url=data['url'],
                           title=data['title'],
                           source=data['source'],
                           url_date=email_info[RECEIVE_TIME])
            article_id = db.ensure_article_exists(article)
            brief = data['brief']
            db.insert_or_update_t_a_rel(topic_title, article_id, brief)

    #tell server to delete deleted email
    #server.expunge()

def get_email_info(part):
    items = dict(part.items())
    return items['From'], items['Date']

def is_google_alert(sender):
    return sender.find('googlealerts-noreply@google.com') >= 0

def parse_message(msgid, data):
    plain = sender = sent_time = ''
    #print
    #print '   ID %d: FLAGS=%s' % (msgid, data['FLAGS'])
    msg =  email.message_from_string(data['RFC822'])
    
    #print dir(msg)
    #print msg.is_multipart()
    #print msg.get_content_subtype()
    #print '-' * 60
    #print base64.b64decode(msg.get_payload().replace('\r\n\r\n', '||||').replace('\r\n', '||||').replace(',||||','||||'))A

    from_google_alert = True
    for part in msg.walk():
        if not from_google_alert:
            break
        content_type = part.get_content_type()
        #print '-'*60
        #print content_type
        #pprint.pprint(dict(part.get_params()))
        #pprint.pprint(dict(part.items()))
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
        #print len(line.encode('utf8')), line
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
