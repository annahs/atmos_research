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


start_time = datetime(2015,4,10,14,0)
end_time = datetime(2015,4,10,17,0)


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

hfmt = dates.DateFormatter('%H:%M:%S')
display_minute_interval = 60

ax1 = fig.add_subplot(111)

ax1.plot(time_stamp,sample_flow, color = 'b')#,linewidth=1)
ax1.set_ylabel('sample_flow')
ax1.set_xlabel('time')
ax1.xaxis.set_major_formatter(hfmt)
ax1.xaxis.set_major_locator(dates.MinuteLocator(interval = display_minute_interval))
#ax1.set_ylim(0.9,1.8)

ax2 = ax1.twinx()
ax2.set_ylabel('yag_power')
ax2.plot(time_stamp,yag_power, color='r')
#ax2.set_ylim(0,6000)

ax3 = ax1.twinx()
ax3.set_ylabel('sheath_flow')
ax3.plot(time_stamp,sheath_flow, color='g', linewidth=1)
ax3.axhline(850)
ax3.axhline(400)

#ax4 = ax1.twinx()
#ax4.set_ylabel('yag_xtal_temp')
#ax4.plot(time_stamp,yag_xtal_temp, color='m',alpha=0.2)

plt.show()
cnx.close()