import sys
import os
import pandas as pd
from scipy import sparse
import numpy as np


#data=pd.read_csv("train2.csv")
data=pd.read_csv("../train.csv")
ids = set()
items = set()
max_id=0
max_item_id=0
for row in data.values:
    print "row0", row[0], "row1", row[1]
    ids.add(row[0])
    items.add(row[1])
    if row[0] > max_id:
        max_id = row[0]
    if max_item_id < row[1]:
        max_item_id = row[1]

print len(ids),len(items)
print max_id, max_item_id
mat = sparse.lil_matrix((max_id+1,max_item_id+1), dtype=np.int)
for row in data.values:
    mat[row[0], row[1]]=row[2]
print mat.shape
print "row[0]", mat[0,:]
print "row[1]", mat[1,:]
print mat[0,:] == mat[1,:]
#csrMat = mat.tocsr()
#print "csrMat", csrMat[0,:]
a = mat.toarray()
print "a",a
