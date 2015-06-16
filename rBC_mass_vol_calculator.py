import sys
import os
from pprint import pprint
from decimal import Decimal
import pickle
from SP2_particle_record_UTC import ParticleRecord
import matplotlib.pyplot as plt
import numpy as np




BC_masses = [0.25,0.94,1.63,3.86,5.5,7.55,10.05]
density = 1.8


for BC_mass in BC_masses:
	BC_VED = (((BC_mass/(10**15*density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
	print BC_mass
	print BC_VED
	
	