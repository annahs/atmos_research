import sqlite3
from datetime import datetime
from pprint import pprint
import sys
import numpy as np

conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()





#sp2b_file TEXT, 			eg 20120405x001.sp2b
#file_index INT, 			
#instr TEXT,				eg UBCSP2, ECSP2
#instr_locn TEXT,			eg WHI, DMT, POLAR6
#particle_type TEXT,		eg PSL, nonincand, incand, Aquadag
#particle_dia FLOAT,				
#unix_ts_utc FLOAT,
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
#coat_thickness_from_actual_scat_amp FLOAT,
#FF_fit_function TEXT,
#LF_fit_function TEXT,
#zeroX_to_LEO_limit FLOAT
#UNIQUE (sp2b_file, file_index, instr)
#)''')

#c.execute('''ALTER TABLE SP2_coating_analysis ADD COLUMN FF_fit_function TEXT''')
#c.execute('''ALTER TABLE SP2_coating_analysis ADD COLUMN zeroX_to_LEO_limit FLOAT''')

#c.execute('''CREATE INDEX SP2_coating_analysis_index1 ON SP2_coating_analysis(instr,instr_locn,particle_type,unix_ts_utc,unix_ts_utc,FF_gauss_width,zeroX_to_peak)''')

#c.execute('''SELECT * FROM SP2_coating_analysis''')
c.execute('''DELETE FROM SP2_coating_analysis WHERE instr=? and instr_locn=? and particle_type=?''', ('UBCSP2', 'POLAR6','nonincand' ))

#names = [description[0] for description in c.description]
#pprint(names)
#print c.fetchone()
#


conn.close()