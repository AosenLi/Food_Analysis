a = {'melbourne':{'apple':8,'Banana':4},'Sydney':{'apple':11,'Banana':0},'Brisbane':{'apple':10,'Banana':3}}

print (a.items())

print (a['melbourne'].values())
for item in (sum(a[location].values()) for location in a.keys()):
    print (item)

a,b,c,d,e = 1,1,1,1,1
print (a + b +c)
a = 3
a /= 2
print (a)