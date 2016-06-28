import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import calendar
import matplotlib.pyplot as plt
from matplotlib import dates

SP2_ID = 'ECSP2'

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute(('SELECT UNIX_UTC_ts,sample_flow FROM whi_hk_data'))
hk_data = cursor.fetchall()

cnx.close()
hk_data.sort()
date = [dates.date2num(datetime.utcfromtimestamp(row[0])) for row in hk_data]
param = [row[1] for row in hk_data]

hfmt  = dates.DateFormatter('%Y%m%d %H:%M')




fig = plt.figure(figsize=(20,6))
ax1 = fig.add_subplot(111)
ax1.scatter(date,param, color = 'darkgrey')
ax1.xaxis.set_major_formatter(hfmt)
ax1.set_xlim(datetime(2009,6,25),datetime(2012,9,10))

#ax1.axhline(22)
#ax1.axvline(datetime(2014,9,9))
ax1.set_ylim(2,200)
ax1.set_ylabel('SP2 #44 yag power' )

plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Alert Data/44_hk_yag_power.png', bbox_inches='tight')

plt.show()