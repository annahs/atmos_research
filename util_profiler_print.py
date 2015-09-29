import pstats
import os 

current_dir = 'C:/test/'
os.chdir(current_dir)

p = pstats.Stats('LEO_profile')
p.strip_dirs()
p.sort_stats('cumulative').print_stats(20)