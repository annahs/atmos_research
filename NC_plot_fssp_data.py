import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import pickle
import math
import calendar
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib import dates


cloud_droplet_conc = 0.5 #threshold droplet conc from FSSP for in-cloud conditions

flight_times = {
'science 1'  : [datetime(2015,4,5,9,43),datetime(2015,4,5,13,48),15.6500, 78.2200, 'Longyearbyen (sc1)']	,	   #longyearbyen
##'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
##'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
#'science 2'  : [datetime(2015,4,7,16,31),datetime(2015,4,7,20,48),-62.338, 82.5014,'Alert (sc2-5)']    ,  #Alert
#'science 3'  : [datetime(2015,4,8,13,51),datetime(2015,4,8,16,43),-62.338, 82.5014,'Alert (sc2-5)']    ,  #Alert
#'science 4'  : [datetime(2015,4,8,17,53),datetime(2015,4,8,21,22),-70.338, 82.5014,'Alert (sc2-5)']   ,   #Alert
#'science 5'  : [datetime(2015,4,9,13,50),datetime(2015,4,9,17,47),-62.338, 82.0,'Alert (sc2-5)']   ,      #Alert
##'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
#'science 6'  : [datetime(2015,4,11,15,57),datetime(2015,4,11,21,16),-90.9408, 80.5,'Eureka (sc6-7)'] ,	   #eureka
#'science 7'  : [datetime(2015,4,13,15,14),datetime(2015,4,13,20,52),-95, 80.1,'Eureka (sc6-7)'] ,          #eureka
#'science 8'  : [datetime(2015,4,20,15,49),datetime(2015,4,20,19,49),-133.7306, 67.1,'Inuvik (sc8-10)'],     #inuvik
#'science 9'  : [datetime(2015,4,20,21,46),datetime(2015,4,21,1,36),-133.7306, 69.3617,'Inuvik (sc8-10)'] ,  #inuvik
#'science 10' : [datetime(2015,4,21,16,07),datetime(2015,4,21,21,24),-131, 69.55,'Inuvik (sc8-10)'],         #inuvik
#
}

start_time = datetime(2015,4,5,9,43)
end_time = datetime(2015,4,13,20,52)
UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())

	
#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


cursor.execute(('''SELECT UNIX_UTC_ts, FSSPTotalConc
				FROM polar6_fssp_cloud_data 
				WHERE UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s '''),
				(UNIX_start_time,UNIX_end_time,))
fssp_data = cursor.fetchall()

times = []
concs = []
cloud_secs = 0
secs = 0
for row in fssp_data:
	ts = row[0] 
	fssp_conc = row[1]
	if fssp_conc >= 0.3:
		cloud_secs +=1
	else: 
		secs += 1
	times.append(dates.date2num(datetime.utcfromtimestamp(ts)))
	concs.append(fssp_conc)
	
print cloud_secs, secs, cloud_secs*100./secs
fig = plt.figure()

hfmt = dates.DateFormatter('%H:%M:%S')
display_minute_interval = 60

ax1 = fig.add_subplot(111)

ax1.plot(times,concs)#,linewidth=1)
ax1.set_ylabel('FSSP total conc (droplets per cm3)')
ax1.set_xlabel('time')
ax1.xaxis.set_major_formatter(hfmt)
ax1.xaxis.set_major_locator(dates.MinuteLocator(interval = display_minute_interval))
ax1.set_ylim(0.85,2.5)


plt.show()