import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import mysql.connector
import math
import matplotlib.pyplot as plt
from scipy import stats

#database connection
cnx = mysql.connector.connect(user='root', password='Suresh15', host='localhost', database='black_carbon')
cursor = cnx.cursor()

cursor.execute(('''SELECT mc.meas_mean_mass_conc, mc.meas_rel_err, mc.UNIX_UTC_6h_midtime, mc.cluster_number, measCO.CO_ppbv
		FROM whi_gc_and_sp2_6h_mass_concs mc
		JOIN whi_co_data measCO on mc.CO_meas_id = measCO.id 
		WHERE mc.RH_threshold = 90 and measCO.CO_ppbv < 250''')
		)
data = cursor.fetchall()

cnx.close()

plot_data_Cont = []
plot_data_SPac = []
plot_data_NPac = []
plot_data_WPac = []

for row in data:
	meas_rBC_v = row[0]/1.29 #density of air is 1.29kg/m3 at 0C and 1atm
	meas_rel_err_v = row[1]
	date = datetime.utcfromtimestamp(row[2])
	cluster_number = row[3]
	meas_CO_v = row[4]
	if date.month == 4:
		color = 'g'
	if date.month == 5:
		color = 'b'
	if date.month == 6:
		color = 'orange'
	if date.month == 7:
		color = 'red'
	if date.month == 8:
		color = 'm'
	
	
	
	line = [meas_rBC_v,meas_rel_err_v,meas_CO_v,color]
	
	if cluster_number in [4]:  #Spac = 6,8,9 Npac = 1,3,5,10, Cont = 4  LRT = 2,7
		plot_data_Cont.append(line)
	if cluster_number in [6,8,9]:  #Spac = 6,8,9 Npac = 1,3,5,10, Cont = 4  LRT = 2,7
		plot_data_SPac.append(line)
	if cluster_number in [1,3,5,10]:  #Spac = 6,8,9 Npac = 1,3,5,10, Cont = 4  LRT = 2,7
		plot_data_NPac.append(line)
	if cluster_number in [2,7]:  #Spac = 6,8,9 Npac = 1,3,5,10, Cont = 4  LRT = 2,7
		plot_data_WPac.append(line)

		
Cont_bc = [row[0] for row in plot_data_Cont]
Cont_bc_err = [row[1]*row[0] for row in plot_data_Cont]
Cont_co = [row[2] for row in plot_data_Cont]
Cont_month = [row[3] for row in plot_data_Cont]
varx = np.array(Cont_co)
vary = np.array(Cont_bc)
mask = ~np.isnan(varx) & ~np.isnan(vary)
Cont_slope, Cont_intercept, Cont_r_value, Cont_p_value, Cont_std_err = stats.linregress(varx[mask], vary[mask])
Cont_line = Cont_slope*varx+Cont_intercept

SPacbc = [row[0] for row in plot_data_SPac]
SPacbc_err = [row[1]*row[0] for row in plot_data_SPac]
SPacco = [row[2] for row in plot_data_SPac]
SPacmonth = [row[3] for row in plot_data_SPac]
varx = np.array(SPacco)
vary = np.array(SPacbc)
mask = ~np.isnan(varx) & ~np.isnan(vary)
SPacslope, SPacintercept, SPacr_value, SPacp_value, SPacstd_err = stats.linregress(varx[mask], vary[mask])
SPacline = SPacslope*varx+SPacintercept

NPacbc = [row[0] for row in plot_data_NPac]
NPacbc_err = [row[1]*row[0] for row in plot_data_NPac]
NPacco = [row[2] for row in plot_data_NPac]
NPacmonth = [row[3] for row in plot_data_NPac]
varx = np.array(NPacco)
vary = np.array(NPacbc)
mask = ~np.isnan(varx) & ~np.isnan(vary)
NPacslope, NPacintercept, NPacr_value, NPacp_value, NPacstd_err = stats.linregress(varx[mask], vary[mask])
NPacline = NPacslope*varx+NPacintercept

WPacbc = [row[0] for row in plot_data_WPac]
WPacbc_err = [row[1]*row[0] for row in plot_data_WPac]
WPacco = [row[2] for row in plot_data_WPac]
WPacmonth = [row[3] for row in plot_data_WPac]
varx = np.array(WPacco)
vary = np.array(WPacbc)
mask = ~np.isnan(varx) & ~np.isnan(vary)
WPacslope, WPacintercept, WPacr_value, WPacp_value, WPacstd_err = stats.linregress(varx[mask], vary[mask])
WPacline = WPacslope*varx+WPacintercept




fig = plt.figure(figsize=(12,10))
         
ax1  = plt.subplot2grid((2,2), (1,1), colspan=1)
ax2  = plt.subplot2grid((2,2), (0,0), colspan=1)
ax3  = plt.subplot2grid((2,2), (0,1), colspan=1)
ax4  = plt.subplot2grid((2,2), (1,0), colspan=1)

CO_upper = 200
CO_lower = 50
BC_upper = 325
info_x_pos = 0.65
info_y_pos = 0.8
label_x_pos = 0.05
label_y_pos = 0.92

ax1.scatter(Cont_co,Cont_bc,c=Cont_month, marker = 'o',s=40)
ax1.errorbar(Cont_co,Cont_bc,yerr = Cont_bc_err,fmt = None,zorder=0)
ax1.plot(Cont_co,Cont_line,color='b')
ax1.text(info_x_pos, info_y_pos+0.07 ,'r-square: ' + str(round(Cont_r_value**2,3)),transform=ax1.transAxes, color='grey')
ax1.text(info_x_pos, info_y_pos,'slope: ' + str(round(Cont_slope,3)),transform=ax1.transAxes, color='grey')
ax1.text(label_x_pos, label_y_pos,'Northern Canada',transform=ax1.transAxes, color='k')
ax1.set_ylabel('rBC ng/kg')
ax1.set_xlabel('CO ppbv')
ax1.set_xlim(CO_lower,CO_upper)
ax1.set_ylim(0,BC_upper)

ax2.scatter(NPacco,NPacbc,c=NPacmonth, marker = 'o',s=40)
ax2.errorbar(NPacco,NPacbc,yerr = NPacbc_err,fmt = None,zorder=0)
ax2.plot(NPacco,NPacline,color='b')
ax2.text(info_x_pos, (info_y_pos+0.07),'r-square: ' + str(round(NPacr_value**2,3)),transform=ax2.transAxes, color='grey')
ax2.text(info_x_pos, info_y_pos,'slope: ' + str(round(NPacslope,3)),transform=ax2.transAxes, color='grey')
ax2.text(label_x_pos,label_y_pos,'Northern Pacific',transform=ax2.transAxes, color='k')
ax2.set_ylabel('rBC ng/kg')
ax2.set_xlabel('CO ppbv')
ax2.set_xlim(CO_lower,CO_upper)
ax2.set_ylim(0,BC_upper)


ax3.scatter(SPacco,SPacbc,c=SPacmonth, marker = 'o',s=40)
ax3.errorbar(SPacco,SPacbc,yerr = SPacbc_err,fmt = None,zorder=0)
ax3.plot(SPacco,SPacline,color='b')
ax3.text(info_x_pos, info_y_pos+0.07,'r-square: ' + str(round(SPacr_value**2,3)),transform=ax3.transAxes, color='grey')
ax3.text(info_x_pos, info_y_pos,'slope: ' + str(round(SPacslope,3)),transform=ax3.transAxes, color='grey')
ax3.text(label_x_pos, label_y_pos,'Southern Pacific',transform=ax3.transAxes, color='k')
ax3.set_ylabel('rBC ng/kg')
ax3.set_xlabel('CO ppbv')
ax3.set_xlim(CO_lower,CO_upper)
ax3.set_ylim(0,BC_upper)

  
ax4.scatter(WPacco,WPacbc,c=WPacmonth, marker = 'o',s=40)
ax4.errorbar(WPacco,WPacbc,yerr = WPacbc_err,fmt = None,zorder=0)
ax4.plot(WPacco,WPacline,color='b')
ax4.text(info_x_pos, info_y_pos+0.07,'r-square: ' + str(round(WPacr_value**2,3)),transform=ax4.transAxes, color='grey')
ax4.text(info_x_pos, info_y_pos,'slope: ' + str(round(WPacslope,3)),transform=ax4.transAxes, color='grey')
ax4.text(label_x_pos, label_y_pos,'Western Pacific/Asia',transform=ax4.transAxes, color='k')
ax4.set_ylabel('rBC ng/kg')
ax4.set_xlabel('CO ppbv')
ax4.set_xlim(CO_lower,CO_upper)
ax4.set_ylim(0,BC_upper)


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/CO data/')
plt.savefig('BC vs CO - all clusters.png', bbox_inches='tight') 


plt.show()