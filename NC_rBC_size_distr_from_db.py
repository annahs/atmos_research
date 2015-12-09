import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import pickle
import math
import calendar
import matplotlib.pyplot as plt
import copy


start_time = datetime(2015,4,5,0,0)
end_time = datetime(2015,4,6,0,0)
min_BC_VED = 70
max_BC_VED = 220


UNIX_start_time = calendar.timegm(start_time.utctimetuple())
UNIX_end_time = calendar.timegm(end_time.utctimetuple())


min_rBC_mass = ((min_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
max_rBC_mass = ((max_BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute(('SELECT rBC_mass_fg from polar6_coating_2015 where UNIX_UTC_ts >= %s and UNIX_UTC_ts < %s and particle_type = %s and rBC_mass_fg >= %s and rBC_mass_fg <= %s '),(UNIX_start_time,UNIX_end_time,'incand', min_rBC_mass,max_rBC_mass))

