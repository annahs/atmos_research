import matplotlib.pyplot as plt
import numpy as np
from holopy.core import Schema, Angles, Optics, marray 
from holopy.scattering.scatterer import Sphere
from holopy.scattering.theory import Mie
import sys
from pymiecoated import Mie as pyMie
import math

rad = 0.1605/2
nparticle = complex(2.26,1.26)# complex(1.59, 0.0)
wl = 1.064
fwd_angles = [12.5,77.5]
bck_angles = [102.5,167.5]
full_cone_angle = 65


schema_std = Schema(positions = Angles(np.linspace(math.radians(0), math.radians(180), 180)), optics =
                Optics(wavelen=wl, index = 1.0, polarization = (1,0)))

schema1 = Schema(positions = Angles(np.linspace(math.radians(fwd_angles[0]), math.radians(fwd_angles[1]), full_cone_angle)), optics =
                Optics(wavelen=wl, index = 1.0, polarization = (1,0)))

schema2 = Schema(positions = Angles(np.linspace(math.radians(bck_angles[0]), math.radians(bck_angles[1]), full_cone_angle)), optics =
                Optics(wavelen=wl, index = 1.0, polarization = (1,0)))
				
optics = Optics(wavelen=wl, index = 1.0, polarization = (0, 1))


sphere = Sphere(r = rad, n = nparticle)


matr_std = Mie.calc_scat_matrix(sphere, schema_std)
matr1 = Mie.calc_scat_matrix(sphere, schema1)
matr2 = Mie.calc_scat_matrix(sphere, schema2)
#print matr

xs = Mie.calc_cross_sections(sphere, optics)

#print xs[0]


a_std = sum(abs(matr_std[:,0,0])**2)
b_std = sum(abs(matr_std[:,1,1])**2)

#print a_std, b_std, np.mean([a_std,b_std])

a1 = sum(abs(matr1[:,0,0])**2)
b1 = sum(abs(matr1[:,1,1])**2)

a2 = sum(abs(matr2[:,0,0])**2)
b2 = sum(abs(matr2[:,1,1])**2)

unpol_fwd = (a1+b1)
unpol_bac = (a2+b2)


overall = np.mean([unpol_fwd,unpol_bac])*math.pi/2
print overall*584


#xs = Mie.calc_cross_sections(sphere, optics)

#print xs[0]


# It is typical to look at scattering matrices on a semilog plot.
# You can make one as follows:
#plt.figure()
#plt.semilogy(np.linspace(0, 180, 180), abs(matr_std[:,0,0])**2)
#plt.semilogy(np.linspace(0, 180, 180), abs(matr_std[:,1,1])**2)
#plt.show()
#

##########pymiecoated
mie = pyMie()



core_rad = rad
shell_thickness = 0.0


size_par = 2*math.pi*core_rad*1/wl
#print size_par

#Refractive indices PSL 1.59-0.0i  rBC 2.26- 1.26i  shell 1.5-0.0i


core_RI = nparticle #complex(1.95,0.79)#
shell_rad = core_rad + shell_thickness
shell_RI = complex(1.5,0.0)

mie.x = 2*math.pi*core_rad/wl
mie.m = core_RI
mie.y = 2*math.pi*shell_rad/wl
mie.m2 = shell_RI

#
abs = mie.qabs()
abss = abs*3.14*shell_rad**2
#print abss



sca = mie.qsca()
sca_xs = sca*math.pi*shell_rad**2
#print sca_xs#*10**-8


#set ranges
incr = 0.1
range1 = []
i=fwd_angles[0]
while i <= fwd_angles[1]:
	range1.append(i)
	i+=incr
	
range2 = []
i=bck_angles[0]
while i <= bck_angles[1]:
	range2.append(i)
	i+=incr	
	
#calc intensity
Itot_fwd = 0
Itot_back = 0
for theta in range1:
	cos_angle=math.cos(math.radians(theta))
	S12 = mie.S12(cos_angle)
	I1 = S12[0].real**2 + S12[0].imag**2
	I2 = S12[1].real**2 + S12[1].imag**2
	Itot_fwd = (Itot_fwd + I1 + I2)
	
for theta in range2:
	cos_angle=math.cos(math.radians(theta))
	S12 = mie.S12(cos_angle)
	I1 = S12[0].real**2 + S12[0].imag**2
	I2 = S12[1].real**2 + S12[1].imag**2
	Itot_back = (Itot_back + I1 + I2)

Itot = np.mean([Itot_fwd*incr,Itot_back*incr])*math.pi/2
	
print 'py', Itot*574
