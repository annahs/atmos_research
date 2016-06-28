import sys
import os
from datetime import datetime
from pprint import pprint
from datetime import timedelta

#Coordinates: 82.5163N, 62.3085W
#Height 10m above ground level
#Use middle time of the sampling period as the start time for back trajectory. Times in EDT

timezone_corr = 4  #UTC = EDT + 4

date_time_list = [
[1 ,datetime.strptime('03/11/2016 13:10:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/12/2016 13:10:00', '%m/%d/%Y %H:%M:%S')],
[2 ,datetime.strptime('03/12/2016 16:25:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/13/2016 13:30:00', '%m/%d/%Y %H:%M:%S')],
[3 ,datetime.strptime('03/13/2016 14:28:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/14/2016 14:25:00', '%m/%d/%Y %H:%M:%S')],
[4 ,datetime.strptime('03/14/2016 15:00:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/15/2016 15:00:00', '%m/%d/%Y %H:%M:%S')],
[5 ,datetime.strptime('03/15/2016 15:50:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/16/2016 14:30:00', '%m/%d/%Y %H:%M:%S')],
[6 ,datetime.strptime('03/16/2016 15:05:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/17/2016 14:10:00', '%m/%d/%Y %H:%M:%S')],
[7 ,datetime.strptime('03/17/2016 14:40:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/18/2016 14:10:00', '%m/%d/%Y %H:%M:%S')],
[8 ,datetime.strptime('03/18/2016 14:30:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/19/2016 13:58:00', '%m/%d/%Y %H:%M:%S')],
[9 ,datetime.strptime('03/19/2016 14:25:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/20/2016 13:53:00', '%m/%d/%Y %H:%M:%S')],
[10,datetime.strptime('03/20/2016 14:18:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/21/2016 11:03:00', '%m/%d/%Y %H:%M:%S')],
[11,datetime.strptime('03/21/2016 11:28:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/22/2016 10:27:00', '%m/%d/%Y %H:%M:%S')],
[12,datetime.strptime('03/22/2016 11:15:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/23/2016 11:05:00', '%m/%d/%Y %H:%M:%S')],
[13,datetime.strptime('03/23/2016 11:31:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/24/2016 10:34:00', '%m/%d/%Y %H:%M:%S')],
[14,datetime.strptime('03/24/2016 11:02:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/25/2016 09:40:00', '%m/%d/%Y %H:%M:%S')],
[15,datetime.strptime('03/25/2016 10:14:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/26/2016 10:15:00', '%m/%d/%Y %H:%M:%S')],
[16,datetime.strptime('03/26/2016 12:19:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/27/2016 12:23:00', '%m/%d/%Y %H:%M:%S')],
[17,datetime.strptime('03/27/2016 12:51:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/28/2016 10:37:00', '%m/%d/%Y %H:%M:%S')],
[18,datetime.strptime('03/28/2016 11:17:00', '%m/%d/%Y %H:%M:%S')	,datetime.strptime('03/29/2016 10:50:00', '%m/%d/%Y %H:%M:%S')],
]

for item in date_time_list:
	sample_number = item[0]
	start = item[1]
	end = item[2]
	
	print sample_number
	print start + (end-start)/2 + timedelta(hours = timezone_corr)