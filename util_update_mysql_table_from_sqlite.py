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

		  
			  


i =0 
instrument = 'UBCSP2'
instrument_locn = 'POLAR6'

for row in c.execute('''SELECT 
sp2b_file,
file_index,
zeroX_to_peak,
FF_peak_pos
FROM SP2_coating_analysis WHERE instr_locn=? and particle_type =? and unix_ts_utc <?''', 
(instrument_locn,'PSL',1422576000)):	
	sp2b_file = row[0]
	file_index = row[1]
	zeroX_to_peak =	row[2]
	FF_peak_pos = row[3]
	zeroX_posn = zeroX_to_peak+FF_peak_pos
	
	cursor.execute(('UPDATE polar6_coating_2015 SET actual_zero_x_posn = %s WHERE sp2b_file = %s and file_index = %s'),(zeroX_posn,sp2b_file,file_index))		
	cnx.commit()

	i+=1
	if (i % 1000) == 0:
		print 'record: ', i
	
conn.close()
cnx.close()
