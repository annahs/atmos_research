import sqlite3
from datetime import datetime
from pprint import pprint
import numpy as np
import matplotlib.pyplot as plt
import sys
import calendar
import os


conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()
instrument = 'UBCSP2'
location = 'POLAR6' #WHI or DMT
type_particle = 'nonincand' #PSL, nonincand, incand
fit_function = 'Gauss' #Gauss or Giddings
size = 240.
start_date = datetime(2015,4,5)
end_date =   datetime(2015,4,6)
start_date_ts = calendar.timegm(start_date.timetuple())
end_date_ts = calendar.timegm(end_date.timetuple())

#check actual vs fit peak posns	

#####rows in SP2_coating_analysis table

#sp2b_file TEXT, 			eg 20120405x001.sp2b
#file_index INT, 			
#instr TEXT,				eg UBCSP2, ECSP2
#instr_locn TEXT,			eg WHI, DMT, POLAR6
#particle_type TEXT,		eg PSL, nonincand, incand, Aquadag
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
#zero_crossing_posn FLOAT,
#coat_thickness_from_actual_scat_amp FLOAT,
#FF_fit_function TEXT,
#LF_fit_function TEXT,
#zeroX_to_LEO_limit FLOAT
#UNIQUE (sp2b_file, file_index, instr)
#)''')
	

c.execute('''SELECT LF_scat_amp, actual_scat_amp, sp2b_file, file_index  FROM SP2_coating_analysis 
WHERE instr=? and particle_type=? and unix_ts_utc>=? and unix_ts_utc<? and FF_fit_function=? and LF_fit_function=? and file_index<?''', 
(instrument,type_particle, start_date_ts,end_date_ts,fit_function,fit_function,500))

#c.execute('''SELECT FF_fit_function,  FF_fit_function FROM SP2_coating_analysis 
#WHERE instr=? and particle_type=? and unix_ts_utc>=? and unix_ts_utc<? and file_index<?''', 
#(instrument,type_particle, start_date_ts,end_date_ts,10))

result = c.fetchall()

x = []
y = []
j = []
k = []
l = []

for row in result:
	if row[0] != None:
		y.append(row[0])
		x.append(row[1])
		j.append(row[1])
		k.append(row[0])
		l.append(row[0]/row[1])
		

		
print len(x), np.nanmedian(x) , np.nanmean(x), np.percentile(x,10), np.percentile(x,90), 'actual'

print len(y), np.nanmedian(y) , np.nanmean(y), np.percentile(y,10), np.percentile(y,90), 'LF'

#print x
#print y
#sys.exit()



#print 'FF med', np.median(x)
#print 'actual med', np.median(y)
label1 = [row[2] for row in result] 
label2 = [row[3] for row in result]


conn.close()

os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/')


#####plots
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

########hist1

fig = plt.figure()
ax = fig.add_subplot(111)
ax.hist(j, bins=100,range=(0,4000), histtype='step', color = 'black',linewidth=1.5, label = 'Actual scat amp (au)' )
ax.hist(k, bins=100,range=(0,4000), histtype='step', color = 'red',linewidth=1.5,  label = 'LF scat amp (au)' )
ax.axvline(np.nanmedian(j), color= 'black',  label = 'Actual median' )
ax.axvline(np.nanmedian(k), color= 'red',  label = 'LEO median')
#plt.text (0.1,0.94, str(size) + 'nm PSL', transform=ax.transAxes)
plt.legend()

#plt.savefig('Netcare Spring 2015 - scattering ' + str(size) + 'nm PSL - full Gauss fit and actual scattering amplitude.png', bbox_inches='tight')


plt.show()


########hist1
print 'median ratio', np.nanmedian(l)

fig = plt.figure()
ax = fig.add_subplot(111)
#ax.hist(j, bins=100,range=(0,4000), histtype='step', color = 'black',linewidth=1.5, label = 'Actual scat amp (au)' )
ax.hist(l, bins=100,range=(0,10), histtype='step', color = 'red',linewidth=1.5,  label = 'LF scat amp/Actual scat amp' )
ax.axvline(np.nanmedian(l), color= 'black',  label = 'median ratio')
ax.axvline(1, color= 'red',  label = '1')
plt.xlim(0,10)
#plt.text (0.1,0.94, str(size) + 'nm PSL', transform=ax.transAxes)
plt.legend()

#plt.savefig('Netcare Spring 2015 - scattering ' + str(size) + 'nm PSL - full Gauss fit and actual scattering amplitude.png', bbox_inches='tight')


plt.show()
