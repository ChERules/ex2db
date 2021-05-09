# Project ex2db.py
# support file: functions.py
# by: Albert Lam <albert@lamfamily.hk>
#
import os
import datetime
import sqlite3
import functions as mf

# MAIN Function starts

# setting up storage Enviroments
# hdir : for download html and converted text file
# ddir : for storing the extracted data
# adir : for result from processing extracted data
wdir = os.getcwd()
hdir = wdir + '/HTML/'
ddir = wdir + '/Data/'
adir = wdir + '/Analysis/'
if not os.path.exists(hdir): os.mkdir(hdir)
if not os.path.exists(ddir): os.mkdir(ddir)
if not os.path.exists(adir): os.mkdir(adir)

dbs = 'exdb.sqlite'
reset = 'No'
if not os.path.isfile(ddir+dbs): reset = 'Yes'
if reset == 'No':
    print('\nDo you want to rebuild the database? (Yes/No)')
    ans = input('Default is (No): ')
    if ans == 'Yes': reset = 'Yes'
########## DOWNLOAD WEBPAGE
#
# DOWNLOADING DAILY QUOTATION WEBPAGES FROM HONG KONG STOCK EXCHANGE
# and strip all inline html tags to create a text version of the file
#

# Setting up Enviroument
# Read today's date in yymmdd format
now = datetime.datetime.now()
lst = str(now.year)[-2:]+('00'+str(now.month))[-2:]+('00'+str(now.day))[-2:]

# Set up the starting date for downloading the quotation wegpage.
# set default to '190430' then update it in the following order:
# 1. look for the last downloaded file date in env.text
# 2. check the list of html files already downloaded to determine the last day.
fst = '190430'
os.chdir(hdir)
if os.path.isfile('env.txt'):
    f = open('env.txt', 'r')
    for line in f:
        if line.startswith('lastdate'):
            fst = line[9:15]
            break
    f.close()
else:
    # return a list of names of downloaded html files without extention
    datelist = mf.extlist(hdir, '.html', 'N')
    # extract the latest from all filename
    if len(datelist) > 1:
        datelist.sort()
        fst = datelist[len(datelist)-1]
lastdate = fst

# Download the web page for next and consquence date from HKEX if they exist.
# Delete the files that is too small to contain useful data; update lastdate
# after each successful download
while fst < lst:
    # advance fst to nextday and setup the URL and filenames
    fst = mf.nextday(fst)
    url = "https://www.hkex.com.hk/eng/stat/smstat/dayquot/d"+fst+"e.htm"
    if mf.url_is_alive(url):
        fname = fst + '.html'
        print('Downloading : ', fname)
        mf.dnload(url, fname)
        finfo = os.stat(fname)
        if finfo.st_size < 1024:
            os.remove(fname)
        else:
            lastdate = fst

# record the last date which webpage was downloaded in env.txt
f = open('env.txt','w')
f.write('lastdate:'+lastdate+'\n')
f.close()

######### EXGTRACT DATA FROM HTML FILES
#
# EXTRACT THE SUMMARY OF THE DAILY ACTIVITY FROM EACH HTMLFILES
# Save the information in "quotations.csv"
#
os.chdir(ddir)
conn = sqlite3.connect('exdb.sqlite')
cur  = conn.cursor()
if reset == 'Yes': mf.initialize(cur)

#
# create database tables if it doesn't exists
#

# READ WHAT HAS BEEN DONE PREVIOUSLY TO AVOID REPEATITION
# retrive a list of all html files with extention in HTML directory
# and sort them
htmlfiles = mf.extlist(hdir, '.html', 'Y')
htmlfiles.sort()

# dictionary of trading date which result had been read/extracted previously
cur.execute("SELECT * FROM session ORDER BY idx DESC LIMIT 1")
extracted = cur.fetchone()
if extracted != None:
    xfile = extracted[1][2:4]+extracted[1][5:7]+extracted[1][8:]+'.html'
    htmlfiles = htmlfiles[htmlfiles.index(xfile):]
    if len(htmlfiles) > 1:
        htmlfiles = htmlfiles[1:]
    else:
        htmlfiles = []

# loop throught all the downloaded webpages
if len(htmlfiles) > 0:
    for file in htmlfiles:
        # extract the data and add it to the "quotations.csv"
        print('Processing : ', file)
        tdn = mf.html2db(hdir+file, cur)
        conn.commit()
    # record the files has been processed before move on to next one
    # update session table
conn.close()
