# -*- coding:utf-8 -*- __author__ = 'paldinzhang'
import csv
import sys
import logging
import math
import operator
import sqlite3
import collections

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
        print "(uid, iid, score, timeStamp)", (uid, iid, score, timeStamp)
        cursor.execute("insert into user_item values(?, ?, ?, ?)", (uid, iid, score, timeStamp))

    #create index
    cursor.execute("drop index if exists index_on_user_item")
    cursor.execute("create index if not exists index_on_user_item on user_item(uid, iid)")
    cursor.execute("drop table if exists user_score")
    cursor.execute('''create table if not exists user_score as select
            uid, avg(score) as avg_score, count(iid) as count_iid from user_item group by uid order by uid 
            ''')
    #id1,id2相关度，即打过分的物品共有相同的多少个
    cursor.execute("ANALYZE")
    cursor.execute("drop table if exists user_relativity")
    cursor.execute("create table if not exists user_relativity as select u1.uid as uid1, u2.uid as uid2, count(u1.iid) as count_iid from user_item u1 inner join user_item u2 on u1.iid = u2.iid  where u1.uid > u2.uid group by u1.uid, u2.uid")
    quit()
    #按测试数据计算分数 格式 uid,iid
    rank = collections.OrderedDict()
    K = 80
    reader = csv.reader(file("../test.csv", "r"))
    next(reader)
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
        cursor.execute("select avg_score, count_iid from user_score where uid = ?", (uid,))
        row = cursor.fetchone()
        if not row:
            continue
        selfAvgScore = row[0]
        ni = row[1]
        print "i", i, "uid", uid, "selfAvgScore", selfAvgScore, "ni", ni 
        #找到和uid相关的所有用户,按相关度降序排序
        cursor.execute("select uid2,count_iid from user_relativity where uid1  = ? order by count_iid desc", (uid,))
        #计算每个用户对iid的打分
        for row in cursor:
            uid2 = row[0]
            sameCount = row[1]
            print "uid2", uid2, "sameCount", sameCount
            #找到相关用户对应的平均分及评价物品的个数
            cur1 = conn.cursor()
            cur1.execute("select avg_score, count_iid from user_score where uid = ?", (uid2,))
            row1 = cur1.fetchone()
            avgScore = row1[0]
            nj = row1[1]
            print "uid2", uid2, "avgScore", avgScore, "nj", nj
            #相似度
            wuv = sameCount / math.sqrt(ni * nj)
            if k < K:
                print "uid2", uid2, "iid", iid
                cur1.execute("select score from user_item where uid = ? and iid = ?", (uid2, iid))
                row1 = cur1.fetchone()
                if not row1:
                    continue
                #相关用户对iid的打分
                score = row1[0]
                print "uid2", uid2, "iid", iid, "score", score
                scoreSum += wuv * float(float(score) - avgScore)
                similaritySum += wuv
                k += 1
        if 0 == k:
            rank[uid][iid] = 0.0
        else:
            rank[uid][iid] = selfAvgScore + scoreSum / similaritySum
        if i > 2:
            break
    #print rank
    testFile = open("test.csv", "w")
    writer = csv.writer(testFile)
    writer.writerow(['uid', 'iid', 'score'])
    for u, vs in rank.iteritems():
        for v, s in rank[u].iteritems():
            writer.writerow([u, v, s])
    testFile.close() 
