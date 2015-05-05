#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2015年4月9日

@author: zhangdebo
可以一次插入版本，暂不支持增量添加
'''
import mysql.connector
from _mysql import NULL
import string
#定义urlmap 
# note或project为key
#{"note/projectname":[ip,status,...],"test2":[]...}
dic_urlmap={}

#创建的应用程序名称
applicationname="webmonitor"
#DB
dbhost_zabbix="127.0.0.1"
username_zabbix="root"
password_zabbix="1234"
#自动部署系统的库名
dbname_zabbix="zabbix" 

dbport_zabbix = 3306


#自动部署系统
dbhost_deploy="192.168.165.107"
username_deploy="deploy"
password_deploy="deploy"
#自动部署系统的库名
dbname_deploy="deploy" 
#deploy的库名
dbport_deploy = 3311

#hostid = 10084
hostid=10106
applicationid=469

items_name1 = "Response code for step \"$2\" of scenario \"$1\"."
items_name2 = "Response time for step \"$2\" of scenario \"$1\"."
items_name3 = "Download speed for step \"$2\" of scenario \"$1\"."
config_zabbix={'host':dbhost_zabbix,#默认127.0.0.1  
        'user':username_zabbix, 
        'password':password_zabbix,  
        'port':dbport_zabbix ,#默认即为3306  
        'database':dbname_zabbix,
        'charset':'utf8'#默认即为utf8  
        }

config_deploy={'host':dbhost_deploy,#默认127.0.0.1  
            'user':username_deploy, 
            'password':password_deploy,  
            'port':dbport_deploy ,#默认即为3306  
            'database':dbname_deploy,  
            'charset':'utf8'#默认即为utf8  
        }

"""
    遍历deploy中的url
"""
def queryDeploy():
    try:
        conn= mysql.connector.connect(**config_deploy)
        cursor = conn.cursor()
        sql="select * from deploy_chk_hosts where type='weburl'"
        cursor.execute(sql)
        for i in cursor.fetchall():
            urlMaps(i)
        #to insert
    except mysql.connector.Error as e:
        print 'query Deploy fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()
        insertToZabbix()
        #print dic_urlmap


"""
    查询ids表
"""
def queryIds(table,field):
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor()
        sql="select nextid from ids where table_name = %s and field_name= %s"
        data=(table,field)
        cursor.execute(sql,data)
        #print cursor.fetchone()[0]
        return cursor.fetchone()[0]
    except mysql.connector.Error as e:
        print 'queryIDs fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()
    
"""
    更新ids表
"""
def updateIds(table,field,nextid):
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor()
        sql="update ids set nextid  = %s where table_name = %s and field_name= %s"
        data=(nextid,table,field)
        cursor.execute(sql,data)
        conn.commit()
    except mysql.connector.Error as e:
        print 'updateIDs fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()

"""
    处理deploy里面的url数据，相同的note或projectname则为一组
    {u'getjar_service_detect': [
        [
            u'Getjar\u4e1a\u52a1\uff0c\u8bf7\u76f4\u63a5\u8054\u7cfb\u4e01\u6797\u6ce21858873127',
            u'http: //pbasuser01.dc.gomo.com: 9088/getjar_service_detect/CheckingAvailable?service=promoted_apps',
            1
        ],]}
"""
def urlMaps(urlcp):
    if dic_urlmap.get(urlcp[4]):
        tmp=urlcp[4]
        isNum=tmp[-1]
        nextKey=""
        if isNum.isdigit():
            nextKey=string.atoi(isNum)+1
        else:
            nextKey="1" 
        dic_urlmap[urlcp[4]+str(nextKey)] = [[urlcp[4],urlcp[2],urlcp[6]]]
    elif dic_urlmap.get(urlcp[12]):
        tmp=urlcp[12]
        isNum=tmp[-1]
        nextKey=""
        if isNum.isdigit():
            nextKey=string.atoi(isNum)+1
        else:
            nextKey="1" 
        dic_urlmap[urlcp[12]+str(nextKey)] = [[urlcp[12],urlcp[2],urlcp[6]]]
    else:
        if urlcp[4]:
            dic_urlmap[urlcp[4].title()] = [[urlcp[4],urlcp[2],urlcp[6]]]
        elif urlcp[12]:
            dic_urlmap[urlcp[12].title()] = [[urlcp[12],urlcp[2],urlcp[6]]]
        else:
            dic_urlmap[urlcp[2]] = [[urlcp[2],urlcp[2],urlcp[6]]]

"""
    去掉重复的url数据
"""
def duplicate(dicMap):
    dic_tmp={}
    for i in dicMap.keys():
        dic_tmp[i] = list(set(dicMap.get(i)))
    print dic_tmp
    return dic_tmp   

def insertToZabbix():
    try:
        print dic_urlmap
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        for i in dic_urlmap.keys():
            step_index = 1
            httptestid=1 #临时
            if querDuplicateHttpTest(i,hostid) > 0:
                print "WEB拨测大项已经存在",i,"，跳过插入，进入步骤"
                #查出id等
                #insertHttptest(querDuplicateHttpTest(i,hostid),i,cursor)
                httptestid=querDuplicateHttpTest(i,hostid)
            else:
                print "____开始处理",i,"WEB拨测大项"
                httptestid=queryIds("httptest","httptestid")+1
                insertHttptest(httptestid,i,cursor)
            for j in dic_urlmap.get(i):
                #step插入
                if querDuplicateHttpStep(j[1],httptestid):
                    print "        ---已存在",j[0],"的步骤跟url，跳过插入"
                else:
                    httpstepid = queryIds("httpstep", "httpstepid")+1
                    sql_step = """
                                        insert into httpstep(httpstepid,httptestid,name,no,url,timeout,posts,
                                        required,status_codes,variables,follow_redirects,retrieve_mode,headers)
                                         values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                        """
                    #data2=[httpstepid,httptestid,j[0].encode("utf8"),step_index,j[1],15,"","","","",1,0,""]
                    if i == j[0]:
                        j[0]=j[0]+str(step_index)
                    data2 = [httpstepid,httptestid,j[0],step_index,j[1],15,"","","200","",1,0,""]
                    cursor.execute(sql_step,data2)
                    step_index=step_index+1
                    updateIds("httpstep", "httpstepid",httpstepid)
                    
                    
                    #插入小的web item
                    itemid=queryIds("items", "itemid")
                    sql_item = """
                                        insert into items(itemid,type,hostid,name,key_,delay,history,trends,status,value_type,units)
                                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                    """
                    
                    data_item1=[itemid+1,9,hostid,items_name1,"web.test.rspcode["+i+","+j[0]+"]",60,30,90,0,3,""]
                    data_item2=[itemid+2,9,hostid,items_name2,"web.test.time["+i+","+j[0]+"]",60,30,90,0,0,"s"]
                    data_item3=[itemid+3,9,hostid,items_name3,"web.test.in["+i+","+j[0]+"]",60,30,90,0,0,"Bps"]
                    if querDuplicateItems(data_item1[4], hostid) or querDuplicateItems(data_item2[4], hostid)  or querDuplicateItems(data_item3[4], hostid):
                        continue
                    else:
                        cursor.execute(sql_item,data_item1)
                        cursor.execute(sql_item,data_item2)
                        cursor.execute(sql_item,data_item3)
                        conn.commit()
                        updateIds("items", "itemid", itemid+3)
                        
                        #插入httpstepitem表
                        httpstepitemid = queryIds("httpstepitem", "httpstepitemid")
                        sql_stepitem = """
                                                    insert into httpstepitem values(%s,%s,%s,%s)
                                                    """
                        data_stepitem1 =[httpstepitemid+1,httpstepid,itemid+1,0]
                        data_stepitem2 =[httpstepitemid+2,httpstepid,itemid+2,1]
                        data_stepitem3 =[httpstepitemid+3,httpstepid,itemid+3,2]
                        updateIds("httpstepitem", "httpstepitemid", httpstepitemid+3)
                        
                        cursor.execute(sql_stepitem,data_stepitem1)
                        cursor.execute(sql_stepitem,data_stepitem2)
                        cursor.execute(sql_stepitem,data_stepitem3)
                        conn.commit()
                    print " |______",j[0]," WEB拨测小项处理完成"
            #插入大的web item
            try:
                preitemid1= queryIds("items", "itemid")+1
                data_preitem1 = [preitemid1,9,hostid,"Last error message of scenario \"$1\".","web.test.error["+i+"]",60,30,90,0,1,""]
                if querDuplicateItems(data_preitem1[4], hostid):
                    continue
                cursor.execute(sql_item,data_preitem1)
                updateIds("items", "itemid", preitemid1)
                
                preitemid2= queryIds("items", "itemid")+1
                data_preitem2 = [preitemid2,9,hostid,"Failed step of scenario \"$1\".","web.test.fail["+i+"]",60,30,90,0,3,""]
                cursor.execute(sql_item,data_preitem2)
                updateIds("items", "itemid", preitemid2)
                
                preitemid3= queryIds("items", "itemid")+1
                data_preitem3 = [preitemid3,9,hostid,"Download speed for scenario \"$1\".","web.test.in["+i+",,bps]",60,30,90,0,0,"Bps"]
                cursor.execute(sql_item,data_preitem3)
                updateIds("items", "itemid", preitemid3)
                
                #插入httptestitem
                sql_httptestitem= "insert into httptestitem values(%s,%s,%s,%s)"
                httptestitemid = queryIds("httptestitem", "httptestitemid")
                data_httptestitem1 = [httptestitemid+1,httptestid,preitemid3,2]
                data_httptestitem2 = [httptestitemid+2,httptestid,preitemid2,3]
                data_httptestitem3 = [httptestitemid+3,httptestid,preitemid1,4]
                cursor.execute(sql_httptestitem,data_httptestitem1)
                cursor.execute(sql_httptestitem,data_httptestitem2)
                cursor.execute(sql_httptestitem,data_httptestitem3)
                updateIds("httptestitem", "httptestitemid",httptestitemid+3)
                conn.commit()
                #cursor.fetchall()
            except:
                #print j[0],"插入出错"
                continue
            print "|___",i,"WEB拨测大项处理完成","\n"
    except mysql.connector.Error as e:
        print 'insert into zabbix fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()
        print "所有任务已处理完成！！！"
   
    
"""
    查询该主机上的一个application id，如果没有则创建一个名为“webmonitor”的
"""
def getAppId(hostid):
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql="select applicationid from applications where hostid = %s and name = 'webmonitor'"
        cursor.execute(sql, [hostid])
        appid = cursor.fetchone()
        if appid:
            #return appid[0]
            return 469
        else:
            print "empty,will create"
            sql_insert = """ insert into applications(applicationid,hostid,name) 
                                        values(%s,%s,%s) """
            next_applicationid = queryIds("applications", "applicationid")+1
            data=[next_applicationid,hostid,applicationname]
            print data
            cursor.execute(sql_insert,data)
            conn.commit()
            updateIds("applications", "applicationid", next_applicationid)
            #return next_applicationid
            return 469
        
    except mysql.connector.Error as e:
        print 'query appid fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()
        

"""
    查询httptest表，查看是否已经存在了
"""
def querDuplicateHttpTest(name,hostid):
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql="select httptestid from httptest where name like %s and hostid= %s"
        data=(name,hostid)
        cursor.execute(sql,data)
        httptestid = cursor.fetchone()
        if httptestid:
            return httptestid[0]
        else:
            return 0
    except mysql.connector.Error as e:
        print 'queryHttpTest fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()


"""
    查询httpstep表，查看是否已经插入了
"""
def querDuplicateHttpStep(url,httptestid):
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql="select count(1) from httpstep where  url= %s and httptestid = %s"
        data=(url,httptestid)
        cursor.execute(sql,data)
        httpstepid =  cursor.fetchone()[0]
        if httpstepid > 0:
            return True
        else:
            return False
        
    except mysql.connector.Error as e:
        print 'queryHttpStep fails!{}'.format(e)
#     except:
#         print "error"
    finally:
        conn.close()
        cursor.close()


"""
    查询items表，查看是否已经插入了
"""
def querDuplicateItems(key,hostid):
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql="select count(1) from items where key_ = %s and hostid= %s"
        data=(key,hostid)
        cursor.execute(sql,data)
        countitem =  cursor.fetchall()[0][0]
        if countitem > 0:
            return True
        else:
            return False
        
    except mysql.connector.Error as e:
        print 'queryHttpStep fails!{}'.format(e)
#     except:
#         print "error"
    finally:
        conn.close()
        cursor.close()



def insertHttptest(httptestid,i,cursor):
        sql='''insert into httptest(httptestid,name,applicationid,delay,status,agent,hostid) 
                values(%s,%s,%s,%s,%s,%s,%s)'''
        data=[httptestid,i,getAppId(hostid),60,0,"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",hostid]
        #print data
        cursor.execute(sql,data)
        #conn.commit()
        updateIds("httptest", "httptestid",httptestid)

if __name__ == "__main__":
    #queryIds("httptest","httptestid")
    queryDeploy()
    #testInsert()
    #getAppId(hostid)
    
    
    
    
    