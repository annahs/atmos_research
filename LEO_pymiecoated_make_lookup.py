from pymiecoated import Mie
import numpy as np
import matplotlib.pyplot as plt
import pickle
import math
import sys
import os
from pprint import pprint 

#lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/Forest Fires/2012/SP2-2012/Calibration/'
lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/LEO fitting/LJ-EC-SP2/lookup tables'
#lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/SP2_2010/BB period 2010/EC_SP2/lookup tables/'
#lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/SP2_2010/FT periods 2012/lookup tables/'
os.chdir(lookup_dir)

#************setup********************

wl = 1064 #nm
core_RI = complex(2.26,1.26)#complex(1.95, 0.79)  #from Moteki 2010 (and Laborde and Taylor)
shell_RI = complex(1.5, 0)
PSL_RI = complex(1.59,0)

#UBC 2012 WHI SP2
#scat_cal_limit = 3542 #signal for 300nm PSLs our highest calibration std (b/c we use a polynomial fit for calc scattering vs instr response we can't extrapolate outside the caibration curve)

#LJ EC SP2
scat_cal_limit = 4000

#WHI 2010 SP2
#scat_cal_limit = 3500


def scat_amp(Itotal):
    calc_scattering_amplitude = 112*Itotal  #calibration fit is in origin file for LJ-EC_SP2
    #calc_scattering_amplitude = 3.72*Itotal+9.65  #calibration from Aquadag numbers Jason sent for LJ
    #calc_scattering_amplitude = 231.72*Itotal # 2012 WHI-UBC-SP2
    #calc_scattering_amplitude = 67.76*Itotal  #in C:\Users\Sarah Hanna\Documents\Data\Forest Fires\data tracker.xls  - ECSP2 WHI 2010
    
    return calc_scattering_amplitude
    
    
#**********calc the lookup table*************************

#set the maximum shell radius (note: this is a radius not a thickness)
max_shell_rad = 2300 #in nm*10
shell_step_size = 5 #radius in nm*10, 5 will give 1nm steps in final diameter
core_step_size = 5 #radius in nm*10, 5 will give 1nm steps in final diameter

#set the range and increment value of core radii to be used
core_rad_range = range(300,1100,core_step_size) #these are in nm*10
#core_rad_range = range(500,510,core_step_size) #these are in nm*10


lookup_table = {}

print 'core RI: ', core_RI
print 'shell RI: ', shell_RI

for core_rad in core_rad_range:
    print 'core diameter: ',core_rad*2/10.0, ' nm'
    #for each core size create a dictionary of shell radii and associated scattering amplitudes
    shell_data = {}
    
    #start at zero coating thickness
    shell_rad = core_rad
    
    while shell_rad < max_shell_rad:    

        #account for our nm*10 fudge in mie calcs
        core_radius = core_rad/10
        shell_radius = shell_rad/10

        mie = Mie()
        mie.x = 2*math.pi*core_radius/wl
        mie.m = core_RI
        mie.y = 2*math.pi*shell_radius/wl
        mie.m2 = shell_RI

        Itot = 0
        for theta in range(4, 87):  #4, 87
            cos_angle=math.cos(math.radians(theta))
            S12 = mie.S12(cos_angle)
            I1 = S12[0].real**2 + S12[0].imag**2
            I2 = S12[1].real**2 + S12[1].imag**2
            Itot = Itot+ I1 + I2
            
        for theta in range(94, 177):  #94, 177
            cos_angle=math.cos(math.radians(theta))
            S12 = mie.S12(cos_angle)
            I1 = S12[0].real**2 + S12[0].imag**2
            I2 = S12[1].real**2 + S12[1].imag**2
            Itot = Itot+ I1 + I2
        
        
        coating_thickness = (shell_rad/10.0-core_rad/10.0)
        scattering_amplitude = scat_amp(Itot)

        if scattering_amplitude <= scat_cal_limit:
            shell_data[scattering_amplitude] = coating_thickness
        if scattering_amplitude > scat_cal_limit:
            break
        shell_rad+=shell_step_size  

    #fig = plt.figure()
    #ax1 = fig.add_subplot()
    #plt.scatter(shell_data.keys(), shell_data.values())
    #plt.show()
    
    core_diameter = core_rad*2/10.0+core_step_size/10.0
    lookup_table[core_diameter] = shell_data


file = open('coating_lookup_table_LJ_RI_2p26-scat.lupckl', 'w')
pickle.dump(lookup_table, file)
file.close()  


