import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
from matplotlib import dates


#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute(('''SELECT *
		FROM whi_gc_and_sp2_1h_mass_concs
	
		''')
		)
data_1h = cursor.fetchall()

times_PST = []
meas = []
GC = []
for row in data_1h:
	ts = row[1]
	ms = row[2]
	gc = row[3]

	ts_datetime = datetime.utcfromtimestamp(ts)
	#if ts_datetime.hour >= 4:
	times_PST.append(dates.date2num(ts_datetime+timedelta(hours=-8)))
	meas.append(ms)
	GC.append(gc)
	


cursor.execute(('''SELECT UNIX_UTC_6h_midtime,meas_mean_mass_conc,meas_rel_err,GC_v10_default
		FROM whi_gc_and_sp2_6h_mass_concs
		WHERE RH_threshold = 90	
		ORDER BY UNIX_UTC_6h_midtime
		''')
		)
data_6h = cursor.fetchall()

times_PST_6h = []
meas_6h = []
meas_err_6h = []
GC_6h = []
for row in data_6h:
	ts_6h = row[0]
	ms_6h = row[1]
	ms_err_6h = row[2]
	gc_6h = row[3]
	
	ts_datetime_6h = datetime.utcfromtimestamp(ts_6h)
	abs_err = ms_6h*ms_err_6h
	
	times_PST_6h.append(dates.date2num(ts_datetime_6h+timedelta(hours=-8)))
	meas_6h.append(ms_6h)
	meas_err_6h.append(abs_err)
	GC_6h.append(gc_6h)


###Plotting

#fire times for plotting shaded areas
fire_span2_09s=datetime.strptime('2009/07/27', '%Y/%m/%d') #dates follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011
fire_span2_09f=datetime.strptime('2009/08/08', '%Y/%m/%d') 

fire_span1_10s=datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M') #jason's BC clear report
fire_span1_10f=datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')

fire_alpha = 0.25
fire_color = '#990000'		

hfmt = dates.DateFormatter('%b')
#hfmt = dates.DateFormatter('%m-%d')

display_month_interval = 1
max_display_conc = 305

startdate_2009 = '2009/06/25'
enddate_2009 = '2009/08/20'
startdate_2010 = '2010/06/05'
enddate_2010 = '2010/08/04'
startdate_2012 = '2012/03/29'
enddate_2012 = '2012/06/05'

fig = plt.figure(figsize=(11.5,7.5))
 
ax1a  = plt.subplot2grid((6,3), (0,0), colspan=1,rowspan = 1)
ax1b  = plt.subplot2grid((6,3), (1,0), colspan=1,rowspan = 2)
ax2   = plt.subplot2grid((6,3), (0,1), colspan=1,rowspan = 3)
ax3   = plt.subplot2grid((6,3), (0,2), colspan=1,rowspan = 3)
ax4a  = plt.subplot2grid((6,3), (3,0), colspan=1,rowspan = 1)
ax4b  = plt.subplot2grid((6,3), (4,0), colspan=1,rowspan = 2)
ax5   = plt.subplot2grid((6,3), (3,1), colspan=1,rowspan = 3)
ax6   = plt.subplot2grid((6,3), (3,2), colspan=1,rowspan = 3)


ax1a.scatter(times_PST,meas,color='darkgrey',marker='.')
ax1a.errorbar(times_PST_6h,meas_6h,yerr=meas_err_6h, color='blue',marker='o',linestyle='')
ax1a.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax1a.xaxis.set_major_formatter(hfmt)
ax1a.xaxis.set_visible(False)
ax1a.yaxis.set_visible(True)
ax1a.set_ylim(480, 860)
ax1a.set_xlim(dates.date2num(datetime.strptime(startdate_2009, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2009, '%Y/%m/%d')))
ax1a.axvspan(dates.date2num(fire_span2_09s),dates.date2num(fire_span2_09f), facecolor=fire_color, alpha=fire_alpha)
ax1a.text(0.1, 0.7,'2009', transform=ax1a.transAxes)
ax1a.set_yticks([500,600,700,800])

ax1b.scatter(times_PST,meas,color='darkgrey',marker='.')
ax1b.errorbar(times_PST_6h,meas_6h,yerr=meas_err_6h, color='blue',marker='o',linestyle='')
ax1b.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax1b.xaxis.set_major_formatter(hfmt)
ax1b.xaxis.set_visible(False)
ax1b.yaxis.set_visible(True)
ax1b.set_ylabel('measured rBC mass\n(ng/m3 - STP)')
ax1b.set_ylim(0, 470)
ax1b.set_xlim(dates.date2num(datetime.strptime(startdate_2009, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2009, '%Y/%m/%d')))
ax1b.axvspan(dates.date2num(fire_span2_09s),dates.date2num(fire_span2_09f), facecolor=fire_color, alpha=fire_alpha)

# hide the spines between ax1a and ax1b
ax1a.spines['bottom'].set_visible(True)
ax1b.spines['top'].set_visible(True)
ax1a.xaxis.tick_top()
ax1a.tick_params(labeltop='off')  # don't put tick labels at the top
ax1b.xaxis.tick_bottom()

#d = .015  # how big to make the diagonal lines in axes coordinates
## arguments to pass plot, just so we don't keep repeating them
#kwargs = dict(transform=ax1a.transAxes, color='k', clip_on=False)
#ax1a.plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
#ax1a.plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
#kwargs.update(transform=ax1b.transAxes)  # switch to the bottom axes
#ax1b.plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
#ax1b.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal




ax2.scatter(times_PST,meas,color='darkgrey',marker='.')
ax2.errorbar(times_PST_6h,meas_6h,yerr=meas_err_6h, color='blue',marker='o',linestyle='')
ax2.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax2.xaxis.set_major_formatter(hfmt)
ax2.xaxis.set_visible(False)
ax2.yaxis.set_visible(True)
ax2.set_yticklabels([])
ax2.set_ylim(0, max_display_conc)
ax2.set_xlim(dates.date2num(datetime.strptime(startdate_2010, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2010, '%Y/%m/%d')))
ax2.axvspan(dates.date2num(fire_span1_10s),dates.date2num(fire_span1_10f), facecolor=fire_color, alpha=fire_alpha)
ax2.text(0.1, 0.9,'2010', transform=ax2.transAxes)

ax3.scatter(times_PST,meas,color='darkgrey',marker='.')
ax3.errorbar(times_PST_6h,meas_6h,yerr=meas_err_6h, color='blue',marker='o',linestyle='')
ax3.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax3.xaxis.set_major_formatter(hfmt)
ax3.xaxis.set_visible(False)
ax3.yaxis.set_visible(True)
ax3.yaxis.tick_right()
ax3.set_ylim(0, max_display_conc)
ax3.set_xlim(dates.date2num(datetime.strptime(startdate_2012, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2012, '%Y/%m/%d')))
ax3.text(0.1, 0.9,'2012', transform=ax3.transAxes)


ax4a.scatter(times_PST,GC,color='darkgrey',marker='.')
ax4a.scatter(times_PST_6h,GC_6h, color='r',marker='o')
ax4a.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax4a.xaxis.set_major_formatter(hfmt)
ax4a.xaxis.set_visible(True)
ax4a.yaxis.set_visible(True)
ax4a.set_ylim(480, 860)
ax4a.set_xlim(dates.date2num(datetime.strptime(startdate_2009, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2009, '%Y/%m/%d')))
ax4a.axvspan(dates.date2num(fire_span2_09s),dates.date2num(fire_span2_09f), facecolor=fire_color, alpha=fire_alpha)
ax4a.set_yticks([500,600,700,800])


ax4b.scatter(times_PST,GC,color='darkgrey',marker='.')
ax4b.scatter(times_PST_6h,GC_6h, color='r',marker='o')
ax4b.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax4b.xaxis.set_major_formatter(hfmt)
ax4b.xaxis.set_visible(True)
ax4b.yaxis.set_visible(True)
ax4b.set_ylabel('simulated rBC mass\n(ng/m3 - STP)')
ax4b.set_ylim(0, 470)
ax4b.set_xlim(dates.date2num(datetime.strptime(startdate_2009, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2009, '%Y/%m/%d')))
ax4b.axvspan(dates.date2num(fire_span2_09s),dates.date2num(fire_span2_09f), facecolor=fire_color, alpha=fire_alpha)

# hide the spines between ax4a and ax4b
ax4a.spines['bottom'].set_visible(True)
ax4b.spines['top'].set_visible(True)
ax4a.xaxis.tick_top()
ax4a.tick_params(labeltop='off')  # don't put tick labels at the top
ax4b.xaxis.tick_bottom()

ax5.scatter(times_PST,GC,color='darkgrey',marker='.')
ax5.scatter(times_PST_6h,GC_6h, color='r',marker='o')
ax5.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax5.xaxis.set_major_formatter(hfmt)
ax5.xaxis.set_visible(True)
ax5.yaxis.set_visible(True)
ax5.set_yticklabels([])
ax5.set_ylim(0, max_display_conc)
ax5.set_xlim(dates.date2num(datetime.strptime(startdate_2010, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2010, '%Y/%m/%d')))
ax5.axvspan(dates.date2num(fire_span1_10s),dates.date2num(fire_span1_10f), facecolor=fire_color, alpha=fire_alpha)

ax6.scatter(times_PST,GC,color='darkgrey',marker='.')
ax6.scatter(times_PST_6h,GC_6h, color='r',marker='o')
ax6.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax6.xaxis.set_major_formatter(hfmt)
ax6.xaxis.set_visible(True)
ax6.yaxis.set_visible(True)
ax6.yaxis.tick_right()
ax6.set_ylim(0, max_display_conc)
ax6.set_xlim(dates.date2num(datetime.strptime(startdate_2012, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2012, '%Y/%m/%d')))

plt.subplots_adjust(hspace=0.15)
plt.subplots_adjust(wspace=0.02)

os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
plt.savefig('timeseries - FT only GEOS-Chem v10 v measurements - db - default 1h and 6h.png', bbox_inches='tight')

plt.show()