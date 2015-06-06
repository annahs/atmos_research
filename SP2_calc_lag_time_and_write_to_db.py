import sys
import os
from datetime import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
from SP2_particle_record_UTC import ParticleRecord
import sqlite3

data_dir = 'D:/2012/WHI_UBCSP2/Binary/' 
start_analysis_at = datetime.strptime('20120408','%Y%m%d')
end_analysis_at = datetime.strptime('20120601','%Y%m%d')
record_size_bytes = 1498 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458)

instrument = 'UBCSP2'
instrument_locn = 'WHI'
type_particle = 'incand' #PSL, nonincand, incand


#**********parameters dictionary**********
parameters = {
'acq_rate': 5000000,
#date and time
'timezone':-8,
}

#connect to database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

os.chdir(data_dir)
for directory in os.listdir(data_dir):
	if os.path.isdir(directory) == True and directory.startswith('20'):
		parameters['folder']= directory
		folder_date = datetime.strptime(directory, '%Y%m%d')		
		if folder_date >= start_analysis_at and folder_date <= end_analysis_at:
			parameters['directory']=os.path.abspath(directory)
			os.chdir(parameters['directory'])

			print parameters['folder']
			
			for file in os.listdir('.'):
				if file.endswith('.sp2b'):	
					print file
					f2 = open(file, 'rb')			
					
					path = parameters['directory'] + '/' + str(file)
					file_bytes = os.path.getsize(path) #size of entire file in bytes
					number_of_records = (file_bytes/record_size_bytes)-1
					
					record_index = 0
					while record_index < number_of_records:
						record = f2.read(record_size_bytes)
						
						#only use files that are in the db
						c.execute('''SELECT * FROM SP2_coating_analysis WHERE instr=? and instr_locn=? and particle_type=? and sp2b_file=? and file_index=?''', 
						(instrument,instrument_locn,type_particle, file, record_index))
						
						result = c.fetchone()
					
						if result is not None:
							particle_record = ParticleRecord(record, parameters['acq_rate'], parameters['timezone'])	
							particle_record.incandPeakInfo() #run the incandPeakInfo method to retrieve various incandescence peak attributes				
							particle_record.scatteringPeakInfo() #run the scatteringPeakInfo method to retrieve various scattering peak attributes			
												
							incand_pk_pos = particle_record.incandMaxPos
							scat_pk_pos = particle_record.scatteringMaxPos

							lag_time_pts = incand_pk_pos-scat_pk_pos
			
							c.execute('''UPDATE SP2_coating_analysis SET 
							lag_time_fit_to_incand=?
							WHERE sp2b_file=? and file_index=? and instr=?''', 
							(lag_time_pts,
							file, record_index, instrument))
			
						record_index+=1    
			
					f2.close()        
				conn.commit()
			
			os.chdir(data_dir)
conn.close()	

