import os
import sys

#current_dir = 'D:/2013_a/WHI_UBCSP2/Binary'#

for root, dirs, files in os.walk(current_dir, topdown=False):
    for name in files:
		if name.endswith('.sp2b'):
			print name
			os.remove(os.path.join(root, name))
    
        