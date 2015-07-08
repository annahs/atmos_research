import matplotlib.pyplot as plt
import numpy as np
from holopy.core import Schema, Angles, Optics, marray 
from holopy.scattering.scatterer import Sphere
from holopy.scattering.theory import Mie
import sys



schema = Schema(positions = Angles(np.linspace(0, np.pi, 100)), optics =
                Optics(wavelen=1.064, index = 1.0, polarization = (1, 0)))
				
optics = Optics(wavelen=1.064, index = 1.0, polarization = (0, 1))


sphere = Sphere(r = 0.05, n = complex(1.95, 0.79))


matr = Mie.calc_scat_matrix(sphere, schema,)


a = sum(abs(matr[:,0,0])**2)
b = sum(abs(matr[:,1,1])**2)

print a, b, a+b

xs = Mie.calc_cross_sections(sphere, optics)

print xs

sys.exit()
#print intensity


# It is typical to look at scattering matrices on a semilog plot.
# You can make one as follows:
plt.figure()
plt.semilogy(np.linspace(0, np.pi, 100), abs(matr[:,0,0])**2)
plt.semilogy(np.linspace(0, np.pi, 100), abs(matr[:,1,1])**2)
plt.show()