import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
import mysql.connector
import pickle
import math


instrument = 'UBCSP2' #'UBCSP2' #ECSP2
instrument_locn = 'WHI' #'WHI' POLAR6


#this script will run through all the .ptxt files for the WHI data and put the info into the mySQL database

#1. #alter the dates to set limits on data analysis range
start_analysis_at = datetime.strptime('20080601','%Y%m%d')
end_analysis_at = datetime.strptime('20120411','%Y%m%d')

#2. set the data_dir as the parent folder for the data, the program expects the data dir to contain subfolders named by day (eg 20120101) that contain the actual data
#note that UTC timestamping was used in the ptxt file for 2009 and for <20120412 otherwise timestamps are in PST
data_dir = 'D:/2012/WHI_UBCSP2/Binary/' #'D:/2009/WHI_ECSP2/Binary/'#'D:/2012/WHI_UBCSP2/Binary/' # 'D:/2010/WHI_ECSP2/Binary/'  #'D:/2012/WHI_UBCSP2/Binary/' 
os.chdir(data_dir)

parameters = {
#old calib - need this to retreive incand peak heights which I did not oiriginally write to the ptxt files
#the first three variables are the terms of the calibration fit line which gives mass in fg/count (eg. for the UBC_SP2 in 2012 use 0.20699+0.00246x-1.09254e-7x2) 2010: 0.156 + 0.00606x + 6.3931e-7x2

'BC_calib1': 0.20699 , #0 order term
'BC_calib2': 0.00246,   #1st order term
'BC_calib3': - 1.09254e-7,   #2nd order term
'BC_density': 1.8, #density of ambient BC in g/cc



#new - AD corrected calib with uncertinaty, 2009:(0.0172(+-0.00037)x + 0.01244(+-0.14983))  2010:(0.01081(+-0.0002199)x  - 0.32619(+-0.16465))
'BC_calib1_new':  0.24826, #0 order term
'BC_calib1_new_err': 0.05668, #0 order term +- uncertainty
'BC_calib2_new':  0.003043,   #1st order term
'BC_calib2_new_err': 0.0002323, #1st order term +- uncertainty
}

#sample factor list - 2012 only
sample_factor_list_file = open('D:/2012/WHI_UBCSP2/Binary/sample_rate_changes.srpckl', 'r')
sample_factor_list = pickle.load(sample_factor_list_file)
sample_factor_list_file.close()




#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

#create insert statement variable for database updating
add_particle = ('INSERT IGNORE INTO whi_sp2_single_incand_particle_data'
              '(location, instr, particle_collection_start_time,particle_collection_end_time,sample_flow,incand_pk_height,incand_sat_flag,calc_BC_mass,calc_BC_mass_LL,calc_BC_mass_UL)'
              'VALUES (%(instrument_locn)s,%(instrument)s,%(particle_collection_start_time)s,%(particle_collection_end_time)s,%(sample_flow)s,%(incand_pk_height)s,%(incand_sat_flag)s,%(calc_BC_mass)s,%(calc_BC_mass_LL)s,%(calc_BC_mass_UL)s)')


#this helper method allows conversion of BC mass from a value arrived at via an old calibration to a value arrived at via a new calibration
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
        # This equation has one solution
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
			

for directory in os.listdir(data_dir):
	if os.path.isdir(directory) == True and directory.startswith('20'):
	
		folder_date = datetime.strptime(directory, '%Y%m%d')
	
		if start_analysis_at <= folder_date <= end_analysis_at:
	
			current_dir = os.path.abspath(directory)
			os.chdir(current_dir)
			
			for file in os.listdir('.'):
				if file.endswith('.ptxt'):
					print file
					f = open(file, 'r+')
					f.readline()

					for line in f:
						newline = line.split('\t')
						start_time = float(newline[0])# + 28800 #+28800 converts to UTC from PST
						end_time = float(newline[1])# + 28800 #+28800 converts to UTC from PST
						incand_flag = float(newline[2])
						incand_sat_flag = int(newline[3])
						BC_mass = float(newline[4])
						
						
						if parameters['BC_calib3'] == 0:
							pk_ht = (BC_mass - parameters['BC_calib1'])/parameters['BC_calib2']
						else:
							pk_ht = PeakHtFromMass(BC_mass,  parameters['BC_calib1'],  parameters['BC_calib2'],  parameters['BC_calib3'])
						
						BC_mass = parameters['BC_calib2_new']*pk_ht + parameters['BC_calib1_new'] 
						BC_mass_LL = (parameters['BC_calib2_new']-parameters['BC_calib2_new_err'])*pk_ht + (parameters['BC_calib1_new'] - parameters['BC_calib1_new_err'])
						BC_mass_UL = (parameters['BC_calib2_new']+parameters['BC_calib2_new_err'])*pk_ht + (parameters['BC_calib1_new'] + parameters['BC_calib1_new_err'])
							

						##set correct sample factor - all of 2009 and 2010 were run at 1/1 -
						##note these are in UTC
						#if sample_factor_list:       
						#	first_sample_factor_time = calendar.timegm(sample_factor_list[0][0].utctimetuple()) #get UNIX timesoatmp for first sample factor time in UTC 
						#	#first_sample_factor_time = first_sample_factor_time - 8*3600# use if ptxt files still not UTC, ie post 20120411
						#	
						#	if start_time >= first_sample_factor_time:
						#		sample_factor = float(sample_factor_list[0][1])
						#		sample_factor_list.pop(0)
								
						
						particle_data = {
						'instrument': instrument,
						'instrument_locn':instrument_locn,
						'particle_collection_start_time': start_time,
						'particle_collection_end_time': end_time,
						'sample_flow': 120.,
						'incand_pk_height': pk_ht,
						'incand_sat_flag': incand_sat_flag,
						'calc_BC_mass': BC_mass,
						'calc_BC_mass_LL': BC_mass_LL,
						'calc_BC_mass_UL': BC_mass_UL,
						}
						
					
						cursor.execute(add_particle, particle_data)
						cnx.commit()

			os.chdir(data_dir)

cnx.close()			

