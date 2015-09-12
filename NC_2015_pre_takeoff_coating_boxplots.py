import sys
import os
from datetime import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import math

flight_data = { 
'science1':	[datetime(2015,4,5,9,43,24),	[],[]],
'ferry1':	[datetime(2015,4,6,9,7,51),		[],[]],
'ferry2':	[datetime(2015,4,6,15,11,8),	[],[]],
'science2':	[datetime(2015,4,7,16,31,57),	[],[]],	
'science3':	[datetime(2015,4,8,13,51,19),	[],[]],	
'science4':	[datetime(2015,4,8,17,53,4),	[],[]],	
'science5':	[datetime(2015,4,9,13,50,12),	[],[]],	
'ferry3':	[datetime(2015,4,10,14,28,30),	[],[]],
'science6':	[datetime(2015,4,11,15,57,28),	[],[]],
'science7':	[datetime(2015,4,13,15,14,27),	[],[]],
'ferry4':	[datetime(2015,4,17,21,22,0),	[],[]],
'science8':	[datetime(2015,4,20,15,49,49),	[],[]],
'science9':	[datetime(2015,4,20,21,46,9),	[],[]],
'science10':[datetime(2015,4,21,16,7,56),	[],[]],
}

flights_to_plot = ['science1','ferry1','ferry2','science2','science3','science4','science5','ferry3','science6','science7','ferry4','science8','science9','science10']



#set parameters
instrument_locn = 'POLAR6'
type_particle = 'incand'
min_BC_VED = 155.
max_BC_VED = 180.
metric = 'dp_dc' #coat_th, dp_dc

min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)


#connect to database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

for row in c.execute('''SELECT coat_thickness_nm, unix_ts_utc, rBC_mass_fg
FROM SP2_coating_analysis 
WHERE instr_locn=? and particle_type=? and rBC_mass_fg >=? and rBC_mass_fg <?
ORDER BY unix_ts_utc''', 
(instrument_locn,type_particle, min_rBC_mass,max_rBC_mass )):	
	coat_th = row[0]
	if coat_th != None:
		event_time = datetime.utcfromtimestamp(row[1])
		rBC_mass = row[2]
		rBC_density = 1.8
		rBC_VED =(((rBC_mass/(10**15*rBC_density))*6/3.14159)**(1/3.0))*10**7
		dp_dc = (rBC_VED+2*coat_th)/rBC_VED
		
		if event_time.day == 5:
			flight = 'science1'
			
		elif event_time.day == 6:
			if event_time <= datetime(2015,4,6,10,56,28):
				flight = 'ferry1'
			if event_time >= datetime(2015,4,6,15,11,8):
				flight = 'ferry2'
				
		elif event_time.day == 7:
			flight = 'science2'
			
		elif event_time.day == 8:
			if event_time <= datetime(2015,4,8,16,43,44):
				flight = 'science3'
			if event_time >= datetime(2015,4,8,17,53,4):
				flight = 'science4'
				
		elif event_time.day == 9:
			flight = 'science5'
			
		elif event_time.day == 10:
			flight = 'ferry3'
			
		elif event_time.day == 11:
			flight = 'science6'
			
		elif event_time.day == 13:
			flight = 'science7'
			
		elif event_time.day == 17:
			flight = 'ferry4'
			
		elif event_time.day == 20 or 21:
			if event_time <= datetime(2015,4,20,19,49,49):
				flight = 'science8'
			elif datetime(2015,4,20,21,46,9) < event_time <= datetime(2015,4,21,1,36,35) :
				flight = 'science9'
			elif event_time >= datetime(2015,4,21,16,7,56):
				flight = 'science10'
		
		
		if event_time < flight_data[flight][0]:
			if metric == 'coat_th':
				flight_data[flight][1].append(coat_th)
			if metric == 'dp_dc':
				flight_data[flight][1].append(dp_dc)
		else:
			if metric == 'coat_th':
				flight_data[flight][2].append(coat_th)
			if metric == 'dp_dc':
				flight_data[flight][2].append(dp_dc)
		
conn.close()

###histos			
fig, axes = plt.subplots(5,3, figsize=(12, 12), facecolor='w', edgecolor='k')
fig.subplots_adjust(hspace = 0., wspace=0.1)
axes[-1, -1].axis('off')
axs = axes.ravel()
i=0

for flight_to_plot in flights_to_plot:
	pre_takeoff_coatings = flight_data[flight_to_plot][1]
	post_takeoff_coatings = flight_data[flight_to_plot][2]	
	
	
	if metric == 'coat_th':
		if len(pre_takeoff_coatings) >200:
			coat = axs[i].hist(pre_takeoff_coatings,bins = 40, range = (-40,160),  histtype='step',normed=True,color='k')
		coat = axs[i].hist(post_takeoff_coatings,bins = 40, range = (-40,160),  histtype='step',normed=True,color='b')
		axs[i].set_xlim(-40,160)
	if metric == 'dp_dc':
		if len(pre_takeoff_coatings) >200:
			coat = axs[i].hist(pre_takeoff_coatings,bins = 40, range = (0.5,3),  histtype='step',normed=True,color='k')
		coat = axs[i].hist(post_takeoff_coatings,bins = 40, range = (0.5,3),  histtype='step',normed=True, color='b')
		axs[i].set_xlim(0.5,3)
	#axs[i].set_ylim(0,3200)
	axs[i].axvline(np.nanmedian(pre_takeoff_coatings), color= 'black', linestyle = '--')
	axs[i].axvline(np.nanmedian(post_takeoff_coatings), color= 'b', linestyle = '--')
	axs[i].text(0.7, 0.7,flight_to_plot,transform=axs[i].transAxes)
	if i in [4,5]:
		if metric =='coat_th':
			axs[i].set_xlabel('Coating Thickness (nm)')
		if metric =='dp_dc':
			axs[i].set_xlabel('Dp/Dc')
			
		
		
	print flight_to_plot, np.nanmedian(pre_takeoff_coatings)
	
	i+=1

	
if metric =='coat_th':
	plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating histos by flight for rBC cores from ' + str(min_BC_VED) + ' to ' + str(max_BC_VED) + ' nm.png')
if metric =='dp_dc':
	plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/DpDc histos by flight for rBC cores from ' + str(min_BC_VED) + ' to ' + str(max_BC_VED) + ' nm.png')

	
plt.show()

#########box-plots
fig = plt.figure( figsize=(10, 6))
ax = fig.add_subplot(111)

pre_takeoff_coating_bp_data = []
post_takeoff_coating_bp_data = []
i=0
x1=[]
for flight_to_plot in flights_to_plot:

	pre_takeoff_coatings = flight_data[flight_to_plot][1]
	post_takeoff_coatings = flight_data[flight_to_plot][2]
	
	if len(pre_takeoff_coatings) > 200:
		pre_takeoff_coating_bp_data.append(pre_takeoff_coatings)
		x1.append(i)
	post_takeoff_coating_bp_data.append(post_takeoff_coatings)
	i+=1
	

pre_coating_bp = ax.boxplot(pre_takeoff_coating_bp_data, whis=[10,90],sym='', widths = 0.2, positions = np.array(x1))	
x=np.array([0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,])
post_coating_bp = ax.boxplot(post_takeoff_coating_bp_data, whis=[10,90],sym='', widths = 0.2, positions = x)
plt.setp(pre_coating_bp['boxes'], color='g')
plt.setp(pre_coating_bp['whiskers'], color='g',linestyle='-')
plt.setp(pre_coating_bp['caps'], color='g')
plt.setp(pre_coating_bp['medians'], color='g')	

plt.xticks([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], ['science1','ferry1','ferry2','science2','science3','science4','science5','ferry3','science6','science7','ferry4','science8','science9','science10',''],rotation=60)

ax.yaxis.grid(True, linestyle='-', which='major', color='grey', alpha=1)

if metric =='coat_th':
	ax.set_ylabel('Coating Thickness (nm)')
if metric =='dp_dc':
	ax.set_ylabel('Dp/Dc')
		
if metric =='coat_th':
	plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/coating boxplots by flight for rBC cores from ' + str(min_BC_VED) + ' to ' + str(max_BC_VED) + ' nm.png', bbox_inches='tight')
if metric =='dp_dc':
	plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/DpDc boxplots by flight for rBC cores from ' + str(min_BC_VED) + ' to ' + str(max_BC_VED) + ' nm.png', bbox_inches='tight')

		


plt.show()      

