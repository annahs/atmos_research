#SP2 particle record class
#timestamps are in UTC

import numpy as np
from struct import *
import sys
from scipy.optimize import curve_fit
import scipy.special
import math

class ParticleRecord:
	
	
	def __init__(self, record, acq_rate):
		self.timestamp = np.nan
		
		self.acqPoints = []
		self.scatData = []
		self.wideBandIncandData = []
		self.narrowBandIncandData = []
		self.splitData = []
		self.lowGainScatData = []
		self.lowGainWideBandIncandData = []
		self.lowGainNarrowBandIncandData = []
		self.lowGainSplitData = []
		
		self.flag = np.nan
		self.scatteringIsSat = False
		self.scatteringSatFlag = False
		self.scatteringBaseline = np.nan
		self.scatteringBaselineNoiseThresh = np.nan
		self.scatteringMax = np.nan
		self.scatteringMaxPos = np.nan
		self.doublePeak = False
		self.splitMin = np.nan
		self.splitMax = np.nan
		self.splitBaseline = np.nan
		self.LEOMaxIndex = np.nan
		self.incandBaseline = np.nan
		self.incandMax = np.nan
		self.incandMaxPos = np.nan
		self.incandIsSat = False
		self.narrowIncandBaseline = np.nan
		self.narrowIncandMax = np.nan
		self.narrowIncandMaxPos = np.nan
		self.narrowIncandIsSat = False
		self.zeroCrossingPos = np.nan
		self.FF_scattering_amp = np.nan
		self.FF_peak_pos = np.nan     
		self.FF_width = np.nan
		self.FF_results = []
		self.LF_scattering_amp = np.nan
		self.LF_max_index = np.nan
		self.LF_baseline = np.nan
		self.LF_results = []
		self.beam_center_pos = np.nan
		self.LF_x_vals_to_use = []
		self.LF_y_vals_to_use = []
		
		
		self.importFromBinary(record, acq_rate)
		
		
	#Misc methods
	
	def importFromBinary(self, record, acq_rate):
		
		start_byte = 0
		#get the data record length (180 for UBCSP2 2012 - present, 300 for ECSP2 2009, 100 for CalTech SP2 at Soledad)
		data_length = unpack('>I',record[start_byte:start_byte+4])
		start_byte += 4

		#get the number of channels used (should be 4 for us)
		channels = unpack('>I',record[start_byte:start_byte+4])
		start_byte += 4
		
		
		#loop through the data, unpack it, and dump it into particle_data array
		for row_index in range(data_length[0]):
			new_line = [row_index]
			for col_index in range(channels[0]):
				value = unpack('>h',record[start_byte:start_byte+2])	
				new_line.append(value[0])
				start_byte += 2
			
			self.acqPoints.append(new_line[0])
			self.scatData.append(new_line[1])
			self.wideBandIncandData.append(new_line[2])
			self.narrowBandIncandData.append(new_line[3])
			self.splitData.append(new_line[4])	

			if channels[0] == 8:
				self.lowGainScatData.append(new_line[5])
				self.lowGainWideBandIncandData.append(new_line[6])
				self.lowGainNarrowBandIncandData.append(new_line[7])
				self.lowGainSplitData.append(new_line[8])
		
		
		#get the flag data (gives saturation and trigger info)
		flag = unpack('>H',record[start_byte:start_byte+2])
		start_byte += 2
		
		#get the seconds since midnight local time
		short_timestamp = unpack('>f',record[start_byte:start_byte+4])
		start_byte += 4
		
		#'Reserved for future use'
		null_data = unpack('>f',record[start_byte:start_byte+4])
		start_byte += 4
		
		#get event index
		event_index = unpack('>f',record[start_byte:start_byte+4])
		start_byte += 4
		
		#The SP2b data file format includs several locations for storing Single Precision Reals, but none for Double Precision Reals. 
		#Since the full LabVIEW timestamp (seconds since midnight Jan 1, 1904) requires a Double Precision Real, the following two time quantities are a way of packaging this full timestamp into Single Precision Reals.
		
		#get Time/10000 (ie Seconds Since Midnight Jan 1, 1904 UTC divided by 10000)
		time_10000 = unpack('>f',record[start_byte:start_byte+4])
		start_byte += 4
		
		#get Time remainder (ie the remainder of the full time stamp after that division)
		time_remainder = unpack('>f',record[start_byte:start_byte+4])
		start_byte += 4
				
		#next is 4 'Reserved for future use' fields
		for i in range(2):
			null_data = unpack('>f',record[start_byte:start_byte+4])
			start_byte += 4
			
		for i in range(2):
			null_data = unpack('>d',record[start_byte:start_byte+8])
			start_byte += 8
		
		#number of elements in dimension 1 of the Spare array 
		spare_array_size = unpack('>I',record[start_byte:start_byte+4])
		start_byte += 4
		
		#spare array (consists of Single Prec. Reals)
		array_bytes = spare_array_size[0]*4
		start_byte += array_bytes
		
		####end data grab####
		####################
		
		#Time/10000 is Seconds Since Midnight Jan 1, 1904 UTC divided by 10000. Time Remainder is the remainder of the full time stamp after that division.
		labview_timestamp = time_10000[0]*10000+time_remainder[0]
		
		#this combines the above with The time position within the buffer of data at which the event was found.  gives UNIXts inUTC
		self.timestamp  = labview_timestamp+event_index[0]/acq_rate-2082844800 #UNIX epoch is 1 Jan 1970, Labview epoch is 1 Jan 1904 therefore LVts_to_UNIXts = -2082844800 
	
		#self.flag = flag[0]

	def getAcqPoints(self):
		return self.acqPoints
	
		
	def isSingleParticle(self):
		#determine if it's a single particle by looking at scattering profile and seeing if rising and falling slopes of teh gaussian are roughly equal. Will not be the case if shoulder, dbl pk, etc
		index_of_maximum = np.argmax(self.scatData)  #get the peak position
		run = 55. #define the run to use
		
		left_rise = self.scatData[index_of_maximum]-self.scatData[index_of_maximum-int(run)] #get the rise from posn 10 to the peak
		left_slope = left_rise/run
		
		try:
			right_rise = self.scatData[index_of_maximum]-self.scatData[index_of_maximum+int(run)] #get the rise from a point the same distance away from teh peak as position 10, but on the other side
			right_slope = right_rise/run
		except:
			return
			
		percent_diff = np.absolute((right_slope-left_slope)/(0.5*right_slope+0.5*left_slope))
		if percent_diff > 0.1:
			self.doublePeak = True
					
	
	#Scattering methods
		
	def getScatteringSignal(self):
		return self.scatData
				
	def scatteringPeakInfo(self):
		self.scatteringBaseline = (np.mean(self.scatData[0:10]))
		self.scatteringBaselineNoiseThresh = 3*np.std(self.scatData[0:10])

		raw_max = np.amax(self.scatData)
		max = raw_max - self.scatteringBaseline
		if raw_max > 1750:
			self.scatteringIsSat = True
			
		self.scatteringMaxPos = np.argmax(self.scatData)
		self.scatteringMax = max

	
	def isScatteringSatFlagSet(self):
		decoded_flag = bin(self.flag)[2:].rjust(8, '0')
		if decoded_flag[0] == True:
			self.scatteringSatFlag = True
			print 'scattering saturation flag set'
		
	#Incandesence methods
		
	def getWidebandIncandSignal(self):
		return self.wideBandIncandData
	
	def incandPeakInfo(self):
	
		self.incandBaseline = (np.mean(self.wideBandIncandData[0:10]))
		#self.incandBaselineNoiseThresh = 3*np.std(self.wideBandIncandData[0:10])
				
		raw_incand_max = np.amax(self.wideBandIncandData)
		incand_max = raw_incand_max - self.incandBaseline
		if raw_incand_max > 2000:
			self.incandIsSat = True
		
		
		incand_max_index = np.argmax(self.wideBandIncandData)
		
		self.incandMax =incand_max
		self.incandMaxPos = incand_max_index
		
		
	def getNarrowbandIncandSignal(self):
		return self.narrowBandIncandData
		
	def narrowIncandPeakInfo(self):
	
		self.narrowIncandBaseline = (np.mean(self.narrowBandIncandData[0:10]))
		#self.narrowIncandBaselineNoiseThresh = 3*np.std(self.narrowBandIncandData[0:10])
				
		raw_narrowIncand_max = np.amax(self.narrowBandIncandData)
		narrowIncand_max = raw_narrowIncand_max - self.narrowIncandBaseline
		if raw_narrowIncand_max > 2000:
			self.narrowIncandIsSat = True
		
		
		narrowIncand_max_index = np.argmax(self.narrowBandIncandData)
		
		self.narrowIncandMax =narrowIncand_max
		self.narrowIncandMaxPos = narrowIncand_max_index    
		
	#Split detector methods
		
	def getSplitDetectorSignal(self):
		return self.splitData
		
	def splitDetectorPeakInfo(self):
		split_raw_min = np.amin(self.splitData)
		split_min = split_raw_min - self.splitBaseline
				
		split_raw_max = np.amax(self.splitData)
		split_max = split_raw_max - self.splitBaseline
	
		self.splitMax = split_max
		self.splitMin = split_min
	
	def zeroCrossing(self):
		self.splitBaseline =(np.mean(self.splitData[0:10]))	
		split_max_index = np.argmax(self.splitData)
		split_min_index = np.argmin(self.splitData)

		if split_max_index >= split_min_index:
			return self.zeroCrossingPosSlope()
		
		if split_max_index < split_min_index:
			return self.zeroCrossingNegSlope()
		
	
	
	
	def zeroCrossingPosSlope(self):
		self.splitBaseline = np.mean(self.splitData[0:10])
		split_max_index = np.argmax(self.splitData)
		split_min_index = np.argmin(self.splitData)
		split_max_value = np.max(self.splitData)
		split_min_value = np.min(self.splitData)
	
		if (self.splitBaseline-split_min_value) >= 140 and (split_max_value-self.splitBaseline) >=140:  #avoid particles evaporating before the notch position can be properly determined (details in Taylor et al. 10.5194/amtd-7-5491-2014)
			try:
				for index in range(split_min_index, split_max_index+1): #go to max +1 because 'range' function is not inclusive
					if self.splitData[index] < self.splitBaseline:
						value_zero_cross_neg = float(self.splitData[index])
						index_zero_cross_neg = index
					if self.splitData[index] >= self.splitBaseline:
						value_zero_cross_pos = float(self.splitData[index])
						index_zero_cross_pos = index
						break
				zero_crossing = index+((value_zero_cross_pos-self.splitBaseline)*(index_zero_cross_pos-index_zero_cross_neg))/(value_zero_cross_pos-value_zero_cross_neg)           
			except:
				zero_crossing = -1 
				
		else:
			zero_crossing = -2   
		
		self.zeroCrossingPos = zero_crossing
		return zero_crossing
		
	def zeroCrossingNegSlope(self):
		self.splitBaseline = np.mean(self.splitData[0:10])
		split_max_index = np.argmax(self.splitData)
		split_min_index = np.argmin(self.splitData)
		split_max_value = np.max(self.splitData)
		split_min_value = np.min(self.splitData)
		
		
		if (self.splitBaseline-split_min_value) >= 140 and (split_max_value-self.splitBaseline) >= 140: #avoid particles evaporating before the notch position can be properly determined (details in Taylor et al. 10.5194/amtd-7-5491-2014)
			try:
				for index in range(split_max_index, split_min_index+1):  #go to max +1 because 'range' function is not inclusive
					if self.splitData[index] > self.splitBaseline:
						value_zero_cross_pos = float(self.splitData[index])
						index_zero_cross_pos = index
					if self.splitData[index] <= self.splitBaseline:
						value_zero_cross_neg = float(self.splitData[index])
						index_zero_cross_neg = index
						break
				zero_crossing = index+((value_zero_cross_pos-self.splitBaseline)*(index_zero_cross_pos-index_zero_cross_neg))/(value_zero_cross_pos-value_zero_cross_neg)           
			except:
				zero_crossing = -1
		
		else: 
			zero_crossing = -2

		self.zeroCrossingPos = zero_crossing
		return zero_crossing
		
		
		

		
	def fullGaussFit(self):
		#run the scatteringPeakInfo method to retrieve various peak attributes 
		self.scatteringPeakInfo()
		
		#set parameters for fitting
		baseline = self.scatteringBaseline
		x_vals = self.getAcqPoints()
		y_vals = self.getScatteringSignal()	
		
		#initial values for amplitude(a) center(u) and gauss width(sig)
		guess_a = self.scatteringMax  
		guess_u = self.scatteringMaxPos
		guess_sig = 10
		p_guess = [guess_a,guess_u,guess_sig]
		
		def fullGauss(x, a, u, sig):
			return baseline+a*np.exp((-(x-u)**2)/(2*sig**2))  #Gaussian
			#return baseline + (2*a/math.pi)*(sig/(4*(x-u)**2 + sig**2)) #Lorentzian - not good!
			
		#run the fitting
		try:
			popt, pcov = curve_fit(fullGauss, x_vals, y_vals, p0=p_guess)
		except:
			popt, pcov = [np.nan, np.nan, np.nan], [np.nan, np.nan, np.nan]   
		
		self.FF_scattering_amp = popt[0]
		self.FF_peak_pos = popt[1]   
		self.FF_width = popt[2]
		fit_result = []
		for x in x_vals:
			fit_result.append(fullGauss(x,popt[0],popt[1],popt[2]))
		self.FF_results = fit_result

		
	def leoGaussFit(self,zeroX_to_LEO_limit,calib_zeroX_to_peak,calib_gauss_width):
		#run the scatteringPeakInfo method to retrieve various peak attributes 
		self.scatteringPeakInfo()
		
		#get the baseline
		baseline = self.scatteringBaseline
		
		#get the zero-crossing for the particle
		zero_crossing_pt_LEO = self.zeroCrossing()
		
		if zero_crossing_pt_LEO < 0:  #ie we can't find the zero crossing
			self.LF_scattering_amp = -2
			self.LF_baseline = -2
			self.LF_results = []
			self.LF_max_index = -2
			self.beam_center_pos = -2
			
		else:
			#LEO max index sets the x-limit for fitting based on the desired magnification factor
			LEO_max_index = int(round(zero_crossing_pt_LEO-zeroX_to_LEO_limit))
			self.LF_max_index = LEO_max_index
			LEO_min_index = 0
			
			x_vals_all = self.getAcqPoints()
			self.LF_x_vals_to_use = x_vals_all[LEO_min_index:LEO_max_index]

			y_vals_all = self.getScatteringSignal()
			self.LF_y_vals_to_use = y_vals_all[LEO_min_index:LEO_max_index]

			self.beam_center_pos = zero_crossing_pt_LEO-calib_zeroX_to_peak
							
			def LEOGauss(x, a, b):
				return b+a*np.exp((-(x-self.beam_center_pos)**2)/(2*calib_gauss_width**2)) #Gaussian
			

			#run the fitting
			try:
				popt, pcov = curve_fit(LEOGauss, self.LF_x_vals_to_use, self.LF_y_vals_to_use)
			except:
				popt, pcov = [-1,-1], [np.nan, np.nan] 

			self.LF_scattering_amp = popt[0] 
			self.LF_baseline = popt[1]

			fit_result = []
			for x in x_vals_all:
				fit_result.append(LEOGauss(x,popt[0],popt[1]))
			self.LF_results = fit_result
			

	def GCASFit(self):
		#run the scatteringPeakInfo method to retrieve various peak attributes 
		self.scatteringPeakInfo()
		
		#set parameters for fitting
		baseline = self.scatteringBaseline
		x_vals = np.array(self.getAcqPoints())
		y_vals = np.array(self.getScatteringSignal()	)
		
		#initial values for amplitude(a) center(u) and gauss width(sig)
		guess_a = self.scatteringMax  
		guess_u = self.scatteringMaxPos
		guess_sig = 10
		p_guess = [53000,73,17, -0.031,-0.1]
		
		def GCAS(x, a, xc, w, a3, a4):
			return baseline + (a /(w*math.sqrt(2*math.pi)))*np.exp(-((x-xc)/w)**2/2.)*(1+np.abs((a3/6)*(((x-xc)/w)**3-3.*((x-xc)/w))+ (a4/24)*( ((x-xc)/w)**4 -6.*((x-xc)/w)**3 + 3 ) ))
						
		#run the fitting
		#try:
		popt, pcov = curve_fit(GCAS, x_vals, y_vals, p0=p_guess)
		#except:
		#	popt, pcov = [np.nan, np.nan, np.nan, np.nan, np.nan], [np.nan, np.nan, np.nan, np.nan, np.nan]   
		
		self.FF_scattering_amp = popt[0]
		self.FF_peak_pos = popt[1]   
		self.FF_width = popt[2]
		fit_result = []
		for x in x_vals:
			fit_result.append(GCAS(x,popt[0],popt[1],popt[2],popt[3],popt[4]))
		self.FF_results = fit_result
				

	def GiddingsFit(self):
		#run the scatteringPeakInfo method to retrieve various peak attributes 
		self.scatteringPeakInfo()
		
		#set parameters for fitting
		baseline = self.scatteringBaseline
		x_vals = np.array(self.getAcqPoints()) + 1 #avoids divide by zero in Giddings fit
		y_vals = np.array(self.getScatteringSignal())
		
		#initial values for amplitude(a) center(u) and gauss width(sig)
		guess_a = self.scatteringMax  
		guess_u = self.scatteringMaxPos
		guess_sig = 10
		p_guess = [53000,73,2]
		
		
		def Giddings(x, a, xc, w):
			# Note: scipy.special.iv is the modified Bessel function of the first kind
			return baseline + (a/w)*np.sqrt(xc/x)*(scipy.special.iv(0,(2*np.sqrt(xc*x)/w))) * np.exp((-x-xc)/w)

				
		#run the fitting
		try:
			popt, pcov = curve_fit(Giddings, x_vals, y_vals, p0=p_guess)
		except:
			popt, pcov = [np.nan, np.nan, np.nan, np.nan, np.nan], [np.nan, np.nan, np.nan, np.nan, np.nan]   
				
		fit_result = []
		for x in x_vals:
			fit_result.append(Giddings(x,popt[0],popt[1],popt[2]))
		
	
		self.FF_results = fit_result
		self.FF_scattering_amp = np.max(fit_result)-baseline#popt[0]
		self.FF_peak_pos = popt[1]   
		self.FF_width = popt[2]
		
	def leoGiddingsFit(self,zeroX_to_LEO_limit,calib_zeroX_to_peak,calib_gauss_width):
		#run the scatteringPeakInfo method to retrieve various peak attributes 
		self.scatteringPeakInfo()
		
		#get the baseline
		baseline = self.scatteringBaseline
		
		#get the zero-crossing for the particle
		zero_crossing_pt_LEO = self.zeroCrossing()
		
		if zero_crossing_pt_LEO < 0:  #ie we can't find the zero crossing
			self.LF_scattering_amp = -2
			self.LF_baseline = -2
			self.LF_results = []
			self.LF_max_index = -2
			self.beam_center_pos = -2
			
		else:
			#LEO max index sets the x-limit for fitting based on the desired magnification factor
			LEO_max_index = int(round(zero_crossing_pt_LEO-zeroX_to_LEO_limit))
		
			self.LF_max_index = LEO_max_index
			LEO_min_index = 0
			
			x_vals_all =  np.array(self.getAcqPoints()) + 1 #avoids divide by zero in Giddings fit
			self.LF_x_vals_to_use = x_vals_all[LEO_min_index:LEO_max_index]

			y_vals_all =  np.array(self.getScatteringSignal())
			self.LF_y_vals_to_use = y_vals_all[LEO_min_index:LEO_max_index]

			self.beam_center_pos = zero_crossing_pt_LEO-calib_zeroX_to_peak
							
			def LEOGiddings(x, a):
				# Note: scipy.special.iv is the modified Bessel function of the first kind
				return baseline + (a/calib_gauss_width)*np.sqrt(self.beam_center_pos/x)*(scipy.special.iv(0,(2*np.sqrt(self.beam_center_pos*x)/calib_gauss_width))) * np.exp((-x-self.beam_center_pos)/calib_gauss_width)

			#run the fitting
			try:
				popt, pcov = curve_fit(LEOGiddings, self.LF_x_vals_to_use, self.LF_y_vals_to_use)
			except:
				popt, pcov = [-1], [np.nan] 
	

			fit_result = []
			for x in x_vals_all:
				fit_result.append(LEOGiddings(x,popt[0]))
			self.LF_results = fit_result
			self.LF_scattering_amp = np.max(fit_result)-baseline#popt[0] 
			self.LF_baseline = np.nan
				