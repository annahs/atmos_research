#look through hk files to find periods of bad sample flow or laser power. Log these so incandesence data collected during these times can be ignored.
#use where hk columns 1,3,4 = timestamp(UTC), measured sample flow, Yag power

import sys
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import pickle

def find_bad_hk_durations(parameters):
    os.chdir(parameters['directory'])
          
    hk_alldata = np.empty([0,3])

    #find and concatenate any hk files in directory
    for file in os.listdir('.'):
        if file.endswith('.hk'):
            print file
            hk_filedata = np.genfromtxt(file, delimiter="\t", skip_header=1, usecols=(1,3,4)) #timestamp, measured sample flow, Yag power
            hk_alldata = np.concatenate((hk_alldata, hk_filedata), axis=0)

    #conversion for labview timestamp to UNIX timestamp (in s). UNIX epoch is 1 Jan 1970, Labview epoch is 1 Jan 1904
    LVts_to_UNIXts = -2082844800 #http://www.onlineconversion.com/unix_time.htm
    timezone = parameters['timezone']*3600
    date = datetime.datetime.utcfromtimestamp(hk_alldata[0,0]+LVts_to_UNIXts+timezone)

    #calc mean and sd for YAG power and set conf level. Also set min and max values        
    lasermean = np.average(hk_alldata[:,2])
    lasersd = np.std(hk_alldata[:,2])
    laser_CIsds = 2
    flow_min = parameters['flow_min']
    flow_max = parameters['flow_max']
    laser_min = lasermean-0.5*lasermean
    laser_max = lasermean+0.5*lasermean

    #generate YAG and flow plots
    plt.figure(1)
    plt.plot(hk_alldata[:,0], hk_alldata[:,2])
    lasermean_line = plt.axhline(y=lasermean, color='g')
    lasersd_line_pos = plt.axhline(y=laser_max, color='r')
    lasersd_line_neg = plt.axhline(y=laser_min, color='r')

    plt.figure(2)
    plt.plot(hk_alldata[:,0], hk_alldata[:,1])
    flow120_line = plt.axhline(y=120, color='g')
    flowsd_line_pos = plt.axhline(y=flow_max, color='r')
    flowsd_line_neg = plt.axhline(y=flow_min, color='r')

    if parameters['show_plot']:
        plt.show()

    #loop through hk_alldata and find intervals where laser and/or flow were bad, log these intervals to new lists
    hk_baddurations_yag = []
    hk_baddurations_flow = []
    duration_start_yag = False
    duration_start_flow = False

    for i, vals in enumerate(hk_alldata):
        if hk_alldata[i,2] > laser_max or hk_alldata[i,2] < laser_min:  #note a bad laser value
            if duration_start_yag == False: #we're not in the middle of a bad duration right now
                duration_start_yag = hk_alldata[i,0]+LVts_to_UNIXts+timezone    #set the duration start time
        if hk_alldata[i,2] < laser_max and hk_alldata[i,2] > laser_min and duration_start_yag != False: #we were in a bad duration, but now we're good
            hk_baddurations_yag.append([duration_start_yag, hk_alldata[i,0]+LVts_to_UNIXts+timezone]) #add the duration to the list
            duration_start_yag = False 
            
        if hk_alldata[i,1] > flow_max or hk_alldata[i,1] < flow_min: #as above for flows
            if duration_start_flow == False:
                duration_start_flow = hk_alldata[i,0]+LVts_to_UNIXts+timezone
        if hk_alldata[i,1] < flow_max and hk_alldata[i,1] > flow_min and duration_start_flow != False:
            hk_baddurations_flow.append([duration_start_flow, hk_alldata[i,0]+LVts_to_UNIXts+timezone]) 
            duration_start_flow = False

    #take care of special case of last row 
    if duration_start_yag != False:
        hk_baddurations_yag.append([duration_start_yag, hk_alldata[i,0]+LVts_to_UNIXts+timezone]) 
        duration_start_yag = False
    if duration_start_flow != False:
        hk_baddurations_flow.append([duration_start_flow, hk_alldata[i,0]+LVts_to_UNIXts+timezone]) 
        duration_start_flow = False

    #if good periods between bad durations in the flow are only a few sec long, we'll assume the flow was oscillating and passed through set point only briefly
    #in this case we'll merge into larger bad durations
    #minimum number of good points in a row to say oscillation has stopped
    min_good_points = parameters['min_good_points']

    hk_baddurations_flow_merged = []

    if hk_baddurations_flow:
        merged_duration_start = hk_baddurations_flow[0][0]
        merging = False

        for i, vals in enumerate(hk_baddurations_flow):
            if i+1 == len(hk_baddurations_flow): #deals with case of last row
                hk_baddurations_flow_merged.append([merged_duration_start, hk_baddurations_flow[i][1]]) 
            else:
                if hk_baddurations_flow[i+1][0]-hk_baddurations_flow[i][1] > min_good_points:
                    hk_baddurations_flow_merged.append([merged_duration_start, hk_baddurations_flow[i][1]])
                    merged_duration_start = hk_baddurations_flow[i+1][0]
                    merging = False
                if hk_baddurations_flow[i+1][0]-hk_baddurations_flow[i][1] < min_good_points:
                    if merging == False:
                        merged_duration_start =  hk_baddurations_flow[i][0]
                        merging = True
                    
                   
    #create single list of bad durations and sort by start time
    hk_all_baddurations = hk_baddurations_yag + hk_baddurations_flow_merged
    hk_all_baddurations.sort()

    #write final sorted list of bad durations to file for reading and pickle for later access
    file = open('hk_bad_durations_' + parameters['folder'] + '.txt', 'w')
    for row in hk_all_baddurations:
        line = ' '.join(str(x) for x in row)
        file.write(line + '\n')
    file.close()

    file2 = open('hk_bad_durations_pickle' + date.strftime('%Y%m%d') + '.hkpckl', 'w')
    pickle.dump(hk_all_baddurations, file2)
    file2.close()  
                
    #need to find average good flow to calc concentrations, so run through hk_alldata and get average of flows not occuring in bad durations

    flows_to_avg = []
    i = 0

    while i < len(hk_alldata):
        event_time = hk_alldata[i,0]+LVts_to_UNIXts+timezone
        number_bad_durations = len(hk_baddurations_flow_merged)
        if number_bad_durations:
            duration_end_time = hk_baddurations_flow_merged[0][1]
            duration_start_time = hk_baddurations_flow_merged[0][0]
            
        if number_bad_durations and event_time >= duration_end_time:
            hk_baddurations_flow_merged.pop(0)
            continue
        if not number_bad_durations or event_time < duration_start_time:
            flows_to_avg.append(hk_alldata[i,1])
        i+=1
            
    current_avg_flow = sum(flows_to_avg)/len(flows_to_avg)

    #write average good flow to file 
    file = open('average_sample_flow_' + parameters['folder'] + '.txt', 'w')
    file.write(str(current_avg_flow))
    file.close()


    return current_avg_flow
    print current_avg_flow


            
        


