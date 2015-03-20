#SP2 particle record class
#timestamps are in UTC

import numpy as np
from struct import *
import sys

class ParticleRecord:
	
	
	def __init__(self, record, acq_rate, timezone):
		self.timestamp = None
		
		self.acqPoints = []
		self.scatData = []
		self.wideBandIncandData = []
		self.narrowBandIncandData = []
		self.splitData = []
		self.lowGainScatData = []
		self.lowGainWideBandIncandData = []
		self.lowGainNarrowBandIncandData = []
		self.lowGainSplitData = []
		
		self.flag = None
		self.scatteringIsSat = False
		self.scatteringSatFlag = False
		self.scatteringBaseline = None
		self.scatteringBaselineNoiseThresh = None
		self.scatteringMax = None
		self.scatteringMaxPos = None
		self.doublePeak = False
		self.splitMin = None
		self.splitMax = None
		self.splitBaseline = None
		self.LEOMaxIndex = None
		self.incandBaseline = None
		self.incandMax = None
		self.incandMaxPos = None
		self.incandIsSat = False
		self.narrowIncandBaseline = None
		self.narrowIncandMax = None
		self.narrowIncandMaxPos = None
		self.narrowIncandIsSat = False
		self.zeroCrossingPos = None
		
		self.importFromBinary(record, acq_rate, timezone)
		
		
	#Misc methods
	
	def importFromBinary(self, record, acq_rate, timezone):
		
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
		
		#this is The seconds since midnight LOCAL time when the current buffer of data was acquired
		labview_timestamp = time_10000[0]*10000+time_remainder[0]
		
		#this combines the above with The time position within the buffer of data at which the event was found.  gives UNIXts inUTC
		self.timestamp  = labview_timestamp+event_index[0]/acq_rate-2082844800+(timezone*3600) #UNIX epoch is 1 Jan 1970, Labview epoch is 1 Jan 1904 therefore LVts_to_UNIXts = -2082844800 
		
	
		#self.flag = flag[0]

	def getAcqPoints(self):
		return self.acqPoints
		
	def isSingleParticle(self):
		prev_point = 200
		for point in range(len(self.splitData)):
			value = self.splitData[point]
			if value > 500:
				gap = point - prev_point
				if gap > 1:
					self.doublePeak = True
					print 'double peak detected'
				prev_point = point
			
	
	#Scattering methods
		
	def getScatteringSignal(self):
		return self.scatData
				
	def scatteringPeakInfo(self, LEO_amplification_factor):
		self.scatteringBaseline = (np.mean(self.scatData[0:10]))#+np.mean(self.scatData[150:-1]))/2
		self.scatteringBaselineNoiseThresh = 3*np.std(self.scatData[0:10])

		raw_max = np.amax(self.scatData)
		max = raw_max - self.scatteringBaseline
		if raw_max > 1750:
			self.scatteringIsSat = True
		
		
		max_index = np.argmax(self.scatData)
		
		self.scatteringMax = max
		self.scatteringMaxPos = max_index

		LEO_max = (self.scatteringMax/LEO_amplification_factor)+ self.scatteringBaseline
		
		
		LEO_pt = 0
		for index in range(0, max_index):
			if self.scatData[index] <= LEO_max:
				LEO_pt = index
			if self.scatData[index] > LEO_max:   
				break
	
		self.LEOMaxIndex = LEO_pt
		
	
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
		self.splitBaseline = np.mean(self.splitData[0:10])
		split_max_index = np.argmax(self.splitData)
		split_min_index = np.argmin(self.splitData)

		if split_max_index > split_min_index:
			return self.zeroCrossingPosSlope()
		
		if split_max_index < split_min_index:
			return self.zeroCrossingNegSlope()
		
	
	
	
	def zeroCrossingPosSlope(self):
		self.splitBaseline = np.mean(self.splitData[0:5])
		split_max_index = np.argmax(self.splitData)
		split_min_index = np.argmin(self.splitData)
		split_min_value = np.min(self.splitData)
		#split_value = split_min_value +(self.splitBaseline-split_min_value)/2
		split_value = self.splitBaseline
	
		if (self.splitBaseline-split_min_value) >= 10:
			try:
				for index in range(split_min_index, split_max_index+1): #go to max +1 because 'range' function is not inclusive
					if self.splitData[index] < split_value:
						value_zero_cross_neg = float(self.splitData[index])
						index_zero_cross_neg = index
					if self.splitData[index] >= split_value:
						value_zero_cross_pos = float(self.splitData[index])
						index_zero_cross_pos = index
						break
				zero_crossing = index+((value_zero_cross_pos-split_value)*(index_zero_cross_pos-index_zero_cross_neg))/(value_zero_cross_pos-value_zero_cross_neg)           
			except:
				zero_crossing = -1 
				
		if (self.splitBaseline-split_min_value) < 10:
			zero_crossing = -1   
		
		self.zeroCrossingPos = zero_crossing
		return zero_crossing
		
	def zeroCrossingNegSlope(self):
		self.splitBaseline = np.mean(self.splitData[0:5])
		split_max_index = np.argmax(self.splitData)
		split_min_index = np.argmin(self.splitData)
		split_min_value = np.min(self.splitData)
		
		
		if (self.splitBaseline-split_min_value) >= 10:
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
		
		if (self.splitBaseline-split_min_value) < 10:
			zero_crossing = -2

		self.zeroCrossingPos = zero_crossing
		return zero_crossing
		
		
	
