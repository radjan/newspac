import liberty_parse
import rss_base

class Handler(rss_base.RssBaseHandler):
    def fecth_text(self, link):
        return liberty_parse.fetch_text(link)
