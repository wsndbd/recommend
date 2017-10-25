# -*- coding:utf-8 -*-
__author__ = 'paldinzhang'
import csv
import sys
import logging

reload(sys)
sys.setdefaultencoding('utf8')

logPath = "."
logFileName = "error"
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger()
fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, logFileName))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

def silentRemove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

if __name__ == "__main__":
    reader = csv.reader(file("../train.csv", "r"))
#    rowCount = sum(1 for row in reader)
#    print rowCount
#    print len(open("../train.csv").readlines())
    itemUsers = {}
    #uid,iid,score,time
    #first build inverse table for item to user
    for i, line in enumerate(reader):
        if 0 == i:
            continue
        if line[1] not in itemUsers:
            itemUsers[line[1]] = []
        itemUsers[line[1]].append(line[0])
        if i > 100:
            break
    print itemUsers
    #计算n(u)和相关度矩阵
    N = {}
    C = {}
    for item, users in itemUsers:
       print item, users 
