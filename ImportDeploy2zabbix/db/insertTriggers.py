#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2015年4月13日

@author: zhangdebo
@note: 跟进导入的web监控项，自动创建关联触发器
'''
import mysql.connector
from dbconn import queryIds
from dbconn import updateIds
#DB
dbhost_zabbix="127.0.0.1"
username_zabbix="root"
password_zabbix="1234"
#自动部署系统的库名
dbname_zabbix="zabbix" 

dbport_zabbix = 3306

config_zabbix={'host':dbhost_zabbix,#默认127.0.0.1  
        'user':username_zabbix, 
        'password':password_zabbix,  
        'port':dbport_zabbix ,#默认即为3306  
        'database':dbname_zabbix,
        'charset':'utf8'#默认即为utf8  
        }

#告警级别
priority=4

"""
    {"key":[itemid,itemid],}
"""
dic_triggerMap={}
"""
    遍历Items中的web监控项
"""
def queryItems():
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor()
        sql="""
                select key_,group_concat(itemid) from items 
                where type=9 and name not in ('Last error message of scenario \"$1\".','Failed step of scenario \"$1\".','Download speed for scenario \"$1\".')
                and hostid in (%s,%s,%s)
                group by key_
    """
        data = [10084,10107,10108]
        cursor.execute(sql,data)
        """
            "web.test.rspcode["+i+","+j[0]+"]",60,30,90,0,3,""]
            "web.test.time["+i+","+j[0]+"]",60,30,90,0,0,"s"]
             "web.test.in["+i+","+j[0]+"]",60,30,90,0,0,"Bps"]
        """
        for i in cursor.fetchall():
            dic_triggerMap[i[0]] = i[1]
    except mysql.connector.Error as e:
        print 'query Items fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()
        insertTriggersAndFunctions()

"""
    插入triggers表
"""
def insertTriggersAndFunctions():
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor()
        sql="""
                insert into triggers(triggerid,expression,description,priority,type,flags)
                 values(%s,%s,%s,%s,%s,%s)  
                """
        
        #根据key的类型，拼接不同的告警规则
        #如过是time，则是小于100ms告警等
        for i in dic_triggerMap.keys():
            functionid = queryIds("functions", "functionid")+1
            triggerid = queryIds("triggers", "triggerid") +1
            list_itemid  = dic_triggerMap.get(i).split(",")
            if  len(list_itemid) == 0:
                print "监控项不存在，跳过..."
                continue
            expression = ""
            triggername=""
            for j in range(len(list_itemid)):
                if i.startswith("web.test.rspcode"):
                     triggername="-返回码"
                     expression+="{%s}<>200 and " %(functionid+j)
            for j in range(len(list_itemid)):
                if i.startswith("web.test.time"):
                    triggername="-响应时间"
                    expression+="{%s} > 0.1 and " %(functionid+len(list_itemid)+j)
            for j in range(len(list_itemid)):
                if i.startswith("web.test.in"):
                    triggername="-数据获取"
                    expression+="{%s}=1 and " %(functionid+len(list_itemid)*2+j)
            if len(expression) == 0:
                print"告警规则不符合，跳过..."
                continue
            #截取掉最后一个and
            expression = expression[:-5]
            description = "WEB告警-"+queryItemName(list_itemid[0])+triggername
            data=[triggerid,expression,description,priority,1,0]
            #已经存在的跳过
            if queryTriggerName(description,list_itemid[0]):
                print "该主机上已经存在同名的触发器了，跳过"
                continue
            cursor.execute(sql,data)
            print "插入triggers表---",triggerid
            updateIds("triggers", "triggerid", triggerid)
            updateIds("functions", "functionid", functionid+len(list_itemid)*3-1)
            #插入triggers表
            #然后插入functions表
            sql_function = """
                                    insert into functions(functionid,itemid,triggerid,function,parameter)
                                    values(%s,%s,%s,%s,%s) 
                                    """
            list_itemid = dic_triggerMap.get(i).split(",")
            for j in range(len(list_itemid)):
                data_rspcode=[functionid+j,list_itemid[j],triggerid,"last",0]
                cursor.execute(sql_function,data_rspcode)
                data_rstime=[functionid+len(list_itemid)+j,list_itemid[j],triggerid,"last",0]
                cursor.execute(sql_function,data_rstime) #再次执行
                data_nodata=[functionid+len(list_itemid)*2+j,list_itemid[j],triggerid,"nodata",180]
                cursor.execute(sql_function,data_nodata)
                print "___插入functions表"
        conn.commit()
        #要先插triggers表，所以再执行一遍。。。
    except mysql.connector.Error as e:
        print 'insert  fails!{}'.format(e)
        conn.rollback()
    finally:
        conn.close()
        cursor.close()
        print "处理完成！！！"


"""
    查询item name
"""
def queryItemName(itemid):
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql="""
                select hs.name from httpstep hs
                left join httpstepitem hsi
                on hs.httpstepid = hsi.httpstepid
                where hsi.itemid = %s
        """
        data=[itemid]
        cursor.execute(sql,data)
        countitem =  cursor.fetchone()
        if countitem:
            return countitem[0].encode("utf8")
        else:
            return ""
    except mysql.connector.Error as e:
        print 'queryItemName fails!{}'.format(e)
#     except:
#         print "error"
    finally:
        conn.close()
        cursor.close()

"""
    查询trigger name
"""
def queryTriggerName(description,itemid):
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql="""
                select count(1) from triggers t
                left join functions f
                on t.triggerid = f.triggerid
                left join items i 
                on i.itemid = f.itemid
                where t.description = %s
                and i.hostid = (
                select hostid from items 
                where itemid = %s
)
                group by hostid
            """
        data=[description,itemid]
        cursor.execute(sql,data)
        countitem =  cursor.fetchone()
        if countitem > 0 :
            #该主机上已经存在相同描述的触发器名了
            return True
        else:
            return False
    except mysql.connector.Error as e:
        print 'queryItemName fails!{}'.format(e)
#     except:
#         print "error"
    finally:
        conn.close()
        cursor.close()
        
if __name__ == '__main__':
    queryItems()