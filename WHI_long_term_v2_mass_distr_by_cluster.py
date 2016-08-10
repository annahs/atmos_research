import matplotlib.pyplot as plt
import numpy as np
from matplotlib import dates
import os
import pickle
from datetime import datetime
from pprint import pprint
import sys
from datetime import timedelta
import calendar
import math
import copy
import mysql.connector
import calendar

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


AD_corr = True

#alter the dates to set limits on data analysis range
start_analysis_at = datetime.strptime('20090501','%Y%m%d')
end_analysis_at = datetime.strptime('20120531','%Y%m%d')


########data dirs
directory_list = [
'D:/2009/WHI_ECSP2/Binary/',
'D:/2010/WHI_ECSP2/Binary/',
'D:/2012/WHI_UBCSP2/Binary/',
]

#traking odd neg intervals (buffering issue?)
argh = 0
ok = 0
err_count = 0
non_err_count = 0

##############initialize binning variables
bins = []
start_size = 70 #VED in nm
end_size = 220 #VED in nm
interval_length = 5 #in nm

#need durations to calc sampled volume later for concs
sampling_duration_BB = 0
sampling_duration_FR = 0
sampling_duration_NPac = 0
sampling_duration_SPac = 0
sampling_duration_Cont = 0
sampling_duration_LRT  = 0 
sampling_duration_GBPS = 0
sampling_duration_allFT = 0



#create list of size bins
while start_size < end_size:    
    bins.append(start_size)
    start_size += interval_length

#create dictionary with size bins as keys
binned_data = {}
for bin in bins:
	binned_data[bin] = [0,0]


###create a binning dictionary for each air mass category
rBC_BB_24h_data = copy.deepcopy(binned_data)
rBC_24h_data = copy.deepcopy(binned_data) #does not include BB data
rBC_FT_data_cluster_NPac = copy.deepcopy(binned_data)
rBC_FT_data_cluster_SPac = copy.deepcopy(binned_data)
rBC_FT_data_cluster_Cont = copy.deepcopy(binned_data)
rBC_FT_data_cluster_LRT = copy.deepcopy(binned_data)
rBC_FT_data_cluster_GBPS = copy.deepcopy(binned_data)
rBC_FT_data_all = copy.deepcopy(binned_data)


######get spike times
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/')
file = open('WHI_rBC_record_2009to2013-spike_times.rbcpckl', 'r')
spike_times = pickle.load(file)
file.close()

#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST


   
######this helper method allows cenversion of BC mass from a value arrived at via an old calibration to a value arrived at via a new calibration
#quad eqytn = ax2 + bx + c
def PeakHtFromMass(BC_mass,var_C,var_b,var_a):
    C = var_C   
    b = var_b   
    a = var_a   

    
    c = C - BC_mass
    d = b**2-4*a*c

    if d < 0:
        #This equation has no real solution"
        return np.nan
    elif d == 0:
        # This equation has one solutions
        x = (-b+math.sqrt(b**2-4*a*c))/(2*a)
        return x

    else:
        #This equation has two solutions
        x1 = (-b+math.sqrt((b**2)-(4*(a*c))))/(2*a)
        x2 = (-b-math.sqrt((b**2)-(4*(a*c))))/(2*a)
        if x1 <4000:
            return x1
        if x2 <4000:
            return x2         


def build_distr(distr,BC_VED,BC_mass,sample_factor):
	for key in distr:
		key_value = float(key)
		interval_end = key_value + interval_length
		if key_value <= BC_VED < interval_end:
			distr[key][0] = distr[key][0] + (BC_mass*sample_factor)
			distr[key][1] = distr[key][1] + (1*sample_factor)
				
	return distr
			

#get BC data
for directory in directory_list:
	
    os.chdir(directory)
    print directory
    for item in os.listdir('.'):
	
        if os.path.isdir(item) == True and item.startswith('20'):		
			folder_date = datetime.strptime(item, '%Y%m%d')
			if folder_date >= start_analysis_at and folder_date <= end_analysis_at:
			
				if folder_date.year == 2009:
					old_C = 0
					old_b = 0.012
					old_a = 0
					
					new_C = 0.01244
					new_b = 0.0172 
					 

				if folder_date.year == 2010:
					old_C = 0.156
					old_b = 0.00606
					old_a = 6.3931e-7
					
					new_C = -0.32619
					new_b = 0.01081
					
				if folder_date.year == 2012:
					old_C = 0.20699
					old_b = 0.00246
					old_a = -1.09254e-7
					
					new_C = 0.24826
					new_b = 0.003043

		
				os.chdir(item)
				for file in os.listdir('.'):
					if file.endswith('.ptxt'):
						
						print file
						f = open(file,'r')
						f.readline()
						
						
						for line in f:
							newline = line.split('\t')             
							start_time = float(newline[0])
							end_time = float(newline[1])
							incand_flag = float(newline[2])
							incand_sat_flag = int(newline[3])
							BC_mass = float(newline[4])
							BC_mass_old = float(newline[4])
							
							if AD_corr == True:	
								if folder_date.year == 2009:
									pk_ht = BC_mass/old_b
								else:
									pk_ht = PeakHtFromMass(BC_mass, old_C, old_b, old_a)
								
								BC_mass = new_b*pk_ht + new_C

							try:
								BC_VED = (((BC_mass/(10**15*1.8))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
							except:	
								#print BC_mass, BC_mass_old, datetime.utcfromtimestamp(end_time), err_count
								err_count+=1
								continue
							non_err_count +=1
							
							#this is to account for me running the first few 2012 days and all of 2009 with the new UTC code (the rest are old PST code)
							timezone = timedelta(hours = 0) #using zero here b/c most files were written with old PST code, have a correction further down for those (2009 early 2012) run with newer UTC code
							if datetime.strptime('20120401', '%Y%m%d') <= datetime.utcfromtimestamp(start_time) <= datetime.strptime('20120410', '%Y%m%d'):
								timezone = timedelta(hours = -8)
							if datetime.utcfromtimestamp(start_time) <= datetime.strptime('20091231', '%Y%m%d'):
								timezone = timedelta(hours = -8)
								
							start_time_obj = datetime.utcfromtimestamp(start_time)+timezone 
							end_time_obj = datetime.utcfromtimestamp(end_time)+timezone

							#####now have correct UTC times
							
							#sample rate changes
							if end_time_obj < datetime(2012,4,4,19,43,4):
								sample_factor = 1.0
							if datetime(2012,4,4,19,43,4) <= end_time_obj < datetime(2012,4,5,13,47,9):
								sample_factor = 3.0
							if datetime(2012,4,5,13,47,9) <= end_time_obj < datetime(2012,4,10,3,3,25):
								sample_factor = 1.0
							if datetime(2012,4,10,3,3,25) <= end_time_obj < datetime(2012,5,16,6,9,13):
								sample_factor = 3.0
							if datetime(2012,5,16,6,9,13) <= end_time_obj < datetime(2012,6,7,18,14,39):
								sample_factor = 10.0
							####
							
							
																
							#ignore annoying neg intervals
							if end_time_obj < start_time_obj:
								argh += 1
								continue
							else:
								ok +=1
							
							
							#ignore spike times	
							spike_buffer = 5*60  
							end_timestamp=calendar.timegm(end_time_obj.utctimetuple())
							cursor.execute('''(SELECT 
							    spike_start_UTC,
								spike_end_UTC
								FROM whi_spike_times_2009to2012
								WHERE
								%s BETWEEN (spike_start_UTC-%s) AND (spike_end_UTC+%s))''',
								(end_timestamp,spike_buffer,spike_buffer))

							spike_data = cursor.fetchall()
							if spike_data != []:
								continue  
														
								

							#if in a BB time, put this data in BB dict
							if (fire_time1[0] <= end_time_obj <= fire_time1[1]) or (fire_time2[0] <= end_time_obj <= fire_time2[1]):
								sampling_duration_BB = sampling_duration_BB + end_time - start_time #need duration to calc sampled volume later for concs
								
								rBC_BB_24h_data = build_distr(rBC_BB_24h_data,BC_VED,BC_mass,sample_factor)
																
								continue #do not go on to put this data into a cluster dictionary or the FR dictionary
							
							

							####### get cluster number					
							end_timestamp=calendar.timegm(end_time_obj.utctimetuple())
							cursor.execute('''(SELECT 
							    cluster_start_time,
								cluster_number
								FROM whi_ft_cluster_times_2009to2012
								WHERE
								%s BETWEEN cluster_start_time AND cluster_end_time
								AND 
								id > %s
								AND 
								cluster_number IS NOT NULL)''',
								(end_timestamp,0))

							cluster = cursor.fetchall()
							if cluster == []:
								continue  #if we don't have a cluster number it's not in an FT time!!
							cluslist_current_cluster_no = cluster[0][0]
							cluster_start_time = datetime.utcfromtimestamp(cluster[0][1])
							
									
							
							#add data to list in cluster dictionaries (1 list per cluster time early night/late night)
							if ((cluster_start_time) <= end_time_obj < (cluster_start_time+timedelta(hours=6))):

								#if cluslist_current_cluster_no == 9:
								#	sampling_duration_GBPS = sampling_duration_GBPS + end_time - start_time #need duration to calc sampled volume later for concs
								#	sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 
								#	
								#	rBC_FT_data_cluster_GBPS = build_distr(rBC_FT_data_cluster_GBPS,BC_VED,BC_mass,sample_factor)
								#	rBC_FT_data_all = build_distr(rBC_FT_data_all,BC_VED,BC_mass,sample_factor)
		
												
								if cluslist_current_cluster_no == 4:
									sampling_duration_Cont = sampling_duration_Cont + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 
									
									rBC_FT_data_cluster_Cont = build_distr(rBC_FT_data_cluster_Cont,BC_VED,BC_mass,sample_factor)
									rBC_FT_data_all = build_distr(rBC_FT_data_all,BC_VED,BC_mass,sample_factor)
									
																			
								if cluslist_current_cluster_no in [6,8,9]:
									sampling_duration_SPac = sampling_duration_SPac + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 
									
									rBC_FT_data_cluster_SPac = build_distr(rBC_FT_data_cluster_SPac,BC_VED,BC_mass,sample_factor)
									rBC_FT_data_all = build_distr(rBC_FT_data_all,BC_VED,BC_mass,sample_factor)
											
								if cluslist_current_cluster_no in [2,7]:
									sampling_duration_LRT = sampling_duration_LRT + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 
									
									rBC_FT_data_cluster_LRT = build_distr(rBC_FT_data_cluster_LRT,BC_VED,BC_mass,sample_factor)
									rBC_FT_data_all = build_distr(rBC_FT_data_all,BC_VED,BC_mass,sample_factor)

											
								if cluslist_current_cluster_no in [1,3,5,10]:
									sampling_duration_NPac = sampling_duration_NPac + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 

									rBC_FT_data_cluster_NPac = build_distr(rBC_FT_data_cluster_NPac,BC_VED,BC_mass,sample_factor)
									rBC_FT_data_all = build_distr(rBC_FT_data_all,BC_VED,BC_mass,sample_factor)

							
										
						f.close()
						
			os.chdir(directory)
			
print 'neg times', argh, ok, argh*100./(argh+ok)
print err_count, non_err_count, err_count*100./(err_count+non_err_count)
average_flow = 120

total_sampled_volume_BB   = sampling_duration_BB*average_flow/60   #flow is in cc/min and sampling duration is in sec, so use min/60sec to get vol in cc
total_sampled_volume_FR   = sampling_duration_FR*average_flow/60
total_sampled_volume_NPac = sampling_duration_NPac*average_flow/60
total_sampled_volume_SPac = sampling_duration_SPac*average_flow/60
total_sampled_volume_Cont = sampling_duration_Cont*average_flow/60
total_sampled_volume_LRT  = sampling_duration_LRT *average_flow/60
total_sampled_volume_GBPS = sampling_duration_GBPS*average_flow/60
total_sampled_volume_allFT = sampling_duration_allFT*average_flow/60

#v=create lists
rBC_BB_24h_data_l = []
rBC_24h_data_l = []
rBC_FT_data_cluster_NPac_l = []
rBC_FT_data_cluster_SPac_l = []
rBC_FT_data_cluster_Cont_l = []
rBC_FT_data_cluster_LRT_l = []
rBC_FT_data_cluster_GBPS_l = []
rBC_FT_data_all_l = []

#put lists etc in array
binned_data_lists = [
[rBC_BB_24h_data		  ,rBC_BB_24h_data_l		  , total_sampled_volume_BB  ,'BB'],
[rBC_24h_data			  ,rBC_24h_data_l			  , total_sampled_volume_FR  ,'FR'],
[rBC_FT_data_cluster_NPac ,rBC_FT_data_cluster_NPac_l , total_sampled_volume_NPac,'NPac'],
[rBC_FT_data_cluster_SPac ,rBC_FT_data_cluster_SPac_l , total_sampled_volume_SPac,'SPac'],
[rBC_FT_data_cluster_Cont ,rBC_FT_data_cluster_Cont_l , total_sampled_volume_Cont,'Cont'],
[rBC_FT_data_cluster_LRT  ,rBC_FT_data_cluster_LRT_l  , total_sampled_volume_LRT ,'LRT'],
[rBC_FT_data_cluster_GBPS ,rBC_FT_data_cluster_GBPS_l , total_sampled_volume_GBPS,'GBPS'],
[rBC_FT_data_all ,rBC_FT_data_all_l , total_sampled_volume_allFT,'all_FT'],
]
   

#fiddle with data (sort, normalize, etc)   
for line in binned_data_lists:
	dict = line[0]
	list = line[1]
	sampled_vol = line[2]
	
	for bin, value in dict.iteritems():
		bin_mass = value[0]
		bin_numb = value[1]
		try:
			bin_mass_conc = bin_mass/sampled_vol #gives mass per cc
			bin_numb_conc = bin_numb/sampled_vol #gives number per cc
			temp = [bin,bin_mass_conc,bin_numb_conc]
		except:
			temp = [bin,np.nan,np.nan]
		list.append(temp)
	list.sort()
	
	for row in list: 	#normalize
		row.append(row[1]) #these 2 lines append teh raw mass and number concs
		row.append(row[2]) 
		row[1] = row[1]/(math.log(row[0]+interval_length,10)-math.log(row[0],10)) #d/dlog(VED)
		row[2] = row[2]/(math.log(row[0]+interval_length,10)-math.log(row[0],10)) #d/dlog(VED)
		row[0] = row[0]+interval_length/2 #correction for our binning code recording bin starts as keys instead of midpoints


	
VED_bin_BB = [row[0] for row in rBC_BB_24h_data_l]
mass_BB = [row[1] for row in rBC_BB_24h_data_l]
numb_BB = [row[2] for row in rBC_BB_24h_data_l]

VED_bin_FR = [row[0] for row in rBC_24h_data_l]
mass_FR = [row[1] for row in rBC_24h_data_l]
numb_FR = [row[2] for row in rBC_24h_data_l]

VED_bin_NPac = [row[0] for row in rBC_FT_data_cluster_NPac_l]
mass_NPac = [row[1] for row in rBC_FT_data_cluster_NPac_l]
numb_NPac = [row[2] for row in rBC_FT_data_cluster_NPac_l]

VED_bin_SPac = [row[0] for row in rBC_FT_data_cluster_SPac_l]
mass_SPac = [row[1] for row in rBC_FT_data_cluster_SPac_l]
numb_SPac = [row[2] for row in rBC_FT_data_cluster_SPac_l]

VED_bin_Cont = [row[0] for row in rBC_FT_data_cluster_Cont_l]
mass_Cont = [row[1] for row in rBC_FT_data_cluster_Cont_l]
numb_Cont = [row[2] for row in rBC_FT_data_cluster_Cont_l]

VED_bin_LRT = [row[0] for row in rBC_FT_data_cluster_LRT_l]
mass_LRT = [row[1] for row in rBC_FT_data_cluster_LRT_l]
numb_LRT = [row[2] for row in rBC_FT_data_cluster_LRT_l]

VED_bin_GBPS = [row[0] for row in rBC_FT_data_cluster_GBPS_l]
mass_GBPS = [row[1] for row in rBC_FT_data_cluster_GBPS_l]
numb_GBPS = [row[2] for row in rBC_FT_data_cluster_GBPS_l]

VED_bin_allFT = [row[0] for row in rBC_FT_data_all_l]
mass_allFT = [row[1] for row in rBC_FT_data_all_l]
numb_allFT = [row[2] for row in rBC_FT_data_all_l]


#write final list of interval data to file and pickle
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/size_distrs/from ptxt v2/')

for list in binned_data_lists:
	file = open('AD_corr - size distr - FT - ' + list[3] + 'base 10.txt', 'w')
	file.write('size_bin_midpoint(VEDnm)' + '\t'+ 'dM/dlog(VED)_(ng/cm3)' + '\t'+ 'd#/dlog(VED)_(#/cm3)' +  '\t' + 'dM(VED)_(ng/cm3)' +  '\t'+  'd#(VED)_(#/cm3)' + '\n')
	file.write('total sampled volume:' + str(list[2]) + 'cc' + '\n')
	for row in list[1]:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()

	file = open('AD_corr - size distr - FT - ' + list[3] + '.sdbinpickl', 'w')
	pickle.dump(list[1], file)
	file.close()

        


#plotting
fig = plt.figure()

ax1 = fig.add_subplot(111)
ax1.semilogx(VED_bin_BB,mass_BB		, label = 'BB')
ax1.semilogx(VED_bin_FR,mass_FR		, label = 'FR')
ax1.semilogx(VED_bin_NPac,mass_NPac	, label = 'NPac')
ax1.semilogx(VED_bin_SPac,mass_SPac	, label = 'SPac')
ax1.semilogx(VED_bin_Cont,mass_Cont	, label = 'Cont')
ax1.semilogx(VED_bin_LRT,mass_LRT	, label = 'LRT')
ax1.semilogx(VED_bin_GBPS,mass_GBPS	, label = 'GBPS')
ax1.semilogx(VED_bin_allFT,mass_allFT, label = 'all FT')
plt.xlabel('VED (nm)')
plt.ylabel('dM/dlog(VED)')

plt.legend()

plt.show()
     

	 
fig = plt.figure()

ax1 = fig.add_subplot(111)
ax1.semilogx(VED_bin_BB  ,numb_BB		, label = 'BB')
ax1.semilogx(VED_bin_FR  ,numb_FR		, label = 'FR')
ax1.semilogx(VED_bin_NPac,numb_NPac	, label = 'NPac')
ax1.semilogx(VED_bin_SPac,numb_SPac	, label = 'SPac')
ax1.semilogx(VED_bin_Cont,numb_Cont	, label = 'Cont')
ax1.semilogx(VED_bin_LRT ,numb_LRT	, label = 'LRT')
ax1.semilogx(VED_bin_GBPS,numb_GBPS	, label = 'GBPS')
ax1.semilogx(VED_bin_allFT,numb_allFT	, label = 'all FT')
plt.xlabel('VED (nm)')
plt.ylabel('d#/dlog(VED)')

plt.legend()

plt.show()


        
        