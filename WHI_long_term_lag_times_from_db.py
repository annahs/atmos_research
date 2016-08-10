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

date1 = datetime(2009,7,1,10)
date2 = datetime(2010,8,31)
date3 = datetime(2012,5,1)
span = 1
UNIX_UTC_ts1 = calendar.timegm(date1.utctimetuple())
UNIX_UTC_ts2 = calendar.timegm(date2.utctimetuple())
UNIX_UTC_ts3 = calendar.timegm(date3.utctimetuple())

lags = []

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#cursor.execute(('''SELECT pd.BB_incand_pk_pos,pd.BB_scat_pk_pos, pd.sp2b_file, pd.file_index,pd.BB_scat_pkht 
#	FROM whi_sp2_particle_data pd
#	JOIN whi_hysplit_hourly_data hy on 
#	WHERE pd.BB_scat_pkht > %s 
#	AND pd.UNIX_UTC_ts_int_start >= %s 
#	AND pd.UNIX_UTC_ts_int_start < %s'''),
#	(20,UNIX_UTC_ts1,(UNIX_UTC_ts2)))

cursor.execute(('''SELECT 
    pd.BB_incand_pk_pos,
    pd.BB_scat_pk_pos,
    pd.sp2b_file,
    pd.file_index,
    pd.BB_scat_pkht,
    hy.cluster_number_6h
FROM
    whi_sp2_particle_data pd,
    whi_hysplit_hourly_data hy
WHERE
    pd.BB_scat_pkht > %s
		AND pd.instrument_ID = %s 
        AND (hy.cluster_number_6h = %s OR hy.cluster_number_6h = %s )
        AND  pd.UNIX_UTC_ts_int_start BETWEEN hy.UNIX_UTC_start_time AND hy.UNIX_UTC_end_time'''),
		(20,'UBCSP2',2,7))
		

data = cursor.fetchall()
print len(data)
for row in data:
	i_pk = row[0]
	s_pk = row[1]
	sp2b_file = row[2]
	file_index = row[3]
	s_pk_ht = row[4]
	lag = (i_pk-s_pk)*0.2
	if (-10< lag < 10) and s_pk_ht > 20:
		lags.append(lag)
		

print len(lags)
cnx.close()

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax1.hist(lags, bins = 60)

plt.show()

