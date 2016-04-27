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
import matplotlib.cm as cm


SP2_ID = 58
start = datetime(2013,9,27)
end =   datetime(2013,11,1)
UNIX_start = calendar.timegm(start.utctimetuple())
UNIX_end = calendar.timegm(end.utctimetuple())

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute(('SELECT FF_gauss_width,FF_peak_posn,actual_zero_x_posn,actual_scat_amp FROM alert_leo_params_from_nonincands WHERE instrument_ID =%s and UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s '),(SP2_ID,UNIX_start,UNIX_end))
data = cursor.fetchall()

cnx.close()
data.sort()
FF_width = [row[0] for row in data]
FF_center_pos = [row[1] for row in data]
FF_zerox = [row[2] for row in data]
scat_amp = [row[3] for row in data]

print np.median(FF_width),np.mean(FF_width)
print np.median(FF_center_pos),np.mean(FF_center_pos)
print np.median(FF_zerox),np.mean(FF_zerox)

fig = plt.figure()
ax1 = fig.add_subplot(311)
ax1.hist(FF_width,bins = 80, range = (5,15), color = 'green')
#ax1.hexbin(scat_amp, FF_width,, cmap=cm.jet, gridsize = 500,mincnt=1)


ax2 = fig.add_subplot(312)
ax2.hist(FF_center_pos,bins = 80, range = (0,100), color = 'r')
#ax2.hexbin(scat_amp, FF_center_pos, cmap=cm.jet, gridsize = 500,mincnt=1)
#ax2.set_xlim(0, 60000)
#ax2.set_ylim(5, 15)


ax3 = fig.add_subplot(313)
ax3.hist(FF_zerox,bins = 80, range = (0,100), color = 'b')
#ax3.hexbin(scat_amp, FF_zerox, cmap=cm.jet, gridsize = 500,mincnt=1)



plt.show()