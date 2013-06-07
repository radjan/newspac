newspac
=======

RESTful api
======= 

list all topics
```
GET api/topics 
["topic1", "topic2", ...]
```

get a topic and related articles
```
GET api/topic/{topic_name}
params:
 limit: an integer between 0-1000
 start: specify the start date of the articles, format YYYY-MM-DD
 end: specify the end date of the articles, YYYY-MM-DD
{"last_modified": "2012-04-08 15:22:55",
 "created": "2012-04-08 15:22:55",
 "brief": null, #no use for now
 "title": "topic_name"
 "articles": [{"url_date": "2013-06-07 15:01:52+00:00",
               "created": "2013-06-07 16:21:49",
               "url": "http://news.chinatimes.com/politics/130502/132013060700004.html",
               "title": "article title",
               "brief": "balabala...",
               "source_url": "http://news.chinatimes.com",
               "source": "中時電子報",
               "url_status": null, #no use for now
               "id": 162791
              },
              ...
             ]
 }
```

get all sources
```
GET api/sources
[{"url": "http://xxoo.com", "name": "xxoo" }, ...]
```

get a source and related articles
```
GET api/source/{source_name}
params:
 limit: an integer between 0-1000
 start: specify the start date of the articles, format YYYY-MM-DD
 end: specify the end date of the articles, YYYY-MM-DD
{"url": "http://www.google.com",
 "logo": null, #no use for now
 "name": "AFP",
 "articles": [{"url_date": "2013-05-29 02:35:09+00:00",
               "created": "2013-05-29 04:16:26",
               "url": "http://bala.com/bala.html"
               "title": "balabala"
               "source_url": "http://www.google.com",
               "source": "AFP",
               "url_status": null,
               "id": 156594
              },
              ...
             ] 
 }
```

get an article
```
GET api/article/{article_id}
{"url_date": "2013-05-29 02:35:09+00:00",
 "title": "美議員馬侃訪敘會反對派領袖",
  "url": "http://www.google.com/hostednews/afp/article/ALeqM5hRc0ca5BxAp3lEl12e8YGXUUteng?docId=int0008.130528120502",
   "topics": [{"topic_title": "議員",
               "brief": "balabalabala",
              },
              ...
             ]  
   "source": {"url": "http://www.google.com",
              "logo": null,
              "name": "AFP"},
   "url_status": null,
   "cached": "cached_text_if_any", 
    "id": {article_id}}
```

License
=======
The Simplified BSD License

Copyright (c) 2012, Rad Jan
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met: 

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer. 
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies, 
either expressed or implied, of the FreeBSD Project.
