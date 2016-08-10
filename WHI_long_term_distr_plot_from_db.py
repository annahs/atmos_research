import matplotlib.pyplot as plt
from matplotlib import dates
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import copy
import collections
import calendar
import mysql.connector
import math

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

def get_data(cluster,cluster_interval):
	cursor.execute('''(SELECT 
		bin_LL, 
		bin_UL, 
		mass, 
		number, 
		volume
		FROM whi_sp2_distr_data
		WHERE
		cluster_interval = %s
		AND	cluster = %s
		)''',
		(6,cluster))	
		
	return cursor.fetchall()

def parse_data(distr_data):
	new_plot_data = []
	total_volume = 0
	for row in distr_data:
		bin_LL = row[0]
		bin_UL = row[1]
		mass  = row[2]
		number  = row[3]
		volume  = row[4]
		total_volume +=  volume
		numb_conc_norm = number/(math.log(bin_UL,10)-math.log(bin_LL,10)) #normalize number
		mass_conc_norm = mass/(math.log(bin_UL,10)-math.log(bin_LL,10)) #normalize number

		new_plot_data.append([(bin_LL+(bin_UL-bin_LL)/2),mass_conc_norm,numb_conc_norm])

	return [new_plot_data,total_volume]

	
clus_list = ['NPac','SPac','NCan','WPac','BB']
plot_data = {}
for cluster in clus_list:
	distr_data = get_data(cluster, 6)
	distr_results = parse_data(distr_data)
	plot_data[cluster] = distr_results[0] 
	tot_volume = distr_results[1]
	
fig = plt.figure()
ax1 = fig.add_subplot(111)
for cluster in clus_list:
	print cluster 
	mass_max_val = max([row[1] for row in plot_data[cluster]])
	numb_max_val = max([row[2] for row in plot_data[cluster]])
	bin =          [row[0] for row in plot_data[cluster]]
	mass_distr =   [row[1] for row in plot_data[cluster]]
	number_distr = [row[2]/numb_max_val for row in plot_data[cluster]]
	
	

	ax1.plot(bin,mass_distr,marker = 'o',label = cluster)
	#ax1.plot(bin,number_distr,marker = 's',label = cluster)
	#ax1.set_xlim(0,300)
	#ax1.set_ylim(0,60)
	ax1.set_ylabel('mass conc')

plt.legend(loc=4)
plt.show()	


cnx.close()
