import sys
import os
import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt

files = [
'fraction of detectable notch positions by BC core size for 20150405.pickl',
'fraction of detectable notch positions by BC core size for 20150406.pickl',
'fraction of detectable notch positions by BC core size for 20150407.pickl',
'fraction of detectable notch positions by BC core size for 20150408.pickl',
'fraction of detectable notch positions by BC core size for 20150409.pickl',
'fraction of detectable notch positions by BC core size for 20150410.pickl',
'fraction of detectable notch positions by BC core size for 20150411.pickl',
'fraction of detectable notch positions by BC core size for 20150413.pickl',
'fraction of detectable notch positions by BC core size for 20150417.pickl',
'fraction of detectable notch positions by BC core size for 20150420.pickl',
'fraction of detectable notch positions by BC core size for 20150421.pickl',
]

keys = [
'20150405',
'20150406',
'20150407',
'20150408',
'20150409',
'20150410',
'20150411',
'20150413',
'20150417',
'20150420',
'20150421',
]

colors = [
'r',
'b',
'g',
'k',
'orange',
'm',
'cyan',
'yellow',
'grey',
'brown',
'olive'
]


os.chdir('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/')

fig = plt.figure()
ax = fig.add_subplot(111)
i=0
for file in files:
	data_file = open(file, 'r')
	fractions_detectable = pickle.load(data_file)
	data_file.close()
	
	bins = [row[0] for row in fractions_detectable]
	fractions = [row[1]/100 for row in fractions_detectable]
	
	ax.plot(bins,fractions, marker='o', label = keys[i], color = colors[i] )
	i+=1

ax.set_ylabel('fraction of successful LEO fits')
ax.set_xlabel('rBC core VED')
plt.ylim(0,1)
plt.xlim(60,220)
plt.legend(loc=4)

plt.savefig('C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/fraction of detectable split detector notches AND sufficient data pts for fitting vs core size all days.png')

plt.show()