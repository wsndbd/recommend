# -*- coding:utf-8 -*- __author__ = 'paldinzhang'
import os
import csv
import sys
import logging
import math
import operator
import sqlite3
import collections
import getopt
import errno
import time
from scipy import sparse
import numpy as np
import pandas as pd

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

TRAINFILE= "../train.csv"
TESTFILE = "../test.csv"

def silentRemove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

if __name__ == "__main__":
    reCreate = False
    opts, args = getopt.getopt(sys.argv[1:], "c", [])
    for o, a in opts:
        #recreate database
        if "-c" == o:
            reCreate = True 
            silentRemove("./dict.db")
    #table not exist
    if reCreate:
        print "pandas reading..."
        startTime = time.time()
        data = pd.read_csv(TRAINFILE)
        print "eclapsed time", time.time() - startTime
        #uid,iid,score,time
        uids = set()
        iids = set()
        maxUid = 0
        maxIid = 0

        print "reading file..."
        startTime = time.time()
        for row in data.values:
            #print ".",
            uids.add(row[0])
            iids.add(row[1])
            if row[0] > maxUid:
                maxUid = row[0]
            if row[1] > maxIid:
                maxIid = row[1]
        print "eclapsed time", time.time() - startTime

        print "len(uids)", len(uids), "len(iids)", len(iids)
        print "maxUid", maxUid, "maxIid", maxIid
        print "creating matrix..."
        startTime = time.time()
        m = sparse.lil_matrix((maxUid + 1, maxIid + 1), dtype = np.int8)
        for row in data.values:
            #print "row0", row[0], "row1", row[1], "row2", row[2]
            m[row[0], row[1]] = row[2]
        print "eclapsed time", time.time() - startTime
        #建立各用户的相关性稀疏矩阵
        mu = sparse.lil_matrix((maxUid + 1, maxUid + 1), dtype = np.int)

    uids = sorted(uids)
    lenUids = len(uids)

    #id1,id2相关度，即打过分的物品共有相同的多少个
    for i in xrange(lenUids):
        uid = uids[i]
        print "calculate similarrity i = ", i, "uid", uid, "of", lenUids
        startTime = time.time()
        arrayU = m[uid,:].toarray()
        for j in xrange(lenUids):
            vid = uids[j]
            if vid > uid:
                if 0 == mu[uid, vid]:
                    arrayV = m[vid,:].toarray()
                    #先用sign函数把打过的分转换成1，0，-1，再相与出都是1的个数，就是共同参与过打分的物品数
                    mu[uid, vid] = np.count_nonzero(np.logical_and(arrayU, arrayV))
        print "eclapsed time", time.time() - startTime

    #id1,id2相关度，即打过分的物品共有相同的多少个
    rowCount = sum(1 for row in file(TESTFILE, "r"))
    rank = collections.OrderedDict()
    K = 80
    reader = csv.reader(file(TESTFILE, "r"))
    next(reader)
    lastUid = 0
    W = {}
    for i, line in enumerate(reader):
        k = 0
        iid = int(line[1])
        uid = int(line[0])
        if uid not in rank:
            rank[uid] = {}
        if iid not in rank[uid]:
            rank[uid][iid] = 0
        scoreSum = 0
        similaritySum = 0
        #计算相似度
        #找到自身的平均分及评价过的商品个数
        if uid >= m.shape[0]:
            print "error row index", uid, " out of bounds", m.shape[0]
            continue
        arrayU = m[uid,:].toarray()
        ni = np.count_nonzero(arrayU)
        selfAvgScore = float(arrayU.sum()) / ni  
        print "calculate similarrity", i, "of", rowCount
        startTime = time.time()
        #print "i", i, "uid", uid, "selfAvgScore", selfAvgScore, "ni", ni,
        #找到和uid相关的所有用户,按相关度降序排序
        if uid != lastUid or 0 == lastUid:
            W = {}
            #print "caclatuing same count"
            for vid in xrange(maxUid + 1):
                if uid != vid:
                    W[vid] = 0
                    if 0 != mu[uid, vid]:
                        W[vid] = mu[uid, vid]
                    else:
                        W[vid] = mu[vid, uid]
        #计算每个用户对iid的打分
        print "eclapsed time", time.time() - startTime
        print "calculate score", i, "of", rowCount
        startTime = time.time()
        #print "calclating score"
        for u2, w in sorted(W.iteritems(), key = operator.itemgetter(1), reverse = True): 
            uid2 = u2
            sameCount = w
            #print "uid", uid, "uid2", uid2, "sameCount", sameCount,
            #找到相关用户对应的平均分及评价物品的个数
            arrayV = m[uid2,:].toarray()
            nj = np.count_nonzero(arrayV)
            if 0 == nj:
                #print
                continue
            avgScore = float(arrayV.sum()) / nj
            #相似度
            wuv = float(sameCount) / math.sqrt(ni * nj)
            #print "nj", nj, "avgScore", avgScore, "wuv", wuv
            if k < K:
                #相关用户对iid的打分
                score = arrayV[0][iid]
                if 0 == score:
                    continue
                #print "k", k, "uid2", uid2, "iid", iid, "score", score
                scoreSum += wuv * float(float(score) - avgScore)
                similaritySum += wuv
                k += 1
            else:
                break
        if 0 == k:
            rank[uid][iid] = 0.0
        else:
            rank[uid][iid] = selfAvgScore + scoreSum / similaritySum
        print "eclapsed time", time.time() -startTime
        lastUid = uid

    #print rank
    print "write score to file..."
    startTime = time.time()
    testFile = open("test.csv", "w")
    writer = csv.writer(testFile)
    writer.writerow(['uid', 'iid', 'score'])
    for u, vs in rank.iteritems():
        for v, s in rank[u].iteritems():
            writer.writerow([u, v, s])
    testFile.close() 
    print "eclapsed time", time.time() -startTime
