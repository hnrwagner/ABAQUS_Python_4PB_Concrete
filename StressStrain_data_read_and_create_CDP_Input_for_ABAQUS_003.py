# -*- coding: utf-8 -*-
"""
Created on Sat Aug 13 10:52:06 2022

@author: Ronald Wagner
"""

import numpy as np
import matplotlib.pyplot as plt


#---------------------------------------------------------------------------------------------------------------------------------

# functions

#---------------------------------------------------------------------------------------------------------------------------------

def Open_txt_to_List(txt_name):
    CDP_Load_Stress_Strain_txt = np.loadtxt(txt_name)[:]
    CDP_Load_Strain_list = []
    CDP_Load_Strain_list = CDP_Load_Stress_Strain_txt[:,0]
    
    CDP_Load_Stress_list = []
    CDP_Load_Stress_list = CDP_Load_Stress_Strain_txt[:,1]
    
    return CDP_Load_Strain_list,CDP_Load_Stress_list

#---------------------------------------------------------------------------------------------------------------------------------

def Create_XY_Plot(X,Y,name,X_name,Y_name,X_max,Y_max):
    fig, ax = plt.subplots()
    ax.plot(X,Y, "r--",label = name)
    legend = ax.legend(loc="lower right", shadow=True)
    plt.ylabel(Y_name)
    plt.xlabel(X_name)
    plt.grid(True)
    plt.axis([0.0 , X_max, 0.0 , Y_max])

#---------------------------------------------------------------------------------------------------------------------------------

def index_of_max_in_list(list_data, max_value):
    for i in list_data:
        if i >max_value: break
    return list_data.index(i)

#---------------------------------------------------------------------------------------------------------------------------------

def Stress_Strain_to_ABAQUS_CDP(index_list,Load_Strain_list,Load_Stress_list,E_Load,Y_Load):
    CDP_Load_Strain_list = []
    
    for ic in range(0,index_list,1):
        CDP_Load_Strain_list = Load_Strain_list-Load_Stress_list/E_Load
            
        
    CDP_Load_Strain_list = CDP_Load_Strain_list.tolist()
    Load_Stress_list = Load_Stress_list.tolist()
    
    CDP_DamageParameter = []
    for Stress in Load_Stress_list:
        CDP_DamageParameter.append(1.0-(Stress/Y_Load))
       

    MinIndex_2 = index_of_max_in_list(Load_Stress_list,Y_Load)
    
    
    del CDP_DamageParameter[0:MinIndex_2]
    del CDP_Load_Strain_list[0:MinIndex_2]
    del Load_Stress_list[0:MinIndex_2]
    
    MinIndex= CDP_DamageParameter.index(min([i for i in CDP_DamageParameter if i > 0]))
    
    CDP_DamageParameter = np.array(CDP_DamageParameter)
    CDP_DamageParameter[0:MinIndex] = 0
    CDP_DamageParameter = CDP_DamageParameter.tolist()
    CDP_Load_Strain_list[0] = 0
    return CDP_DamageParameter, CDP_Load_Strain_list, Load_Stress_list 
    
#---------------------------------------------------------------------------------------------------------------------------------   

myE_Compression = 34007.32018
myY_Compression = 42
myE_Tension = 37000
myY_Tension = 2.0


myCDP_Compression_Strain_list, myCDP_Compression_Stress_list = Open_txt_to_List("Stress_Strain_Compression_2.txt")
myCDP_Tension_Strain_list, myCDP_Tension_Stress_list = Open_txt_to_List("Stress_Strain_Tension_2.txt")

Create_XY_Plot(myCDP_Compression_Strain_list, myCDP_Compression_Stress_list,"Stress-Strain-Compression","Strain [-]","Stress [MPa]",max(myCDP_Compression_Strain_list),max(myCDP_Compression_Stress_list))
Create_XY_Plot(myCDP_Tension_Strain_list, myCDP_Tension_Stress_list,"Stress-Strain-Tension","Strain [-]","Stress [MPa]",max(myCDP_Tension_Strain_list),max(myCDP_Tension_Stress_list))

myIndex = len(myCDP_Compression_Stress_list)
myIndex2 = len(myCDP_Tension_Stress_list)


myDamageParameter_Compression, myInelastic_Compression_Strain, myCDP_Compression_Stress_list = Stress_Strain_to_ABAQUS_CDP(myIndex,myCDP_Compression_Strain_list,myCDP_Compression_Stress_list,myE_Compression,myY_Compression)
myDamageParameter_Tension, myCracking_Tension_Strain, myCDP_Tension_Stress_list = Stress_Strain_to_ABAQUS_CDP(myIndex2,myCDP_Tension_Strain_list,myCDP_Tension_Stress_list,myE_Tension,myY_Tension)



Create_XY_Plot(myInelastic_Compression_Strain,myCDP_Compression_Stress_list,"concrete","Inelastic Strain","Stress",max(myInelastic_Compression_Strain),max(myCDP_Compression_Stress_list))
Create_XY_Plot(myInelastic_Compression_Strain,myDamageParameter_Compression,"concrete","Inelastic Strain","Damage Parameter",max(myInelastic_Compression_Strain),1.0)

Create_XY_Plot(myCracking_Tension_Strain,myCDP_Tension_Stress_list,"concrete","Cracking Strain","Stress",max(myCracking_Tension_Strain),max(myCDP_Tension_Stress_list))
Create_XY_Plot(myCracking_Tension_Strain,myDamageParameter_Tension,"concrete","Cracking Strain","Damage Parameter",max(myCracking_Tension_Strain),1.0)

np.savetxt("Damage.txt",myDamageParameter_Compression,fmt='%1.4e')
np.savetxt("Strain.txt",myInelastic_Compression_Strain,fmt='%1.4e')
