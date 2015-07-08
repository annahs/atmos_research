from pymiecoated import Mie
import math
import sys

mie = Mie()

wl = 1.064

core_rad = 0.2/2 #nm
shell_thickness = 0.0


size_par = 2*math.pi*core_rad*1/wl
print size_par

#Refractive indices PSL 1.59-0.0i  rBC 2.26- 1.26i  shell 1.5-0.0i


core_RI = complex(1.59, 0.0) #complex(1.95,0.79)#
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
print sca_xs*10**-8


#set ranges
incr = 1
range1 = []
i=0
while i <= 90:
	range1.append(i)
	i+=incr
	
range2 = []
i=90
while i <= 180:
	range2.append(i)
	i+=incr	
	
#calc intensity
Itot = 0
for theta in range1:
	cos_angle=math.cos(math.radians(theta))
	S12 = mie.S12(cos_angle)
	print S12[0].real
	sys.exit()
	I1 = S12[0].real**2 + S12[0].imag**2
	I2 = S12[1].real**2 + S12[1].imag**2
	Itot = Itot+ I1 + I2
	
for theta in range2:
	cos_angle=math.cos(math.radians(theta))
	S12 = mie.S12(cos_angle)
	I1 = S12[0].real**2 + S12[0].imag**2
	I2 = S12[1].real**2 + S12[1].imag**2
	Itot = Itot+ I1 + I2

plt.figure()
plt.semilogy(np.linspace(0, np.pi, 100), abs(matr[:,0,0])**2)
plt.semilogy(np.linspace(0, np.pi, 100), abs(matr[:,1,1])**2)
plt.show()
	
	
print Itot/2#*331.2