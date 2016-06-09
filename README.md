# downloadian
Python HTTP (Proxy+) File Downloader

### Description
Downloads files through HTTP protocol. Light-weight and easy-to-use.
Some tags for you: Sockets in Python (3.4, actually), HTTP protocol, Proxy authorization.

### Manual
1. If you don't use proxy-server, all you need is to COPY-and-PASTE your URL and press ENTER.
2. If you do use proxy-server:
   1. Find this string in code: ```username, password = '', ''```;
   2. Initialize variables ```username``` and ```password``` using your brain and hands;
   3. Launch the program and type ```proxy```;
   4. Finally, COPY-and-PASTE URL and press ENTER.
3. To cancel the download press ENTER while downloading.
4. To resume type ```resume URL``` or ```URL resume``` (URL is your URL).

### Commands
1. proxy - to enable or disable proxy
2. headers - to enable or disable displaying headers in 200 case
3. removing - to enable or disable removing downloaded data after canceling a download
