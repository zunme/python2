import requests
from bs4 import BeautifulSoup
import urllib.parse

from urllib import parse
import pymysql.cursors
import time
import json
from requests_toolbelt.utils import dump
import datetime
import re
from config import conf

totalpage = 0

def daum(addr) :
    headers = {'Authorization': 'KakaoAK ' + conf.daum_key}
    #res = requests.get( daum_url + parse.quote(addr) , headers=headers );
    p = re.compile('\(.*?\)')
    p1 = re.compile('\[.*?\]')
    addr = re.sub(p, "", addr)
    addr = re.sub(p1, "", addr)

    req = urllib.request.Request(conf.daum_url + parse.quote(addr))
    req.add_header('Authorization', 'KakaoAK ' + conf.daum_key)

    try:
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
             retData = response.read().decode('utf-8')
             jsond = json.loads(retData)
             if jsond['meta']['total_count'] == 1 :
                address = jsond['documents'][0]['address']
                lat = address['y']
                lng = address['x']
                law_dong = address['b_code']
                return [law_dong, lat, lng]
        return ['','','']
    except Exception as e:
        return ['','','']

def upateGeo() :
    with conn.cursor() as cursor:
        sql='SELECT BROKER_OFFICE_INFO_IDX, FULL_ADDR FROM ' + conf.office_table + ' where searched = "N" '
        cursor.execute(sql)
        rows = cursor.fetchall()
    for row in rows :
        daumdata = daum( row[1].replace("(*)", "")  )
        with conn.cursor() as cursor:
            sql = "update " + conf.office_table + " set LAW_CODE = %s, LAT = %s, LNG = %s , searched='Y' where BROKER_OFFICE_INFO_IDX = %s"
            cursor.execute(sql, (daumdata[0],daumdata[1],daumdata[2],row[0]))
        conn.commit()

def init ():
    global totalpage
    global conn
    totalpage = 0

    with conn.cursor() as cursor:
        sql = 'DELETE FROM potal_log WHERE logtime <  DATE_SUB( NOW(), INTERVAL -14 DAY)'
        cursor.execute(sql)
    conn.commit()

    with conn.cursor() as cursor:
        sql='SELECT SIDO_CODE, SIGUNGU_CODE FROM TB_CB_ADDR a WHERE a.USE_YN ="Y" AND SIGUNGU_CODE != "" and DONG_CODE=""'
        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result :
            getallpage( row[0], row[1] )
    return

def getallpage(sido, sigungu ) :
    global totalpage
    with conn.cursor() as cursor:
        sql='SELECT * FROM potal_prc_log where sigungu = %s '
        cursor.execute(sql, (sigungu ))
        logres = cursor.fetchone()

    if  logres == None :
        page = 1
        geturl(sido,sigungu, page )
        with conn.cursor() as cursor:
            sql = "insert into potal_prc_log (sigungu,totalpage,done ) values( %s, %s, %s)"
            cursor.execute(sql, (sigungu,totalpage,'1'))
        conn.commit()
        print('[ '+ sigungu + ' ] TOTAL ' + str(totalpage) )

    elif logres[1] != logres[2] and  logres[2] < logres[1]:
        page = int(logres[2])
        totalpage = logres[1]
        print('[ '+ sigungu + ' ] restart ' + str(page + 1)+ ' TOTAL ' + str(totalpage) )
    else :
        print('[ '+ sigungu + ' ] was done ' )
        return

    if totalpage > 1 :
        a = range( page + 1 , totalpage+1 )
        for page in a :
            time.sleep(conf.page_sleep_time)
            geturl(sido,sigungu,page)

    totalpage = 0
    time.sleep(conf.sigungu_sleep_time)

def geturl(sido, sigungu,page) :
    global totalpage
    global s

    url = conf.geturl_str + str(page)
    data = {'shInit': 'N', 'pageIndex': '1', 'shSido': sido, 'shSigungu': sigungu, 'shDong': '', 'shSelect': '1', 'shWord': '', 'shWord1': '', 'shWord2': '', 'shWord3': '', 'shSelect3': '', 'orderSelect': '1', 'orderSelect1': '0', 'pageSize': '10'}
    res = s.post(url, data=data)
    html = res.text
    getdata(html)
    with conn.cursor() as cursor:
        sql = "update potal_prc_log set done = %s where sigungu = %s"
        cursor.execute(sql, (page,sigungu))
    conn.commit()
    upateGeo()
    if page > 1 :
        print ('   page: '+ str(page))
    if totalpage < 1 :
        gettltalpage(html)

def gettltalpage(html) :
    global totalpage
    soup = BeautifulSoup(html, 'html.parser')
    total = soup.select('#searchVO > div.bl_table > div.global-btn-wrap > p > span')[0].get_text()
    total = int(total.replace(',', ''))
    if total > 0 :
        totalpage = (total // 10) + 1
    else :
        totalpage = 1
    return

def getdata(html) :
    soup = BeautifulSoup(html, 'html.parser')
    tbody =  soup.select('#searchVO > div.bl_table > table > tbody')[0]
    trs = tbody.find_all('tr')
    for row in trs :
        cell = row.find_all('td')
        d_num = cell[1].get_text().strip();
        d_office = cell[2].get_text().strip();
        d_addr = cell[3].get_text().strip();
        d_name = cell[4].get_text().strip();
        d_phone = cell[5].get_text().strip();
        d_status = cell[7]['title']
        #getGeoData(d_addr)
        with conn.cursor() as cursor:
            sql='INSERT INTO ' + conf.office_table + ' (BROKER_OFFICE_CODE,BROKER_OFFICE_NAME,BROKER_NAME,BROKER_PHONE,BROKER_STATUS,FULL_ADDR ) values (%s , %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE BROKER_STATUS = %s'
            cursor.execute(sql, (d_num,d_office,d_name,d_phone,d_status,d_addr,d_status ))
        conn.commit()

conn = pymysql.connect(host=conf.db_host,
        user=conf.db_user,
        password=conf.db_pwd,
        db=conf.db_db,
        charset=conf.db_char)

with conn.cursor() as cursor:
    sql = 'SELECT IFNULL( COUNT(1) ,0) AS cnt from potal_log a WHERE a.logtime > CURDATE()'
    cursor.execute(sql)
    logcnt = cursor.fetchone()
if  int(logcnt[0]) > 0 :
    print("there is today log")
    exit()

s = requests.Session()
s.headers.update({'referer': conf.start_referer})
init()

with conn.cursor() as cursor:
    sql = "TRUNCATE potal_prc_log"
    cursor.execute(sql)
conn.commit()
with conn.cursor() as cursor:
    sql = 'INSERT into potal_log ( logtime, isDone) VALUES ( NOW(), "Y")' 
    cursor.execute(sql)
conn.commit()

upateGeo()
conn.close()

