#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2015年4月9日

@author: zhangdebo
'''
a={"1":[[1],[1],2,3],"2":[2,3,44,44]}

def duplicate(dicMap):
    dic_tmp={}
    for i in dicMap.keys():
        dic_tmp[i] = list(set(dicMap.get(i)))
    print dic_tmp

b="asd大写"
print b.title()
if 3>0:
    print "OK"
#if __name__ == "__main__":
    #duplicate(a)