#bin .ptxt data into desired time intervals
#ptxt files from the UTC code are in UTC
#final conversion to correct timezone from UTC happens here

import sys
import os
import datetime
from datetime import timedelta
from datetime import datetime
import calendar
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import pickle
import sys
import calendar
import math

#outputs timestamp of the bin middle point, number/cm3,  fg/cm3 BC, and sampling duration in s
#takes in .ptxt file with format [sampling interval start, sampling interval end, incandecence flag, incandecence saturated flag, BC mass]

def bin_data_by_time(parameters):
    os.chdir(parameters['directory'])
   
    #create new list for final binned data
    binned_data = []
                   
    #initialize holder variables
    interval_incand_count = 0
    interval_BC_mass = 0
    interval_BC_mass_LL = np.nan
    interval_BC_mass_UL = np.nan
    interval_sampling_duration = 0 
    BC_mass_LL = np.nan
    BC_mass_UL = np.nan
    sample_factor = parameters['current_sample_factor']
    
    #get list of sample factors changes
    sample_factor_list = parameters['sampling_factors']
    
    #set start time for intervals (midnight of appropriate day) and interval length
    #then calc the end time for the first interval in UNIX timestamp format for comparing to data (should be midnight + interval length)
    #somewhat lengthy code, but clearer I think to leave it broken out like this
    interval_length = parameters['binning_interval'] #in sec
    print interval_length
    start_dateandtime = parameters['time_binning_start'] #sets the start time and date
    print start_dateandtime
    interval_timedelta = timedelta(seconds=interval_length) #defines a timedelta object of interval length (this can be added to datetime objects)
    first_interval_end = start_dateandtime + interval_timedelta #calc end of first interval
    current_interval_end = calendar.timegm(first_interval_end.timetuple()) #converts interval end back to UNIX timestamp
      
    for file in os.listdir('.'):
        if file.endswith('.ptxt'):
            print file
            f = open(file, 'r+')
            first_interval = True
            f.readline()
            
            
            for line in f:
                newline = line.split('\t')
                start_time = float(newline[0])
                end_time = float(newline[1])
                incand_flag = float(newline[2])
                incand_sat_flag = float(newline[3])
                BC_mass = float(newline[4])
                
                if parameters['use_new_calib'] == True:
                    if parameters['BC_calib3'] == 0:
                        pk_ht = (BC_mass - parameters['BC_calib1'])/parameters['BC_calib2']
                    else:
                        pk_ht = PeakHtFromMass(BC_mass,  parameters['BC_calib1'],  parameters['BC_calib2'],  parameters['BC_calib3'])
                    
                    BC_mass = parameters['BC_calib2_new']*pk_ht + parameters['BC_calib1_new'] 
                    BC_mass_LL = (parameters['BC_calib2_new']-parameters['BC_calib2_new_err'])*pk_ht + (parameters['BC_calib1_new'] - parameters['BC_calib1_new_err'])
                    BC_mass_UL = (parameters['BC_calib2_new']+parameters['BC_calib2_new_err'])*pk_ht + (parameters['BC_calib1_new'] + parameters['BC_calib1_new_err'])
                    
               

                #set correct sample factor
                if sample_factor_list:       
                    first_sample_factor_time = calendar.timegm(sample_factor_list[0][0].utctimetuple()) #get UNIX timesoatmp for first sample factor time in UTC 
                    first_sample_factor_time = first_sample_factor_time + parameters['timezone']*3600# add the time delta if ptxt files still not UTC
                    
                    if start_time >= first_sample_factor_time:
                        sample_factor = float(sample_factor_list[0][1])
                        parameters['current_sample_factor'] = sample_factor
                        sample_factor_list.pop(0)

                
                #we need to hop ahead to the first interval that contains data
                #in case collection starts late in the day, we don't want to cycle through all our data in the first 'interval'
                if first_interval == True:
                    while end_time > current_interval_end: 
                        current_interval_end = current_interval_end + interval_length
                    first_interval = False
                
                #start calculating values for data within the current interval
                if end_time <= current_interval_end and start_time >= (current_interval_end - interval_length):
                    interval_incand_count = interval_incand_count + incand_flag
                    interval_sampling_duration = interval_sampling_duration + end_time - start_time

                    if incand_sat_flag == False:
                        if BC_mass >= parameters['BC_min'] and BC_mass <= parameters['BC_max']:
                            interval_BC_mass = interval_BC_mass + BC_mass
                            interval_BC_mass_LL = interval_BC_mass_LL + BC_mass_LL
                            interval_BC_mass_UL = interval_BC_mass_UL + BC_mass_UL
                            
                if end_time > current_interval_end:
                    
                    #do final calcs and write to binned_data list
                    if interval_sampling_duration > 0:
                        interval_sampled_volume = interval_sampling_duration*parameters['avg_flow']/60 #flow is in cc/min and sampling duration is in sec, so use min/60sec to get vol in cc
                        
                        
                        interval_mid_time = current_interval_end - interval_length/2 + parameters['timezone']*3600 #final conversion to correct timezone from UTC here
                        

                        incand_number_conc = interval_incand_count*sample_factor/interval_sampled_volume #/cm3
                        BC_mass_conc = interval_BC_mass*sample_factor/interval_sampled_volume  #fg/cm3 == ng/m3
                        BC_mass_conc_LL = interval_BC_mass_LL*sample_factor/interval_sampled_volume
                        BC_mass_conc_UL = interval_BC_mass_UL*sample_factor/interval_sampled_volume
                        
                        #only write to file is we have found more than 1 particle in the interval (helps correct for data such as WHI ECSP2 2009 where we collected 1/15min and some intervals only catch a very little data)
                        if interval_incand_count > 1:  
                            binned_data.append([interval_mid_time, incand_number_conc, BC_mass_conc, BC_mass_conc_LL, BC_mass_conc_UL, interval_sampling_duration, interval_incand_count ])
                        
                    #clear holder variables
                    interval_incand_count = 0
                    interval_BC_mass = 0
                    interval_BC_mass_LL = 0
                    interval_BC_mass_UL = 0
                    interval_sampling_duration = 0
                    
                    #do calcs on current row for next interval bin
                    interval_incand_count = interval_incand_count + incand_flag
                    interval_sampling_duration = interval_sampling_duration + end_time - start_time

                    if incand_sat_flag == False:
                        if BC_mass >= parameters['BC_min']:
                            interval_BC_mass = interval_BC_mass + BC_mass
                            interval_BC_mass_LL = interval_BC_mass_LL + BC_mass_LL
                            interval_BC_mass_UL = interval_BC_mass_UL + BC_mass_UL
                    
                    if end_time <= current_interval_end + interval_length:
                        current_interval_end = current_interval_end + interval_length
                        
                    if end_time > current_interval_end + interval_length:
                        while end_time > current_interval_end + interval_length: 
                            current_interval_end = current_interval_end + interval_length
                            #print 'looking'
            
            f.close() 
            
            print sample_factor, type(sample_factor)
                           
            #take care of final interval after last row
            if interval_sampling_duration > 0:
                interval_sampled_volume = interval_sampling_duration*parameters['avg_flow']/60 #flow is in cc/min and sampling duration is in sec, so use min/60sec to get vol in cc
                
                interval_mid_time = current_interval_end - interval_length/2 + parameters['timezone']*3600 #final conversion to correct timezone from UTC here
                    
                incand_number_conc = interval_incand_count*sample_factor/interval_sampled_volume
                BC_mass_conc = interval_BC_mass*sample_factor/interval_sampled_volume
                BC_mass_conc_LL = interval_BC_mass_LL*sample_factor/interval_sampled_volume
                BC_mass_conc_UL = interval_BC_mass_UL*sample_factor/interval_sampled_volume
                
                if interval_incand_count > 1:
                    binned_data.append([interval_mid_time, incand_number_conc, BC_mass_conc, BC_mass_conc_LL, BC_mass_conc_UL, interval_sampling_duration, interval_incand_count ])
            
            #write final list of interval data to file and pickle
            file = open('final_binned_data_' + parameters['folder'] + '.txt', 'w')
            file.write('interval_mid_time' + '\t' + 'incand_number_conc(#/cm3)' + '\t' +  'BC_mass_conc(ng/m3)'+ '\t' +  'BC_mass_conc_LL(ng/m3)'+ '\t' +  'BC_mass_conc_UL(ng/m3)' + '\t' +  'interval_sampling_duration(s)' + '\t' +  'interval_incand_count' + '\n')
            for row in binned_data:
                line = '\t'.join(str(x) for x in row)
                file.write(line + '\n')
            file.close()
            
            file = open('final_binned_data_' + parameters['folder'] + '_' + str(parameters['binning_interval']) + 'sbins.binpckl', 'w')
            pickle.dump(binned_data, file)
            file.close()
            
            os.chdir(os.pardir)
            file = open('final_binned_data_' + parameters['folder'] + '_' + str(parameters['binning_interval']) + 'sbins.binpckl', 'w')
            pickle.dump(binned_data, file)
            file.close()
            
            
            
            
            
#this helper method allows cenversion of BC mass from a value arrived at via an old calibration to a value arrived at via a new calibration
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

