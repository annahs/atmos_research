import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import dates
from pprint import pprint
import calendar
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math


SP2_ID = 17
start = datetime(2011,4,1)
end =   datetime(2012,9,27)

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

UNIX_start = calendar.timegm(start.utctimetuple())
UNIX_end = calendar.timegm(end.utctimetuple())


cursor.execute('''(SELECT 
	UNIX_UTC_ts_int_start,  
	UNIX_UTC_ts_int_end,  
	ratio_80_90, 
	ratio_100_110, 
	ratio_120_130, 
	ratio_140_150, 
	ratio_160_170, 
	ratio_180_190, 
	ratio_200_210, 
	ratio_220_230
	FROM alert_color_ratios
	WHERE
	UNIX_UTC_ts_int_start >= %s
	AND UNIX_UTC_ts_int_end < %s
	AND SP2_ID = %s)''',
	(UNIX_start,UNIX_end, SP2_ID))
data  = cursor.fetchall()
	
cnx.close()

date = [datetime.utcfromtimestamp(row[0]) for row in data]
ratio_80_90   = [row[2] for row in data]
ratio_100_110 = [row[3] for row in data]
ratio_120_130 = [row[4] for row in data]
ratio_140_150 = [row[5] for row in data]
ratio_160_170 = [row[6] for row in data]
ratio_180_190 = [row[7] for row in data]
ratio_200_210 = [row[8] for row in data]
ratio_220_230 = [row[9] for row in data]

hfmt = dates.DateFormatter('%Y%m%d')

fig = plt.figure(figsize=(20,6))
ax1 = fig.add_subplot(111)
ax1.xaxis.set_major_formatter(hfmt)
#ax1.scatter(date,ratio_80_90  ,marker ='o',label = '80_90nm',color = 'grey')
#ax1.scatter(date,ratio_100_110,marker ='o',label = '100_110nm',color = 'g')
ax1.scatter(date,ratio_120_130,marker ='o',label = '120_130nm',color = 'r')
ax1.scatter(date,ratio_140_150,marker ='o',label = '140_150nm',color = 'b')
ax1.scatter(date,ratio_160_170,marker ='o',label = '160_170nm',color = 'm')
ax1.scatter(date,ratio_180_190,marker ='o',label = '180_190nm',color = 'c')
ax1.scatter(date,ratio_200_210,marker ='o',label = '200_210nm',color = 'k')
ax1.scatter(date,ratio_220_230,marker ='o',label = '220_230nm',color = 'orange')
ax1.set_ylim(0.75,2.5)
ax1.axvline(datetime(2014,9,9))
ax1.set_ylabel('BB/NB incandescence ratio - SP2#58')
ax1.set_xlabel('date')
ax1.set_xlim(start,end)
plt.legend(title = 'rBC size bins')

plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Alert Data/2014-2015_color_ratio.png', bbox_inches='tight')

plt.show()
	

