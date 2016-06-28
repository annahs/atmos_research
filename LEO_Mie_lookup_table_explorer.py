import os 
import sys
import pickle
from pprint import pprint

core_dia_to_view = 160.5
coat_thickness_to_view = 0.0

lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/lookup_tables/coating_lookup_table_WHI_2012_UBCSP2-neg_coat.lupckl'
lookup_file = 'C:/Users/Sarah Hanna/Documents/Data/WHI long term record/coatings/lookup_tables/coating_lookup_table_WHI_2012_UBCSP2-nc(2p26,1p26).lupckl'
lookup_file =  'C:/Users/Sarah Hanna/Documents/Data/Netcare/Spring 2015/lookup tables/coating_lookup_table_POLAR6_2015_UBCSP2-nc(2p26,1p26)-fullPSLcalib_used_factor545.lupckl'



lookup = open(lookup_file, 'r')
lookup_table = pickle.load(lookup)
lookup.close()
        
#pprint(lookup_table.keys())

#pprint(sorted(lookup_table[core_dia_to_view].values())) #coting thicknesses
core_values_to_view = lookup_table[core_dia_to_view]
pprint(sorted(core_values_to_view.keys()))  #scattering signals


#for key in sorted(core_values_to_view.keys()):
#	if 500 <= key <= 600:
#		print key, core_values_to_view[key]

for signal, coating_thickness in core_values_to_view.items():
    if coating_thickness == coat_thickness_to_view:
        print signal, coating_thickness
        

