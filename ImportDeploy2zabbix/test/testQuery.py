#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2015年4月9日

@author: zhangdebo
'''
import os,sys,time
import xlwt
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
    
for i in xrange(1,4):
    print i
    
a=['123','1232']
print ",".join(a)
print time.time()
b=['1','3']

book=xlwt.Workbook(encoding='utf-8')
table=book.add_sheet('test')
# sheet.write(0,0,"123")
# sheet.write(0,1,"234")
# sheet.write(0,2,"345")
# sheet.write(1,0,"asd")
# #sheet.write_merge(top_row, bottom_row, left_column, right_column)
# sheet.write_merge(0, 1, 0, 1, 'Long Cell')
# sheet.write(2, 0, 1)
# sheet.write(2, 1, 2)
# """
# write_merge(x, x + m, y, w + n, string, sytle)
# x表示行，m表示跨行个数，y表示列，n表示跨列个数，string表示要写入的单元格内容，style表示单元格样式。其中，x，y，w，h，都是以0开始计算的。
# """
# sheet.write_merge(3,5,0,0,"ttt")
# sheet.write_merge(3,5,1,1,"123")
# sheet.write_merge(3,5,2,2,"456")
# title=["hostname","IP","cpu负载","内存占用","连接数","流量峰值"]
# #写入表头
# for i in xrange(len(title)):
#     table.write(0,i,title[i])
# testMap={u'13084905-0075-1': [u'192.168.163.71', 0.11917639751552796, {u'net.if.out[eth1]': 0, u'net.if.in[sit0]': 0, u'net.if.out[eth0]': 0, u'net.if.in[eth0]': 0, u'net.if.in[eth1]': 0, u'net.if.out[sit0]': 0}], u'bind02.hk.gomo.com': [u'10.10.0.28', 0.0074416149068323, {u'net.if.out[eth1]': 0, u'net.if.in[eth0]': 0, u'net.if.in[eth1]': 0, u'net.if.out[eth0]': 0}], u'blog-192-168-1-125': [u'192.168.1.125', 0.08368695652173913, {u'net.if.out[eth1]': 0, u'net.if.in[eth0]': 0, u'net.if.in[eth1]': 0, u'net.if.out[eth0]': 0}], u'applib-192-168-1-97': [u'192.168.1.97', 0.0012341614906832305, {u'net.if.out[eth1]': 0, u'net.if.in[eth0]': 0, u'net.if.in[eth1]': 0, u'net.if.out[eth0]': 0}], u'Esxi-Dc-10.10.9.21': [u'10.10.9.21', 0], u'Esxi-Dc-10.10.9.23': [u'10.10.9.23', 0], u'Esxi-Dc-10.10.9.22': [u'10.10.9.22', 0], u'Esxi-Dc-10.10.9.25': [u'10.10.9.25', 0], u'Esxi-Dc-10.10.9.24': [u'10.10.9.24', 0], u'bind01.hk.gomo.com': [u'10.10.0.25', 0.007414906832298135, {u'net.if.in[eth0]': 0, u'net.if.out[eth0]': 0}]}
# row=1
# for i,y in testMap.items():
#     col=1
#     print "cacac:",row
#     if len(y) >2 and y[2]:
#         col=len(y[2])
#     table.write_merge(row,row+col-1,0,0,i)
#     table.write_merge(row,row+col-1,1,1,y[0])
#     table.write_merge(row,row+col-1,2,2,y[1])
#     print "row+col:",row+col
#     if col>1:
#         tmp_cell=0
#         for j,k in y[2].items():
#             print "wocao:",row+tmp_cell,3,"test"
#             table.write(row+tmp_cell,3,"test")
#             tmp_cell+=1
#     row+=col
# book.save("/home/zhangdebo/test.xls")

a={"1":[1,2,3]}
b={"2":[4,5]}
print dict(a.items()+b.items())
c=[]
c.append(0)
c.append(2)
c.sort()
print c.sort(cmp=None, key=None, reverse=False)