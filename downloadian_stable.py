''' Downloadian 1.0 '''
import socket
import base64
import os
import time

# KB is 1000 Bytes and so on! (according to standards, KiB is 1024 Bytes and so on)
def representWeight(ln,affix):
    if ln < 1000:
        return str(ln) + 'bytes' + affix
    elif ln < 1000*1000:
        return str(round(ln/1000)) + 'KB' + affix
    else:
        return str(round(ln/(1000*1000),1)) + 'MB' + affix

def representTime(time):
    if time < 60:
        return str(time) + ' s'
    elif time < 60*60:
        return str(round(time/(60))) + ' mins'
    else:
        return str(round(time/(60*60),1)) + ' hours'

# THIS CLASS IS FOR PROGRESSBAR
class MonitoringProgress():
    def __init__(self):
        self.maxlen = 0

    def update(self, downloaded, content_length, speed):
        if content_length == -1:
            monitoring = '[unknown] ' + representWeight(downloaded,'')
        else:
            monitoring = '['
            progress = (downloaded/content_length)*100
            for i in range(int(progress/2)): monitoring += '='
            for i in range(50-int(progress/2)): monitoring += ' '
            monitoring += '] ' + str(round(progress,2)) + '%'
            monitoring += ' ' + representWeight(downloaded,'') + '/' + representWeight(content_length,'')
        monitoring += ' (' + representWeight(speed,'/s') + ')'
        if content_length != -1:
            monitoring += ' ~' + representTime(round((content_length-downloaded)/speed))

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
controlVars = {'proxy':['PROXY AUTHORIZATION',0], 'headers':['HEADERS DISPLAYING',0]}


def download(url):
    _indexAfterHTTP = url.index('//')+2
    _afterHTTP = url[_indexAfterHTTP:]
    domain, filename = '', 'DOWNLOADIAN_DOWNLOADS/'
    ext = ''
    try:
        domain = url[_indexAfterHTTP:_indexAfterHTTP+_afterHTTP.index('/')]
        point = url.rindex('.')
        namext = ''
        if point > _indexAfterHTTP+_afterHTTP.index('/'):
            try:
                qmark = url.rindex('?')
                namext = url[url.rindex('/')+1:qmark]
            except:
                namext = url[url.rindex('/')+1:]
            name = ''
            name, ext = namext[:namext.rindex('.')], namext[namext.rindex('.'):]
            filename += name
        else:
            filename += domain
            ext = '.html'
    except:
        domain = url[_indexAfterHTTP:]
        filename += domain
        ext = '.html'

    if os.path.exists(filename+ext):
        i = 1
        while os.path.exists(filename+'(copy '+str(i)+')'+ext): i += 1
        filename += '(copy '+str(i)+')'
    filename += ext

    asset = socket.socket()
    asset.connect((domain, 80))

    request = 'GET ' + url + ' HTTP/1.1\r\nHost:' + domain + '\r\n'
    if controlVars['proxy']:
        request += 'Proxy-authorization: Basic ' + base64.encodestring((username+':'+password).encode('utf-8')).decode('utf-8') + '\r\n'
    request += '\r\n'
    asset.send(request.encode('utf-8'))

    r = b''
    while not('\r\n\r\n' in r.decode('utf-8')):
        r += asset.recv(1)
    _header = r.decode('utf-8')
    if _header[:_header.index('\n')].split(' ')[1] == '200' and not(controlVars['headers'][1]):
        print(_header[:_header.index('\n')])
    else:
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
    buffer = BufToDisk(5*1024*1024, filename)

    r = b''
    def c0(): return downloaded < content_length
    def c1(): return not(b'\r\n\r\n' in r)
    conditions = (c0, c1)


    if endcondition == 1: content_length = -1
    monitoring = MonitoringProgress()
    while conditions[endcondition]():
        r = b''
        try:
            time.sleep(1)
            while not(r):
                asset.settimeout(10)
                r = asset.recv(maxtraffic)
        except:
            print('\n#UNEXPECTED NETWORK ERROR. DOWNLOADED DATA SAVED.')
            break
        buffer.write(r)
        downloaded += len(r)
        monitoring.update(downloaded, content_length, len(r))

    if endcondition == 1: print()
    buffer.close(1)

    asset.shutdown(1)
    asset.close()


print('Downloadian 1.0')
print('RTFM: just COPY-PASTE URL and press ENTER or type close/exit')
while 1:
    url = input('> ')
    if url in ('close','exit'): break
    if url in controlVars:
        controlVars[url][1] = not(controlVars[url][1])
        print('#'+controlVars[url][0]+' IS '+('OFF','ON')[controlVars[url][1]])
    else: download(url)
