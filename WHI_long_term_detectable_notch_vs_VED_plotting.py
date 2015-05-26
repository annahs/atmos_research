import sys
import os
import pickle
import math
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('fraction of detectable notch positions by BC core size - aged.pickl', 'r')
fractions_detectable_aged = pickle.load(file)
file.close()

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('fraction of detectable notch positions by BC core size - fresh.pickl', 'r')
fractions_detectable_fresh = pickle.load(file)
file.close()


fractions_detectable_fresh.pop(0)  #get rid of 65-70 bin, since no data really here
fractions_detectable_aged.pop(0)  #get rid of 65-70 bin, since no data really here

pprint(fractions_detectable_aged)
pprint(fractions_detectable_fresh)

##plotting

bins_aged = [row[0] for row in fractions_detectable_aged]
fractions_aged = [row[1] for row in fractions_detectable_aged]

bins_fresh = [row[0] for row in fractions_detectable_fresh]
fractions_fresh = [row[1] for row in fractions_detectable_fresh]



#####plotting

fig = plt.figure()
ax = fig.add_subplot(111)
ax.scatter(bins_aged, fractions_aged, color = 'b', label = 'Background')
ax.scatter(bins_fresh, fractions_fresh, color = 'r', label = 'Fresh emissions')
ax.set_ylim(0,1.0)
ax.set_ylabel('fraction of particles with detectable notch position')
ax.set_xlabel('rBC core VED (nm)')
#ax.axvline(95, color='g', linestyle='-')
ax.axvline(155, color='r', linestyle='--')
ax.axvline(180, color='r', linestyle='--')

plt.legend(loc = 2)

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
plt.savefig('fraction of particles with detectable zero-crossing', bbox_inches='tight')

plt.show()      