import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import pickle
import copy
from pyhdf.SD import SD, SDC, SDS
import collections
import calendar
import mysql.connector
import math

VED_min = 155.
VED_max = 180.

start_analysis = datetime(2012,4,1,0,0,0) #UTC
end_analysis = datetime(2012,5,31,0,0,0)

high_RH_limit = 90

start_analysis_UNIX = calendar.timegm(start_analysis.utctimetuple())
end_analysis_UNIX = calendar.timegm(end_analysis.utctimetuple())

rBC_mass_min = ((VED_min/10**7)**3)*(math.pi/6)*1.8*10**15
rBC_mass_max = ((VED_max/10**7)**3)*(math.pi/6)*1.8*10**15


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

##
#select data 
cursor.execute(('SELECT rBC_mass_fg, coat_thickness_nm, UNIX_UTC_ts FROM whi_coating_2012 WHERE particle_type = %s and rBC_mass_fg >=%s and rBC_mass_fg <%s and UNIX_UTC_ts >=%s and UNIX_UTC_ts <=%s and LF_scat_amp >%s'),('incand', rBC_mass_min, rBC_mass_max,start_analysis_UNIX,end_analysis_UNIX,0))


coating_data = cursor.fetchall()

start_hour = 3 #PST 20000
end_hour = 15 #PST 0800

high_RH_list = []
fresh_emission_list = []

for row in coating_data:	
	UNIX_UTC_ts = row[3]
	date_time_UTC = datetime.utcfromtimestamp(UNIX_UTC_ts)
	particle_rBC_mass = row[1]
	coat_thickness_nm = row[2] 
	rBC_VED =(((particle_rBC_mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7 #VED in nm
	dp_dc = (rBC_VED+2*coat_thickness_nm)/rBC_VED
	

	#use night only data
	if start_hour <= date_time_UTC.hour < end_hour:
		
		#get high fresh emission times
		cursor.execute(('SELECT * from whi_spike_times_2009to2012 where spike_start_UTC <= %s and spike_end_UTC > %s'),(UNIX_UTC_ts-60,UNIX_UTC_ts+60)) #add a minute buffer
		spike_data = cursor.fetchall()
		if len(spike_data):
			fresh_emission_list.append([coat_thickness_nm,dp_dc])
			continue
		
		
		#get high RH times
		cursor.execute(('SELECT RH from whi_high_rh_times_2009to2012 where high_RH_start_time <= %s and high_RH_end_time > %s'),(UNIX_UTC_ts,UNIX_UTC_ts))
		RH_data = cursor.fetchall()
		if len(RH_data):
			if RH_data[0] > high_RH_limit:
				high_RH_list.append([coat_thickness_nm,dp_dc])
				continue
		
		cursor.execute(('SELECT * from whi_ft_cluster_times_2012_with_precip where cluster_start_time <= %s and cluster_end_time >= %s'),(UNIX_UTC_ts,UNIX_UTC_ts))
		cluster_data = cursor.fetchall()
		#we have a few samples from teh first day of 2009 and 2012 that are before our first cluster, so this ignores those . . 
		if len(cluster_data) == 0:
			continue
		
		print cluster_data
		sys.exit()
		
		cluster_midtime = datetime.strptime(cluster_data[0][4], '%Y%m%d %H:%M:%S')
		cluster_number = cluster_data[0][3]