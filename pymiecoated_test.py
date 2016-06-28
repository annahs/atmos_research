from pymiecoated import Mie
import math
import sys
import numpy as np

mie = Mie()

wl = 1064

core_rad = 300/2 #nm
shell_thickness = 10


size_par = 2*math.pi*core_rad*1/wl
#print size_par

#Refractive indices PSL 1.59-0.0i  rBC 2.26- 1.26i  shell 1.5-0.0i h20 1.3260-0
core_RI = complex(1.59, 0.0) #
shell_rad = core_rad + shell_thickness
shell_RI = complex(1.326,0.0)

mie.x = 2*math.pi*core_rad/wl
mie.m = core_RI
mie.y = 2*math.pi*shell_rad/wl
mie.m2 = shell_RI

abs = mie.qabs()
abs_xs_nm2 = abs*math.pi*shell_rad**2 	#in nm^2
abs_xs  = abs_xs_nm2*1e-14 #in cm^2

sca = mie.qsca()
sca_xs_nm2 = sca*math.pi*shell_rad**2 #in nm^2
sca_xs = sca_xs_nm2*1e-14 #in cm^2

ext_xs = sca_xs+abs_xs

SSA = sca_xs/ext_xs
print ext_xs



#set ranges for integration of scattering (ie detector angles)
incr = 0.1
range1 = []
i=2.5
while i <=77.5:
	range1.append(i)
	i+=incr
	
range2 = []
i=102.5
while i <= 167.5:
	range2.append(i)
	i+=incr	
	
#calc intensity
Itot = 0
Itot_fwd = 0
Itot_back=0
for theta in range1:
	cos_angle=math.cos(math.radians(theta))
	S12 = mie.S12(cos_angle)
	I1 = S12[0].real**2 + S12[0].imag**2
	I2 = S12[1].real**2 + S12[1].imag**2
	Itot = (Itot+ I1 + I2)*incr
	
for theta in range2:
	cos_angle=math.cos(math.radians(theta))
	S12 = mie.S12(cos_angle)
	I1 = S12[0].real**2 + S12[0].imag**2
	I2 = S12[1].real**2 + S12[1].imag**2
	Itot = (Itot+ I1 + I2)*incr


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
	
#plt.figure()
#plt.semilogy(np.linspace(0, np.pi, 100), abs(matr[:,0,0])**2)
#plt.semilogy(np.linspace(0, np.pi, 100), abs(matr[:,1,1])**2)
#plt.show()
print (np.mean([Itot_fwd*incr,Itot_back*incr])*math.pi/2)

