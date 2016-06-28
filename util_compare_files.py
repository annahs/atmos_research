import sys
import os
import numpy as np
from pprint import pprint
from itertools import izip

file0 = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/1Hz-ict-R0/UHSAS_Polar6_20150406_R0_V1.ict'

file1 = 'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/UHSAS/UHSAS-R1/UHSAS_Polar6_20150406_R1_V1.ict'

i=0
for line_from_file_0, line_from_file_1 in izip(open(file0), open(file1)):
	if line_from_file_0 != line_from_file_1:
		print 'line no :', i+1
		print line_from_file_0
		print line_from_file_1
		raw_input("Press Enter to continue...")
	i+=1
	
R0_file.close()
R1_file.close()