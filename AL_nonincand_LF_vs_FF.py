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
from scipy import stats
import matplotlib.cm as cm


SP2_ID = 58
start = datetime(2013,11,1)
end = datetime(2013,11,2)
UNIX_start = calendar.timegm(start.utctimetuple())
UNIX_end = calendar.timegm(end.utctimetuple())

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute(('SELECT FF_scat_amp,LF_ratio_scat_amp FROM alert_leo_params_from_nonincands WHERE instrument_ID =%s and id >%s and UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and LF_scat_amp >0'),(SP2_ID,0,UNIX_start,UNIX_end))
data = cursor.fetchall()
print len(data)
cnx.close()
data.sort()
FF = [row[0] for row in data]
LF = [row[1] for row in data]

varx = np.array(FF)
vary = np.array(LF)
mask = ~np.isnan(varx) & ~np.isnan(vary)
slope, intercept, r_value, p_value, std_err = stats.linregress(varx[mask], vary[mask])
line = slope*varx+intercept



fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.scatter(FF,LF, color = 'g')
#ax1.hexbin(FF, LF, cmap=cm.jet, gridsize = 300,mincnt=1)
ax1.plot([0,1,10,100,1000,10000,60000],[0,1,10,100,1000,10000,60000])
ax1.set_xlim(0,60000)
ax1.set_ylim(0,60000)
ax1.plot(FF,line,color='r')
ax1.text(0.1, 0.9,'r-square: ' + str(round(r_value**2,3)),transform=ax1.transAxes, color='k')
ax1.text(0.1, 0.85,'slope: ' + str(round(slope,3)),transform=ax1.transAxes, color='k')
ax1.set_ylabel('amplitude from leading edge fit')
ax1.set_xlabel('actual amplitude')


plt.show()