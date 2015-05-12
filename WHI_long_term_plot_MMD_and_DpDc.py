import numpy as np
import matplotlib.pyplot as plt
import sys
import pickle
import os
from pprint import pprint
from scipy.optimize import curve_fit
import math
from datetime import datetime
from matplotlib import dates


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
file = open('MMD_and_coating_data.binpickl', 'r')
data = pickle.load(file)
file.close()

def lognorm(x_vals, A, w, xc):
	return A/(np.sqrt(2*math.pi)*w*x_vals)*np.exp(-(np.log(x_vals/xc))**2/(2*w**2))
	

	
i=70
bins = []
while i <= 220:
	i+=0.1
	bins.append(i)

new_data = []	
for row in data:
	datetime =  row[0]
	cluster_no = row[1]
	DpDc = row[2] 	
	
	mass_distr = row[3]
	mass_bins = np.array([row[0] for row in mass_distr])
	masses = [row[1] for row in mass_distr]
	temp = []
	for mass in masses:
		norm_mass = mass/np.max(masses)
		temp.append(norm_mass)
	masses_max1 = np.array(temp)
	A=np.nan
	w=np.nan
	xc=np.nan
	try:
		popt, pcov = curve_fit(lognorm, mass_bins, masses_max1)
		A=popt[0]
		w=popt[1]
		xc=popt[2]
		fit_y_vals = []
		for bin in bins:
			fit_val = lognorm(bin, popt[0], popt[1], popt[2])
			fit_y_vals.append(fit_val)
			
		MMD =  bins[np.argmax(fit_y_vals)]
	except:
		MMD = np.nan
	#print MMD, xc, math.exp(math.log(xc)-(w**2)/2)
	
	##plotting
	#fig = plt.figure()
    #
	#ax1 = fig.add_subplot(111)
	#ax1.scatter(mass_bins, masses_max1)
	#ax1.plot(bins, fit_y_vals)
	#plt.xlabel('VED (nm)')
	#plt.ylabel('dM/dlog(VED)')
	#ax1.set_xscale('log')
    #
	#plt.show()
     
	
	new_data.append([datetime, cluster_no, DpDc, MMD])

GBPS = []
Cont = []
SPac = []
NPac = []
LRT = []

for line in new_data:
	datetime = line[0]
	cluster_no = line[1]
	DpDc= line[2]
	MMD = line[3]

	if MMD >= 220 or MMD <=75:
		MMD = np.nan
	
	newline = [datetime, cluster_no, DpDc, MMD]
	
	if cluster_no == 9:
		GBPS.append(newline)
	if cluster_no == 4:
		Cont.append(newline)
	if cluster_no in [6,8]:
		SPac.append(newline)
	if cluster_no in [2,7]:
		LRT.append(newline)
	if cluster_no in [1,3,5,10]:
		NPac.append(newline)

GBPS_datetimes =  [dates.date2num(row[0]) for row in GBPS]
GBPS_DpDc = [row[2] for row in GBPS] 	
GBPS_MMD = [row[3] for row in GBPS] 	

Cont_datetimes =  [dates.date2num(row[0]) for row in Cont]
Cont_DpDc = [row[2] for row in Cont] 	
Cont_MMD = [row[3] for row in Cont] 	

NPac_datetimes =  [dates.date2num(row[0]) for row in NPac]
NPac_DpDc = [row[2] for row in NPac] 	
NPac_MMD = [row[3] for row in NPac] 	

SPac_datetimes =  [dates.date2num(row[0]) for row in SPac]
SPac_DpDc = [row[2] for row in SPac] 	
SPac_MMD = [row[3] for row in SPac] 	

LRT_datetimes =  [dates.date2num(row[0]) for row in LRT]
LRT_DpDc = [row[2] for row in LRT] 	
LRT_MMD = [row[3] for row in LRT] 	
		
fire_span1_10s=datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M') #jason's BC clear report
fire_span1_10f=datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')
fire_alpha = 0.25
fire_color = '#990000'

fig = plt.figure(figsize=(12,4))

hfmt = dates.DateFormatter('%b')
#hfmt = dates.DateFormatter('%m-%d')

display_month_interval = 1

startdate_2010 = '2010/05/31'
enddate_2010 = '2010/08/04'

startdate_2012 = '2012/03/29'
enddate_2012 = '2012/06/05'
colors = ['r','g','b','k','c','m','grey', 'orange', 'yellow']
                           
ax7 =  plt.subplot2grid((4,2), (0,0), colspan=1,rowspan = 2)
ax8 =  plt.subplot2grid((4,2), (0,1), colspan=1,rowspan = 2, sharey=ax7)
ax9 =  plt.subplot2grid((4,2), (2,0), colspan=1,rowspan = 2)
ax10 =  plt.subplot2grid((4,2), (2,1), colspan=1,rowspan = 2, sharey=ax9)
																			

ax7.scatter(GBPS_datetimes,GBPS_DpDc, marker = 'o', color = 'r', label='GBPS')
ax7.scatter(SPac_datetimes,SPac_DpDc, marker = 'o', color = 'g', label='SPac')
ax7.scatter(NPac_datetimes,NPac_DpDc, marker = 'o', color = 'c', label='NPac')
ax7.scatter(Cont_datetimes,Cont_DpDc, marker = 'o', color = 'm', label='NCan')
ax7.scatter(LRT_datetimes,LRT_DpDc, marker = 'o', color = 'b', label='WPac/Asia')
ax7.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax7.xaxis.set_major_formatter(hfmt)
ax7.xaxis.set_visible(False)
ax7.yaxis.set_visible(True)
ax7.set_ylabel('Dp/Dc')
ax7.set_xlim(dates.date2num(datetime.strptime(startdate_2010, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2010, '%Y/%m/%d')))
ax7.axvspan(dates.date2num(fire_span1_10s),dates.date2num(fire_span1_10f), facecolor=fire_color, alpha=fire_alpha)
ax7.text(0.1, 0.8,'2010', transform=ax7.transAxes)
ax7.set_ylim(0.8,3.5)


ax9.scatter(GBPS_datetimes,GBPS_MMD, marker = '*', color = 'r', label='GBPS')
ax9.scatter(SPac_datetimes,SPac_MMD, marker = '*', color = 'g', label='SPac')
ax9.scatter(NPac_datetimes,NPac_MMD, marker = '*', color = 'c', label='NPac')
ax9.scatter(Cont_datetimes,Cont_MMD, marker = '*', color = 'm', label='NCan')
ax9.scatter(LRT_datetimes, LRT_MMD, marker = '*', color = 'b', label='WPac/Asia')
ax9.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax9.set_xlim(dates.date2num(datetime.strptime(startdate_2010, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2010, '%Y/%m/%d')))
ax9.axvspan(dates.date2num(fire_span1_10s),dates.date2num(fire_span1_10f), facecolor=fire_color, alpha=fire_alpha)
ax9.xaxis.set_major_formatter(hfmt)
ax9.set_ylabel('MMD')
ax9.set_ylim(70,255)

ax8.scatter(GBPS_datetimes,GBPS_DpDc, marker = 'o', color = 'r', label='Georgia Basin/Puget Sound')
ax8.scatter(SPac_datetimes,SPac_DpDc, marker = 'o', color = 'g', label='S. Pacific')
ax8.scatter(NPac_datetimes,NPac_DpDc, marker = 'o', color = 'c', label='N. Pacific')
ax8.scatter(Cont_datetimes,Cont_DpDc, marker = 'o', color = 'm', label='N. Canada')
ax8.scatter(LRT_datetimes,LRT_DpDc, marker = 'o', color = 'b', label='W. Pacific/Asia')
ax8.xaxis.set_major_formatter(hfmt)
ax8.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax8.xaxis.set_visible(False)
ax8.yaxis.set_visible(True)
ax8.yaxis.tick_right()
ax8.set_xlabel('month')
ax8.set_xlim(dates.date2num(datetime.strptime(startdate_2012, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2012, '%Y/%m/%d')))
ax8.text(0.1, 0.8,'2012', transform=ax8.transAxes)
ax8.set_ylim(0.8,3.5)


ax10.scatter(GBPS_datetimes,GBPS_MMD, marker = '*', color = 'r', label='GBPS')
ax10.scatter(SPac_datetimes,SPac_MMD, marker = '*', color = 'g', label='SPac')
ax10.scatter(NPac_datetimes,NPac_MMD, marker = '*', color = 'c', label='NPac')
ax10.scatter(Cont_datetimes,Cont_MMD, marker = '*', color = 'm', label='NCan')
ax10.scatter(LRT_datetimes, LRT_MMD, marker = '*', color = 'b', label='WPac/Asia')
ax10.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax10.xaxis.set_major_formatter(hfmt)
ax10.yaxis.tick_right()
ax10.set_xlim(dates.date2num(datetime.strptime(startdate_2012, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2012, '%Y/%m/%d')))
ax10.set_ylim(70,255)

legend = ax8.legend(loc='upper right', bbox_to_anchor=(0.85, 1.6), ncol=3, numpoints=1)

plt.subplots_adjust(hspace=0.0)
plt.subplots_adjust(wspace=0.0)

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/')
plt.savefig('timeseries-DpDc and MMD.png', bbox_extra_artists=(legend,), bbox_inches='tight')

plt.show()

	