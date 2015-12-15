import matplotlib.pyplot as plt
import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import pickle
import math
import calendar
from math import log10, floor

GC_error = True
test_case =  'Van'#'default' #default, Van, wet_scav, no_bb, all_together
RH_of_interest = 90 #101 = no threshold	
sig_figs_SP2 = 3
sig_figs_gc = 4

def round_to_n(x,n):
	return round(x, -int(floor(log10(x))) + (n - 1))


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

data= []
red_list = []
blue_list = []
clusters = ['all','NPac','SPac','Cont','LRT']
GC_row_no = 2



cursor.execute(('SELECT 10th_percentile_mass_conc, 50th_percentile_mass_conc, 90th_percentile_mass_conc, mean_mass_conc, rel_err, data_source, test_scenario,cluster from whi_gc_and_sp2_stats_on_6h_clustered_ft_data where RH_threshold = %s and cluster = %s and test_scenario = %s '),(RH_of_interest,'all','default'))
data_raw = cursor.fetchall()
cursor.execute(('SELECT 10th_percentile_mass_conc, 50th_percentile_mass_conc, 90th_percentile_mass_conc, mean_mass_conc, rel_err, data_source, test_scenario,cluster from whi_gc_and_sp2_stats_on_6h_clustered_ft_data where RH_threshold = %s and cluster = %s and test_scenario = %s '),(RH_of_interest,'all',test_case))
wet_scav_data = cursor.fetchall()
data_raw.append(wet_scav_data[0])

	
for row in data_raw:
	data_source = row[5]
	case= row[6]
	
	if data_source == 'SP2':
		p10_sp2 = row[0]
		p50_sp2 = row[1]
		p90_sp2 = row[2]
		mean_sp2 = row[3]
		rel_err_sp2 = row[4]
	if data_source == 'GEOS-Chem' and case == 'default':
		p10_gc = row[0]
		p50_gc = row[1]
		p90_gc = row[2]
		mean_gc = row[3]
		if GC_error == True:
			rel_err_gc = row[4]
		else:
			rel_err_gc = 0
	if data_source == 'GEOS-Chem' and case == test_case:
		p10_gc_ws = row[0]
		p50_gc_ws = row[1]
		p90_gc_ws = row[2]
		mean_gc_ws = row[3]
		if GC_error == True:
			rel_err_gc_ws = row[4]
		else:
			rel_err_gc_ws = 0

		
SP2_10 = str(round_to_n(p10_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p10_sp2*rel_err_sp2,sig_figs_SP2))
SP2_50 = str(round_to_n(p50_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p50_sp2*rel_err_sp2,sig_figs_SP2))
SP2_90 = str(round_to_n(p90_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p90_sp2*rel_err_sp2,sig_figs_SP2))
SP2_mean = str(round_to_n(mean_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(mean_sp2*rel_err_sp2,sig_figs_SP2))

if GC_error == True:
	GC_10 = str(round_to_n(p10_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p10_gc*rel_err_gc,sig_figs_gc)) + '\n(' + str(round_to_n(p10_gc/p10_sp2,3)) + ')'
	GC_50 = str(round_to_n(p50_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p50_gc*rel_err_gc,sig_figs_gc)) + '\n(' + str(round_to_n(p50_gc/p50_sp2,3)) + ')'
	GC_90 = str(round_to_n(p90_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p90_gc*rel_err_gc,sig_figs_gc)) + '\n(' + str(round_to_n(p90_gc/p90_sp2,3)) + ')'
	GC_mean = str(round_to_n(mean_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(mean_gc*rel_err_gc,sig_figs_gc)) + '\n(' + str(round_to_n(mean_gc/mean_sp2,3)) + ')'
	
	GC_10_ws = str(round_to_n(p10_gc_ws,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p10_gc_ws*rel_err_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p10_gc_ws/p10_sp2,3)) + ')'
	GC_50_ws = str(round_to_n(p50_gc_ws,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p50_gc_ws*rel_err_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p50_gc_ws/p50_sp2,3)) + ')'
	GC_90_ws = str(round_to_n(p90_gc_ws,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p90_gc_ws*rel_err_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p90_gc_ws/p90_sp2,3)) + ')'
	GC_mean_ws = str(round_to_n(mean_gc_ws,sig_figs_gc)) + u'\u00B1' + str(round_to_n(mean_gc_ws*rel_err_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(mean_gc_ws/mean_sp2,3)) + ')'

else:
	GC_10 = str(round_to_n(p10_gc,sig_figs_gc))  + '\n(' + str(round_to_n(p10_gc/p10_sp2,3)) + ')'
	GC_50 = str(round_to_n(p50_gc,sig_figs_gc))  + '\n(' + str(round_to_n(p50_gc/p50_sp2,3)) + ')'
	GC_90 = str(round_to_n(p90_gc,sig_figs_gc))  + '\n(' + str(round_to_n(p90_gc/p90_sp2,3)) + ')'
	GC_mean = str(round_to_n(mean_gc,sig_figs_gc)) + '\n(' + str(round_to_n(mean_gc/mean_sp2,3)) + ')'

	GC_10_ws = str(round_to_n(p10_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p10_gc_ws/p10_sp2,3)) + ')'
	GC_50_ws = str(round_to_n(p50_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p50_gc_ws/p50_sp2,3)) + ')'
	GC_90_ws = str(round_to_n(p90_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p90_gc_ws/p90_sp2,3)) + ')'
	GC_mean_ws = str(round_to_n(mean_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(mean_gc_ws/mean_sp2,3)) + ')'

GC_list = [p10_gc, p50_gc, p90_gc, mean_gc]
GC_list_ws = [p10_gc_ws, p50_gc_ws, p90_gc_ws, mean_gc_ws]
SP2_list = [p10_sp2, p50_sp2, p90_sp2, mean_sp2]

i = 0
for value in GC_list:
	if (value - value*rel_err_gc) > (SP2_list[i]+ SP2_list[i]*rel_err_sp2):
		red_list.append((2,i+1))
	if (value + value*rel_err_gc) < (SP2_list[i]- SP2_list[i]*rel_err_sp2):
		blue_list.append((2,i+1))
	i+=1

i = 0
for value in GC_list_ws:
	if (value - value*rel_err_gc_ws) > (SP2_list[i]+ SP2_list[i]*rel_err_sp2):
		red_list.append((3,i+1))
	if (value + value*rel_err_gc_ws) < (SP2_list[i]- SP2_list[i]*rel_err_sp2):
		blue_list.append((3,i+1))
	i+=1
	

table_row_SP2 = ['Measurement',SP2_10,SP2_50,SP2_90,SP2_mean]
table_row_GC =  ['GEOS-Chem\ndefault scenario', GC_10,GC_50,GC_90,GC_mean]
table_row_GC_ws =  ['GEOS-Chem\n' + str(test_case), GC_10_ws,GC_50_ws,GC_90_ws,GC_mean_ws]

data.append(table_row_SP2)
data.append(table_row_GC)
data.append(table_row_GC_ws)




colLabels=('data source','10th ptile', '50th ptile', '90th ptile', 'mean')
fig=plt.figure()
ax = fig.add_subplot(111)
ax.axis('off')
#do the table
the_table = ax.table(cellText=data,
          colLabels=colLabels,
          loc='center')
  
		  

table_props=the_table.properties()
table_cells=table_props['child_artists']

i=0
for cell in table_cells:
	ht = cell.get_height()
	wd = cell.get_width()
	cell.set_width(wd*1)
	cell.set_height(ht*2.2)
	cell.set_fontsize(14)	
	#if i in [1,3,5,7]:
	#	cell.set_linewidth(4)	
	i+=1


cellDict = the_table.get_celld()
for cell in red_list:
	cellDict[cell]._text.set_color('r')
	
for cell in blue_list:
	cellDict[cell]._text.set_color('b')
		  
		  
	
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
  
plt.savefig('GC default v10 vs SP2 by cluster for WHI - ' + 'all' + ' - ' + str(RH_of_interest) + '% RH threshold - ' + str(test_case) + '.png',bbox_inches='tight')
plt.show()

#######################

data= []
red_list = []
blue_list = []
clusters = ['NPac','SPac','Cont','LRT']
GC_row_no = 2


for cluster in clusters:
	cursor.execute(('SELECT 10th_percentile_mass_conc, 50th_percentile_mass_conc, 90th_percentile_mass_conc, mean_mass_conc, rel_err, data_source, test_scenario,cluster from whi_gc_and_sp2_stats_on_6h_clustered_ft_data where RH_threshold = %s and cluster = %s and test_scenario = %s '),(RH_of_interest,cluster,'default'))
	data_raw = cursor.fetchall()
	cursor.execute(('SELECT 10th_percentile_mass_conc, 50th_percentile_mass_conc, 90th_percentile_mass_conc, mean_mass_conc, rel_err, data_source, test_scenario,cluster from whi_gc_and_sp2_stats_on_6h_clustered_ft_data where RH_threshold = %s and cluster = %s and test_scenario = %s '),(RH_of_interest,cluster,test_case))
	wet_scav_data = cursor.fetchall()
	data_raw.append(wet_scav_data[0])

	pprint(data_raw)
		
	for row in data_raw:
		print row
		data_source = row[5]
		case= row[6]
		
		if data_source == 'SP2':
			p10_sp2 = row[0]
			p50_sp2 = row[1]
			p90_sp2 = row[2]
			mean_sp2 = row[3]
			rel_err_sp2 = row[4]
		if data_source == 'GEOS-Chem' and case == 'default':
			p10_gc = row[0]
			p50_gc = row[1]
			p90_gc = row[2]
			mean_gc = row[3]
			if GC_error == True:
				rel_err_gc = row[4]
			else:
				rel_err_gc = 0
		if data_source == 'GEOS-Chem' and case == test_case:
			p10_gc_ws = row[0]
			p50_gc_ws = row[1]
			p90_gc_ws = row[2]
			mean_gc_ws = row[3]
			if GC_error == True:
				rel_err_gc = row[4]
			else:
				rel_err_gc = 0

			
	SP2_10 = str(round_to_n(p10_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p10_sp2*rel_err_sp2,sig_figs_SP2))
	SP2_50 = str(round_to_n(p50_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p50_sp2*rel_err_sp2,sig_figs_SP2))
	SP2_90 = str(round_to_n(p90_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p90_sp2*rel_err_sp2,sig_figs_SP2))
	SP2_mean = str(round_to_n(mean_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(mean_sp2*rel_err_sp2,sig_figs_SP2))

	if GC_error == True:
		GC_10 = str(round_to_n(p10_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p10_gc*rel_err_gc,sig_figs_gc)) + '\n(' + str(round_to_n(p10_gc/p10_sp2,3)) + ')'
		GC_50 = str(round_to_n(p50_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p50_gc*rel_err_gc,sig_figs_gc)) + '\n(' + str(round_to_n(p50_gc/p50_sp2,3)) + ')'
		GC_90 = str(round_to_n(p90_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p90_gc*rel_err_gc,sig_figs_gc)) + '\n(' + str(round_to_n(p90_gc/p90_sp2,3)) + ')'
		GC_mean = str(round_to_n(mean_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(mean_gc*rel_err_gc,sig_figs_gc)) + '\n(' + str(round_to_n(mean_gc/mean_sp2,3)) + ')'

		GC_10_ws = str(round_to_n(p10_gc_ws,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p10_gc_ws*rel_err_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p10_gc_ws/p10_sp2,3)) + ')'
		GC_50_ws = str(round_to_n(p50_gc_ws,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p50_gc_ws*rel_err_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p50_gc_ws/p50_sp2,3)) + ')'
		GC_90_ws = str(round_to_n(p90_gc_ws,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p90_gc_ws*rel_err_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p90_gc_ws/p90_sp2,3)) + ')'
		GC_mean_ws = str(round_to_n(mean_gc_ws,sig_figs_gc)) + u'\u00B1' + str(round_to_n(mean_gc_ws*rel_err_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(mean_gc_ws/mean_sp2,3)) + ')'
	
	else:
		GC_10 = str(round_to_n(p10_gc,sig_figs_gc)) + '\n(' + str(round_to_n(p10_gc/p10_sp2,3)) + ')'
		GC_50 = str(round_to_n(p50_gc,sig_figs_gc)) + '\n(' + str(round_to_n(p50_gc/p50_sp2,3)) + ')'
		GC_90 = str(round_to_n(p90_gc,sig_figs_gc)) + '\n(' + str(round_to_n(p90_gc/p90_sp2,3)) + ')'
		GC_mean = str(round_to_n(mean_gc,sig_figs_gc)) + '\n(' + str(round_to_n(mean_gc/mean_sp2,3)) + ')'

		GC_10_ws = str(round_to_n(p10_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p10_gc_ws/p10_sp2,3)) + ')'
		GC_50_ws = str(round_to_n(p50_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p50_gc_ws/p50_sp2,3)) + ')'
		GC_90_ws = str(round_to_n(p90_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(p90_gc_ws/p90_sp2,3)) + ')'
		GC_mean_ws = str(round_to_n(mean_gc_ws,sig_figs_gc)) + '\n(' + str(round_to_n(mean_gc_ws/mean_sp2,3)) + ')'
		
		
	GC_list = [p10_gc, p50_gc, p90_gc, mean_gc]
	GC_list_ws = [p10_gc_ws, p50_gc_ws, p90_gc_ws, mean_gc_ws]
	SP2_list = [p10_sp2, p50_sp2, p90_sp2, mean_sp2]

	i = 0
	for value in GC_list:
		if (value - value*rel_err_gc) > (SP2_list[i]+ SP2_list[i]*rel_err_sp2):
			red_list.append((GC_row_no,i+2))
		if (value + value*rel_err_gc) < (SP2_list[i]- SP2_list[i]*rel_err_sp2):
			blue_list.append((GC_row_no,i+2))
		i+=1
	
	i = 0
	for value in GC_list_ws:
		if (value - value*rel_err_gc_ws) > (SP2_list[i]+ SP2_list[i]*rel_err_sp2):
			red_list.append((GC_row_no+1,i+2))
		if (value + value*rel_err_gc_ws) < (SP2_list[i]- SP2_list[i]*rel_err_sp2):
			blue_list.append((GC_row_no+1,i+2))
		i+=1
		

	table_row_SP2 = [cluster, 'Measurement',SP2_10,SP2_50,SP2_90,SP2_mean]
	table_row_GC =  ['','GEOS-Chem\ndefault scenario', GC_10,GC_50,GC_90,GC_mean]
	table_row_GC_ws =  ['','GEOS-Chem\n' + str(test_case), GC_10_ws,GC_50_ws,GC_90_ws,GC_mean_ws]

	data.append(table_row_SP2)
	data.append(table_row_GC)
	data.append(table_row_GC_ws)
	GC_row_no +=3

	

colLabels=('cluster','data source','10th ptile', '50th ptile', '90th ptile', 'mean')
fig=plt.figure()
ax = fig.add_subplot(111)
ax.axis('off')
#do the table
the_table = ax.table(cellText=data,
          colLabels=colLabels,
          loc='center')
  
		  

table_props=the_table.properties()
table_cells=table_props['child_artists']

i=0
for cell in table_cells:
	ht = cell.get_height()
	wd = cell.get_width()
	cell.set_width(wd*1.3)
	cell.set_height(ht*3)
	cell.set_fontsize(14)	
	#if i in [1,3,5,7]:
	#	cell.set_linewidth(4)	
	i+=1


cellDict = the_table.get_celld()
for cell in red_list:
	cellDict[cell]._text.set_color('r')
	
for cell in blue_list:
	cellDict[cell]._text.set_color('b')
		  
		  
	
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
  
plt.savefig('GC default v10 vs SP2 by cluster for WHI - ' + 'by cluster' + ' - ' + str(RH_of_interest) + '% RH threshold - '+str(test_case)+'.png',bbox_inches='tight')
plt.show()	
cnx.close()		
