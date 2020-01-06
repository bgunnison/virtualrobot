
import math
echoes = 16
delay_start_ticks = 50
s = 0.2
e = 4
a = (e - s)/float(echoes)
delays = []
delayms = []
fs = []
for i in range(echoes):
    v = 0.2 + ((i+1) * a)
    print('v %.03f' % v)
    f = (1.61 + math.log(v))/2.996
    print('f %.03f' % f)
    delay = round(delay_start_ticks * f)
    delays.append(delay)
    
    delayms.append(delay) 

delaysff = []
delayms.reverse()
s = 0
for i, v in enumerate(delayms):
    s += v
    delaysff.append(round(s/4))


print(delays)
print(delaysff)
print('stop')
    