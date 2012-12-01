from datetime import datetime
import appledaily_parse
import rss_base
# Sat, 01 Dec 2012 07:00:00 +0800
process_date = lambda x: x[5:-6]
DATE_FORMAT =  '%d %b %Y %H:%M:%S'

class Handler(rss_base.RssBaseHandler):
    def fetch_text(self, link):
        return appledaily_parse.fetch_text(link)

    def _str_to_ts(self, pubdate_str):
        ts = datetime.strptime(process_date(pubdate_str), DATE_FORMAT)
        ts = ts.replace(tzinfo=rss_base.UTC8())
        return ts.astimezone(rss_base.UTC())
