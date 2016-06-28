##Creates a simple Gantt chart
#Adapted from https://bitbucket.org/DBrent/phd/src/1d1c5444d2ba2ee3918e0dfd5e886eaeeee49eec/visualisation/plot_gantt.py
#BHC 2014

 
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.dates
from matplotlib.dates import MONTHLY, DateFormatter, rrulewrapper, RRuleLocator
from pylab import *
from pprint import pprint
import os


def create_date(year,month,day):
#Creates the date"""
 	date = dt.datetime(int(year), int(month), int(day))
	mdate = matplotlib.dates.date2num(date)
 
	return mdate
 
# Data
 
pos = arange(0.5,3.5,0.5)
 
ylabels = []
ylabels.append('SP2 #17')
ylabels.append('SP2 #44')
ylabels.append('SP2 #58')



customDates = []
customDates.append([create_date(2011,3,5),create_date(2012,3,24)])  #17
customDates.append([create_date(2012,3,27),create_date(2013,9,22)])  #44
customDates.append([create_date(2013,9,27),create_date(2016,1,1)])

task_dates = {}
for i,task in enumerate(ylabels):
	task_dates[task] = customDates[i]

	
# Initialise plot
fig = plt.figure(figsize=(22,6))
# ax = fig.add_axes([0.15,0.2,0.75,0.3]) #[left,bottom,width,height]
ax = fig.add_subplot(111)
 
# Plot the data
 
start_date,end_date = task_dates[ylabels[0]]
ax.barh(0.5, end_date - start_date, left=start_date, height=0.1, align='center', color='blue', alpha = 0.75)
for i in range(0,len(ylabels)-1):
	start_date,end_date = task_dates[ylabels[i+1]]
	ax.barh((i*0.5)+1.0, end_date - start_date,left=start_date, height=0.1, align='center', color='blue', alpha = 0.75)
	 
# Format the y-axis
locsy, labelsy = yticks(pos,ylabels)
plt.setp(labelsy, fontsize = 14)
ax.margins(0, 0.5)

# Format the x-axis
ax.axis('tight')
ax.grid(color = 'g', linestyle = ':')
ax.xaxis_date() #Tell matplotlib that these are dates...
 
rule = rrulewrapper(MONTHLY, interval=1)
loc = RRuleLocator(rule)
formatter = DateFormatter("%b %Y")
 
ax.xaxis.set_major_locator(loc)
ax.xaxis.set_major_formatter(formatter)
 
 
# Format the legend
 
font = font_manager.FontProperties(size='small')
#ax.legend(loc=1,prop=font)
 
# Finish up
ax.invert_yaxis()
fig.autofmt_xdate(rotation=90)
os.chdir('C:/Users/Sarah Hanna/Documents/Data/Alert Data/')
plt.savefig('gantt.png',bbox_inches = 'tight')
plt.show()