import random
def genotp():
    otp=''
    u_c=[chr(i) for i in range(ord('A'),ord('Z')+1)]
    l_c=[chr(i) for i in range(ord('a'),ord('z')+1)]
    for i in range(2):
        otp=otp+random.choice(u_c)+str(random.randint(0,9))+random.choice(l_c)
    return otp