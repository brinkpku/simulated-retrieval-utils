#-*- coding:utf8 -*-
#!/usr/bin/env python


#a demo

import threading
from time import time
from datetime import datetime
from Wok import ThreadSearcher

startTime = time()
threadLst = []
with open('r') as f:
    txt = f.readlines()
rlst = [i.strip() for i in txt]
results = {}
lock = threading.Lock()
for i in range(20):
        t = ThreadSearcher(rlst, lock, results)
        t.selectCitationIndex("SCI", "SSCI", "AHCI", "ISTP", "ISSHP", "ESCI")
        t.setYearRange(2015, 2016)
        threadLst.append(t)
for i in threadLst:
    i.start()
for i in threadLst:
    i.join()
with open('demoResults', 'w') as f:
    f.write('Get data at ' + datetime.today().ctime() + '.\n')
    for i in txt:
        f.write(i.strip() + '\t' + str(results[i.strip()]) + "\n")
print 'Totally ', len(results), 'results, used', time() - startTime, 'seconds.'    
print 'Get data at', datetime.today().ctime() + '.'

