#/usr/bin/env python
#coding=utf8

import pycurl,json

try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode

class Storage:
    def __init__(self):
        self.contents = ''
 
    def store(self, buf):
        self.contents = "%s%s" % (self.contents, buf)
    
    def __str__(self):
        return self.contents

def submit(url,form):
    print url
    print form
    postfields = urlencode(form)
    retrieved_body = Storage()
    retrieved_headers = Storage()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.POSTFIELDS, postfields)
    c.setopt(c.WRITEFUNCTION, retrieved_body.store)
    c.setopt(c.HEADERFUNCTION, retrieved_headers.store)
    c.perform()
    c.close()
    rtn = '%s' % retrieved_body
    print rtn
    try:
        return json.loads(rtn)
    except:
        return rtn
    