#use this script to run the housekeeping analysis, the SP2B file parser, and the time or size binning code in sequence on the files in a single folder. 
#current dir should be set to the parent folder (eg 2012) which contains a folder for each day (eg 20120101)
#ini parser will walk the directory tree and make a list of when sampling factors changed, this is then loaded for future reference
#next, the hk analysis, SP2B parser, and binning code will be run on each day's folder (eg 20120101) in turn 

import SP2B_ini_file_parser_UTC
import SP2B_hk_analysis_UTC
import SP2B_parser_UTC
import SP2B_time_binning_UTC
import sys
from pprint import pprint
import os
import pickle
import numpy as np
from datetime import datetime


#1. #alter the dates to set limits on data analysis range
start_analysis_at = datetime.strptime('20080601','%Y%m%d')
end_analysis_at = datetime.strptime('20120411','%Y%m%d')

#2. set the data_dir as the parent folder for the data, the program expects the data dir to contain subfolders named by day (eg 20120101) that contain the actual data
data_dir = 'D:/2012/WHI_UBCSP2/Binary/' #'D:/2009/WHI_ECSP2/Binary/'# 'D:/2010/WHI_ECSP2/Binary/'  #'D:/2012/WHI_UBCSP2/Binary/' 
os.chdir(data_dir)

#3. set the sample_rate_changes to True if different sampling rates were used over the period of interest (ie 1/10 particles saved to file for a while, hen switching to 1/1, etc)  or set a constant_sample_rate variable if this didn't change
sample_rate_changes = True
constant_sample_rate = 1.0

#4. pick which modules to run 
run_hk_analysis = False
run_SP2B_parser = False
run_time_binning = True

  
#5. set the parameters in the parameters dictionary

#the following dictionaries contains all the parameters that are used for the data analysis
parameters = {

#time
'timezone':-8.,  #-8 for PST, -7 for PDT, -5 for EST (includes Alert) etc

#instrument settings
'current_sample_factor': np.nan, #initialized as nan, no need to change
'acq_rate': 5000000, #in samples/sec
'record_size' : 1498, #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458, CalTech SP2 @Soledad = 1658)

#calibration
#the first three variables are the terms of the calibration fit line which gives mass in fg/count (eg. for the UBC_SP2 in 2012 use 0.20699+0.00246x-1.09254e-7x2) 2014: 1.10702+0.00151x+2.16027E-7x^2
'BC_calib1': 0.20699, #0 order term
'BC_calib2': 0.00246,   #1st order term
'BC_calib3': -1.09254e-7,   #2nd order term
'BC_density': 1.8, #density of ambient BC in g/cc

#sample flow
'avg_flow':120, #in vccm, this will be overwritten by the hk analysis, so no need to change it here

#signal thresholds
'BC_min': 0.324, #detection limit in fg 0.324=70nm-ved
'incand_sat': 3600, #saturation level in counts (this can come from looking at some sample files in the data viewer, or better by generating a histogram of all peak heights and looking for a peak in the distribution at high amplitude) 

#analysis parameters
#time binning
'time_binning_start': datetime.strptime('2008-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'),
'binning_interval': 120, #in secs for time binning
'data_gap':600, #time in seconds which constitutes an overly long gap in the data (instr failure? etc)

#the following parameters are a hack I added to retrieve the original peak heights from files that I had analyzed with a wrong calibration.  I now write the original peak heights to file, so this shouldn't be needed going forward
'use_new_calib':True, 
'BC_calib1_new':  0.24826, #0 order term
'BC_calib1_new_err': 0.05668, #0 order term +- uncertainty
'BC_calib2_new': 0.003043,   #1st order term
'BC_calib2_new_err': 0.0002323, #1st order term +- uncertainty

#parameter to find bad flow and yag durations, this is for the hk analysis 
'flow_min' : 112,
'flow_max' : 130,
'laser_min': 4.0,
'laser_max': 7.0,
'min_good_points' : 10, #this gives the minimum number of 'good' sample flow measurements in a row that need to be detected (ie to know we're not swinging through the good zone during wild oscillations)

#show hk plots?
'show_plot':False,
}


#### no need for further input after this point




#If the sample factor has changed during the measurements (ie the '1 of Every=' in the .ini file changes) then make set sample_rate_changes = True
#if the sample_rate_changes variable is True then the ini_file_parser will be run to get a list of times when these changes occured, the binning code will then use this list to correct for the changes
#if the sample_rate_changes variable is False the constant_sample_rate variable will be used as the sampling factor for all data


if sample_rate_changes == True:
    SP2B_ini_file_parser_UTC.make_sample_factor_list(data_dir, parameters)
    f = open('sample_rate_changes.srpckl', 'r+')
    sample_rates = pickle.load(f)
    f.close()

if sample_rate_changes == False:
    sample_rates = [[datetime.strptime('1900-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'), constant_sample_rate]]


	
##### PART 3 - run the analysis

parameters['sampling_factors'] = sample_rates #table of sampling rates and start times (created above)
	
	
for directory in os.listdir(data_dir):

    if os.path.isdir(directory) == True and directory.startswith('20'):
        

        #add folder info to dictionary
    
        #file i/o
        parameters['folder']= directory
        parameters['directory']= os.path.abspath(directory)

        #date and time
        parameters['date']= directory
        parameters['bin_start']= (directory + ' ' + '00:00') #time is midnight (typically) of this day 
        
        folder_date = datetime.strptime(directory, '%Y%m%d')
        
        if folder_date >= start_analysis_at and folder_date <= end_analysis_at:
                
            #*******HK ANALYSIS************ 
            
            #This should work for the EC Alert flights in spring 2012
            if run_hk_analysis == True:
                print 'hk'
                #avg_flow = SP2B_hk_analysis_UTC.find_bad_hk_durations_with_UTC_time(parameters)
                avg_flow = SP2B_hk_analysis_UTC.find_bad_hk_durations_with_time_since_midnight(parameters)
                parameters['avg_flow'] = avg_flow
            
            #*******DATA ANALYSIS************
            
            ###outputs file with start_time, end_time, incand_flag, incand_sat_flag, BC_mass.  Note: BC mass is in fg

            if run_SP2B_parser == True:
                print 'reading binary'
                SP2B_parser_UTC.parse_sp2b_files(parameters)
                    
            
            #*********BINNING*****************
            
            if run_time_binning == True:
                SP2B_time_binning_UTC.bin_data_by_time(parameters)
                     
            #back to the data dir for the next round
            os.chdir(data_dir)
        