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

def tableExist(cursor, tableName):
    cursor.execute("select name from sqlite_master where type = 'table' and name = '?'", (tableName))
    if None == cursor.fetchone():
        return False
    else:
        return True


if __name__ == "__main__":
    reCreate = False
    opts, args = getopt.getopt(sys.argv[1:], "c", [])
    for o, a in opts:
        print o, a
        #recreate database
        if "-c" == o:
            reCreate = True 
            silentRemove("./dict.db")
    conn = sqlite3.connect("./dict.db")
    cursor = conn.cursor()
    #table not exist
    if reCreate:
        f = open("../train.csv", "r")
        reader = csv.reader(f)
        cursor.execute('''create table if not exists user_item(
        uid INT NOT NULL,
        iid INT NOT NULL,
        score INT NOT NULL,
        timestamp INT,
        PRIMARY KEY(uid, iid)
        );
        ''')
        #uid,iid,score,time
        #first build inverse table for item to user
        next(reader) #跳过表头第一行
        for i, line in enumerate(reader):
            uid = line[0]
            iid = line[1]
            score = line[2]
            timeStamp = line[3]
            #建立用户到商品的映射
            #print uid, iid, score, timeStamp
            print "(uid, iid, score, timeStamp)", (uid, iid, score, timeStamp)
            cursor.execute("insert into user_item values(?, ?, ?, ?)", (uid, iid, score, timeStamp))
        f.close()

        #create index
        print "create index if not exists index_on_user_item_uid_iid on user_item(uid, iid)..."
        startTime = time.time()
        cursor.execute("create index if not exists index_on_user_item_uid_iid on user_item(uid, iid)")
        print "time elapsed ", time.time() - startTime
        print "create index if not exists index_on_user_item_uid on user_item(uid)..."
        startTime = time.time()
        cursor.execute("create index if not exists index_on_user_item_uid on user_item(uid)")
        print "time elapsed ", time.time() - startTime
        print "create index if not exists index_on_user_item_iid on user_item(iid)..."
        startTime = time.time()
        cursor.execute("create index if not exists index_on_user_item_iid on user_item(iid)")
        print "time elapsed ", time.time() - startTime

        #建立item到user的表
        print "create item_users..."
        startTime = time.time()
        cursor.execute("create table if not exists item_users as select iid, group_concat(uid) as uids from user_item group by iid")
        print "time elapsed ", time.time() - startTime
        print "create index if not exists index_on_item_users_iid on item_users(iid)..."
        startTime = time.time()
        cursor.execute("create index if not exists index_on_item_users_iid on item_users(iid)")
        print "time elapsed ", time.time() - startTime
        print "create index if not exists index_on_item_users_uids on item_users(uids)..."
        startTime = time.time()
        cursor.execute("create index if not exists index_on_item_users_uids on item_users(uids)")
        print "time elapsed ", time.time() - startTime
        
        cursor.execute('''create view if not exists user_score as select
            uid, avg(score) as avg_score, count(iid) as count_iid from user_item group by uid
            ''')
        print "ANALYZE..."
        startTime = time.time()
        cursor.execute("ANALYZE")
        print "time elapsed ", time.time() - startTime

    #id1,id2相关度，即打过分的物品共有相同的多少个
    rank = collections.OrderedDict()
    K = 80
    reader = csv.reader(file("../test.csv", "r"))
    next(reader)
    lastUid = 0
    W = {}
    for i, line in enumerate(reader):
        k = 0
        iid = line[1]
        uid = line[0]
        if line[0] not in rank:
            rank[uid] = {}
        if iid not in rank[uid]:
            rank[uid][iid] = 0
        scoreSum = 0
        similaritySum = 0
        #计算相似度
        #找到自身的平均分及评价过的商品个数
        print "select avg_score, count_iid from user_score where uid = %s" %(uid,)
        cursor.execute("select avg_score, count_iid from user_score where uid = ?", (uid,))
        row = cursor.fetchone()
        if not row:
            continue
        selfAvgScore = row[0]
        ni = row[1]
        print "i", i, "uid", uid, "selfAvgScore", selfAvgScore, "ni", ni 
        #找到和uid相关的所有用户,按相关度降序排序
        cursor.execute("select distinct uid from user_item where uid <> ?", (uid,))
        if uid != lastUid:
            W = {}
            for row in cursor:
                otherUid = row[0]
                #比较头，中间，尾是否包含指定uid
                cur1 = conn.cursor()
                sql1 = "(uids||',' like '%s,%%' or ','||uids||',' like '%%,%s,%%' or ','||uids like '%%,%s')" %(uid, uid, uid)
                sql2 = "(uids||',' like '%s,%%' or ','||uids||',' like '%%,%s,%%' or ','||uids like '%%,%s')" %(otherUid, otherUid, otherUid)
                sql = "select count(*) from item_users where  " + sql1 + " and " + sql2
                #print "sql", sql
                cur1.execute(sql)
                row1 = cur1.fetchone()
                if not row1:
                    continue
                W[otherUid] = row1[0]
                print "calc uid1", uid, "ohteruid", otherUid, "samecount", row1[0]
        #计算每个用户对iid的打分
        for u2, w in sorted(W.iteritems(), key = operator.itemgetter(1), reverse = True): 
            uid2 = u2
            sameCount = w
            #找到相关用户对应的平均分及评价物品的个数
            cur1.execute("select avg_score, count_iid from user_score where uid = ?", (uid2,))
            row1 = cur1.fetchone()
            avgScore = row1[0]
            nj = row1[1]
            #相似度
            wuv = sameCount / math.sqrt(ni * nj)
            print "uid", uid, "uid2", uid2, "avgScore", avgScore, "nj", nj, "sameCount", sameCount, "wuv", wuv
            if k < K:
                cur1.execute("select score from user_item where uid = ? and iid = ?", (uid2, iid))
                row1 = cur1.fetchone()
                if not row1:
                    continue
                #相关用户对iid的打分
                score = row1[0]
                print "k", k, "uid2", uid2, "iid", iid, "score", score
                scoreSum += wuv * float(float(score) - avgScore)
                similaritySum += wuv
                k += 1
            else:
                break
        if 0 == k:
            rank[uid][iid] = 0.0
        else:
            rank[uid][iid] = selfAvgScore + scoreSum / similaritySum
        lastUid = uid
    #print rank
    testFile = open("test.csv", "w")
    writer = csv.writer(testFile)
    writer.writerow(['uid', 'iid', 'score'])
    for u, vs in rank.iteritems():
        for v, s in rank[u].iteritems():
            writer.writerow([u, v, s])
    testFile.close() 
