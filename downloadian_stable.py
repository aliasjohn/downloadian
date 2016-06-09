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

    def update(self, downloaded, content_length, speed, errors):
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
        monitoring += ' Errors:' + str(errors)

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


def extractRQData(url, isResume):
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

    if not(isResume):
        if os.path.exists(filename+ext):
            i = 1
            while os.path.exists(filename+'(samename '+str(i)+')'+ext): i += 1
            filename += '(samename '+str(i)+')'
    filename += ext

    if isResume and not(os.path.exists(filename)):
        print('#THERE IS NO '+str(filename[filename.index('/')+1:])+' IN MY DIRECTORY.')
        filename = 'DOWNLOADIAN_DOWNLOADS/' + input('#PLEASE, ENTER FILENAME TO LOAD: ')

    return (domain, filename)

def downloadCore(url,isResume,errors,autoResumeData):
    errorflag = 0

    if not autoResumeData:
        domain, filename = extractRQData(url, isResume)
    else:
        domain, filename = autoResumeData
    curfsize = 0
    if isResume:
        curfsize = os.path.getsize(filename)

    inflag.acquire()

    asset = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cflag = 1
    while cflag:
        try:
            asset.connect((domain, 80))
            cflag = 0
        except:
            if stopflag.locked(): break

    request = 'GET ' + url + ' HTTP/1.1\r\nHost:' + domain + '\r\n'
    if controlTriggers['proxy'][1]:
        request += 'Proxy-authorization: Basic ' + base64.encodestring((username+':'+password).encode('utf-8')).decode('utf-8') + '\r\n'
    if isResume:
        request += 'Range: bytes='+str(curfsize)+'-9999999999\r\n' #replace 7053...
    request += '\r\n'
    asset.send(request.encode('utf-8'))

    # Receiving headers
    r = b''
    while not('\r\n\r\n' in r.decode('utf-8')):
        r += asset.recv(1)
    _header = r.decode('utf-8')
    status_code = int(_header[:_header.index('\n')].split(' ')[1])
    if status_code in (200, 206) and not autoResumeData and not controlTriggers['headers'][1]:
        print(_header[:_header.index('\n')])
    else:
        if not autoResumeData: print(_header[:-4])
        if autoResumeData and not(status_code == 206):
            print('\n'+_header[:-4])
            return 0

    # Extracting Content-Length or trigger to another way of detecting the end of response body (payload)
    endcondition = 0
    try:
        _indexAfterContentLength = _header.index('Content-Length')+16
        _afterContentLength = _header[r.decode('utf-8').index('Content-Length')+16:]
        content_length = int(_header[_indexAfterContentLength:_indexAfterContentLength+_afterContentLength.index('\r\n')])
        if not autoResumeData:
            print('Downloading ('+representWeight(content_length,INFQ)+') in --> '+filename[filename.rindex('/')+1:])
    except:
        endcondition = 1
        if not autoResumeData:
            print('Downloading in --> '+filename[filename.rindex('/')+1:])

    # A bit of prepataions and starting data download (first time or resuming)
    maxtraffic = 10*KBSIZE**2
    if isResume:
        loadedsize = os.path.getsize(filename)
        _afterContentRange = _header[_header.index('Content-Range:'):]
        fullsize = int(_afterContentRange[_afterContentRange.index('/')+1:_afterContentRange.index('\r\n')])
        downloaded = loadedsize
        content_length = fullsize
    else:
        downloaded = 0
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
                asset.settimeout(3)
                r = asset.recv(maxtraffic)
        except:
            #print('\n#UNEXPECTED NETWORK ERROR. DOWNLOADED DATA SAVED.')
            errorflag = 1
            break
        buffer.write(r)
        downloaded += len(r)
        monitoring.update(downloaded, content_length, round(len(r)/DOWNDELAY), errors)

    if endcondition and not errorflag: print()
    buffer.close(1)

    asset.shutdown(1)
    asset.close()

    if stopflag.locked():
        if controlTriggers['removing'][1] and not(isResume): os.remove(filename)
        print('#DOWNLOAD CANCELED. DOWNLOADED DATA ',end='')
        if controlTriggers['removing'][1] and not(isResume): print('REMOVED.')
        else: print('SAVED.')

    inflag.release()
    if errorflag: return (domain, filename)
    else: return 0

def download(url,isResume):
    errors = 0
    r = downloadCore(url,isResume,0,())
    while r:
        errors += 1
        r = downloadCore(url,1,errors,r)
    #inflag.release()


inflag = threading.Lock()
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
    elif 'resume ' in url or ' resume' in url:
        inurl = ''
        if 'resume ' in url: inurl = url.split(' ')[1]
        else: inurl = url.split(' ')[0]
        th = threading.Thread(target=download, args=(inurl,1))
        th.start()
        while not(inflag.locked()):
            time.sleep(1)
        input()
        stopflag.acquire()
        while threading.activeCount() > 1: pass
        stopflag.release()
    else:
        th = threading.Thread(target=download, args=(url,0))
        th.start()
        input() #for canceling
        stopflag.acquire()
        while threading.activeCount() > 1: pass
        stopflag.release()
