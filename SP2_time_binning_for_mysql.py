import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
import mysql.connector
import pickle
import math

#pull all records from individ particle table in DB - ordered by ts
#startog at 20090620 midnight (UTC)
#find all records in 2min intervall
#when reach first past interval take mean and wirte to db, then move to next interval
#limits - min and max rBC mass (70-220nm)


particle_collection_start_time double 
particle_collection_end_time double 
sample_flow float 
incand_pk_height float 
incand_sat_flag tinyint(1) 
calc_BC_mass float 
calc_BC_mass_LL float 
calc_BC_mass_UL float 
location varchar(45) 
instr

query = ("SELECT particle_collection_start_time, particle_collection_end_time, sample_flow, calc_BC_mass,calc_BC_mass_LL,calc_BC_mass_UL FROM employees "
         "WHERE hire_date BETWEEN %s AND %s")

hire_start = datetime.date(1999, 1, 1)
hire_end = datetime.date(1999, 12, 31)

cursor.execute(query, (hire_start, hire_end))

for (first_name, last_name, hire_date) in cursor:
  print("{}, {} was hired on {:%d %b %Y}".format(
    last_name, first_name, hire_date))