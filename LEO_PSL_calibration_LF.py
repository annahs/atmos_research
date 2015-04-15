import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
from scipy.optimize import curve_fit
from scipy import stats
from SP2_particle_record_UTC import ParticleRecord
from struct import *
import hk_new
import hk_new_no_ts_LEO
from scipy import linspace, polyval, polyfit, sqrt, stats
import math
import sqlite3

#setup
current_dir = 'D:/2012/WHI_UBCSP2/Calibrations/20120328/PSL/Binary/200nm/'
os.chdir(current_dir)

num_records_to_analyse = 10000
LEO_factor = 20  # fit up to 1/this_value of max peak height (ie 1/20 is 5%)
show_LEO_fit = False
instrument = 'WHI_UBCSP2'
instrument_locn = 'WHI'
type_particle = 'PSL'

conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

#####rows in SP2_coating_analysis table
#id INTEGER PRIMARY KEY AUTOINCREMENT,
#sp2b_file TEXT, 
#file_index INT, 
#instr TEXT,
#instr_locn TEXT,
#particle_type TEXT,		
#particle_dia FLOAT,				
#date TIMESTAMP,
#actual_scat_amp FLOAT,
#actual_peak_pos INT,
#FF_scat_amp FLOAT,
#FF_peak_pos INT,
#FF_gauss_width FLOAT,
#zeroX_to_peak FLOAT,
#LF_scat_amp FLOAT,
#incand_amp FLOAT,
#UNIQUE (sp2b_file, file_index, instr)
	
c.execute('''SELECT FF_gauss_width, zeroX_to_peak FROM SP2_coating_analysis WHERE instr=? and instr_locn=? and particle_type=?''', (instrument,instrument_locn,type_particle))
result = c.fetchall()

mean_gauss_width = np.mean([row[0] for row in result])
mean_zeroX_to_peak = np.mean([row[1] for row in result]) 

#calculate half-width at x% point (eg 5% for factor 20)  
HWxM = math.sqrt(2*math.log(LEO_factor))*mean_gauss_width
zeroX_to_LEO_limit = HWxM + mean_zeroX_to_peak

print zeroX_to_LEO_limit

#**********parameters dictionary**********

parameters = {
'acq_rate': 5000000,
#file i/o
'directory':current_dir,
#date and time
'timezone':-8,
#will be set by hk analysis
'avg_flow':120, #in vccm
#parameter to find bad flow durations
'flow_min' : 115,
'flow_max' : 125,
'YAG_min' : 4,
'YAG_max' : 6,
'min_good_points' : 10,
#show plots?
'show_plot':False,
}


#start the fitting
for file in os.listdir('.'):
	
	if file.endswith('.sp2b'):
		
		f2 = open(file, 'rb')
		
		print file
		
		path = current_dir + str(file)
		file_bytes = os.path.getsize(path) #size of entire file in bytes
		record_size = 1498 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458)
		number_of_records = (file_bytes/record_size)-1
		if num_records_to_analyse == 'all':
			number_records_toshow =  number_of_records 
		else:
			number_records_toshow = num_records_to_analyse    

		
		## fitting scattering signals to get info for LEO fits
		record_index = 0
		while record_index < number_records_toshow:
			
			##Import and parse binary
			record = f2.read(record_size)
			particle_record = ParticleRecord(record, parameters['acq_rate'], parameters['timezone'])	
			event_time = particle_record.timestamp
			
			#run the scatteringPeakInfo method to retrieve various peak attributes
			particle_record.scatteringPeakInfo()
			
			#get the zero-crossing with the appropriate method
			zero_crossing_pt_LEO = int(round(particle_record.zeroCrossing()))
								
			#grab those records that are in the table 
			c.execute('''SELECT * FROM SP2_coating_analysis WHERE instr=? and instr_locn=? and particle_type=? and sp2b_file=? and file_index=?''', (instrument,instrument_locn,type_particle, file, record_index))
			result = c.fetchone()
			if result is not None:

				#set params for fitting 
				scatteringBaseline = particle_record.scatteringBaseline
				
				#LEO max index sets the x-limit for fitting based on the desired magnification factor
				LEO_max_index = int(round(zero_crossing_pt_LEO-zeroX_to_LEO_limit))
				LEO_min_index = 0
				
				x_vals_all = particle_record.getAcqPoints()
				x_vals_to_use = x_vals_all[LEO_min_index:LEO_max_index]

				y_vals_all = particle_record.getScatteringSignal()
				y_vals_to_use = y_vals_all[LEO_min_index:LEO_max_index]

				center_pos = zero_crossing_pt_LEO-(mean_zeroX_to_peak)
				
				#split detector signal
				y_vals_split = particle_record.getSplitDetectorSignal()
								
				def LEOGauss(x, a, b):
					return b+a*np.exp((-(x-center_pos)**2)/(2*mean_gauss_width**2))

				#run the fitting
				try:
					popt, pcov = curve_fit(LEOGauss, x_vals_to_use, y_vals_to_use)
					
				except:
					popt, pcov = None, None 
					print 'LEO fail'

				if popt != None:
					if popt[0] != None and popt[1] != None:
						LEO_amp = popt[0] 
						LEO_baseline = popt[1]
						
						c.execute('''UPDATE SP2_coating_analysis SET 
							LF_scat_amp=? 
							WHERE sp2b_file=? and file_index=? and instr=?''', 
							(LEO_amp,
							file, record_index, instrument))
			
						
						##only uae data with reasonable LEO amps adn baselines
						#max_allowable_fit_amp = max_peakheight#scat_sat_amp - scatteringBaseline
						#min_allowable_fit_amp = min_peakheight
						#max_baseline_diff = 10
						#baseline_diff = math.fabs(LEO_baseline-scatteringBaseline)
						#
						#if LEO_amp < max_allowable_fit_amp and LEO_amp >= min_allowable_fit_amp and baseline_diff <= max_baseline_diff:
			
						
						if show_LEO_fit == True:
						
							fit_result = LEOGauss(x_vals_all,LEO_amp,LEO_baseline)
							LEO_used = LEOGauss(x_vals_to_use,LEO_amp,LEO_baseline)
									
							print '\n'
							print 'record: ',record_index
							#print particle_record.splitBaseline, particle_record.zeroCrossingPos, particle_record.scatteringMax
							fig = plt.figure()
							ax1 = fig.add_subplot(111)
							ax1.plot(x_vals_all,y_vals_all,'o', markerfacecolor='None')   
							ax1.plot(x_vals_all,fit_result, 'red')
							ax1.plot(x_vals_to_use,y_vals_to_use, color = 'black',linewidth=3)
							#ax1.plot(x_vals_all, y_vals_split, 'o', color ='green')
							plt.axvline(x=zero_crossing_pt_LEO, ymin=0, ymax=1)
							plt.axvline(x=center_pos, ymin=0, ymax=1, color='red')
							plt.show()

					
			record_index+=1    
			
		f2.close()        

conn.commit()
conn.close()

