# -*- coding:utf-8 -*-
__author__ = 'paldinzhang'
import csv
import sys
import logging
import math
import operator

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
    itemUsers = {}
    userItems = {}
    userAvgScore = {} #用户的平均分
    #uid,iid,score,time
    #first build inverse table for item to user
    for i, line in enumerate(reader):
        if 0 == i:
            continue
        uid = line[0]
        iid = line[1]
        score = line[2]
        timeStamp = line[3]
        #建立商品到用户的映射
        if iid not in itemUsers:
            itemUsers[iid] = []
        itemUsers[iid].append(uid)
        #建立用户到商品的映射
        if uid not in userItems:
            userItems[uid] = {}
            userAvgScore[uid] = 0
        userAvgScore[uid] += int(score)
        if iid not in userItems[uid]:
            userItems[uid][iid] = []
        userItems[uid][iid].append(score)
        userItems[uid][iid].append(timeStamp)

        #if i > 10000:
        #    break
    for i, v in userAvgScore.iteritems():
        userAvgScore[i] = float(v) / len(userItems[i])
        print "i", i, "v", v, "count", len(userItems[i]), "avg score", userAvgScore[i]
    #print userItems
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
    #print W
    #for v, wuv in sorted(W['0'].iteritems(), key = operator.itemgetter(1), reverse = True):
    #    print v, wuv
    #按测试数据计算分数 格式 uid,iid
    rank = {}
    K = 80
    reader = csv.reader(file("../test.csv", "r"))
    for i, line in enumerate(reader):
        if 0 == i:
            continue
        k = 0
        iid = line[1]
        uid = line[0]
        if line[0] not in rank:
            rank[uid] = {}
        if iid not in rank[uid]:
            rank[uid][iid] = 0
        if uid not in W:
            continue
        scoreSum = 0
        similaritySum = 0
        for v, wuv in sorted(W[uid].iteritems(), key = operator.itemgetter(1), reverse = True):
            #print "uid", uid, "iid", iid, "v", v, "wuv", wuv
            if k < K:
                if iid in userItems[v]:
                    scoreSum += wuv * float(float(userItems[v][iid][0]) - userAvgScore[v])
                    similaritySum += wuv
                    k += 1
                    print "uid", uid, "vid", v, "iid", iid, "score", userItems[v][iid][0], "rank", rank[uid][iid], "k", k
        if 0 == k:
            rank[uid][iid] = 0.0
        else:
            rank[uid][iid] = userAvgScore[uid] + scoreSum / similaritySum
        print "uid", uid, "avgScore", userAvgScore[uid], "iid", iid, "rank", rank[uid][iid], "k", k, "scoreSum", scoreSum, "similaritySum", similaritySum
    quit()
    #print rank
    testFile = open("test.csv", "w")
    writer = csv.writer(testFile)
    writer.writerow(['uid', 'iid', 'score'])
    for u, vs in rank.iteritems():
        for v, s in rank[u].iteritems():
            writer.writerow([u, v, s])
    testFile.close() 
