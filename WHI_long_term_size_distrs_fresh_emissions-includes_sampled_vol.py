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


timezone = timedelta(hours = 0) #using zero here b/c most files were written with old PST code, have a correction further down for those (2009 early 2012) run with newer UTC code
AD_corr = True

#1. #alter the dates to set limits on data analysis range
start_analysis_at = datetime(2009,6,28,9,55)
end_analysis_at = datetime.strptime('20120531','%Y%m%d')


########data dirs
directory_list = [
'D:/2009/WHI_ECSP2/Binary/',
'D:/2010/WHI_ECSP2/Binary/',
'D:/2012/WHI_UBCSP2/Binary/',
]

#tracking odd neg intervals (buffering issue?)
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

sampling_duration_cluster_1 = 0
sampling_duration_cluster_2 = 0
sampling_duration_cluster_3 = 0 
sampling_duration_cluster_4 = 0
sampling_duration_cluster_5 = 0 
sampling_duration_cluster_6 = 0
sampling_duration_allFT = 0
sampling_duration_GBPS = 0
sampling_duration_fresh = 0


#create list of size bins
while start_size < end_size:    
    bins.append(start_size)
    start_size += interval_length

#create dictionary with size bins as keys
binned_data = {}
for bin in bins:
	binned_data[bin] = [0,0]


###create a binning dictionary for each air mass category
rBC_FT_data_cluster_1 = copy.deepcopy(binned_data)
rBC_FT_data_cluster_2 = copy.deepcopy(binned_data)
rBC_FT_data_cluster_3 = copy.deepcopy(binned_data)
rBC_FT_data_cluster_4 = copy.deepcopy(binned_data)
rBC_FT_data_cluster_5 = copy.deepcopy(binned_data)
rBC_FT_data_cluster_6 = copy.deepcopy(binned_data)

rBC_FT_data_cluster_GBPS = copy.deepcopy(binned_data)
rBC_FT_data_all = copy.deepcopy(binned_data)
rBC_FT_data_fresh = copy.deepcopy(binned_data)

######get spike times (these are sorted by datetime)
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/')
file = open('WHI_rBC_record_2009to2013-spike_times.rbcpckl', 'r')
spike_times_full = pickle.load(file)
file.close()

spike_times = []
for spike in spike_times_full:
	if spike.year >= start_analysis_at.year:
		if spike <= end_analysis_at:
			spike_times.append(spike)


#fire times
fire_time1 = [datetime.strptime('2009/07/27 00:00', '%Y/%m/%d %H:%M'), datetime.strptime('2009/08/08 00:00', '%Y/%m/%d %H:%M')] #row_datetimes follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011 #PST
fire_time2 = [datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M'), datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')] #jason's BC clear report #PST

##########open cluslist and read into a python list
cluslist = []
CLUSLIST_file = 'C:/hysplit4/working/WHI/2hrly_HYSPLIT_files/all_with_sep_GBPS/CLUSLIST_6-mod'
CLUSLIST_file = 'C:/hysplit4/working/WHI/2hrly_HYSPLIT_files/all_with_sep_GBPS/CLUSLIST_6-mod-precip_added-sig_precip_any_time'

with open(CLUSLIST_file,'r') as f:
	for line in f:
		newline = line.split()
		cluster_no = int(newline[0])
		traj_time = datetime(int(newline[2])+2000,int(newline[3]),int(newline[4]),int(newline[5])) + timezone
		if traj_time.year >= start_analysis_at.year:
			cluslist.append([traj_time,cluster_no])

# sort cluslist by row_datetime in place		
cluslist.sort(key=lambda clus_info: clus_info[0])  

   
######this helper method allows conversion of BC mass from a value arrived at via an old calibration to a value arrived at via a new calibration
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
							except Exception,e: 
								print str(e)
								print 'no VED calculated'
								err_count+=1
								continue
							non_err_count +=1

							#this is to account for me running the first few 2012 days and all of 2009 with the new UTC code (the rest are old PST code)
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
							
							
							####use spike times to get fresh emissions data and then ignore
							spike_half_interval = 2
							if len(spike_times):
								spike_start = spike_times[0]-timedelta(minutes=spike_half_interval)
								spike_end = spike_times[0]+timedelta(minutes=spike_half_interval)
								
								while end_time_obj >= spike_end:
									print 'pop spike time', end_time_obj, spike_times[0]
									spike_times.pop(0)
									if len(spike_times):
										spike_start = spike_times[0]-timedelta(minutes=spike_half_interval)
										spike_end = spike_times[0]+timedelta(minutes=spike_half_interval)
									if len(spike_times) == 0:
										print 'no more spike times'
										break
										
								if (start_time_obj < spike_start or start_time_obj < spike_end) and (end_time_obj > spike_start or end_time_obj > spike_end):
									sampling_duration_fresh = sampling_duration_fresh + end_time - start_time #need duration to calc sampled volume later for concs
									for key in rBC_FT_data_fresh:
										key_value = float(key)
										interval_end = key_value + interval_length
										if BC_VED >= key_value and BC_VED < interval_end:
											rBC_FT_data_fresh[key][0] = rBC_FT_data_fresh[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_fresh[key][1] = rBC_FT_data_fresh[key][1] + (1*sample_factor)
									continue
									
							###
							
							#if in a BB time, ignore
							if (fire_time1[0] <= end_time_obj <= fire_time1[1]) or (fire_time2[0] <= end_time_obj <= fire_time2[1]):
								continue #do not go on to put this data into a cluster dictionary or the FR dictionary

							
							#######
							
							
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
								#print end_time_obj, 'no cluster'
								continue  #if we don't have a cluster number it's not in an FT time!!
							cluslist_current_cluster_no = cluster[0][0]
							cluster_start_time = datetime.utcfromtimestamp(cluster[0][1])
							
									
							
							#add data to list in cluster dictionaries (1 list per cluster time early night/late night)
							if ((cluster_start_time) <= end_time_obj < (cluster_start_time+timedelta(hours=6))):

								if cluslist_current_cluster_no == 7:
									sampling_duration_GBPS = sampling_duration_GBPS + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 								
									for key in rBC_FT_data_cluster_GBPS:
										key_value = float(key)
										interval_end = key_value + interval_length
										if BC_VED >= key_value and BC_VED < interval_end:
											rBC_FT_data_cluster_GBPS[key][0] = rBC_FT_data_cluster_GBPS[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_cluster_GBPS[key][1] = rBC_FT_data_cluster_GBPS[key][1] + (1*sample_factor)
											rBC_FT_data_all[key][0] = rBC_FT_data_all[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_all[key][1] = rBC_FT_data_all[key][1] + (1*sample_factor)
											
											
												
								if cluslist_current_cluster_no == 1:
									sampling_duration_cluster_1 = sampling_duration_cluster_1 + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 
									for key in rBC_FT_data_cluster_1:
										key_value = float(key)
										interval_end = key_value + interval_length
										if BC_VED >= key_value and BC_VED < interval_end:
											rBC_FT_data_cluster_1[key][0] = rBC_FT_data_cluster_1[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_cluster_1[key][1] = rBC_FT_data_cluster_1[key][1] + (1*sample_factor)
											rBC_FT_data_all[key][0] = rBC_FT_data_all[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_all[key][1] = rBC_FT_data_all[key][1] + (1*sample_factor)
											
								if cluslist_current_cluster_no == 2:
									sampling_duration_cluster_2 = sampling_duration_cluster_2 + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 
									for key in rBC_FT_data_cluster_2:
										key_value = float(key)
										interval_end = key_value + interval_length
										if BC_VED >= key_value and BC_VED < interval_end:
											rBC_FT_data_cluster_2[key][0] = rBC_FT_data_cluster_2[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_cluster_2[key][1] = rBC_FT_data_cluster_2[key][1] + (1*sample_factor)
											rBC_FT_data_all[key][0] = rBC_FT_data_all[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_all[key][1] = rBC_FT_data_all[key][1] + (1*sample_factor)
											
								if cluslist_current_cluster_no == 3:
									sampling_duration_cluster_3 = sampling_duration_cluster_3 + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 
									for key in rBC_FT_data_cluster_3:
										key_value = float(key)
										interval_end = key_value + interval_length
										if BC_VED >= key_value and BC_VED < interval_end:
											rBC_FT_data_cluster_3[key][0] = rBC_FT_data_cluster_3[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_cluster_3[key][1] = rBC_FT_data_cluster_3[key][1] + (1*sample_factor)
											rBC_FT_data_all[key][0] = rBC_FT_data_all[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_all[key][1] = rBC_FT_data_all[key][1] + (1*sample_factor)
											
								if cluslist_current_cluster_no == 4:
									sampling_duration_cluster_4 = sampling_duration_cluster_4 + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 
									for key in rBC_FT_data_cluster_4:
										key_value = float(key)
										interval_end = key_value + interval_length
										if BC_VED >= key_value and BC_VED < interval_end:
											rBC_FT_data_cluster_4[key][0] = rBC_FT_data_cluster_4[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_cluster_4[key][1] = rBC_FT_data_cluster_4[key][1] + (1*sample_factor)
											rBC_FT_data_all[key][0] = rBC_FT_data_all[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_all[key][1] = rBC_FT_data_all[key][1] + (1*sample_factor)
								
								if cluslist_current_cluster_no == 5:
									sampling_duration_cluster_5 = sampling_duration_cluster_5 + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 
									for key in rBC_FT_data_cluster_5:
										key_value = float(key)
										interval_end = key_value + interval_length
										if BC_VED >= key_value and BC_VED < interval_end:
											rBC_FT_data_cluster_5[key][0] = rBC_FT_data_cluster_5[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_cluster_5[key][1] = rBC_FT_data_cluster_5[key][1] + (1*sample_factor)
											rBC_FT_data_all[key][0] = rBC_FT_data_all[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_all[key][1] = rBC_FT_data_all[key][1] + (1*sample_factor)
								
								if cluslist_current_cluster_no == 6:
									sampling_duration_cluster_6 = sampling_duration_cluster_6 + end_time - start_time #need duration to calc sampled volume later for concs
									sampling_duration_allFT = sampling_duration_allFT + end_time - start_time 
									for key in rBC_FT_data_cluster_6:
										key_value = float(key)
										interval_end = key_value + interval_length
										if BC_VED >= key_value and BC_VED < interval_end:
											rBC_FT_data_cluster_6[key][0] = rBC_FT_data_cluster_6[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_cluster_6[key][1] = rBC_FT_data_cluster_6[key][1] + (1*sample_factor)
											rBC_FT_data_all[key][0] = rBC_FT_data_all[key][0] + (BC_mass*sample_factor)
											rBC_FT_data_all[key][1] = rBC_FT_data_all[key][1] + (1*sample_factor)
											
									
						f.close()
						
			os.chdir(directory)

cnx.close()			
print 'neg times', argh, ok, argh*100./(argh+ok)
print err_count, non_err_count, err_count*100./(err_count+non_err_count)
average_flow = 120

total_sampled_volume_1 = sampling_duration_cluster_1*average_flow/60
total_sampled_volume_2 = sampling_duration_cluster_2*average_flow/60
total_sampled_volume_3 = sampling_duration_cluster_3 *average_flow/60
total_sampled_volume_4 = sampling_duration_cluster_4*average_flow/60
total_sampled_volume_5 = sampling_duration_cluster_5 *average_flow/60
total_sampled_volume_6 = sampling_duration_cluster_6*average_flow/60
total_sampled_volume_GBPS = sampling_duration_GBPS*average_flow/60
total_sampled_volume_allFT = sampling_duration_allFT*average_flow/60
total_sampled_volume_fresh = sampling_duration_fresh*average_flow/60

#v=create lists
rBC_FT_data_cluster_1_l = []
rBC_FT_data_cluster_2_l = []
rBC_FT_data_cluster_3_l = []
rBC_FT_data_cluster_4_l = []
rBC_FT_data_cluster_5_l = []
rBC_FT_data_cluster_6_l = []
rBC_FT_data_cluster_GBPS_l = []
rBC_FT_data_all_l = []
rBC_FT_data_fresh_l = []

#put lists etc in array
binned_data_lists = [
[rBC_FT_data_cluster_1 ,rBC_FT_data_cluster_1_l , total_sampled_volume_1,'c1'],
[rBC_FT_data_cluster_2 ,rBC_FT_data_cluster_2_l , total_sampled_volume_2,'c2'],
[rBC_FT_data_cluster_3 ,rBC_FT_data_cluster_3_l , total_sampled_volume_3,'c3'],
[rBC_FT_data_cluster_4 ,rBC_FT_data_cluster_4_l , total_sampled_volume_4,'c4'],
[rBC_FT_data_cluster_5 ,rBC_FT_data_cluster_5_l , total_sampled_volume_5,'c5'],
[rBC_FT_data_cluster_6 ,rBC_FT_data_cluster_6_l , total_sampled_volume_6,'c6'],
[rBC_FT_data_cluster_GBPS ,rBC_FT_data_cluster_GBPS_l , total_sampled_volume_GBPS,'GBPS'],
[rBC_FT_data_all ,rBC_FT_data_all_l , total_sampled_volume_allFT,'all_FT'],
[rBC_FT_data_fresh ,rBC_FT_data_fresh_l , total_sampled_volume_fresh,'fresh'],
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
		row[1] = row[1]/(math.log(row[0]+interval_length)-math.log(row[0])) #d/dlog(VED)
		row[2] = row[2]/(math.log(row[0]+interval_length)-math.log(row[0])) #d/dlog(VED)
		row[0] = row[0]+interval_length/2 #correction for our binning code recording bin starts as keys instead of midpoints


#write final list of interval data to file and pickle
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/size_distrs/from ptxt v2/')

for list in binned_data_lists:
	file = open('AD_corr - size distr - FT - ' + list[3] + '.txt', 'w')
	file.write('size_bin_midpoint(VEDnm)' + '\t'+ 'dM/dlog(VED)_(ng/cm3)' + '\t'+ 'd#/dlog(VED)_(#/cm3)' +  '\t' + 'dM(VED)_(ng/cm3)' +  '\t'+  'd#(VED)_(#/cm3)' + '\n')
	file.write('total sampled volume:' + str(list[2]) + 'cc' + '\n')
	for row in list[1]:
		line = '\t'.join(str(x) for x in row)
		file.write(line + '\n')
	file.close()

	file = open('AD_corr - size distr - FT - ' + list[3] + '.sdbinpickl', 'w')
	pickle.dump(list[1], file)
	file.close()

