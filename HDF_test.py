import os
import numpy as np
from pyhdf.SD import SD, SDC, SDS
from pprint import pprint


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/wet_scavenging')
os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/Junwei_runs/')


# Open file.
#FILE_NAME = 'ts20120531.150000.hdf'
FILE_NAME = 'ts20090701.010000.hdf'
hdf = SD(FILE_NAME, SDC.READ)

# List available SDS datasets.
#pprint(hdf.datasets())

# Read dataset.
DATAFIELD_NAME='IJ-AVG-$::BCPI'
DATAFIELD_NAME='LON'
data = hdf.select(DATAFIELD_NAME)
pprint(data.attributes())
#pprint(data[10,20,7])

## Read geolocation dataset.
#lat = hdf.select('Latitude')
#latitude = lat[:,:]
#lon = hdf.select('Longitude')
#longitude = lon[:,:]

