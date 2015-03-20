import sys
import os
import numpy as np
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
from matplotlib import dates
import pickle
from haversine_calculator import haversine


os.chdir('C:/Users/Sarah Hanna/Documents/Data/WHI long term record/Fire counts/')

historical_file = 'H_FIRE_PNT.txt'
current_file = 'C_FIRE_PNT.txt'
start_date = datetime.strptime('2009/01/01', '%Y/%m/%d')
WHI_lat = 50.06
WHI_lon = -122.96

f = open(historical_file, 'r')
f.readline() #skip header

daily_counts = {}
first_date_key = datetime.strptime('2009/01/01', '%Y/%m/%d')
last_date_key = datetime.strptime('2014/01/01', '%Y/%m/%d')
current_date_key = first_date_key
while current_date_key <= last_date_key:
    daily_counts[current_date_key] = 0
    current_date_key += timedelta(days = 1)



bad_records = 0

#get historical fire info

for row in f:
    row = row.split('\t')
    try:
        date_stamp = row[2]
        date_stamp = date_stamp[:-6]
        size =  float(row[5])
        lon = float(row[6])
        lat = float(row[10])
        distance = haversine(WHI_lon,WHI_lat,lon, lat)  #haversine function calculates the great circle distance between two points on the earth (specified in decimal degrees), function form is haversine(lon1, lat1, lon2, lat2)
        format = '%Y%m%d'    
        try:
            date = datetime.strptime(date_stamp, format)
        except:
            pass
    except:
        bad_records+=1
        
    
        
    date_key = date  
    
    if distance <= 200 and size > 0 and date >= start_date:
        if daily_counts.has_key(date_key):
            daily_counts[date_key]+=1
        else:
            daily_counts[date_key] = 1
                
f.close()

count = 0
for key, value in daily_counts.iteritems():
    if key >= datetime.strptime('20090727', '%Y%m%d') and key < datetime.strptime('20090808', '%Y%m%d'):
        print value
        count = count + value



#get current fire info

f = open(current_file, 'r')
f.readline() #skip header

for row in f:
    row = row.split('\t')
    try:
        date_stamp = row[14]
        date_stamp = date_stamp[:-6]
        size =  float(row[7])
        lon = float(row[1])
        lat = float(row[5])
        distance = haversine(WHI_lon,WHI_lat,lon, lat)  #haversine function calculates the great circle distance between two points on the earth (specified in decimal degrees), function form is haversine(lon1, lat1, lon2, lat2)
        format = '%Y%m%d'    
        try:
            date = datetime.strptime(date_stamp, format)
        except:
            pass
    except:
        bad_records+=1
        
        
    date_key = date  
    
    if distance <= 200.0 and size > 0 and date >= start_date:
        if daily_counts.has_key(date_key):
            daily_counts[date_key]+=1
        else:
            daily_counts[date_key] = 1
                
f.close()

print bad_records


#get sorted list of lists from dictionary
sorted_count_list = []
sorted_keys = sorted(daily_counts)
for value in sorted_keys:   
    newline = [value,daily_counts[value]]
    sorted_count_list.append(newline)


  
#pickle the list
file = open('fire_counts.firespckl', 'w')
pickle.dump(sorted_count_list, file)
file.close()


#write final sorted list of counts to file
file = open('fire_counts.txt', 'w')
for line in sorted_count_list:
    line_to_write = str(line[0]) + '\t' +  str(line[1]) + '\n'
    file.write(line_to_write)
file.close()

#plotting
np_sorted_count_list = np.array(sorted_count_list)
fire_dates = dates.date2num(np_sorted_count_list[:,0])
counts = np_sorted_count_list[:,1]

fig = plt.figure()

hfmt = dates.DateFormatter('%Y-%m-%d')

ax1 = fig.add_subplot(111)
ax1.bar(fire_dates,counts, width=1.0)      
ax1.xaxis.set_major_formatter(hfmt)
ax1.xaxis.set_major_locator(dates.MonthLocator(interval = 4))
plt.ylabel('fire starts within 200km of WHI')
plt.axhline(y=10, color='black')
plt.xlabel('date')

plt.show()