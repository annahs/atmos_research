import sqlite3
from datetime import datetime
from pprint import pprint
import numpy as np
import matplotlib.pyplot as plt
import sys
import calendar

conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()
instrument = 'UBCSP2'
location = 'WHI' #WHI or DMT
type_particle = 'PSL' #PSL, nonincand, incand
size = 110.
start_date = datetime(2010, 4, 1)
end_date = datetime(2012, 6, 01)
start_date_ts = calendar.timegm(start_date.timetuple())
end_date_ts = calendar.timegm(end_date.timetuple())

#check actual vs fit peak posns	

#####rows in SP2_coating_analysis table
#sp2b_file TEXT, 
#file_index INT, 
#instr TEXT,
#instr_locn TEXT,
#particle_type TEXT,		
#particle_dia FLOAT,				
#unix_ts_utc FLOAT,
#actual_scat_amp FLOAT,
#actual_peak_pos INT,
#FF_scat_amp FLOAT,
#FF_peak_pos INT,
#FF_gauss_width FLOAT,
#zeroX_to_peak FLOAT,
#LF_scat_amp FLOAT,
#incand_amp FLOAT,
#lag_time_fit_to_incand FLOAT,
#LF_baseline_pct_diff FLOAT,
#rBC_mass_fg FLOAT,
#coat_thickness_nm FLOAT,
	
c.execute('''SELECT FF_scat_amp, LF_scat_amp, sp2b_file, file_index FROM SP2_coating_analysis WHERE instr=? and particle_type=? and particle_dia=? and file_index<? and unix_ts_utc>=? and unix_ts_utc<?''', (instrument,type_particle, size,5000 ,start_date_ts,end_date_ts))
#c.execute('''SELECT actual_scat_amp, LF_scat_amp FROM SP2_coating_analysis WHERE instr=? and particle_type=? and particle_dia=? and instr_locn=? and file_index<?''', (instrument,type_particle, size, location, 500))

result = c.fetchall()

x = [row[0] for row in result]
y = [row[1] for row in result]


print len(y), len(x)


#print len(x), np.median(x), np.mean(x)
#print len(y), np.median(y), np.mean(y)

#print 'FF med', np.median(x)
#print 'actual med', np.median(y)
label1 = [row[2] for row in result] 
label2 = [row[3] for row in result]


conn.close()


###plots
labels = []
i = 0
for file in label1:
	label = file + '_' + str(label2[i])
	labels.append(label)
	i+=1
	
data = zip(x, y, labels)

fig = plt.figure()
ax = fig.add_subplot(111)

for x, y, pt_label in data:
	plt.plot(x, y, 'o', picker=5, label = pt_label)

def onpick(event):
	thisline = event.artist
	xdata = thisline.get_xdata()
	ydata = thisline.get_ydata()
	label = thisline.get_label()
	print label
	
fig.canvas.mpl_connect('pick_event', onpick)
ax.set_xlim([0,3600])
ax.set_ylim([0,3600])
plt.xlabel('actual_scat_amp')
plt.ylabel('LF_scat_amp')
plt.plot([0, 3600], [0, 3600], 'k-')
plt.show()

########hist
#
#fig = plt.figure()
#ax = fig.add_subplot(111)
#ax.hist(x, bins=60,range=(0,3000), histtype='step', color = 'black',linewidth=1.5, label = 'Actual scattering amplitude (au)' )
#ax.hist(y, bins=60,range=(0,3000), histtype='step', color = 'red',linewidth=1.5,  label = 'LEO-fit scattering amplitude (au)' )
#
#plt.legend()
#plt.show()
