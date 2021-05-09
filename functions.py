import os
import sqlite3
import urllib.request, urllib.parse, urllib.error
import re

def initialize(hdl):
    hdl.executescript('''
    DROP TABLE IF EXISTS listing;
    DROP TABLE IF EXISTS session;
    DROP TABLE IF EXISTS dailystat;

    CREATE TABLE listing (
        code     SMALLINT NOT NULL PRIMARY KEY UNIQUE,
        name     TEXT,
        currency CHAR(3),
        shares   INTEGER,
        added    DATE
    );

    CREATE TABLE session (
        idx      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        date     DATE UNIQUE,
        sofyr    SMALLINT NOT NULL
    );

    CREATE TABLE dailystat (
        idx      INTEGER,
        code     SMALLINT,
        high     REAL,
        low      REAL,
        close    REAL,
        ask      REAL,
        bid      REAL,
        turnover FLOAT(20.3),
        volume   INTEGER,
        PRIMARY KEY (idx, code)
    )
    ''')
    return()

def sqldate(d):
    nd = '20'+d[:2]+'-'+d[2:4]+'-'+d[4:]
    return(nd)

def nextday(dt):
    # setup the next date to try
    yy = int(dt[:2])
    mm = int(dt[2:4])
    dd = int(dt[4:])
    dd = dd + 1
    if dd > 31:
        mm = mm + 1
        dd = 1
    if mm > 12:
        yy = yy + 1
        mm = 1
    nd = str('00'+str(yy))[-2:]+("00" + str(mm))[-2:]+("00" + str(dd))[-2:]
    return(nd)

def extlist(path, ext, w):
    """
    create a list of files in path with extention ext
    path : str of path to search
    ext : str of extention of files to be search
    w : if 'Y', returen a list of file names with extention
    """
    flist = []
    pos = len(ext)
    for file in os.listdir(path):
        if pos > 0:
            if file.endswith(ext):
                if w == 'Y':
                    flist.append(file)
                else:
                    flist.append(file[:-1*pos])
        else:
            flist.append(file)
    return(flist)

def url_is_alive(url):
    """
    Checks that a given URL is reachable.
    param url: A URL
    """
    try:
        urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        return False
    return True

def dnload(site, fname):
# Read the "site" and write it out to "fname"
# to preserve the original html file
# Then call html2txt to strip down the html tags.
    hl = urllib.request.urlopen(site).read().decode()
    fout = open(fname, 'w')
    fout.write(hl)
    fout.close()

def striptag(l):
    ln = l.rstrip()
    if len(ln) > 0:
        ln = re.sub('<.+?>', '', ln)
        if len(ln) > 0:
            schr = re.findall('&.+;', ln)
            if len(schr) > 0:
                for ch in schr:
                    if ch == '&amp;': ln = re.sub(ch, '&', ln)
                    elif ch == '&quot;': ln = re.sub(ch, '"', ln)
                    elif ch == '&lt;': ln = re.sub(ch, '<', ln)
                    elif ch == '&gt;': ln = re.sub(ch, '>', ln)
    return(ln)

def read_line(t):
    r = []
    r.append(t[1:6].strip())
    r.append(t[7:23].strip())
    r.append(t[24:27].strip())
    r.append(t[28:36].strip().replace(',', ''))
    r.append(t[37:45].strip().replace(',', ''))
    r.append(t[46:54].strip().replace(',', ''))
    r.append(t[55:].strip().replace(',', ''))
    return(r)

def html2db(filename, db):
    td = filename[-11:-5]
    date = sqldate(td)
    qpage = open(filename, 'r')

    st = 's'

    for line in qpage:
        if line.strip() == '': continue
        # strip html tags and convert escape sequence
        line = striptag(line)
        # search and extract the session number for the year
        if st == 's':
            if line.find(td) > -1:
                line = "00" + line
                senum = line[:line.index('/')]
                senum = senum[-3:]
                db.execute('INSERT INTO session (date, sofyr) VALUES (?,?)', \
                (date,senum))
                db.execute('SELECT idx FROM session WHERE date = ?', (date,))
                seq = db.fetchone()[0]
                st = 'h'
        # locate the beginning of the quotation section
        elif st == 'h':
            if line.find('CLOSING      BID     LOW        TURNOVER ($)') > -1:
                st = 'q'
        # read the first line of each quotation
        elif st == 'q':
            # stop the reading operation once the end of section is reached
            if line.startswith('------'):
                st = 'd'
                break
            q = read_line(line)
            if len(q[0]) > 0:
                for i in [0,6]:
                    try:
                        q[i] = int(q[i])
                    except:
                        q[i] = 'NULL'
                for i in [3,4,5]:
                    try:
                        q[i] = float(q[i])
                    except:
                        q[i] = 'NULL'
                code = q[0]
                name = q[1]
                cur  = q[2]
                prv  = q[3]
                ask  = q[4]
                high = q[5]
                traded = q[6]
                # check if company already in listing
                # INSERT a record if it is not
                db.execute("SELECT code FROM listing WHERE code = ?", (code,))
                if db.fetchone() == None:
                    db.execute("INSERT INTO listing (code, name, currency, added) \
                    VALUES (?,?,?,?)", (int(code), name, cur, date))
            else:
                for i in range(3,7):
                    try:
                        q[i] = float(q[i])
                    except:
                        q[i] = 'NULL'
                    # read the next line of the quotation
                close = q[3]
                bid = q[4]
                low = q[5]
                tunovr = q[6]
                db.execute('INSERT INTO dailystat (idx, code, high, low, \
                close, ask, bid, turnover, volume) VALUES (?,?,?,?,?,?,?,\
                ?,?)', (seq, code, high, low, close, ask, bid, tunovr, traded))
    qpage.close()
    return(senum)
