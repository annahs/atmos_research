import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import calendar
from datetime import datetime
import mysql.connector


class CoatingData:

	def __init__(self,lookup_file,incand_saturation):
		self.rBC_density = 1.8 
		self.incand_sat = incand_saturation
		
		lookup = open(lookup_file, 'r')
		self.lookup_table = pickle.load(lookup)
		lookup.close()
		
		
	def get_rBC_mass(self,incand_pk_ht, instrument, year):
		if year == 2012 and instrument=='UBCSP2':
			rBC_mass = 0.003043*incand_pk_ht + 0.24826 #AD corrected linear calibration for UBCSP2 at WHI 2012
		if year == 2010 and instrument=='ECSP2':
			rBC_mass = 0.01081*incand_pk_ht - 0.32619  #AD corrected linear calibration for ECSP2 at WHI 2010
		if year == 2015 and instrument=='UBCSP2':
			#rBC_mass = 0.00289*incand_pk_ht + 0.15284  #AD corrected linear calibration - Jan calib
			rBC_mass = 0.00310*incand_pk_ht + 0.19238  #AD corrected linear calibration - Alert calib
		return rBC_mass

	def get_coating_thickness(self, BC_VED,LEO_amp):
		#get the coating thicknesses from the lookup table which is a dictionary of dictionaries, the 1st keyed with BC core size and the second being coating thicknesses keyed with calc scat amps                  
		coating_lookup_table = self.lookup_table
		core_diameters = sorted(coating_lookup_table.keys())
		prev_diameter = core_diameters[0]

		for core_diameter in core_diameters:
			if core_diameter > BC_VED:
				core_dia_to_use = prev_diameter
				break
			prev_diameter = core_diameter
		
		scat_amp_to_use = np.nan
		scattering_amps = sorted(coating_lookup_table[core_dia_to_use].keys())
		for scattering_amp in scattering_amps:
			if LEO_amp < scattering_amp:
				scat_amp_to_use = scattering_amp
				break
		
		if np.isnan(scat_amp_to_use) == True:
			coating_thickness = np.nan
		else:
			coating_thickness = coating_lookup_table[core_dia_to_use].get(scat_amp_to_use, np.nan) # returns value for the key, or none
		
		return coating_thickness




