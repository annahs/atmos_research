import sqlite3
from datetime import datetime
from pprint import pprint
import sys
import numpy as np

conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()




#sp2b_file TEXT, 
#file_index INT, 
#instr TEXT,
#instr_locn TEXT,
#particle_type TEXT,		
#particle_dia FLOAT,				
#UTC_datetime TIMESTAMP,
#actual_scat_amp FLOAT,
#actual_peak_pos INT,
#FF_scat_amp FLOAT,
#FF_peak_pos INT,
#FF_gauss_width FLOAT,
#zeroX_to_peak FLOAT,
#LF_scat_amp FLOAT,
#incand_amp FLOAT,
#lag_time_fit_to_incand FLOAT,
#LF_baseline_pct_diff FLOAT,
#rBC_mass_fg FLOAT,
#coat_thickness_nm FLOAT,
#zero_crossing_posn FLOAT,
#UNIQUE (sp2b_file, file_index, instr)
#)''')

#c.execute('''ALTER TABLE SP2_coating_analysis ADD COLUMN coat_thickness_from_actual_scat_amp_nm FLOAT''')


c.execute('''SELECT * FROM SP2_coating_analysis''')
names = [description[0] for description in c.description]
pprint(names)




conn.close()