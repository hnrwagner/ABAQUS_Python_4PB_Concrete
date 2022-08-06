# -*- coding: utf-8 -*-
"""
Created on Sat Aug  6 12:41:49 2022

@author: Ronald Wagner
"""

from abaqus import *
from abaqusConstants import *
import regionToolset
import __main__
import section
import regionToolset
import part
import material
import assembly
import step
import interaction
import load
import mesh
import job
import sketch
import visualization
import xyPlot
import connectorBehavior
import odbAccess
from operator import add


import numpy as np
import matplotlib.pyplot as plt

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

# functions

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def Create_3D_Beam(model,part,length,height,thickness):
    s = mdb.models[model].ConstrainedSketch(name='__profile__', sheetSize=200.0)
    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=STANDALONE)
    s.rectangle(point1=(-length/2.0, height/2.0), point2=(length/2.0, -height/2.0))
    p = mdb.models[model].Part(name=part, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p = mdb.models[model].parts[part]
    p.BaseSolidExtrude(sketch=s, depth=thickness)
    s.unsetPrimaryObject()
    del mdb.models[model].sketches['__profile__']

#------------------------------------------------------------------------------    

def Create_Datum_Plane_by_Principal(type_plane,part,model,offset_plane):  
    p = mdb.models[model].parts[part]
    myPlane = p.DatumPlaneByPrincipalPlane(principalPlane=type_plane, offset=offset_plane)
    myID = myPlane.id
    return myID    

#------------------------------------------------------------------------------

def Create_Partion_by_Plane(model,part,id_plane):
    p = mdb.models[model].parts[part]
    c = p.cells[:]
    d = p.datums
    p.PartitionCellByDatumPlane(datumPlane=d[id_plane], cells=c)
    
#------------------------------------------------------------------------------

def Create_Set_All_Cells(model,part,set_name):
    p = mdb.models[model].parts[part]
    c = p.cells[:]
    p.Set(cells=c, name=set_name) 

#------------------------------------------------------------------------------

def Create_Set_Face(x,y,z,model,part,set_name):
    face = ()
    p = mdb.models[model].parts[part]
    f = p.faces
    myFace = f.findAt((x,y,z),)
    face = face + (f[myFace.index:myFace.index+1],)
    p.Set(faces=face, name=set_name)
    return myFace

#------------------------------------------------------------------------------

def Create_Assembly(model,part,instance,x,y,z):
    a = mdb.models[model].rootAssembly
    p = mdb.models[model].parts[part]
    a.Instance(name=instance, part=p, dependent=ON)
    p = a.instances[instance]
    p.translate(vector=(x,y,z))
    
#------------------------------------------------------------------------------

def Create_Reference_Point(x,y,z,model,setname):
    a = mdb.models[model].rootAssembly
    myRP = a.ReferencePoint(point=(x, y, z))
    r = a.referencePoints
    myRP_Position = r.findAt((x, y, z),)    
    refPoints1=(myRP_Position, )
    a.Set(referencePoints=refPoints1, name=setname)
    return myRP,myRP_Position

#------------------------------------------------------------------------------

def Create_Interaction_Coupling(model,instance,rp_name,rp_face_name,constraint_name):
    a = mdb.models[model].rootAssembly
    region1=a.sets[rp_name]
    region2=a.instances[instance].sets[rp_face_name]
    mdb.models[model].Coupling(name=constraint_name, controlPoint=region1, surface=region2, influenceRadius=WHOLE_SURFACE, couplingType=STRUCTURAL, localCsys=None, u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=ON)

#------------------------------------------------------------------------------

def Create_Analysis_Step(model,step_name,pre_step_name,Initial_inc,Max_inc,Min_inc,Inc_Number,NL_ON_OFF):
    a = mdb.models[model].StaticStep(name=step_name, previous=pre_step_name, initialInc=Initial_inc, maxInc=Max_inc, minInc=Min_inc, nlgeom=ON)
    a = mdb.models[model].steps[step_name].setValues(maxNumInc=Inc_Number)
    
#------------------------------------------------------------------------------

def Create_Gravity_Load(model,load_name,step_name,load):
    mdb.models[model].Gravity(name=load_name, createStepName=step_name, comp2=-load, distributionType=UNIFORM, field='')

#------------------------------------------------------------------------------

def Create_BC(model,set_name,BC_name,step_name,u,v,w,ur,vr,wr):
    a = mdb.models[model].rootAssembly
    region = a.sets[set_name]
    mdb.models[model].DisplacementBC(name=BC_name, createStepName=step_name, region=region, u1=u, u2=v, u3=w, ur1=ur, ur2=vr, ur3=wr, amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)

#------------------------------------------------------------------------------

def Create_BC_2(model,instance_name,set_name,BC_name,step_name,u,v,w,ur,vr,wr):
    a = mdb.models[model].rootAssembly
    region = a.instances[instance_name].sets[set_name]
    mdb.models[model].DisplacementBC(name=BC_name, createStepName=step_name, region=region, u1=u, u2=v, u3=w, ur1=ur, ur2=vr, ur3=wr, amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)

#------------------------------------------------------------------------------

def Create_Mesh(model,part,mesh_size):
    p = mdb.models[model].parts[part]
    p.seedPart(size=mesh_size, deviationFactor=0.1, minSizeFactor=0.1)
    p.generateMesh()

#------------------------------------------------------------------------------

def Create_Material_and_Assign(model,part,material_name,E,Nu,Rho,section_name,set_name):
    p = mdb.models[model].parts[part]
    mdb.models[model].Material(name=material_name)
    mdb.models[model].materials[material_name].Elastic(table=((E, Nu), ))
    mdb.models[model].materials[material_name].Density(table=((Rho, ), ))
    mdb.models[model].HomogeneousSolidSection(name=section_name, material=material_name, thickness=None)
    p = mdb.models[model].parts[part]
    region = p.sets[set_name]
    p = mdb.models[model].parts[part]
    p.SectionAssignment(region=region, sectionName=section_name, offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
    
#------------------------------------------------------------------------------

def Create_Job(model,job_name, cpu):
    a = mdb.models[model].rootAssembly
    mdb.Job(name=job_name, model=model, description='', type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', scratch='', resultsFormat=ODB, numThreadsPerMpiProcess=1, multiprocessingMode=DEFAULT, numCpus=cpu, numDomains=cpu, numGPUs=0)

#------------------------------------------------------------------------------

def SubmitJob(job_name):
    mdb.jobs[job_name].submit(consistencyChecking=OFF)

#------------------------------------------------------------------------------    

def Open_ODB_and_Write_NodeSet_data_to_text(model,step_name,variable_name,set_name,Variable_component):
    # open ODB file - ABAQUS Result file
    odb = session.openOdb(str(model)+'.odb')
    
    # list for the VARIABLE you want to evaluate
    Variable_v = []
    
    # analysis step for your VARIABLE
    lastStep=odb.steps[step_name]
    
    #loop over all increments of the analysis step and save VARIABLE information from each increment
    for x in range(len(lastStep.frames)):
        lastFrame = lastStep.frames[x]
        Variable = lastFrame.fieldOutputs[variable_name]
        center = odb.rootAssembly.nodeSets[set_name]
        centerRForce = Variable.getSubset(region=center)
       
        # loop over the VARIABLE and save component (x,y,z - 0,1,2) to list
        for i in centerRForce.values:
            Variable_vr = [i.data[Variable_component]]
            Variable_v = Variable_v + Variable_vr  
            
    # write VARIABLE - component to text file
    
    np.savetxt(str(set_name)+'_'+str(variable_name)+'_'+str(myString)+'.txt',Variable_v)
    return Variable_v

#------------------------------------------------------------------------------  

def Create_Sum_ABS_List(data_1,data_2):
    data = [(x + y)/20000.0 for (x, y) in zip(data_1, data_2)] 
    data =  [abs(ele) for ele in data]
    max_data = max(data)
    return max_data,data

#------------------------------------------------------------------------------  

def Create_Plot(data_1,data_2,max_data_1,max_data_2):
    fig, ax = plt.subplots()
    ax.plot(data_1, data_2, 'g--', label='Concrete')
    legend = ax.legend(loc='lower right', shadow=True)
    plt.ylabel('Force [N]')
    plt.xlabel('Displacement [mm]')
    plt.grid(True)
    plt.axis([0.0, max_data_1, 0.0, max_data_2])
    plt.savefig('Load_Displacement_Curve_Concrete_4PB.png')

#------------------------------------------------------------------------------

# variables

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------    

myPart = "Frame"
myString = "Concrete_Frame_4PB"
mdb.Model(name=myString)
myMaterialName = "Concrete"
myJobName= "4PB_Concrete_Beam"


myLength = 2100.0
myHeight = 330.0
myThickness = 150.0

myLoad = 40.0


myBCLength = 0.02*myLength
myBCDistance = 0.35*myLength
myBCDistance_2 = 0.92*myLength
myBCDistance_3 = 0.96*myLength

myE = 42000
myNu = 0.2
myRho = 2.5E-09

# Create 3D Beam

Create_3D_Beam(myString, myPart, myLength, myHeight, myThickness)

# Create Planes for Partitions

myID_0 = Create_Datum_Plane_by_Principal(YZPLANE,myPart,myString,myBCDistance/2.0+myBCLength/2.0)
myID_1 = Create_Datum_Plane_by_Principal(YZPLANE,myPart,myString,myBCDistance/2.0-myBCLength/2.0)

myID_2 = Create_Datum_Plane_by_Principal(YZPLANE,myPart,myString,-myBCDistance/2.0+myBCLength/2.0)
myID_3 = Create_Datum_Plane_by_Principal(YZPLANE,myPart,myString,-myBCDistance/2.0-myBCLength/2.0)

myID_4 = Create_Datum_Plane_by_Principal(YZPLANE,myPart,myString,myBCDistance_2/2.0+myBCLength/2.0)
myID_5 = Create_Datum_Plane_by_Principal(YZPLANE,myPart,myString,myBCDistance_2/2.0-myBCLength/2.0)

myID_6 = Create_Datum_Plane_by_Principal(YZPLANE,myPart,myString,-myBCDistance_2/2.0+myBCLength/2.0)
myID_7 = Create_Datum_Plane_by_Principal(YZPLANE,myPart,myString,-myBCDistance_2/2.0-myBCLength/2.0)

myID_8 = Create_Datum_Plane_by_Principal(YZPLANE,myPart,myString,myBCDistance_3/2.0+myBCLength/2.0)
myID_9 = Create_Datum_Plane_by_Principal(YZPLANE,myPart,myString,-myBCDistance_3/2.0-myBCLength/2.0)

# Create Partitions

Create_Partion_by_Plane(myString,myPart,myID_0)
Create_Partion_by_Plane(myString,myPart,myID_1)
Create_Partion_by_Plane(myString,myPart,myID_2)
Create_Partion_by_Plane(myString,myPart,myID_3)
Create_Partion_by_Plane(myString,myPart,myID_4)
Create_Partion_by_Plane(myString,myPart,myID_5)
Create_Partion_by_Plane(myString,myPart,myID_6)
Create_Partion_by_Plane(myString,myPart,myID_7)
Create_Partion_by_Plane(myString,myPart,myID_8)
Create_Partion_by_Plane(myString,myPart,myID_9)

# Create Set - Cell for whole model

Create_Set_All_Cells(myString,myPart,"Beam_3D")

# Create Set - Face RP-1 & RP-2

Create_Set_Face(-myBCDistance/2.0,myHeight/2.0,myThickness/2.0,myString,myPart,"Face_RP_1")
Create_Set_Face(myBCDistance/2.0,myHeight/2.0,myThickness/2.0,myString,myPart,"Face_RP_2")


# Creaete Set - Face RP-3 & RP-4

Create_Set_Face(-myBCDistance_2/2.0,-myHeight/2.0,myThickness/2.0,myString,myPart,'Face_RP_3')
Create_Set_Face(myBCDistance_2/2.0,-myHeight/2.0,myThickness/2.0,myString,myPart,'Face_RP_4')

# Create Assembly

Create_Assembly(myString,myPart,"Beam-1",0,0,0)

# Creaete Set - RP RP-1 & RP-2

myRP1,myRP_Position1 = Create_Reference_Point(-myBCDistance/2.0,myHeight/2.0,myThickness/2.0,myString,'RP-1')
myRP2,myRP_Position2 = Create_Reference_Point(myBCDistance/2.0,myHeight/2.0,myThickness/2.0,myString,'RP-2')

# Create Coupling Interaction between RP-1 & RP-2 and Corresponding Faces

for ic in range(1,3,1):
    Create_Interaction_Coupling(myString,"Beam-1","RP-"+str(ic),"Face_RP_"+str(ic),"RP-"+str(ic)+"_to_Face")
    
# Create Analysis Step

Create_Analysis_Step(myString,"Gravity","Initial",0.1,0.1,1E-05,100,ON)    
Create_Analysis_Step(myString,"Loading","Gravity",0.01,0.01,1E-05,300,ON)  

# Create Gravity Load

Create_Gravity_Load(myString,"Gravity","Gravity",9810)

# Create Boundary Conditions

Create_BC_2(myString,"Beam-1",'Face_RP_3',"Support_1","Initial",SET,SET,UNSET,UNSET,SET,SET)
Create_BC_2(myString,"Beam-1",'Face_RP_4',"Support_2","Initial",SET,SET,SET,UNSET,SET,SET)

# Create Loading

Create_BC(myString,'RP-1',"Loading-1","Loading",UNSET,-myLoad,UNSET,UNSET,UNSET,UNSET)
Create_BC(myString,'RP-2',"Loading-2","Loading",UNSET,-myLoad,UNSET,UNSET,UNSET,UNSET)

# Create Mesh

Create_Mesh(myString,myPart,10.0)

# Create Material Definition

Create_Material_and_Assign(myString,myPart,myMaterialName,myE,myNu,myRho,"Concrete_Beam_3D_Sectio","Beam_3D")

# Create Job

Create_Job(myString, myJobName, 4)

# Submit Job

#SubmitJob(myJobName)

# Create Txt File with Load-Displacement Data

RF_data_1 = Open_ODB_and_Write_NodeSet_data_to_text(myJobName,'Loading','RF','RP-1',1)
U_data_1 = Open_ODB_and_Write_NodeSet_data_to_text(myJobName,'Loading','U','RP-1',1)
RF_data_2 = Open_ODB_and_Write_NodeSet_data_to_text(myJobName,'Loading','RF','RP-2',1)
U_data_2 = Open_ODB_and_Write_NodeSet_data_to_text(myJobName,'Loading','U','RP-2',1)

# Create Figure of Load-Displacement Data

Len_RF, RF_data = Create_Sum_ABS_List(RF_data_1,RF_data_2)
Len_U, U_data = Create_Sum_ABS_List(U_data_1,U_data_2)

Create_Plot(U_data,RF_data,Len_U,Len_RF)
