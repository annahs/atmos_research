#!/usr/bin/python
# -*- coding: utf-8 -*-

#creates an ICARTT format text file
#format described at http://www-air.larc.nasa.gov/missions/etc/IcarttDataFormat.htm#2

import numpy as np
import sys
import os
from pprint import pprint


class CreateIcarttFile:
	
	
	def __init__(self, filename, filelocation):
		self.PI_names = '' 						#PI last name, first name/initial.
		self.PI_affiliations = ''				#Organization/affiliation of PI.
		self.data_source = ''					#Data source description (e.g., instrument name, platform name, model name, etc.).
		self.mission_name = ''					#Mission name (usually the mission acronym).
		self.file_vol = ''						#File volume number, number of file volumes (these integer values are used when the data require more than one file per day; for data that require only one file these values are set to 1, 1) - comma delimited.
		self.data_start_date = ''				#UTC date when data begin, UTC date of data reduction or revision 
		self.data_revision_date = ''			#UTC date of data reduction or revision	- comma delimited (yyyy, mm, dd, yyyy, mm, dd) with data_start_date
		self.data_interval = ''					#Data Interval (This value describes the time spacing (in seconds) between consecutive data records. It is the (constant) interval between values of the independent variable. For 1 Hz data the data interval value is 1 and for 10 Hz data the value is 0.1. All intervals longer than 1 second must be reported as Start and Stop times, and the Data Interval value is set to 0. The Mid-point time is required when it is not at the average of Start and Stop times).
		self.indep_variable_name = '' 			#Description or name of independent variable (This is the name chosen for the start time. It always refers to the number of seconds UTC from the start of the day on which measurements began. It should be noted here that the independent variable should monotonically increase even when crossing over to a second day.).
		self.no_of_variables =  '' 				#Number of variables (Integer value showing the number of dependent variables: the total number of columns of data is this value plus one.).
		self.scale_factors = ''					#Scale factors (1 for most cases, except where grossly inconvenient) - comma delimited.
		self.missing_data_indicators = ''		#Missing data indicators (This is -9999 (or -99999, etc.) for any missing data condition, except for the main time (independent) variable which is never missing) - comma delimited.
		self.variable_names = ''				#Variable names and units (Short variable name and units are required, and optional long descriptive name, in that order, and separated by commas. If the variable is unitless, enter the keyword "none" for its units. Each short variable name and units (and optional long name) are entered on one line. The short variable name must correspond exactly to the name used for that variable as a column header, i.e., the last header line prior to start of data.).
		self.no_special_comment_lines = ''		#Number of SPECIAL comment lines (Integer value indicating the number of lines of special comments, NOT including this line.).
		self.special_comments = ''				#Special comments (Notes of problems or special circumstances unique to this file. An example would be comments/problems associated with a particular flight.).
		self.no_normal_comments = ''			#Number of Normal comments (i.e., number of additional lines of SUPPORTING information: Integer value indicating the number of lines of additional information, NOT including this line.).
		self.normal_comments = ''				#Normal comments (SUPPORTING information: This is the place for investigators to more completely describe the data and measurement parameters. The supporting information structure is described below as a list of key word: value pairs. Specifically include here information on the platform used, the geo-location of data, measurement technique, and data revision comments. Note the non-optional information regarding uncertainty, the upper limit of detection (ULOD) and the lower limit of detection (LLOD) for each measured variable. The ULOD and LLOD are the values, in the same units as the measurements that correspond to the flags -7777’s and -8888’s within the data, respectively. The last line of this section should contain all the “short” variable names on one line. The key words in this section are written in BOLD below and must appear in this section of the header along with the relevant data listed after the colon. For key words where information is not needed or applicable, simply enter N/A.).
		self.data_headers = ''					#headers for data columns
		
		self.createFile(filename, filelocation)
		self.filename = filename
		

	def createFile(self, filename, filelocation):
		os.chdir(filelocation)
		file = open(filename, 'w')
		file.close()
			
	def createHeader(self):
		header = []
		
		date_line = self.data_start_date + '; ' + self.data_revision_date

		
		header = [
		self.PI_names,
		self.PI_affiliations,			
		self.data_source,				
		self.mission_name,				
		self.file_vol,					
		date_line,				
		self.data_interval,				
		self.indep_variable_name ,	
		self.no_of_variables, 			
		self.scale_factors,				
		self.missing_data_indicators,	
		self.variable_names,			
		self.no_special_comment_lines,		
		self.no_normal_comments,		
		self.normal_comments,
		self.data_headers
		]		
		
		if self.special_comments != '':
			header.insert(13, self.special_comments)
		
		header.insert(0, str(len(header)+ int(self.no_normal_comments)+int(self.no_of_variables)-1) + ', 1001')
		
		
		
		
		file = open(self.filename, 'w')
		for line in header:
			file.write(line + '\n')
		file.close()
		
	def writeData(self,data_list):
		file = open(self.filename, 'a')
		for row in data_list:
			for index, item in enumerate(row):
				if np.isnan(item) == True:
					row[index] = '-9999'   
			line = ','.join(str(x) for x in row)
			file.write(line + '\n')
		file.close()
		
			
