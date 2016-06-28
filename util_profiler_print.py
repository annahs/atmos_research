#call thios:  python -m cProfile [-o output_file] [-s sort_order] myscript.py

import pstats
import os 

current_dir = 'C:/test/'
os.chdir(current_dir)

p = pstats.Stats('AL_mass')
p.strip_dirs()
#p.print_callers()
p.sort_stats('cumulative').print_stats(20)
#p.sort_stats('cum').print_stats(.5, 'init')
p.print_callers(20)