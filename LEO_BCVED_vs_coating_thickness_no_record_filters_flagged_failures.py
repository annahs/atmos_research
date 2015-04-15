import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
from pprint import pprint
from scipy.optimize import curve_fit
from scipy import stats
from SP2_particle_record_UTC import ParticleRecord
from struct import *
import hk_new
import hk_new_no_ts_LEO
from scipy import linspace, polyval, polyfit, sqrt, stats   
import math
from datetime import datetime
import calendar


###FLag definintions

# 0 good
# 1 no_scattering
# 2 neg_LEO 
# 3 no_convergence
# 4 flat_fit 
# 5 baseline_mismatch 
# 6 LEO_value_over_sat_level 

#######********************************************************************************************************************************************


#event 2 20120612 to 20120613
event_name = '20120612_20120613_moteki_RI_2p26'
data_dir = 'C:/Users/Sarah Hanna/Documents/Data/LEO fitting/LJ-EC-SP2/Measurements/LJ Event 2/'
start_time_dt=datetime.strptime('2012/06/12 20:45', '%Y/%m/%d %H:%M')
end_time_dt = datetime.strptime('2012/06/13 11:35', '%Y/%m/%d %H:%M')
start_time = calendar.timegm(start_time_dt.utctimetuple())
end_time = calendar.timegm(end_time_dt.utctimetuple())

####event 3 20120617 to 20120618
#event_name = '20120617_20120618_moteki_RI_2p26'
#data_dir = 'C:/Users/Sarah Hanna/Documents/Data/LEO fitting/LJ-EC-SP2/Measurements/LJ Event 3/'
#start_time_dt=datetime.strptime('2012/06/18 02:12', '%Y/%m/%d %H:%M')
#end_time_dt = datetime.strptime('2012/06/18 07:52', '%Y/%m/%d %H:%M')
#start_time = calendar.timegm(start_time_dt.utctimetuple())
#end_time = calendar.timegm(end_time_dt.utctimetuple())



#event_name = '2010_BB'
#data_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/SP2_2010/BB period 2010/EC_SP2/20100726/'
#start_time_dt=datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M') #jason's BC clear report
#end_time_dt = datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')
#start_time = calendar.timegm(start_time_dt.utctimetuple())
#end_time = calendar.timegm(end_time_dt.utctimetuple())

#*****inputs******
records_to_use = 4000 #use 'all' to use all records
show_LEO_fit = False

#######********************************************************************************************************************************************

zeroX_to_LEO_limit = 65 #65 for 5% (amp=20) of laser intensity (LI), 60 for 10% (amp=10) of LI, 52 for 20% (amp=5) of LI, 42 for 50% (amp=2) of LI, 21 for 100% (amp=1) of LI
LEO_amplification_factor = 10 

#scattering peak conditions
min_peakheight = 10 #threshold for attempting a LEO fit to the scatter signal (below this threshold particles are consdiered to be bare BC) 5 is ~3xsd of the baseline noise
min_peakpos = 20
max_peakpos = 150

#declare the average zero-cross to peak distance (from PSL calibration)        
avg_cross_to_peak = 21.91 #La Jolla = 21.91, WHI UBC 2010 = -24.258, WHI EC 2010 = 1.269 WHI 
print 'avg zero-crossing to peak time: ', avg_cross_to_peak

#declare the average gauss width (from PSL calibration)
avg_gauss_width =  19.14 #La Jolla = 19.14, WHI UBC 2010 = 16.998,  WHI EC 2010 = 21.57
print 'avg Gauss width: ',avg_gauss_width

#incandescence to BC mass calibration factors  # for EC WHI 2010 0.156+0.000606x+ 6.3931e-7, LJ = calib1 = 0.23523 calib2 = 0.00235 calib3 = 1.4928e-8, LJ Aquadag scaled = 0.2152+0.002401x
calib1 = 0.2152
calib2 = 0.002401
calib3 = 0
BC_density = 1.8 #density of ambient BC in g/cc
BC_det_limit = 0.25 #in fg (0.23fg = 62nm VED)


parameters = {
'acq_rate': 5000000,
#file i/o
'directory':data_dir,
#date and time
'timezone':-7,
}


#********** Mie calc lookup table ********
lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/LEO fitting/LJ-EC-SP2/lookup tables/'
#lookup_dir = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/SP2_2010/BB period 2010/EC_SP2/lookup tables/'
os.chdir(lookup_dir)

for lookup_file in os.listdir('.'):
    if lookup_file.endswith('.lupckl'):
        print lookup_file
        lookup = open(lookup_file, 'r')
        lookup_table = pickle.load(lookup)
        lookup.close()

os.chdir(data_dir)


#*********initialize variables********
LEO_data = []
total_particles = 0
particles_used = 0
LEO_fail = 0
no_scatter = 0
saturated_particles = 0

#*************Particle analysis************
ooh_boy = 0
first_file = True
for file in os.listdir('.'):
    
    if file.endswith('.sp2b'):
        
       
        
        path = data_dir + str(file)
        file_bytes = os.path.getsize(path) #size of entire file in bytes
        record_size = 1498 #size of a single particle record in bytes(UBC_SP2 = 1498, EC_SP2 in 2009 and 2010 = 2458)
        number_of_records = (file_bytes/record_size)-1
        if records_to_use == 'all':
            number_records_to_show =  number_of_records 
        else:
            number_records_to_show = records_to_use
    
        f2 = open(file, 'rb')       
        print file

        
        #Grab the particle records
        record_index = 0
        while record_index < number_records_to_show:
            
            ##Import and parse binary
            record = f2.read(record_size)
            particle_record = ParticleRecord(record, parameters['acq_rate'], parameters['timezone'])
            event_time = particle_record.timestamp

                            
            #if the particle event time is after the period we're interested in we can skip the rest of the analysis
            if event_time > end_time:
                break
                          
           #check if the event_time is within the cloud event
            if event_time >= start_time and event_time <= end_time:
                total_particles+=1     
                
                                 
                #run the scatteringPeakInfo method to retrieve various scattering peak attributes
                particle_record.scatteringPeakInfo(LEO_amplification_factor)  
                scattering_pk_pos = particle_record.scatteringMaxPos
                
                #run the incandPeakInfo method to retrieve various incandescence peak attributes
                particle_record.incandPeakInfo()
                incand_pk_amp = particle_record.incandMax
                BC_mass_fg = calib1 + calib2*incand_pk_amp + calib3*(incand_pk_amp**2)
                incand_pk_pos = particle_record.incandMaxPos
                lag_time = (incand_pk_pos - scattering_pk_pos)*0.2
                saturated = particle_record.incandIsSat
                if saturated == True:
                    saturated_particles += 1
                                        
                    
                #get the zero-crossing (note: a neg value indicates an exception was thrown when determining the zero-crossing)
                zero_crossing_pt_LEO = particle_record.zeroCrossingPosSlope()
                if zero_crossing_pt_LEO == -1:
                    ooh_boy +=1
                
                #if particle record fits criteria for a good record, continue with analysis
                if BC_mass_fg > BC_det_limit and saturated == False: 
                    LEO_coating_thickness = np.nan
                    LEO_pt_amp = np.nan
                    center = np.nan
                    coating_volume = np.nan
                    scat_amp = particle_record.scatteringMax
                    BC_VED = (((BC_mass_fg/(10**15*BC_density))*6/3.14159)**(1/3.0))*10**7 #VED in nm with 10^15fg/g and 10^7nm/cm
                    
                    #get data for BC particles with no scatter signal
                    if particle_record.scatteringMax < min_peakheight:

                        flag = 1
                        LEO_amp = np.NaN
                        LEO_coating_thickness = 0.0
                          
                      
                    
                    #get data for BC particles with some scatter signal
                    if particle_record.scatteringMax >= min_peakheight:                      
                        
                        #set up the LEO fitting
                        try:
							LEO_max_index = int(zero_crossing_pt_LEO - zeroX_to_LEO_limit) #sets the x-limit for fitting based on the desired magnification factor particle_record.LEOMaxIndex #
                        except:
                            print 'LEO_max_index failure', zero_crossing_pt_LEO, zeroX_to_LEO_limit                        
                        #if leading edge distance that we're fitting is negative we can't do a LEO fit and we use this in our error calculation
                        if LEO_max_index <= 0:
                            flag = 2
                            LEO_amp = np.NaN

                            
                        #only proceed if the leading edge distance that we're fitting isn't negative
                        if LEO_max_index > 0:
                            
                                                      
                            scatteringBaseline = particle_record.scatteringBaseline               

                            LEO_min_index = 0
                            center = zero_crossing_pt_LEO-(avg_cross_to_peak)
                            width_to_use = avg_gauss_width                            
                            
                            #set range of values to fit
                            x_vals_all = np.array(particle_record.getAcqPoints())
                            x_vals_to_use = x_vals_all[LEO_min_index:LEO_max_index]
                            
                            y_vals_all = np.array(particle_record.getScatteringSignal())
                            y_vals_to_use = y_vals_all[LEO_min_index:LEO_max_index] 
                            
                            try:
                                if np.max(y_vals_to_use)>3600:
                                    print np.max(y_vals_to_use)
                                    counter+=1
                            except:
                                print 'yval err',record_index
                            
                            
                            LEO_pt_amp = y_vals_all[LEO_max_index]-scatteringBaseline
							
                            #incandescence data (for plotting if desired)
                            y_vals_incand = particle_record.getWidebandIncandSignal()
                            
                            #split detector signal
                            y_vals_split = particle_record.getSplitDetectorSignal()
                                                      
                            p_guess = (scat_amp, -2016)
                                
                            def LEOGauss(x_vals, a, b):
                                return b+a*np.exp((-np.power((x_vals-center),2))/(2*np.power(width_to_use,2)))

                            try:
                                popt, pcov = curve_fit(LEOGauss, x_vals_to_use, y_vals_to_use, p0 = p_guess)
                                
                            #if the fitting procedure fails we fold this into our error                                     
                            except:
                                popt, pcov = None, None
                                
                                flag = 3
                                LEO_amp = np.NaN
                                
                                                           
                                                       
                            
                            fit_result = []
                            for x in range(0,300):
                                fit_result.append(LEOGauss(x,scat_amp,-2016))                         
                                                      
                                
                            #if the fitting procedure succeeds we continue
                            if popt != None:
                                LEO_amp = popt[0]
                                LEO_baseline = popt[1]
                                
                                #if the fit was good, we give a flag = 0
                                flag = 0
                                
                                #check that the fit didn't just produce a flat line and overwrite LEO_amp as NaN if it did
                                if LEO_amp < 5:#min_peakheight:
                                    flag = 4
                                    #LEO_amp = np.NaN 
                                    
                                    i=0
                                    
                                
                                #if it's not a flat line check if there is a big baseline mismatch, if there is we have a LEO failure and this goes into our error
                                if LEO_amp >= min_peakheight:
                                    #get baseline and check for mismatch
                                    #limit for baseline mismatch of LEO fit vs real baseline is 10
                                    max_baseline_diff = 100
                                    baseline_diff = math.fabs(LEO_baseline-scatteringBaseline)
                                    if baseline_diff > max_baseline_diff:
                                        flag = 5
                                        #LEO_amp = np.NaN 
                                    
      
                                                       
                    
                    ####Now we get and write the coatig info to file
                    #get the coating thicknesses from the lookup table which is a dictionary of dictionaries, the 1st keyed with BC core size and the second being coating thicknesses keyed with calc scat amps                  
                    #get the core size first regardless of a valid LEO fit
                    core_diameters = sorted(lookup_table.keys())
                    prev_diameter = core_diameters[0]

                    for core_diameter in core_diameters:
                        if core_diameter > BC_VED:
                            core_dia_to_use = prev_diameter
                            break
                        prev_diameter = core_diameter
                        
                    #now get the coating thickness for the scat_amp this is the coating thickness based on the raw scattering max
                    scattering_amps = sorted(lookup_table[core_dia_to_use].keys())
                    prev_amp = scattering_amps[0]
                    for scattering_amp in scattering_amps:
                        if scat_amp < scattering_amp:
                            scat_amp_to_use = prev_amp
                            
                            break
                        prev_amp = scattering_amp

                    scat_coating_thickness = lookup_table[core_dia_to_use].get(scat_amp_to_use, np.nan) # returns value for the key, or none
                        
                    #this is the coating thickness based on the LEO_amp,
                    
                    
                    #if we got a LEO fit find the coatign thickness fro this
                    if np.isnan(LEO_amp) != True:      
                        
                        #get the calc coating thickness from the LEO_amp
                        prev_amp = scattering_amps[0]
                        scatter_below_saturation_level = False #initialize to false, but set to true asoon as we find a scattering match in our table, this is only an issue with the LEO scat since we checked the raw scattering for saturation earlier

                        for scattering_amp in scattering_amps:
                            if LEO_amp < scattering_amp:
                                amp_to_use = prev_amp
                                scatter_below_saturation_level = True
                                break
                            prev_amp = scattering_amp
                        
                        if scatter_below_saturation_level == False:
                            flag = 6  


                        #if scatter_below_saturation_level == True:
                        LEO_coating_thickness = lookup_table[core_dia_to_use].get(amp_to_use, np.nan) # returns value for the key, or none
                        coated_VED = BC_VED + 2*LEO_coating_thickness
                        coating_volume = ((4.0/3)*math.pi*(coated_VED/2.0)**3) - ((4.0/3)*math.pi*(BC_VED/2.0)**3)  #nm3
							
                            
                            
                        #***stops to show us the leo fit if we want##########################################
                        if show_LEO_fit == True and scat_amp >= 95 and scat_amp <=105:
                            print '\n'
                            print 'record: ',record_index
                            print 'core VED: ', BC_VED
                            print 'center', center
                            print 'LEO_pt_amp, LEO_amp', LEO_pt_amp, LEO_amp
                            print 'coating', LEO_coating_thickness
                            print 'flag', flag
                            print 'scat_amp', scat_amp
                            print 'scat_amp_to_use',scat_amp_to_use
                                                                
                            fit_result = LEOGauss(x_vals_all,LEO_amp,LEO_baseline)
                            LEO_used = LEOGauss(x_vals_to_use,LEO_amp,LEO_baseline)
                                       
                            fig = plt.figure()
                            ax1 = fig.add_subplot(111)
                            ax1.plot(x_vals_all,y_vals_all,'o', markeredgecolor='blue',markerfacecolor='None')   
                            ax1.plot(x_vals_all,fit_result, 'blue')
                            ax1.plot(x_vals_to_use,y_vals_to_use, color = 'black',linewidth=3)
                            ax1.plot(x_vals_all, y_vals_incand, 'o',  markeredgecolor='red', markerfacecolor='None')
                            #ax1.plot(x_vals_all, y_vals_split, 'green')
                            plt.ylim(-2500,1800)
                            plt.axvline(x=zero_crossing_pt_LEO, ymin=0, ymax=1, color= 'red')
                            plt.axvline(x=center, ymin=0, ymax=1)
                            plt.text(0.55, 0.8,file + '  index: ' +str(record_index) + '\n' + 'core VED (nm): ' + str(round(BC_VED,2)) + '\n' +  'coating: ' +str(LEO_coating_thickness), transform = ax1.transAxes)
                            plt.show()
                        
                    #write our data to file
                    

                    newline = [LEO_amp, scattering_pk_pos, BC_VED, incand_pk_pos, lag_time, LEO_coating_thickness, event_time, flag, scat_amp, scat_coating_thickness, LEO_pt_amp, center, coating_volume]
                    LEO_data.append(newline)
                
                    

                    
                
            record_index+=1    
        
        #write to file after each sp2bfile/loop to avoid bogging down from holding huge array in memory
        print 'to file'
        file = open(event_name +' testeroo'+'.coattxt', 'a')
        if first_file == True:
            file.truncate(0)
            file.write('LEO_amp'+ '\t' + 'scattering_pk_pos'+ '\t' + ' BC_VED_nm'+ '\t' + ' incand_pk_pos'+ '\t' + ' lag_time_us'+ '\t' + ' LEO_coating_thickness_nm'+ '\t' + ' event_time'+ '\t' + ' flag'+ '\t' + ' scat_amp'+ '\t' +  ' scat_coating_thickness_nm'+ '\t'+' LEO_pt_amp'+ '\t'+' beam_center_pos'+ '\t'+' coating_volume_nm3' + '\n')
            first_file = False
        for row in LEO_data:
            line = '\t'.join(str(x) for x in row)
            file.write(line + '\n')
        file.close()
        LEO_data = []
        
        f2.close()        
print ooh_boy
print 'LEO fail', LEO_fail    
print 'no scattering', no_scatter    
print 'total particles:', total_particles
print 'particles used:', particles_used
print '# of saturated incandesence',saturated_particles

#create numpy array
LEO_data_np = np.array(LEO_data)


#*******Plotting***********

fig = plt.figure()

ax1 = fig.add_subplot(111)

LF_scattering_amp = LEO_data_np[:,0]
scattering_pk_position = LEO_data_np[:,1]
BC_VED = LEO_data_np[:,2]
incand_pk_position = LEO_data_np[:,3]
lag = LEO_data_np[:,4]
LEO_coating_thickness = LEO_data_np[:,5]
timestamp = LEO_data_np[:,6]

###timeseries###

#plt.scatter(timestamp, BC_VED, c=LEO_coating_thickness, cmap=cm.jet)
#plt.xlabel('timestamp')
#plt.ylabel('BC_VED')
#cb = plt.colorbar()
#cb.set_label('LEO_coating_thickness')

####hexbin###

plt.hexbin(BC_VED, LEO_coating_thickness, cmap=cm.jet, gridsize = 50)#, norm= norm) #bins='log', norm=norm
plt.xlabel('BC_VED')
plt.ylabel('LEO_coating_thickness')
#cb = plt.colorbar()
#cb.set_label('frequency')


#plt.savefig(event_name + 'CT VS BCVED', bbox_inches='tight',pad_inches=0.25) 


plt.show()      
