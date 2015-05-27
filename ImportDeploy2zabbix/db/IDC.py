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
dic_esxihost={}
#{host:[ip,cpu,mem,conn,[eth0,eth1],ip2...}
dic_value={}
dic_esxivalue={}
key_cpu="system.cpu.load[percpu,avg5]"
key_mem="system.swap.size[,pfree]"
key_conn="netstat.established"

key_esxi_cpu="hrCpuCoreUsedPer"
key_esxi_mem="hrMemoryFreePerc"
key_esxi_net="ifHC%Octets%"
key_esxi_conn=""

start_time=time.strftime("%a %b %d %H:%M:%S %Y", time.localtime()) 
"""
    查询除esxi之外的主机
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
        and it.type != 2
        GROUP BY h.`host`
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
查询esxi主机
"""
def queryEsxiHost():
    try:
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql="""
        select it.ip,h.hostid,h.`host`,h.`name`,h.available from hosts h
        left JOIN interface it
        on h.hostid = it.hostid
        where h.status = 0
        and h.flags != 2
        and it.type = 2
        GROUP BY h.`host`
        """
        cursor.execute(sql)
        for i in cursor.fetchall():
            dic_esxihost[i[1]]=[i[0],i[2]]
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
        sql_items_net="select itemid,type,value_type,hostid,key_ from items where hostid = "+str(hostid)+\
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
        if not tmp_list:
            return ()
        return tmp_list
    except mysql.connector.Error as e:
        print 'query items fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()
        
"""
查询esxi主机的监控项
"""
def queryItems_esxi(hostid,key):
    try: 
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor(buffered=True)
        sql_items="""
                        select itemid,type,value_type,`status`,key_ from items where hostid = %s
                        and key_ like %s 
                        and flags =4 
                        """
        cursor.execute(sql_items,[hostid,key])
        tmplist_esxi=[]
        for i in cursor.fetchall():
            tmplist_esxi.append(i)
        if not tmplist_esxi:
            return ()
        return tmplist_esxi
    except mysql.connector.Error as e:
        print 'query items fails!{}'.format(e)
    finally:
        conn.close()
        cursor.close()
"""
查询历史表数据
"""
def queryHistory(itemList,queryType):
    if not itemList:
        return []
    try: 
        conn= mysql.connector.connect(**config_zabbix)
        cursor = conn.cursor()
        #存储值的list
        value_list=[]
        item_type = itemList[2]
        table_hist ="trends"
        if item_type == 3 or item_type == "3":
            
            table_hist+="_uint"
        elif item_type == 0:
            pass
        queryfrom="value_avg"
        if queryType == "mem":
            queryfrom = "100 - value_avg"
        elif queryType == "net":
            queryfrom = "value_avg/1000"
        else:
            pass
        sql_hist="select "+queryfrom+" from " + table_hist+" where itemid  = %s and clock > %s and clock < %s"
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
            table_hist+="_uint"
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
    title=["hostname","IP","cpu负载(个)","内存占用(%)","连接数(个)","网卡","流量(kbps)"]
    #写入表头
    for i in xrange(len(title)):
        table.write(0,i,title[i])
    #table.write_merge(0,0,5,6,"流量峰值(kbps)")
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
    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1
    style = xlwt.XFStyle()
    style.borders = borders 
    #dic_all=dict(dic_value.items()+dic_esxivalue.items())
    dic_all= dict(dic_value, **dic_esxivalue)
    for i,y in dic_all.items():
        col=1
        if len(y) >2 and y[2]:
            col=len(y[2])
#         table.write_merge(row,row+col-1,0,0,i)
#         table.write_merge(row,row+col-1,1,1,y[0])
#         table.write_merge(row,row+col-1,2,2,y[1])
#         table.write_merge(row,row+col-1,3,3,y[-2])
#         table.write_merge(row,row+col-1,4,4,y[-1])
        if col>1:
            tmp_cell=0
            for j,k in y[2].items():
                table.write(row,0,i)
                table.write(row,1,y[0])
                table.write(row,2,y[1])
                table.write(row,3,y[-2])
                table.write(row,4,y[-1])
                table.write(row+tmp_cell,5,j)
                table.write(row+tmp_cell,6,k)
                tmp_cell+=1
        else:
            table.write(row,0,i)
            table.write(row,1,y[0])
            table.write(row,2,y[1])
            table.write(row,3,y[-2])
            table.write(row,4,y[-1])
            table.write(row,5,"")
            table.write(row,6,"")
        row+=col
        
        
    book.save(excel_file)

def init():
    queryHost()
    if not dic_host:
        print "host empty"
        return
    for i,j in dic_host.items():
        print "处理主机:",j[1]
        #queryItems_net(i)
        itemlist_cpu=queryItems_others(i,key_cpu)
        value_cpulist=queryHistory(itemlist_cpu,"cpu")
        avg_num=numFactory(value_cpulist)
        dic_value[j[1]]=[j[0],avg_num]
        #itemlist_mem=
        #网络
        itemlist_net = queryItems_net(i)
        #print "net:",itemlist_net
        #{key_:value}
        dic_net={}
        if not itemlist_net:
            continue
        for k in itemlist_net:
            value_netlist=queryHistory(k,"net")
            avg_num=numFactory(value_netlist)
            dic_net[k[4]] =avg_num
        dic_value[j[1]].append(dic_net)
        #内存
        itemlist_mem=queryItems_others(i, key_mem)
        value_menlist=queryHistory(itemlist_mem,"mem")
        avg_num=numFactory(value_menlist)
        dic_value[j[1]].append(avg_num)
        #连接数
        itemlist_conn=queryItems_others(i, key_conn)
        value_conn=queryHistory(itemlist_conn,"")
        avg_num=numFactory(value_conn)
        dic_value[j[1]].append(avg_num)
    
    
    #开始查询esxi
    queryEsxiHost()
    print "dic_esxihost,",dic_esxihost
    if not dic_esxihost:
        print "esxi host empty"
        return
    for i,j in dic_esxihost.items():
        print "处理主机:",j[1]
        #esxi cpu
        itemlist_esxicpu=queryItems_esxi(i, key_esxi_cpu)
        dic_esxicpu=[]
        if itemlist_esxicpu:
            for k in itemlist_esxicpu:
                value_esxicpu=queryHistory(k, "cpu")
                avg_num=numFactory(value_esxicpu)
                dic_esxicpu.append(avg_num)
        else:
            dic_esxicpu.append(0)
        dic_esxivalue[j[1]]=[j[0],numFactory(dic_esxicpu)]
        #网络
        itemlist_esxinet=queryItems_esxi(i, key_esxi_net)
        dic_esxinet={}
        if itemlist_esxinet:
            for k in itemlist_esxinet:
                value_esxinet=queryHistory(k, "net")
                avg_num=numFactory(value_esxinet)
                dic_esxinet[k[4]]=avg_num
        dic_esxivalue[j[1]].append(dic_esxinet)
        #esxi mem
        itemlist_esximem=queryItems_esxi(i, key_esxi_mem)
        dic_esximem=[]
        if  itemlist_esximem:
            for k in itemlist_esximem:
                value_esximem=queryHistory(k, "mem")
                avg_num=numFactory(value_esximem)
                dic_esximem.append(avg_num)
        else:
            dic_esximem.append(0)
        dic_esxivalue[j[1]].append(numFactory(dic_esximem))
        #连接数
        #跳过
        dic_esxivalue[j[1]].append("")
       
        
    print "dic_value:",dic_value
    print "dic_esxivalue:",dic_esxivalue
    createExcel()
    print "all done!"

if __name__ == "__main__":
    init()
    