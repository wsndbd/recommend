# -*- coding:utf-8 -*-
__author__ = 'paldinzhang'
import csv
import sys
import logging
import math

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
    userItems = {}
    #uid,iid,score,time
    #first build inverse table for item to user
    for i, line in enumerate(reader):
        if 0 == i:
            continue
        #建立商品到用户的映射
        if line[1] not in itemUsers:
            itemUsers[line[1]] = []
        itemUsers[line[1]].append(line[0])
        #建立用户到商品的映射
        if line[0] not in userItems:
            userItems[line[0]] = {}
        if line[1] not in userItems[line[0]]:
            userItems[line[0]][line[1]] = []
        userItems[line[0]][line[1]].append([line[2], line[3]])

        if i > 10:
            break
    print userItems
    #print itemUsers
    #计算n(u)和相关度矩阵
    N = {}
    C = {}
    for item, users in itemUsers.iteritems():
        for u in users:
            if u not in N:
                N[u] = 0
            N[u] += 1
            for v in users:
                if u == v:
                    continue
                if v not in N:
                    N[v] = 0
                N[v] += 1
                if u not in C:
                    C[u] = {}
                if v not in C[u]:
                    C[u][v] = 0
                C[u][v] += 1
    W = {}
    for u, r in C.iteritems():
        for v, cuv in r.iteritems():
            if u not in W:
                W[u] = {}
            if v not in W[u]:
                W[u][v] = 0
            W[u][v] = cuv / math.sqrt(N[u] * N[v])
    #按测试数据计算分数 格式 uid,iid
    K = 80
    reader = csv.reader(file("../test.csv", "r"))
    for i, line in enumerate(reader):
         
    #for v, wuv in sorted(W[u].iteritems, key = itemgetter(1), reverse = True):
    #    k = 0
    #    if k < K:

    #print W
