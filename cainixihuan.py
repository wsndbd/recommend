# -*- coding:utf-8 -*- __author__ = 'paldinzhang'
import csv
import sys
import logging
import math
import operator
import sqlite3

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
    if 0 == len(cursor.fetchall()):
        return False
    else:
        return True


if __name__ == "__main__":
    reader = csv.reader(file("../train.csv", "r"))
    conn = sqlite3.connect("./dict.db")
    cursor = conn.cursor()
    #table not exist
    cursor.execute("drop table if exists user_item")
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
        cursor.execute("insert into user_item values(?, ?, ?, ?)", (uid, iid, score, timeStamp))
        #cursor.execute("select * from user_item")
        #print cursor.fetchall()
        if i > 1000:
            break

    #create index
    cursor.execute("drop index if exists index_on_user_item")
    cursor.execute("create index if not exists index_on_user_item on user_item(uid, iid)")
    cursor.execute("drop view if exists user_score")
    cursor.execute('''create view if not exists user_score as select
            uid, avg(score) as avg_score, count(iid) as count_iid from user_item group by uid order by uid 
            ''')
    #cursor.execute("select avg_score from user_score")
    #print cursor.fetchall()
    #cursor.execute("select * from sqlite_master where tbl_name = 'user_score' and type = 'view'")
    #print cursor.fetchall()
    #id1,id2相关度，即打过分的物品共有相同的多少个
    cursor.execute("drop view if exists user_relativity")
    cursor.execute("create view if not exists user_relativity as select u1.uid as uid1, u2.uid as uid2, count(u1.iid) as count_iid from user_item u1 inner join user_item u2 on u1.iid = u2.iid  where u1.uid <> u2.uid group by u1.uid, u2.uid")
    #cursor.execute("select uid1 from user_relativity")
    #print cursor.fetchall()
    #计算n(u)和相关度矩阵*
    #for u, r in C.iteritems():
    #    for v, cuv in r.iteritems():
    #        if u not in W:
    #            W[u] = {}
    #        if v not in W[u]:
    #            W[u][v] = 0
    #        W[u][v] = cuv / math.sqrt(N[u] * N[v])
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
        scoreSum = 0
        similaritySum = 0
        #计算相似度
        print "uid", uid
        cursor.execute("select uid2,count_iid from user_relativity where uid1  = ? order by count_iid desc", (uid,))
        W = cursor.fetchall()
        cursor.execute("select avg_score, count_iid from user_score where uid = ?", (uid,))
        ni = cursor.fetchall()[0][0]
        avgScore = cursor.fetchall()[0][1]
        for j, item in enumerate(W):
            uid2 = item[0]         
            print "uid2", uid2
            cursor.execute("select count_iid from user_score where uid = ?", (uid2,))
            nj = cursor.fetchall()[0][0]
            print "nj", nj
            wuv = item[1] / math.sqrt(ni * nj)
            cursor.execute("select score")
            scoreSum += wuv * 
            if k < K:
                scoreSum += wuv * float(float(userItems[v][iid][0]) - userAvgScore[v])
                similaritySum += wuv
                k += 1
                print "uid", uid, "vid", v, "iid", iid, "score", userItems[v][iid][0], "rank", rank[uid][iid], "k", k
        if 0 == k:
            rank[uid][iid] = 0.0
        else:
            rank[uid][iid] = userAvgScore[uid] + scoreSum / similaritySum
        print "uid", uid, "avgScore", userAvgScore[uid], "iid", iid, "rank", rank[uid][iid], "k", k, "scoreSum", scoreSum, "similaritySum", similaritySum
    #print rank
    testFile = open("test.csv", "w")
    writer = csv.writer(testFile)
    writer.writerow(['uid', 'iid', 'score'])
    for u, vs in rank.iteritems():
        for v, s in rank[u].iteritems():
            writer.writerow([u, v, s])
    testFile.close() 
