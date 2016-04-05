import matplotlib.pyplot as plt
from matplotlib import dates
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import copy
import calendar
import mysql.connector

timezone = -8

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


#select data (spikes and fire times already rmoved) 
SP2_data_query = ('SELECT UNIX_UTC_6h_midtime, meas_mean_mass_conc, meas_rel_err, GC_v10_default, GC_default_rel_err, cluster,cluster_number FROM whi_gc_and_sp2_6h_mass_concs WHERE RH_threshold = 90')
			

cursor.execute(SP2_data_query)
raw_data = cursor.fetchall()

correlation_plot1 = []
correlation_plot3 = []
correlation_plot5 = []
correlation_plot10 = []

for row in raw_data:
	UTC_ts = row[0]
	PST_date_time = datetime.utcfromtimestamp(UTC_ts) + timedelta(hours = timezone)
	meas_mass_conc = float(row[1])
	meas_rel_err = float(row[2])
	meas_abs_err = meas_rel_err*meas_mass_conc
	GC_mass_conc = row[3]
	GC_rel_err = 0#row[4]
	GC_abs_err = GC_rel_err*GC_mass_conc
	cluster = row[5]
	ratio = GC_mass_conc/meas_mass_conc
	ratio_abs_err = (meas_rel_err + GC_rel_err)*ratio
	cluster_number = row[6]
	
	if cluster_number == 1:
		correlation_plot1.append([meas_mass_conc,GC_mass_conc])
	if cluster_number == 3:
		correlation_plot3.append([meas_mass_conc,GC_mass_conc])
	if cluster_number == 5:
		correlation_plot5.append([meas_mass_conc,GC_mass_conc])
	if cluster_number == 10:
		correlation_plot10.append([meas_mass_conc,GC_mass_conc])
	#if cluster == 'Cont':
	#	correlation_plot.append([meas_mass_conc,GC_mass_conc])
	
meas1 = [row[0] for row in correlation_plot1]
GC1 = [row[1] for row in correlation_plot1]

meas3 = [row[0] for row in correlation_plot3]
GC3 = [row[1] for row in correlation_plot3]

meas5 = [row[0] for row in correlation_plot5]
GC5 = [row[1] for row in correlation_plot5]

meas10 = [row[0] for row in correlation_plot10]
GC10 = [row[1] for row in correlation_plot10]

fig = plt.figure(figsize=(10,8))



ax1 = fig.add_subplot(224)
ax1.scatter(meas1, GC1,color='m')
ax1.set_ylim(0,300)
ax1.set_xlim(0,300)
ax1.set_ylabel('GEOS-Chem 6h mass conc')
ax1.set_xlabel('SP2 6h mass conc')

ax2 = fig.add_subplot(222)
ax2.scatter(meas3, GC3,color='g')
ax2.set_ylim(0,300)
ax2.set_xlim(0,300)
ax2.set_ylabel('GEOS-Chem 6h mass conc')
ax2.set_xlabel('SP2 6h mass conc')

ax3 = fig.add_subplot(223)
ax3.scatter(meas5, GC5,color='b')
ax3.set_ylim(0,300)
ax3.set_xlim(0,300)
ax3.set_ylabel('GEOS-Chem 6h mass conc')
ax3.set_xlabel('SP2 6h mass conc')

ax4 = fig.add_subplot(221)
ax4.scatter(meas10, GC10, color='c')
ax4.set_ylim(0,300)
ax4.set_xlim(0,300)
ax4.set_ylabel('GEOS-Chem 6h mass conc')
ax4.set_xlabel('SP2 6h mass conc')


plt.show()