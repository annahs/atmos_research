import os
import numpy as np
from pyhdf.SD import SD, SDC, SDS
from pprint import pprint
import sys


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/default/')


# Open file.
#FILE_NAME = 'ts20120531.150000.hdf'
FILE_NAME = 'ts20090701.010000.hdf'
hdf = SD(FILE_NAME, SDC.READ)

# List available SDS datasets.
pprint(hdf.datasets())

for dataset in hdf.datasets():
	print dataset
	data = hdf.select(dataset)
	pprint(data.attributes())
	raw_input("Press Enter to continue...")
	
	
# Read dataset.
DATAFIELD_NAME='PEDGE-$::PSURF'
data = hdf.select(DATAFIELD_NAME)
pprint(data.attributes())
pprint(data[:])

pressures = hdf.select('PEDGE-$::PSURF')
lats = hdf.select('LAT')
lons = hdf.select('LON')
print lats[:], lons[:]



