import matplotlib.pyplot as plt
from matplotlib import dates
import numpy as np
import os
import sys
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import copy
import calendar
import mysql.connector

timezone = -8

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()


#select data (spikes and fire times already rmoved) 
SP2_data_query = ('SELECT UNIX_UTC_6h_midtime, meas_mean_mass_conc, meas_rel_err, GC_v10_default, GC_default_rel_err, cluster FROM whi_gc_and_sp2_6h_mass_concs WHERE RH_threshold = 90')
			

cursor.execute(SP2_data_query)
raw_data = cursor.fetchall()

#sort by ts
raw_data.sort(key=lambda x: x[0])


SP2_6h_NPac = []
SP2_6h_SPac = []
SP2_6h_Cont = []
SP2_6h_LRT = []

GC2009_BC_concs = []
GC2010_BC_concs = []
GC2012_BC_concs = []

for row in raw_data:
	UTC_ts = row[0]
	PST_date_time = datetime.utcfromtimestamp(UTC_ts) + timedelta(hours = timezone)
	meas_mass_conc = float(row[1])
	meas_rel_err = float(row[2])
	meas_abs_err = meas_rel_err*meas_mass_conc
	GC_mass_conc = row[3]
	GC_rel_err = 0#row[4]
	GC_abs_err = GC_rel_err*GC_mass_conc
	cluster = row[5]
	ratio = GC_mass_conc/meas_mass_conc
	ratio_abs_err = (meas_rel_err + GC_rel_err)*ratio
	
	if cluster == 'NPac':
		SP2_6h_NPac.append([PST_date_time,meas_mass_conc,meas_abs_err,ratio,ratio_abs_err])
	if cluster == 'SPac':
		SP2_6h_SPac.append([PST_date_time,meas_mass_conc,meas_abs_err,ratio,ratio_abs_err])
	if cluster == 'Cont':
		SP2_6h_Cont.append([PST_date_time,meas_mass_conc,meas_abs_err,ratio,ratio_abs_err])
	if cluster == 'GBPS':
		SP2_6h_SPac.append([PST_date_time,meas_mass_conc,meas_abs_err,ratio,ratio_abs_err])
	if cluster == 'LRT':
		SP2_6h_LRT.append([PST_date_time,meas_mass_conc,meas_abs_err,ratio,ratio_abs_err])
	
		
	if PST_date_time.year == 2009:
		GC2009_BC_concs.append([PST_date_time,GC_mass_conc,GC_abs_err])
		GC2009_BC_concs.append([datetime.strptime('2009/07/27', '%Y/%m/%d'),np.nan,np.nan])
		GC2009_BC_concs.append([datetime.strptime('2009/08/08', '%Y/%m/%d'),np.nan,np.nan])
		
	if PST_date_time.year == 2010:
		GC2010_BC_concs.append([PST_date_time,GC_mass_conc,GC_abs_err])
	if PST_date_time.year == 2012:
		GC2012_BC_concs.append([PST_date_time,GC_mass_conc,GC_abs_err])

GC2009_BC_concs.sort(key=lambda x: x[0])

###################plotting

SP2_6h_NPac_date = [dates.date2num(row[0]) for row in SP2_6h_NPac] 
SP2_6h_NPac_mass_conc = [row[1] for row in SP2_6h_NPac]
SP2_6h_NPac_abs_err = [row[2] for row in SP2_6h_NPac]

SP2_6h_SPac_date = [dates.date2num(row[0]) for row in SP2_6h_SPac]
SP2_6h_SPac_mass_conc = [row[1] for row in SP2_6h_SPac]
SP2_6h_SPac_abs_err = [row[2] for row in SP2_6h_SPac]

SP2_6h_Cont_date = [dates.date2num(row[0]) for row in SP2_6h_Cont]
SP2_6h_Cont_mass_conc = [row[1] for row in SP2_6h_Cont]
SP2_6h_Cont_abs_err = [row[2] for row in SP2_6h_Cont]

SP2_6h_LRT_date =  [dates.date2num(row[0]) for row in SP2_6h_LRT]
SP2_6h_LRT_mass_conc = [row[1] for row in SP2_6h_LRT]
SP2_6h_LRT_abs_err = [row[2] for row in SP2_6h_LRT]



ratio_dates_NPac = [dates.date2num(row[0]) for row in SP2_6h_NPac]
ratio_mass_conc_NPac = [row[3] for row in SP2_6h_NPac] 
ratio_err_NPac = [row[4] for row in SP2_6h_NPac]
	
ratio_dates_SPac = [dates.date2num(row[0]) for row in SP2_6h_SPac]
ratio_mass_conc_SPac = [row[3] for row in SP2_6h_SPac] 
ratio_err_SPac = [row[4] for row in SP2_6h_SPac]


ratio_dates_Cont = [dates.date2num(row[0]) for row in SP2_6h_Cont]
ratio_mass_conc_Cont = [row[3] for row in SP2_6h_Cont] 
ratio_err_Cont = [row[4] for row in SP2_6h_Cont]

ratio_dates_LRT = [dates.date2num(row[0]) for row in SP2_6h_LRT]
ratio_mass_conc_LRT = [row[3] for row in SP2_6h_LRT] 
ratio_err_LRT = [row[4] for row in SP2_6h_LRT]


		
GC_6h_2009_date = [dates.date2num(row[0]) for row in GC2009_BC_concs] 
GC_6h_2009_mass_conc = [row[1] for row in GC2009_BC_concs]
GC_6h_2009_neg_err = [row[2] for row in GC2009_BC_concs]
GC_6h_2009_pos_err = [row[2] for row in GC2009_BC_concs]

GC_6h_2010_date = [dates.date2num(row[0]) for row in GC2010_BC_concs] 
GC_6h_2010_mass_conc = [row[1] for row in GC2010_BC_concs]
GC_6h_2010_neg_err = [row[2] for row in GC2010_BC_concs]
GC_6h_2010_pos_err = [row[2] for row in GC2010_BC_concs]

GC_6h_2012_date = [dates.date2num(row[0]) for row in GC2012_BC_concs] 
GC_6h_2012_mass_conc = [row[1] for row in GC2012_BC_concs]
GC_6h_2012_neg_err = [row[2] for row in GC2012_BC_concs]
GC_6h_2012_pos_err = [row[2] for row in GC2012_BC_concs]	

		
		
		
		
#fire times for plotting shaded areas
fire_span2_09s=datetime.strptime('2009/07/27', '%Y/%m/%d') #dates follwing Takahama et al (2011) doi:10.5194/acp-11-6367-2011
fire_span2_09f=datetime.strptime('2009/08/08', '%Y/%m/%d') 

fire_span1_10s=datetime.strptime('2010/07/26 09:00', '%Y/%m/%d %H:%M') #jason's BC clear report
fire_span1_10f=datetime.strptime('2010/07/28 09:30', '%Y/%m/%d %H:%M')


fire_alpha = 0.25
fire_color = '#990000'			

			
###################plotting#####################


fig = plt.figure(figsize=(11.5,7.5))

hfmt = dates.DateFormatter('%b')
#hfmt = dates.DateFormatter('%m-%d')

display_month_interval = 1
max_display_conc = 340

startdate_2009 = '2009/06/25'
enddate_2009 = '2009/08/20'

startdate_2010 = '2010/05/31'
enddate_2010 = '2010/08/04'

startdate_2012 = '2012/03/29'
enddate_2012 = '2012/06/05'


ax7 =  plt.subplot2grid((4,3), (0,0), colspan=1,rowspan = 2)
ax8 =  plt.subplot2grid((4,3), (0,1), colspan=1,rowspan = 2)
ax9 =  plt.subplot2grid((4,3), (0,2), colspan=1,rowspan = 2, sharey=ax8)
										
ax10 = plt.subplot2grid((4,3), (2,0), colspan=1,rowspan = 2)
ax11 = plt.subplot2grid((4,3), (2,1), colspan=1,rowspan = 2, sharey=ax10)
ax12 = plt.subplot2grid((4,3), (2,2), colspan=1,rowspan = 2, sharey=ax10)
											
#combo

ax7.errorbar(SP2_6h_NPac_date,SP2_6h_NPac_mass_conc,yerr = SP2_6h_NPac_abs_err, color='cyan', alpha = 1, fmt = '*')
ax7.errorbar(SP2_6h_SPac_date,SP2_6h_SPac_mass_conc,yerr = SP2_6h_SPac_abs_err, color='green', alpha = 1, fmt = 'o')
ax7.errorbar(SP2_6h_Cont_date,SP2_6h_Cont_mass_conc,yerr = SP2_6h_Cont_abs_err, color='magenta', alpha = 1, fmt = '>')
ax7.errorbar(SP2_6h_LRT_date,SP2_6h_LRT_mass_conc,yerr = SP2_6h_LRT_abs_err, color='blue', alpha = 1, fmt = 's')
ax7.errorbar(GC_6h_2009_date,GC_6h_2009_mass_conc,yerr=[GC_6h_2009_neg_err,GC_6h_2009_pos_err], color = 'k', alpha = 1, marker = 'x')
ax7.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax7.xaxis.set_visible(False)
ax7.yaxis.set_visible(True)
ax7.set_ylabel('rBC mass concentration (ng/m3 - STP)')
ax7.set_ylim(0, max_display_conc)
ax7.set_xlim(dates.date2num(datetime.strptime(startdate_2009, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2009, '%Y/%m/%d')))
ax7.axvspan(dates.date2num(fire_span2_09s),dates.date2num(fire_span2_09f), facecolor=fire_color, alpha=fire_alpha)
ax7.text(0.1, 0.9,'2009', transform=ax7.transAxes)


ax8.errorbar(SP2_6h_NPac_date,SP2_6h_NPac_mass_conc,yerr = SP2_6h_NPac_abs_err, color='cyan', alpha = 1, fmt = '*', label = 'N. Pacific')
ax8.errorbar(SP2_6h_SPac_date,SP2_6h_SPac_mass_conc,yerr = SP2_6h_SPac_abs_err, color='green', alpha = 1, fmt = 'o', label = 'S. Pacific')
ax8.errorbar(SP2_6h_Cont_date,SP2_6h_Cont_mass_conc,yerr = SP2_6h_Cont_abs_err, color='magenta', alpha = 1, fmt = '>', label = 'N. Canada')
ax8.errorbar(SP2_6h_LRT_date,SP2_6h_LRT_mass_conc,yerr = SP2_6h_LRT_abs_err, color='blue', alpha = 1, fmt = 's', label = 'W. Pacific/Asia')
ax8.errorbar(GC_6h_2010_date,GC_6h_2010_mass_conc,yerr=[GC_6h_2010_neg_err,GC_6h_2010_pos_err], color = 'k', alpha = 1, marker = 'x')
ax8.xaxis.set_major_formatter(hfmt)
ax8.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax8.xaxis.set_visible(False)
ax8.yaxis.set_visible(False)
ax8.set_xlabel('month')
ax8.set_ylim(0, max_display_conc)
ax8.set_xlim(dates.date2num(datetime.strptime(startdate_2010, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2010, '%Y/%m/%d')))
ax8.axvspan(dates.date2num(fire_span1_10s),dates.date2num(fire_span1_10f), facecolor=fire_color, alpha=fire_alpha)
ax8.text(0.1, 0.9,'2010', transform=ax8.transAxes)


ax9.errorbar(SP2_6h_NPac_date,SP2_6h_NPac_mass_conc,yerr = SP2_6h_NPac_abs_err, color='cyan', alpha = 1, fmt = '*', label = 'NPac')
ax9.errorbar(SP2_6h_SPac_date,SP2_6h_SPac_mass_conc,yerr = SP2_6h_SPac_abs_err, color='green', alpha = 1, fmt = 'o', label = 'SPac')
ax9.errorbar(SP2_6h_Cont_date,SP2_6h_Cont_mass_conc,yerr = SP2_6h_Cont_abs_err, color='magenta', alpha = 1, fmt = '>', label = 'Cont')
ax9.errorbar(SP2_6h_LRT_date,SP2_6h_LRT_mass_conc,yerr = SP2_6h_LRT_abs_err, color='blue', alpha = 1, fmt = 's', label = 'LRT')
ax9.errorbar(GC_6h_2012_date,GC_6h_2012_mass_conc,yerr=[GC_6h_2012_neg_err,GC_6h_2012_pos_err], color = 'k', alpha = 1, marker = 'x')
ax9.xaxis.set_major_formatter(hfmt)
ax9.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax9.xaxis.set_visible(False)
ax9.yaxis.set_visible(True)
ax9.yaxis.tick_right()
ax9.set_ylim(0, max_display_conc)
ax9.set_xlim(dates.date2num(datetime.strptime(startdate_2012, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2012, '%Y/%m/%d')))
ax9.text(0.1, 0.9,'2012', transform=ax9.transAxes)

legend = ax8.legend(loc='upper center', bbox_to_anchor=(0.5, 1.275), ncol=3, numpoints=1)


#ratios

ax10.errorbar(ratio_dates_SPac,ratio_mass_conc_SPac,yerr = ratio_err_SPac, color='green', alpha = 1, fmt = 'o')
ax10.errorbar(ratio_dates_NPac,ratio_mass_conc_NPac,yerr = ratio_err_NPac, color='cyan', alpha = 1, fmt = '*')
ax10.errorbar(ratio_dates_Cont,ratio_mass_conc_Cont,yerr = ratio_err_Cont, color='magenta', alpha = 1, fmt = '>')
ax10.errorbar(ratio_dates_LRT,ratio_mass_conc_LRT,yerr = ratio_err_LRT, color='blue', alpha = 1, fmt = 's')
ax10.xaxis.set_major_formatter(hfmt)
ax10.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax10.xaxis.set_minor_locator(dates.DayLocator(interval = 2))
ax10.xaxis.set_visible(True)
ax10.yaxis.set_visible(True)
ax10.set_ylabel('GEOS-Chem/Measurements')
#ax10.set_ylim(0, 70)
ax10.set_xlim(dates.date2num(datetime.strptime(startdate_2009, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2009, '%Y/%m/%d')))
ax10.axhline(y=1,color = 'grey', linestyle = '--')
ax10.axvspan(dates.date2num(fire_span2_09s),dates.date2num(fire_span2_09f), facecolor=fire_color, alpha=fire_alpha)
ax10.set_yscale('log')


ax11.errorbar(ratio_dates_SPac,ratio_mass_conc_SPac,yerr = ratio_err_SPac, color='green', alpha = 1, fmt = 'o')
ax11.errorbar(ratio_dates_NPac,ratio_mass_conc_NPac,yerr = ratio_err_NPac, color='cyan', alpha = 1, fmt = '*')
ax11.errorbar(ratio_dates_Cont,ratio_mass_conc_Cont,yerr = ratio_err_Cont, color='magenta', alpha = 1, fmt = '>')
ax11.errorbar(ratio_dates_LRT,ratio_mass_conc_LRT,yerr = ratio_err_LRT, color='blue', alpha = 1, fmt = 's')
ax11.xaxis.set_major_formatter(hfmt)
ax11.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax11.xaxis.set_minor_locator(dates.DayLocator(interval = 2))
ax11.xaxis.set_visible(True)
ax11.yaxis.set_visible(False)
ax11.set_xlabel('month')
ax11.set_xlim(dates.date2num(datetime.strptime(startdate_2010, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2010, '%Y/%m/%d')))
ax11.axhline(y=1,color = 'grey', linestyle = '--')
ax11.axvspan(dates.date2num(fire_span1_10s),dates.date2num(fire_span1_10f), facecolor=fire_color, alpha=fire_alpha)
ax11.set_yscale('log')

ax12.errorbar(ratio_dates_SPac,ratio_mass_conc_SPac,yerr = ratio_err_SPac, color='green', alpha = 1, fmt = 'o')
ax12.errorbar(ratio_dates_NPac,ratio_mass_conc_NPac,yerr = ratio_err_NPac, color='cyan', alpha = 1, fmt = '*')
ax12.errorbar(ratio_dates_Cont,ratio_mass_conc_Cont,yerr = ratio_err_Cont, color='magenta', alpha = 1, fmt = '>')
ax12.errorbar(ratio_dates_LRT,ratio_mass_conc_LRT,yerr = ratio_err_LRT, color='blue', alpha = 1, fmt = 's')
ax12.xaxis.set_major_formatter(hfmt)
ax12.xaxis.set_major_locator(dates.MonthLocator(interval = display_month_interval))
ax12.xaxis.set_minor_locator(dates.DayLocator(interval = 2))
ax12.xaxis.set_visible(True)
ax12.yaxis.set_visible(True)
ax12.yaxis.tick_right()
#ax12.spines['top'].set_visible(False)
#ax12.xaxis.tick_bottom()
ax12.set_xlim(dates.date2num(datetime.strptime(startdate_2012, '%Y/%m/%d')), dates.date2num(datetime.strptime(enddate_2012, '%Y/%m/%d')))
ax12.axhline(y=1,color = 'grey', linestyle = '--')
ax12.set_yscale('log')

#legend = ax12.legend(loc='upper right', shadow=False)

plt.subplots_adjust(hspace=0.08)
plt.subplots_adjust(wspace=0.05)


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/GOES-Chem/')
plt.savefig('timeseries - FT only GEOS-Chem v10 v measurements - db - default 6h - RH90.png', bbox_extra_artists=(legend,), bbox_inches='tight',dpi=600)




plt.show()