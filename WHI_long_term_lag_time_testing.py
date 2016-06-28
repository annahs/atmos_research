import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.cm as cm
from pprint import pprint
import calendar
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math

#need to filter on spike times, hk (flow, yag, etc), RH (for in-cloud times), local BB

start_ts = datetime(2009,7,5,12)  #2010 - 20100610   2012 - 20100405
end_ts = datetime(2012,6,1)  #2010 - 20100726   2012 - 20100601
bin_incr = 10
min_bin = 70
max_bin = 220
timestep = 1 #hours for RH and cluster filtering

#hk parameters
sample_min = 117  #117 for all 2009-2012
sample_max = 123  #123 for all 2009-2012
yag_min = 3.8  #3.8 for all 2009-2012
yag_max = 6	 #6  for all 2009-2012


#local BB times
fire_span_09s=datetime.strptime('2009/07/27', '%Y/%m/%d') #dates follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011
fire_span_09f=datetime.strptime('2009/08/08', '%Y/%m/%d') 

fire_span_10s=datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M') #jason's BC clear report
fire_span_10f=datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute('''(SELECT 
	hrly.mean_lag_time,
	hy.precip_total,
	hy.precip_first_72h,
	hy.precip_last_72h,
	hy.cluster_number_1h,
	hy.cluster_number_6h,
	met.RH
	FROM whi_sp2_hourly_data hrly
	JOIN whi_hysplit_hourly_data hy on hrly.hysplit_hourly_id = hy.id
	JOIN whi_sampling_conditions met on hrly.whi_sampling_cond_id = met.id
	WHERE
	met.RH <= %s
	AND hrly.id > %s
	AND hrly.mean_lag_time IS NOT NULL)''',
	(101,0))
	
hrly_data = cursor.fetchall()

npac  = []
spac  = []
wpac  = []
ncan  = []
test  = []
hp  = []
lp  = []

for row in hrly_data:
	thickly_coated = False
	heavy_precip = False

	lag = row[0]
	precip_total = row[1]
	precip_first_72h = row[2]
	precip_last_72h = row[3]
	cluster_number_1h = row[4] 
	cluster_number_6h = row[5] 
	RH = row[6] 
	
	if RH >= 90:
		heavy_precip = True
		hp.append(lag)
	else:
		lp.append(lag)
		
	if lag >= 1:
		thickly_coated = True
	
	
	if cluster_number_6h in [1,3,5,10]:
		npac.append([lag,precip_total,heavy_precip,thickly_coated])
		test.append([lag,precip_total,heavy_precip,thickly_coated])
	if cluster_number_6h in [2,7]:
		wpac.append([lag,precip_total,heavy_precip,thickly_coated])
		test.append([lag,precip_total,heavy_precip,thickly_coated])
	if cluster_number_6h == 4:
		ncan.append([lag,precip_total,heavy_precip,thickly_coated])
		test.append([lag,precip_total,heavy_precip,thickly_coated])
	if cluster_number_6h in [6,8,9]:
		spac.append([lag,precip_total,heavy_precip,thickly_coated])
		test.append([lag,precip_total,heavy_precip,thickly_coated])

print 'hp',np.median(hp),'lp',np.median(lp)
hc = 0
tc = 0
for lag in lp:
	if lag >=2:
		hc += 1

print hc*1.0/len(lp)		

print 'npac', 'f_hp', sum([row[2] for row in npac])*1.0/len(npac), 'f_tc', sum([row[3] for row in npac])*1.0/len(npac), len(npac)
print 'wpac', 'f_hp', sum([row[2] for row in wpac])*1.0/len(wpac), 'f_tc', sum([row[3] for row in wpac])*1.0/len(wpac), len(wpac)
print 'ncan', 'f_hp', sum([row[2] for row in ncan])*1.0/len(ncan), 'f_tc', sum([row[3] for row in ncan])*1.0/len(ncan), len(ncan)
print 'spac', 'f_hp', sum([row[2] for row in spac])*1.0/len(spac), 'f_tc', sum([row[3] for row in spac])*1.0/len(spac), len(spac)
		
		
fig = plt.figure()
ax1 = fig.add_subplot(111)
#ax1.scatter([row[1] for row in npac],[row[0] for row in npac],color = 'b')
#ax1.scatter([row[1] for row in wpac],[row[0] for row in wpac],color = 'g')
#ax1.scatter([row[1] for row in ncan],[row[0] for row in ncan],color = 'r')
#ax1.scatter([row[1] for row in spac],[row[0] for row in spac],color = 'c')

#ax1.hexbin([row[1] for row in test],[row[0] for row in test], cmap=cm.jet, gridsize = 50,mincnt=1)

#ax1.hist([row[1] for row in test],bins=40)
ax1.hist(lp,bins=40,color = 'r')
ax1.hist(hp,bins=40,color = 'b')




#ax1.hist([row[0] for row in npac],bins=40,color = 'b')
#ax1.hist([row[0] for row in wpac],bins=40,color = 'g')
#ax1.hist([row[0] for row in ncan],bins=40,color = 'r')
#ax1.hist([row[0] for row in spac],bins=40,color = 'c')
#ax1.hist([row[0] for row in test],bins=40,color = 'c')

#ax1.scatter(precips_total,lag_times)
#ax1.axvline(30)
#ax1.axhline(1)
ax1.set_ylabel('lags')
ax1.set_xlabel('precip')
plt.show()	