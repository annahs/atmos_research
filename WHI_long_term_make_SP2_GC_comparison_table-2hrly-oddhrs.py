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

case = 'default' #default, Van, wet_scav, no_bb, all_together
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
for cluster in clusters:
	cursor.execute(('SELECT 10th_percentile_mass_conc, 50th_percentile_mass_conc, 90th_percentile_mass_conc, mean_mass_conc, rel_err, data_source from whi_gc_and_sp2_stats_on_2h_clustered_ft_data where RH_threshold = %s and cluster = %s and test_scenario = %s'),(RH_of_interest,cluster,case))
	data_raw = cursor.fetchall()

	if case != 'default':
		cursor.execute(('SELECT 10th_percentile_mass_conc, 50th_percentile_mass_conc, 90th_percentile_mass_conc, mean_mass_conc, rel_err, data_source from whi_gc_and_sp2_stats_on_2h_clustered_ft_data where RH_threshold = %s and cluster = %s and test_scenario = %s and data_source = %s'),(RH_of_interest,cluster,'default','SP2'))
		sp2_data = cursor.fetchall()
		data_raw.append(sp2_data[0])
	
	if cluster == 'all':
		cluster = 'all clusters\ncombined'
	if cluster == 'NPac':
		cluster = 'N. Pacific'
	if cluster == 'SPac':
		cluster = 'S. Pacific'
	if cluster == 'Cont':
		cluster = 'N. Canada'
	if cluster == 'LRT':
		cluster = 'W. Pacific/Asia'
		
	for row in data_raw:
		data_source = row[5]
		if data_source == 'SP2':
			p10_sp2 = row[0]
			p50_sp2 = row[1]
			p90_sp2 = row[2]
			mean_sp2 = row[3]
			rel_err_sp2 = row[4]
		if data_source == 'GEOS-Chem':
			p10_gc = row[0]
			p50_gc = row[1]
			p90_gc = row[2]
			mean_gc = row[3]
			rel_err_gc = row[4]


			
	SP2_10 = str(round_to_n(p10_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p10_sp2*rel_err_sp2,sig_figs_SP2))
	SP2_50 = str(round_to_n(p50_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p50_sp2*rel_err_sp2,sig_figs_SP2))
	SP2_90 = str(round_to_n(p90_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p90_sp2*rel_err_sp2,sig_figs_SP2))
	SP2_mean = str(round_to_n(mean_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(mean_sp2*rel_err_sp2,sig_figs_SP2))

	GC_10 = str(round_to_n(p10_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p10_gc*rel_err_gc,sig_figs_gc))
	GC_50 = str(round_to_n(p50_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p50_gc*rel_err_gc,sig_figs_gc))
	GC_90 = str(round_to_n(p90_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(p90_gc*rel_err_gc,sig_figs_gc))
	GC_mean = str(round_to_n(mean_gc,sig_figs_gc)) + u'\u00B1' + str(round_to_n(mean_gc*rel_err_gc,sig_figs_gc))

	GC_list = [p10_gc, p50_gc, p90_gc, mean_gc]
	SP2_list = [p10_sp2, p50_sp2, p90_sp2, mean_sp2]

	i = 0
	for value in GC_list:
		if (value - value*rel_err_gc) > (SP2_list[i]+ SP2_list[i]*rel_err_sp2):
			red_list.append((GC_row_no,i+2))
		if (value + value*rel_err_gc) < (SP2_list[i]- SP2_list[i]*rel_err_sp2):
			blue_list.append((GC_row_no,i+2))
		i+=1
		
	
	table_row_SP2 = [cluster,'Measurement',SP2_10,SP2_50,SP2_90,SP2_mean]
	table_row_GC =  [cluster,'GEOS-Chem', GC_10,GC_50,GC_90,GC_mean]

	data.append(table_row_SP2)
	data.append(table_row_GC)
	
	GC_row_no +=2


colLabels=('cluster','data dource','10th ptile', '50th ptile', '90th ptile', 'mean')
fig=plt.figure(figsize=(8,10))
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
	#cell.set_width(0.1)
	cell.set_height(ht*2)
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
  
plt.savefig('GC default v10 vs SP2 by cluster 2hr intervals -oddhrs for WHI - ' + case + ' - ' + str(RH_of_interest) + '% RH threshold.png',bbox_inches='tight')
plt.show()	
cnx.close()		

#######################



cases = ['default', 'Van', 'wet_scav', 'no_bb', 'all_together']

def round_to_n(x,n):
	return round(x, -int(floor(log10(x))) + (n - 1))


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

data= []
red_list = []
blue_list = []
GC_row_offset = 0
for cluster in clusters:
	col = 2
	
	
	if cluster == 'all':
		cluster_name = 'all clusters\ncombined'
	if cluster == 'NPac':
		cluster_name = 'N. Pacific'
	if cluster == 'SPac':
		cluster_name = 'S. Pacific'
	if cluster == 'Cont':
		cluster_name = 'N. Canada'
	if cluster == 'LRT':
		cluster_name = 'W. Pacific/Asia'
	
	p10_row = [cluster_name,'10th',]
	p50_row = ['','50th',]
	p90_row = ['','90th',]
	mean_row = ['','mean',]
	
	

	for case in cases:
		
		cursor.execute(('SELECT 10th_percentile_mass_conc, 50th_percentile_mass_conc, 90th_percentile_mass_conc, mean_mass_conc, rel_err, data_source from whi_gc_and_sp2_stats_on_2h_clustered_ft_data where RH_threshold = %s and cluster = %s and test_scenario = %s'),(RH_of_interest,cluster,case))
		data_raw = cursor.fetchall()

		if case != 'default':
			cursor.execute(('SELECT 10th_percentile_mass_conc, 50th_percentile_mass_conc, 90th_percentile_mass_conc, mean_mass_conc, rel_err, data_source from whi_gc_and_sp2_stats_on_2h_clustered_ft_data where RH_threshold = %s and cluster = %s and test_scenario = %s and data_source = %s'),(RH_of_interest,cluster,'default','SP2'))
			sp2_data = cursor.fetchall()
			data_raw.append(sp2_data[0])
		
		for row in data_raw:
			data_source = row[5]
			if data_source == 'SP2':
				p10_sp2 = row[0]
				p50_sp2 = row[1]
				p90_sp2 = row[2]
				mean_sp2 = row[3]
				rel_err_sp2 = row[4]
			if data_source == 'GEOS-Chem':
				p10_gc = row[0]
				p50_gc = row[1]
				p90_gc = row[2]
				mean_gc = row[3]
				rel_err_gc = row[4]


				
		SP2_10 = str(round_to_n(p10_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p10_sp2*rel_err_sp2,sig_figs_SP2))
		SP2_50 = str(round_to_n(p50_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p50_sp2*rel_err_sp2,sig_figs_SP2))
		SP2_90 = str(round_to_n(p90_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(p90_sp2*rel_err_sp2,sig_figs_SP2))
		SP2_mean = str(round_to_n(mean_sp2,sig_figs_SP2)) + u'\u00B1' + str(round_to_n(mean_sp2*rel_err_sp2,sig_figs_SP2))

		GC_10 = str(round_to_n(p10_gc,sig_figs_gc))
		GC_50 = str(round_to_n(p50_gc,sig_figs_gc))
		GC_90 = str(round_to_n(p90_gc,sig_figs_gc))
		GC_mean = str(round_to_n(mean_gc,sig_figs_gc)) 

		GC_list = [p10_gc, p50_gc, p90_gc, mean_gc]
		SP2_list = [p10_sp2, p50_sp2, p90_sp2, mean_sp2]

		i = 0
		GC_row_no = 1
		for value in GC_list:
			if (value - value*rel_err_gc) > (SP2_list[i]+ SP2_list[i]*rel_err_sp2):
				red_list.append((GC_row_no + GC_row_offset,col))
				print case, cluster, value,(GC_row_no + GC_row_offset,col)
			if (value + value*rel_err_gc) < (SP2_list[i]- SP2_list[i]*rel_err_sp2):
				blue_list.append((GC_row_no + GC_row_offset,col))
			GC_row_no +=1
			i+=1
		
		p10_row.append(round_to_n(p10_gc/p10_sp2,3))
		p50_row.append(round_to_n(p50_gc/p50_sp2,3))
		p90_row.append(round_to_n(p90_gc/p90_sp2,3))
		mean_row.append(round_to_n(mean_gc/mean_sp2,3))
		
		col += 1	
	GC_row_offset += 4
	
	data.append(p10_row)
	data.append(p50_row)
	data.append(p90_row)
	data.append(mean_row)
	
	


colLabels=('cluster','percentile','default\nscenario', 'no Vancouver\nemissions', 'improved wet\nscavenging', 'no biomass\nburning', 'all changes\ntogether')
fig=plt.figure(figsize=(12,14))
ax = fig.add_subplot(111)
ax.axis('off')
#do the table
the_table = ax.table(cellText=data,
          colLabels=colLabels,
          loc='center')

cellDict = the_table.get_celld()

table_props=the_table.properties()
table_cells=table_props['child_artists']

for cell in table_cells:
	ht = cell.get_height()
	#cell.set_width(0.1)
	cell.set_height(ht*2.2)
	cell.set_fontsize(14)
	


for cell in red_list:
	cellDict[cell]._text.set_color('r')
	
for cell in blue_list:
	cellDict[cell]._text.set_color('b')
		  
		  
	
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
  
plt.savefig('GC all tests v10 vs SP2 by cluster 2hr intervals -oddhrs for WHI - ' + str(RH_of_interest) + '% RH threshold.png',bbox_inches='tight')
plt.show()	
cnx.close()			