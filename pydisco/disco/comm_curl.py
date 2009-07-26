import cStringIO, struct, time, sys, os
from pycurl import *
from disco.comm_httplib import CommException

MAX_BUF = 1024**2
MAX_RETRIES = 10
dl_handle = None

def check_code(c, expected):
        code = c.getinfo(HTTP_CODE)
        if code != expected:
                raise CommException(code)

def download(url, data = None, redir = False):
        global dl_handle
        if not dl_handle:
                dl_handle = Curl()
                dl_handle.setopt(FOLLOWLOCATION, 1)
        retry = 0
        while True:
                dl_handle.setopt(URL, url)
                outbuf = cStringIO.StringIO()
                dl_handle.setopt(WRITEFUNCTION, outbuf.write)
                if data != None:
                        inbuf = cStringIO.StringIO(data)
                        dl_handle.setopt(READFUNCTION, inbuf.read)
                        dl_handle.setopt(POSTFIELDSIZE, len(data))
                        dl_handle.setopt(HTTPHEADER, ["Expect:"])
                        dl_handle.setopt(POST, 1)
                try:
                        dl_handle.perform()
                        break
                except:
                        if retry == MAX_RETRIES:
                                raise CommException("Downloading %s failed "\
                                        "after %d attempts: %s" %\
                                        (url, MAX_RETRIES, dl_handle.errstr()))
                        retry += 1

        dl_handle.setopt(POST, 0)
        check_code(dl_handle, 200)
        return outbuf.getvalue()

class CurlConn:
        def __init__(self, url, handle = None, expect = 200):
                if handle:
                        self.handle = handle
                else:
                        self.handle = Curl()

                for i in range(MAX_RETRIES):
                        self.init_handle(url)
                        self.perform()
                        x, succ, fail = self.multi.info_read(1) 
                        if not fail:
                                break
                        self.handle = Curl()
                        time.sleep(1.0)
                else:
                        raise CommException(
                                "Couldn't connect after %d attempts: %s" %\
                                        (MAX_RETRIES, fail[0][2]))
                
                # make sure all headers are read
                while self.cont and not self.body:
                        self.perform()

                code = self.handle.getinfo(HTTP_CODE)
                if code == 0:
                        raise CommException("Couldn't receive http response")
                check_code(self.handle, expect)
                
        def init_handle(self, url):
                self.handle.setopt(URL, url)
                self.handle.setopt(WRITEFUNCTION, self.write)
                self.handle.setopt(HEADERFUNCTION, self.head)
                self.multi = CurlMulti()
                self.multi.add_handle(self.handle)
                self.buf = ""
                self.cont = 1
                self.length = None
                self.body = False

        def perform(self):
                if not self.cont:
                        return
                r = -1
                while r == -1:
                        r = self.multi.select(100.0)
                ret = E_CALL_MULTI_PERFORM
                while ret == E_CALL_MULTI_PERFORM:
                        ret, num_handles = self.multi.perform()
                        self.cont = num_handles
        
        def head(self, buf):
                buf = buf.lower()
                if buf.startswith("content-length:"):
                        self.length = int(buf.split(":")[1])
                elif buf.startswith("location:"):
                        self.location = buf.split(":", 1)[1].strip()

        def getheader(self, x):
                if x == "location":
                        return self.location

        def write(self, buf):
                self.body = True
                self.buf += buf

        def read(self, bytes):
                while self.cont and not self.buf:
                        self.perform()
                r = self.buf[:bytes]
                self.buf = self.buf[bytes:]
                return r

        def disco_stats(self):
                pass

def open_remote(url, expect = 200):
        c = Curl()
        conn = CurlConn(url, handle = c, expect = expect)
        return conn.length, conn



                



                
                

        
