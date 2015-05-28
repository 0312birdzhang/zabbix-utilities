#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2015年5月28日

@author: zhangdebo
'''

 
import urllib2
import re
import os
 
def getMeinv():
    # 首先应该分页解析所有的链接和名字
    # 定义页码
    page = 1
    # 请求数据
    responseHtml = getHtml('http://sexy.faceks.com/?page=' + str(page))
    # 解析出数据的路径和文件夹名称
    linkAndName = getLinkAndName(responseHtml)
    print "len:",len(linkAndName)
    # 当找出的数据大于0的时候进入循环
    while(len(linkAndName) > 0):
        # 循环解析每个链接的数据
        for l in linkAndName:
            print l[0],l[1]
            fileDirReg = r'<.*>'
            fileDirPatter = re.compile(fileDirReg)
            fileDirFindList = re.findall(fileDirPatter,l[1])
            fileName = l[1]
            print fileDirFindList
            for f in fileDirFindList:
                fileName = fileName.replace(f, "")
            fileName = fileName.replace('&nbsp;', "")
            if not fileName:
                fileName = '没有名称'
            makeDir(fileName)
            try:
                picResponseHtml = getHtml(l[0])
                picList = getImageUrl(picResponseHtml)
                for p in picList:
                    writeImage(fileName,p)
            except:
                continue
 
        page += 1
        responseHtml = getHtml('http://sexy.faceks.com/?page=' + str(page))
        linkAndName = getLinkAndName(responseHtml)
 
 
 
 
 
 
#得到网页源码
def getHtml(reqUrl):
    # 请求网络 8s 超时，如果出现各种异常，重新请求，累计5次返回失败
    try:
        response = urllib2.urlopen(reqUrl, timeout=8)
    except:
        for i in xrange(4):
            try:
                response = urllib2.urlopen(reqUrl, timeout=8)
            except:
                continue
            else:
                return response.read()
                break
    else:
        return response.read()
 
#得到返回的链接和名称
def getLinkAndName(responseHtml):
    reg = r'<a class="img" href="(.*)">[\s]*<img src=".*" />[\s]*</a>[\s]*</div>[\s]*<div class="text"><p>(.*)</p>'
    pattern=re.compile(reg)
    findList = re.findall(pattern,responseHtml)
    return findList
 
def getImageUrl(responseHtml):
    reg = r'<img src="(.*)"/>'
    pattern=re.compile(reg)
    findList = re.findall(pattern,responseHtml)
    return findList
 
def makeDir(dirName):
    dirPath = os.getcwd() + '/' + dirName
    if not os.path.exists(dirPath):
        print '文件夹不存在，创建文件夹:' , dirName
        os.mkdir(dirPath)
    else:
        print dirName,'以存在'
 
def writeImage(dirName,url):
    dirPath = os.getcwd() + '/' + dirName
    print '正在写出' + os.path.basename(url)
    try:
        r = urllib2.urlopen(url, timeout=8)
        with open(dirPath + '/' + os.path.basename(url), "wb") as f:
            f.write(r.read())
    except:
        for i in xrange(4):
            try:
                #urllib.urlretrieve(url,dirPath + '/' + os.path.basename(url))
                r = urllib2.urlopen(url, timeout=8)
                with open(dirPath + '/' + os.path.basename(url), "wb") as f:
                    f.write(r.read())
            except:
                continue
            else:
                break
 
 
if __name__ == '__main__':
    getMeinv();