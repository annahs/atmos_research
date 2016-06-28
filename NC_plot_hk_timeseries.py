import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib import dates
from mpl_toolkits.basemap import Basemap
import calendar


flight = 'all'

flight_times = {
'science 1'  : [datetime(2015,4,5,9,0),datetime(2015,4,5,14,0),15.6500, 78.2200]	,	
'ferry 1'    : [datetime(2015,4,6,9,0),datetime(2015,4,6,11,0),15.6500, 78.2200]     ,
'ferry 2'    : [datetime(2015,4,6,15,0),datetime(2015,4,6,18,0),-16.6667, 81.6000]   ,
'science 2'  : [datetime(2015,4,7,16,0),datetime(2015,4,7,21,0),-62.338, 82.5014]    ,
'science 3'  : [datetime(2015,4,8,13,0),datetime(2015,4,8,17,0),-62.338, 82.5014]    ,
'science 4'  : [datetime(2015,4,8,17,30),datetime(2015,4,8,22,0),-70.338, 82.5014]   ,
'science 5'  : [datetime(2015,4,9,13,30),datetime(2015,4,9,18,0),-62.338, 82.0]   ,
'ferry 3'    : [datetime(2015,4,10,14,0),datetime(2015,4,10,17,0),-75.338, 81]  ,
'science 6'  : [datetime(2015,4,11,15,0),datetime(2015,4,11,22,0),-90.9408, 80.5] ,
'science 7'  : [datetime(2015,4,13,15,0),datetime(2015,4,13,21,0),-95, 80.1] ,
'science 8'  : [datetime(2015,4,20,15,0),datetime(2015,4,20,20,0),-133.7306, 67.1],
'science 9'  : [datetime(2015,4,20,21,0),datetime(2015,4,21,2,0),-133.7306, 69.3617] ,
'science 10' : [datetime(2015,4,21,16,0),datetime(2015,4,21,22,0),-131, 69.55],
'Alert calib': [datetime(2015,4,9,1,0),datetime(2015,4,9,2,15),-131, 69.55],
'Jan AD calib':   [datetime(2015,1,28,21,15),datetime(2015,1,29,5,0),-131, 69.55],
'all':   [datetime(2015,4,5,9,0),datetime(2015,4,21,22,0),-131, 69.55]
}



start_time = flight_times[flight][0]
end_time = flight_times[flight][1]

UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute(('SELECT * from polar6_hk_data_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s'),(UNIX_start_time,UNIX_end_time))
hk_data = cursor.fetchall()

time_stamp   = [dates.date2num(datetime.utcfromtimestamp(row[1])) for row in hk_data]
sample_flow  = [row[2] for row in hk_data]
yag_power    = [row[3] for row in hk_data]
sheath_flow  = [row[4] for row in hk_data]
yag_xtal_temp= [row[5] for row in hk_data]


####plotting	
#timeseries
fig = plt.figure()

hfmt = dates.DateFormatter('%m-%d')
display_minute_interval = 1

ax1 = fig.add_subplot(111)

ax1.scatter(time_stamp,sheath_flow, color = 'b')#,linewidth=1)
ax1.set_ylabel('sheath_flow')
ax1.set_xlabel('2015')
ax1.xaxis.set_major_formatter(hfmt)
ax1.xaxis.set_major_locator(dates.DayLocator(interval = display_minute_interval))
ax1.set_ylim(500,800)

#ax2 = ax1.twinx()
#ax2.set_ylabel('yag_power')
#ax2.plot(time_stamp,yag_power, color='r')
#ax2.set_ylim(3,6)

#ax3 = ax1.twinx()
#ax3.set_ylabel('sheath_flow')
#ax3.plot(time_stamp,sheath_flow, color='g', linewidth=1)
#ax3.axhline(850)
#ax3.axhline(400)
#ax3.set_ylim(300,1020)

#ax4 = ax1.twinx()
#ax4.set_ylabel('yag_xtal_temp')
#ax4.plot(time_stamp,yag_xtal_temp, color='m',alpha=0.2)
plt.xlim(dates.date2num(start_time),dates.date2num(end_time))

plt.show()
cnx.close()