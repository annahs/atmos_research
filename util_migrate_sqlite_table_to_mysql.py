import sys
import os
import numpy as np
import sqlite3
import mysql.connector


#connect to sqlite database
conn = sqlite3.connect('C:/projects/dbs/SP2_data.db')
c = conn.cursor()

#connect to mysql database 
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

add_stats = ('INSERT INTO polar6_coating_2015'
              '(sp2b_file,file_index,instrument,instrument_locn,particle_type,particle_dia,UNIX_UTC_ts,actual_scat_amp,actual_peak_posn,actual_zero_x_posn,FF_scat_amp,FF_peak_posn,FF_gauss_width,incand_amp,LF_scat_amp,LF_baseline_pct_diff,rBC_mass_fg,coat_thickness_nm)'
              'VALUES (%(sp2b_file)s,%(file_index)s,%(instr)s,%(instr_locn)s,%(particle_type)s,%(particle_dia)s,%(unix_ts_utc)s,%(actual_scat_amp)s,%(actual_peak_pos)s,%(zero_crossing_posn)s,%(FF_scat_amp)s,%(FF_peak_pos)s,%(FF_gauss_width)s,%(incand_amp)s,%(LF_scat_amp)s,%(LF_baseline_pct_diff)s,%(rBC_mass_fg)s,%(coat_thickness_nm)s)')

			  
			  


errs =0 
instrument = 'UBCSP2'
instrument_locn = 'POLAR6'

for row in c.execute('''SELECT 
sp2b_file,
file_index,
instr,
instr_locn,
particle_type,
particle_dia,
unix_ts_utc,
actual_scat_amp,
actual_peak_pos,
zero_crossing_posn,
FF_scat_amp,
FF_peak_pos,
FF_gauss_width,
incand_amp,
LF_scat_amp,
LF_baseline_pct_diff,
rBC_mass_fg,
coat_thickness_nm
FROM SP2_coating_analysis WHERE instr = ? and instr_locn=? 
ORDER BY unix_ts_utc''', 
(instrument, instrument_locn)):	
	

	stats = {
	'sp2b_file':			row[0],
	'file_index': 			row[1],
	'instr'	:				row[2],
	'instr_locn':			row[3],
	'particle_type':		row[4],
	'particle_dia': 		row[5],
	'unix_ts_utc': 			row[6],
	'actual_scat_amp':		row[7],
	'actual_peak_pos':		row[8],
	'zero_crossing_posn':	row[9],
	'FF_scat_amp':			row[10],
	'FF_peak_pos':			row[11],
	'FF_gauss_width':		row[12],
	'incand_amp':			row[13],
	'LF_scat_amp':			row[14],
	'LF_baseline_pct_diff':	row[15],
	'rBC_mass_fg':			row[16],
	'coat_thickness_nm':	row[17],
	}

	try: 
		cursor.execute(add_stats, stats)
	except mysql.connector.Error as err:
		print("Something went wrong: {}".format(err))
		errs += 1
	cnx.commit()

print 'errors', errs

conn.close()
cnx.close()