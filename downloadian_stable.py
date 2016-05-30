''' Downloadian 1.0 '''
import socket
import base64
import os
#import time

# THIS CLASS IS FOR PROGRESSBAR
class MonitoringProgress():
    def __init__(self):
        self.maxlen = 0
        #self.lastspeed = 0

    def update(self, downloaded, content_length):
        if content_length == -1:
            monitoring = '[unknown] ' + str(downloaded) + ' bytes'
        else:
            monitoring = '['
            progress = (downloaded/content_length)*100
            for i in range(int(progress/2)): monitoring += '='
            for i in range(50-int(progress/2)): monitoring += ' '
            monitoring += '] ' + str(round(progress,2)) + '%'
            monitoring += ' ' + str(downloaded) + '/' + str(content_length) + ' bytes'
        '''if speed == -1: speed = self.lastspeed
        monitoring += ' ('
        if speed < 1024:
            monitoring += str(round(speed)) + 'bytes/s'
        elif speed < 1024*1024:
            monitoring += str(round(speed/1024)) + 'KB/s'
        else:
            monitoring += str(round(speed/(1024*1024),1)) + 'MB/s'
        monitoring += ')'
        self.lastspeed = speed'''

        curlen = len(monitoring)
        if curlen > self.maxlen: self.maxlen = curlen
        else:
            for i in range(self.maxlen-curlen): monitoring += ' '
        print(monitoring, end='\r')

        if content_length != -1 and progress >= 100: self.complete('')

    def complete(self, message):
        if message == '': print()
        else: print('\n'+message)

# THIS CLASS IS FOR BUFFERING DATA IN RAM
class BufToDisk:
    def __init__(self, size, path):
        self.buffer = b''
        self.maxsize = size
        self.file = open(path, 'ab')

    def write(self, byte):
        if len(self.buffer) >= self.maxsize: self.writeOnDisk()
        self.buffer += byte

    def writeOnDisk(self):
        if len(self.buffer) != 0:
            self.file.write(self.buffer)
            self.buffer = b''

    def close(self, option):
        if option: self.writeOnDisk()
        self.file.close()

if not os.path.exists('DOWNLOADIAN_DOWNLOADS'):
    os.makedirs('DOWNLOADIAN_DOWNLOADS')

username, password = '', ''
isProxy = 0

def download(url):
    _indexAfterHTTP = url.index('//')+2
    _afterHTTP = url[url.index('//')+2:]
    domain, filename = '', 'DOWNLOADIAN_DOWNLOADS/'
    try:
        domain = url[_indexAfterHTTP:_indexAfterHTTP+_afterHTTP.index('/')]
        point = url.rindex('.')
        if point > _indexAfterHTTP+_afterHTTP.index('/'):
            filename += url[url.rindex('/')+1:]
        else:
            filename += domain + '_file.html'
    except:
        domain = url[_indexAfterHTTP:]
        filename += domain + '_file.html'

    asset = socket.socket()
    asset.connect((domain, 80))

    request = 'GET ' + url + ' HTTP/1.1\r\nHost:' + domain + '\r\n'
    if isProxy:
        request += 'Proxy-authorization: Basic ' + base64.encodestring((username+':'+password).encode('utf-8')).decode('utf-8') + '\r\n'
    request += '\r\n'
    asset.send(request.encode('utf-8'))

    r = b''
    while not('\r\n\r\n' in r.decode('utf-8')):
        r += asset.recv(1)
    _header = r.decode('utf-8')
    print(_header[:-4])

    endcondition = 0
    try:
        _indexAfterContentLength = _header.index('Content-Length')+16
        _afterContentLength = _header[r.decode('utf-8').index('Content-Length')+16:]
        content_length = int(_header[_indexAfterContentLength:_indexAfterContentLength+_afterContentLength.index('\r\n')])
    except:
        endcondition = 1

    maxtraffic = 10*1024*1024
    downloaded = 0
    progress = 0.0
    buffer = BufToDisk(100*1024*1024, filename)

    r = b''
    def c0(): return downloaded < content_length
    def c1(): return not(b'\r\n\r\n' in r)
    conditions = (c0, c1)

    #stime = etime = time.time()
    #delta = 0

    if endcondition == 1: content_length = -1
    monitoring = MonitoringProgress()
    while conditions[endcondition]():
        r = b''
        try:
            while not(r):
                asset.settimeout(10)
                r = asset.recv(maxtraffic)
                #etime = time.time()
        except:
            print('\nUNEXPECTED NETWORK ERROR. DOWNLOADED DATA SAVED.')
            break
        buffer.write(r)
        downloaded += len(r)
        #delta += len(r)
        #if etime - stime > 2:
            #monitoring.update(downloaded, content_length, delta/(etime-stime))
            #stime = time.time()
            #delta = 0
        #else:
        monitoring.update(downloaded, content_length)

    if endcondition == 1: print()
    buffer.close(1)

    asset.shutdown(1)
    asset.close()


print('Downloadian 1.0')
print('RTFM: just COPY-PASTE URL and press ENTER or type close/exit')
while 1:
    url = input('> ')
    if url in ('close','exit'): break
    if url == 'proxy': isProxy = 1
    else: download(url)
