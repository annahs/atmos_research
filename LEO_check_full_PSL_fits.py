import sqlite3
from datetime import datetime
from pprint import pprint
import numpy as np
import matplotlib.pyplot as plt
import sys

#id INTEGER PRIMARY KEY AUTOINCREMENT,
#sp2b_file TEXT, 
#file_index INT, 
#instr TEXT,
#instr_locn TEXT,
#psl_size_nm FLOAT,
#date TIMESTAMP,
#actual_scat_amp FLOAT,
#actual_peak_pos INT,
#FF_scat_amp FLOAT,
#FF_peak_pos INT,
#FF_gauss_width FLOAT,
#zeroX_to_peak FLOAT,
#zeroX_to_LEO_limit FLOAT, 
#LF_scat_amp FLOAT,
#UNIQUE (sp2b_file, file_index, instr)



conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()
instrument = 'WHI_UBCSP2'
size = 200.

#check actual vs fit peak posns	

#####rows in SP2_coating_analysis table
#id INTEGER PRIMARY KEY AUTOINCREMENT,
#sp2b_file TEXT, 
#file_index INT, 
#instr TEXT,
#instr_locn TEXT,
#particle_type TEXT,		
#particle_dia FLOAT,				
#date TIMESTAMP,
#actual_scat_amp FLOAT,
#actual_peak_pos INT,
#FF_scat_amp FLOAT,
#FF_peak_pos INT,
#FF_gauss_width FLOAT,
#zeroX_to_peak FLOAT,
#zeroX_to_LEO_limit FLOAT, 
#LF_scat_amp FLOAT,
#incand_amp FLOAT,
#UNIQUE (sp2b_file, file_index, instr)
	
c.execute('''SELECT actual_scat_amp, LF_scat_amp, sp2b_file, file_index FROM SP2_coating_analysis WHERE instr=? and particle_dia=?''', (instrument,size))
result = c.fetchall()


x = [row[0] for row in result]
y = [row[1] for row in result]
label1 = [row[2] for row in result] 
label2 = [row[3] for row in result]


conn.close()


#plots
#labels = []
#i = 0
#for file in label1:
#	label = file + '_' + str(label2[i])
#	labels.append(label)
#	i+=1
#	
#data = zip(x, y, labels)
#
#fig = plt.figure()
#ax = fig.add_subplot(111)
#
#for x, y, pt_label in data:
#	plt.plot(x, y, 'o', picker=5, label = pt_label)
#
#def onpick(event):
#	thisline = event.artist
#	xdata = thisline.get_xdata()
#	ydata = thisline.get_ydata()
#	label = thisline.get_label()
#	print label
#	
#fig.canvas.mpl_connect('pick_event', onpick)
#ax.set_xlim([0,1000])
#ax.set_ylim([0,1000])

fig = plt.figure()
ax = fig.add_subplot(111)
ax.hist(x, bins=100,range=(0,1000), histtype='step', color = 'black',linewidth=1.5)
ax.hist(y, bins=100,range=(0,1000), histtype='step', color = 'red',linewidth=1.5)
plt.show()
