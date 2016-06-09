#!/usr/bin/env python3
''' Downloadian 1.0 '''
import socket
import base64
import os
import time
import threading

KBSIZE = 1024
BFSIZE = 10
DOWNDELAY = 0.5
TIME = (60, ' seconds', ' minutes', ' hours')
INFQ = (KBSIZE, 'bytes', 'KB', 'MB')
SPD = (KBSIZE, ' bytes/s', ' KB/s', ' MB/s')

def representWeight(weight,base):
    if weight < base[0]:
        return str(weight) + base[1]
    elif weight < base[0]**2:
        return str(round(weight/base[0])) + base[2]
    else:
        return str(round(weight/(base[0]**2),1)) + base[3]

# Progressbar (changing)
class MonitoringProgress():
    def __init__(self):
        self.prevlen = 0
        self.avgspeed = 0
        self.avgrate = self.maxrate = 5
        self.sumspeed = 0

    def update(self, downloaded, content_length, speed):
        if stopflag.locked(): return

        if self.avgrate != 0:
            self.sumspeed += speed
            self.avgrate -= 1
        else:
            self.avgspeed = round(self.sumspeed / self.maxrate)
            self.avgrate = self.maxrate
            self.sumspeed = 0

        if content_length == -1:
            monitoring = '\r[unknown] ' + representWeight(downloaded,INFQ)
        else:
            monitoring = '\r['
            progress = (downloaded/content_length)*100
            for i in range(int(progress/2)): monitoring += '='
            for i in range(50-int(progress/2)): monitoring += ' '
            monitoring += '] ' + str(round(progress,2)) + '%'
            monitoring += ' ' + representWeight(downloaded,(KBSIZE,'','','')) + '/' + representWeight(content_length,INFQ)
        monitoring += ' (' + representWeight(speed,SPD) + ')'
        if content_length != -1 and self.avgspeed != 0:
            monitoring += '[' + representWeight(round((content_length-downloaded)/self.avgspeed),TIME) + ']'
        elif not(self.avgspeed): monitoring += '[calculating]'

        curlen = len(monitoring)
        if self.prevlen > curlen:
            for i in range(self.prevlen-curlen): monitoring += ' '
        self.prevlen = curlen
        print(monitoring,end='')

        if content_length != -1 and progress >= 100: self.complete('')

    def complete(self, message):
        if message == '': print()
        else: print('\n'+message)

# Buffering data in RAM (stable)
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
controlTriggers = {'proxy':['PROXY AUTHORIZATION',0], 'headers':['HEADERS DISPLAYING',0], 'removing':['CANCELED DOWNLOAD DATA REMOVING',1]}

def download(url,threadname):
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
        while os.path.exists(filename+'(samename '+str(i)+')'+ext): i += 1
        filename += '(samename '+str(i)+')'
    filename += ext

    asset = socket.socket()
    asset.connect((domain, 80))

    request = 'GET ' + url + ' HTTP/1.1\r\nHost:' + domain + '\r\n'
    if controlTriggers['proxy']:
        request += 'Proxy-authorization: Basic ' + base64.encodestring((username+':'+password).encode('utf-8')).decode('utf-8') + '\r\n'
    request += '\r\n'
    asset.send(request.encode('utf-8'))

    r = b''
    while not('\r\n\r\n' in r.decode('utf-8')):
        r += asset.recv(1)
    _header = r.decode('utf-8')
    if _header[:_header.index('\n')].split(' ')[1] == '200' and not(controlTriggers['headers'][1]):
        print(_header[:_header.index('\n')])
    else:
        print(_header[:-4])
    print('Downloading in --> '+filename[filename.rindex('/')+1:])


    endcondition = 0
    try:
        _indexAfterContentLength = _header.index('Content-Length')+16
        _afterContentLength = _header[r.decode('utf-8').index('Content-Length')+16:]
        content_length = int(_header[_indexAfterContentLength:_indexAfterContentLength+_afterContentLength.index('\r\n')])
    except:
        endcondition = 1

    maxtraffic = 10*KBSIZE**2
    downloaded = 0
    progress = 0.0
    buffer = BufToDisk(BFSIZE*KBSIZE**2, filename)

    r = b''
    def c0(): return downloaded < content_length
    def c1(): return not(b'\r\n\r\n' in r)
    conditions = (c0, c1)


    if endcondition: content_length = -1
    monitoring = MonitoringProgress()
    while conditions[endcondition]():
        r = b''
        try:
            if stopflag.locked(): break
            time.sleep(DOWNDELAY)
            while not(r):
                asset.settimeout(5)
                r = asset.recv(maxtraffic)
        except:
            print('\n#UNEXPECTED NETWORK ERROR. DOWNLOADED DATA SAVED.')
            break
        buffer.write(r)
        downloaded += len(r)
        monitoring.update(downloaded, content_length, round(len(r)/DOWNDELAY))

    if endcondition: print()
    buffer.close(1)

    asset.shutdown(1)
    asset.close()

    if stopflag.locked():
        if controlTriggers['removing'][1]: os.remove(filename)
        print('#DOWNLOAD CANCELED. DOWNLOADED DATA ',end='')
        if controlTriggers['removing'][1]: print('REMOVED.')
        else: print('SAVED.')

stopflag = threading.Lock()

print('Downloadian 1.0')
print('RTFM: just COPY-PASTE URL and press ENTER or type close/exit')
while 1:
    url = input('> ')
    if url in ('close','exit'): break
    if url == 'buffer': print(str(BFSIZE)+' MB')
    elif url[:6] == 'buffer':
        BFSIZE = int(url.split(' ')[1])
        print('#BUFFER SET UP ON '+str(BFSIZE)+' MB')
    elif url in controlTriggers:
        controlTriggers[url][1] = not(controlTriggers[url][1])
        print('#'+controlTriggers[url][0]+' IS '+('OFF','ON')[controlTriggers[url][1]])
    else:
        th = threading.Thread(target=download, args=(url,'Thread'))
        th.start()
        input() #for canceling
        stopflag.acquire()
        while threading.activeCount() > 1: pass
        stopflag.release()
