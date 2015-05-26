#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2015年5月26日

@author: zhangdebo
@version: 0.1
@summary:  CPU负载(system.cpu.load[percpu,avg5])、内存占用()、连接数、网络流量

'''
import mysql.connector
import time
import xlwt

#导出的excel名
excel_file = "/home/zhangdebo/IDC.xls"
#创建的应用程序名称
#DB
# dbhost_zabbix="127.0.0.1"
# username_zabbix="root"
# password_zabbix="1234"
# #自动部署系统的库名
# dbname_zabbix="zabbix" 
#dbhost_zabbix="192.168.3.52"
dbhost_zabbix="pmysql09.rmz.gomo.com"
username_zabbix="zabbix"
password_zabbix="3G_gomo_2015"
dbname_zabbix="zabbix_new" 
dbport_zabbix = 3306

dbport_zabbix = 3306
config_zabbix={'host':dbhost_zabbix,#默认127.0.0.1  
        'user':username_zabbix, 
        'password':password_zabbix,  
        'port':dbport_zabbix ,#默认即为3306  
        'database':dbname_zabbix,
        'charset':'utf8'#默认即为utf8  
        }

#{hostid:[ip,host,[item1,item2...]]
dic_host={}
#{host:[ip,cpu,mem,conn,[eth0,eth1],ip2...}
dic_value={}

key_cpu="system.cpu.load[percpu,avg5]"
key_men=""
key_conn=""
"""
    遍历deploy中的url
"""
def queryHost():
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql="""
        select it.ip,h.hostid,h.`host`,h.`name`,h.available from hosts h
        left JOIN interface it
        on h.hostid = it.hostid
        where h.status = 0
        and h.flags != 2
        GROUP BY h.`host`
        limit 10
        """
        cursor.execute(sql)
        for i in cursor.fetchall():
            dic_host[i[1]]=[i[0],i[2]]
        #to insert
        print "hosts:",dic_host
    except mysql.connector.Error as e:
        print 'query Hosts fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()

"""
查询主机下面网络的监控项
"""
def queryItems_net(hostid):
    try: 
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql_items_net="select itemid,type,`status`,hostid,key_ from items where hostid = "+str(hostid)+\
                    " and key_ like 'net.if%' and key_  not in ( 'net.if.discovery','net.if.in[{#IFNAME}]','net.if.out[{#IFNAME}]')"
        cursor.execute(sql_items_net)
        tmplist_net=[]
        for i in cursor.fetchall():
            tmplist_net.append(i)
        return tmplist_net
    except mysql.connector.Error as e:
        print 'query items_net fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()

"""
查询其他关键字的监控项
"""
def queryItems_others(hostid,key):
    try: 
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql_items="""
                        select itemid,type,value_type,`status`,key_ from items where hostid = %s
                        and key_  = %s
                        """
        cursor.execute(sql_items,[hostid,key])
        tmp_list=cursor.fetchone()
        return tmp_list
    except mysql.connector.Error as e:
        print 'query items fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()
        
"""
查询历史表数据
"""
def queryHistory(itemList):
    if not itemList:
        return []
    try: 
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor()
        #存储值的list
        value_list=[]
        item_type = itemList[2]
        table_hist ="trends"
        if item_type == 3:
            table_hist+="_unit"
        elif item_type == 0:
            pass
        sql_hist="select value_avg from " + table_hist+" where itemid  = %s and clock > %s and clock < %s"
        current_time = time.time()
        before_time = current_time - 7*24*60*60
        data=[itemList[0],before_time,current_time]
        #print sql_hist,data
        cursor.execute(sql_hist,data)
        for i in cursor.fetchall():
            value_list.append(i[0])
        return value_list            
    except mysql.connector.Error as e:
        print 'query history fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()

def queryHistoryNet(itemList):
    if not itemList:
        return []
    try: 
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor()
        #存储值的list
        value_list=[]
        item_type = itemList[2]
        table_hist ="history"
        if item_type == 3:
            table_hist+="_unit"
        elif item_type == 0:
            pass
        sql_hist="select value from " + table_hist+" where itemid  = %s and clock > %s and clock < %s"
        current_time = time.time()
        before_time = current_time - 7*24*60*60
        data=[itemList[0],before_time,current_time]
        #print sql_hist,data
        cursor.execute(sql_hist,data)
        for i in cursor.fetchall():
            value_list.append(i[0])
        print value_list
        return value_list            
    except mysql.connector.Error as e:
        print 'query history fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()

"""
处理数据,去掉5%最大的
"""
def numFactory(listnum):
    len_num = len(listnum)
    if len_num == 0:
        return 0
    listnum.sort(reverse=True)
    cute_num=int(round(len_num*0.05))
    listnum=listnum[cute_num:len_num]
    avg_num = sum(listnum)/len_num
    return avg_num



"""
创建excel
"""
def createExcel():
    book=xlwt.Workbook(encoding='utf-8')
    table=book.add_sheet('IDC')
    title=["hostname","IP","cpu负载","内存占用","连接数"]
    #写入表头
    for i in xrange(len(title)):
        table.write(0,i,title[i])
    table.write_merge(0,0,5,6,"流量峰值")
    """
    sheet.write(top_row, left_column, 'Long Cell')
    sheet.write_merge(top_row, bottom_row, left_column, right_column,"xxx")
    """
    #{host:[ip,cpu,mem,conn,[eth0,eth1],ip2...}
    row=1
    #write_merge(x, x + m, y, w + n, string, sytle)
    #x表示行，y表示列，m表示跨行个数，n表示跨列个数，string表示要写入的单元格内容，style表示单元格样式。其中，x，y，w，h，都是以0开始计算的。
    #sheet.write_merge(3,4,1,2,"ttt")
    """
    sheet.write_merge(3,4,0,0,"ttt")
    sheet.write_merge(3,4,1,1,"123")
    """
    for i,y in dic_value.items():
        col=1
        if len(y) >2 and y[2]:
            col=len(y[2])
        table.write_merge(row,row+col-1,0,0,i)
        table.write_merge(row,row+col-1,1,1,y[0])
        table.write_merge(row,row+col-1,2,2,y[1])
        #占位用
        table.write_merge(row,row+col-1,3,3,"")
        table.write_merge(row,row+col-1,4,4,"")
        if col>1:
            tmp_cell=0
            for j,k in y[2].items():
                #eth=j.split("[")[1].split("]")[0]
                table.write(row+tmp_cell,5,j)
                table.write(row+tmp_cell,6,k)
                tmp_cell+=1
        row+=col
    
        
    book.save(excel_file)

def init():
    queryHost()
    for i,j in dic_host.items():
        #queryItems_net(i)
        itemlist_cpu=queryItems_others(i,key_cpu)
        value_cpulist=queryHistory(itemlist_cpu)
        avg_num=numFactory(value_cpulist)
        dic_value[j[1]]=[j[0],avg_num]
        #itemlist_men=
        #网络
        itemlist_net = queryItems_net(i)
        #{key_:value}
        dic_net={}
        if not itemlist_net:
            continue
        for k in itemlist_net:
            value_netlist=queryHistory(k)
            avg_num=numFactory(value_netlist)
            dic_net[k[4]] =avg_num
        dic_value[j[1]].append(dic_net)
    print "value",dic_value
    createExcel()

if __name__ == "__main__":
    init()
    
    #createExcel()