
x = 50000
y1 = 0.18821 + 1.36864E-4*x 
corr = y1/0.7

print y1, corr, corr/y1


y = 0.18821 + (1.36864E-4/0.7)*x 


print y, y/y1