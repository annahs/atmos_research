import sys
import os
from pprint import pprint
from decimal import Decimal
import pickle
from SP2_particle_record_UTC import ParticleRecord
import matplotlib.pyplot as plt
import numpy as np
import math



BC_masses = [0.25,.4,4,6,8,10,12.5,41]
density = 1.8

sig = 16.700000000000045
print (0.18569 + 8.7668e-3 * sig + 8.8322e-7 * sig*sig)*0.7
print 0.01081*sig  - 0.32619
sys.exit()

for BC_mass in BC_masses:
	BC_VED = (((BC_mass/(10**15*density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
	BC_VED2 = (BC_mass**(1/3.0))*101.994391398 #VED in nm with 10^15fg/g and 10^7nm/cm
	print BC_mass
	print BC_VED
	#print BC_VED2
	
	
for BC_VED in range(70,230,10):
	mass = ((BC_VED/(10.**7))**3)*(math.pi/6.)*1.8*(10.**15)
	signal = (mass - 0.19238)/0.0031
	UL_mass = 0.00338*signal + 0.259713
	err = (UL_mass-mass)*100/mass
	print BC_VED,mass, signal, err
	
