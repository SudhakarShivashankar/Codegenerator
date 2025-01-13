#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  3 23:06:28 2021

@author: sven
"""
# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'qt4'
import os
# os.environ['ETS_TOOLKIT'] = 'qt4' 

import math
import numpy as np
from numpy.linalg import norm 
import tkinter as tk
from scipy.interpolate import interp1d
from scipy import interpolate
from scipy.interpolate import LinearNDInterpolator
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.path as mplPath
from tkinter.ttk import Separator
from numba import jit
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import colors
# from Landformer_Functions import Draw_contours
import matplotlib.transforms as mtransforms
import matplotlib.gridspec as gridspec
import threading
import csv
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import Tk
import matplotlib
import shapefile
from shapely.geometry import shape
from matplotlib.patches import Polygon
import time


@jit
def GenRidges(xy,A,cellsize):
    # print(xy.shape)
    # print(xy[0,0])
    # print(xy[0,:])
    expo=2
    endz=5
    length=50
    b=1/20
    a=(endz-b*length)/(length**expo)
    for kk in range (0,xy.shape[0]):
        
        k=xy[kk,:]
        print(k)
        jy=int(k[0])
        ix=int(k[1])
        z=A[ix,jy]
        print(z)
        for i in range(-200,200):
            for j in range(-200,200):
                if i+ix>0 and i+ix<A.shape[0] and j+jy>0 and j+jy<A.shape[1]:
                    d=((i*cellsize)**2+(j*cellsize)**2)**0.5
                    S=expo*a*d**(expo-1)+b
                    S=1/S
                    if S<3.0:
                        S=3.0
                    if z+d/S<A[i+ix,j+jy]:
                        # print('here')
                        A[i+ix,j+jy]=z+d/S
        # ret
                    
                    
@jit
def Set_to_constant(Design,Poly,ID,constant):
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Poly[i,j]==ID:
                Design[i,j]=constant

@jit
def Invert_Settlement(Design,Survey,Poly,ID):
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Poly[i,j]==ID:
                if Design[i,j]>Survey[i,j]:
                    thickness=Design[i,j]-Survey[i,j]
                    settlement1=thickness*0.05
                    ds=0.1
                    dz=0
                    check=1
                    for k in range (0,100):
                       settlement1=(thickness+dz)*0.05
                       er=Design[i,j]-(Design[i,j]-settlement1+dz)
                       if check*er<0:
                           check=-check
                           ds=-0.5*ds
                       dz+=ds
                    Design[i,j]=Design[i,j]+dz
                    
@jit
def Create_Settlement(Design,Survey,Poly,ID):
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Poly[i,j]==ID:
                if Design[i,j]>Survey[i,j]:
                    thickness=Design[i,j]-Survey[i,j]
                    settlement1=thickness*0.05
                    
                    Design[i,j]=Design[i,j]-settlement1
                  

# matplotlib.use("TKAgg")
def DrawDistance(Surfaces,Sf,Distances,Tailings):
    background = Sf.f.canvas.copy_from_bbox(Sf.f.bbox)
    for l in range (0,3):
        for im in Sf.a.images:
            Sf.a.images.remove(im)
            try:
                im.colorbar.remove()
            except:
                pass
    Sf.f.canvas.restore_region(background)
    Sf.f.canvas.blit(Sf.f.bbox)
    # Draw_Update(Sf,Surfaces)
    im=Sf.a.imshow(Distances,interpolation='none')
    Sf.f.canvas.blit(Sf.f.bbox)
    
    transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
    background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
    try:
        for tp in Sf.l[0].collections:
            tp.remove()
    except:
        pass
    Sf.l=[Sf.a.contour(Tailings[int(Sf.a.get_ylim()[0]):int(Sf.a.get_ylim()[1]),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])], Sf.levels,linewidths=0.3,colors='red',antialiased=True) ]   
    Sf.f.canvas.restore_region(background)
    for tp in Sf.l[0].collections:
        tp.set_transform(transform+Sf.a.transData)
        Sf.a.draw_artist(tp)
    Sf.f.canvas.blit(Sf.a.bbox)
    
    # Draw_contours(Sf,Surfaces)
    
@jit
def Distance_to_spigot2(Spigots,Design,cellsize,Poly,ID,Distance):
    diag=(2*cellsize**2)**0.5
    for iteration in range(0,2000):
        for i in range (0,Spigots.shape[0]):
            Distance[Spigots[i,0],Spigots[i,1]]=1
        for i in range (0,Design.shape[0]):
            for j in range (0,Design.shape[1]):
                if Poly[i,j]==ID:
                    for ioff in range (-1,2):
                        for joff in range (-1,2):
                            if i+ioff>0 and i+ioff<Design.shape[0] and j+joff>0 and j+joff<Design.shape[1]:
                                d=diag
                                if ioff==0 or joff==0:
                                    d=cellsize
                                if Design[i+ioff,j+joff]<Design[i,j] and Distance[i+ioff,j+joff] > Distance[i,j]+d and Distance[i,j]>0:
                                    Distance[i+ioff,j+joff]=Distance[i,j]+d
                                if Design[i+ioff,j+joff]<Design[i,j] and Distance[i+ioff,j+joff]==0 and Distance[i,j]>0:
                                    Distance[i+ioff,j+joff]=Distance[i,j]+d
                                    
@jit
def Distance_to_spigotGPU(Design,cellsize,Poly,ID,Distance):
    diag=(2*cellsize**2)**0.5
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if i <Design.shape[0] and j<Design.shape[1]:
                if Poly[i,j]==ID:
                    for ioff in range (-1,2):
                        for joff in range (-1,2):
                            if i+ioff>0 and i+ioff<Design.shape[0] and j+joff>0 and j+joff<Design.shape[1]:
                                d=diag
                                if ioff==0 or joff==0:
                                    d=cellsize
                                if Design[i+ioff,j+joff]<Design[i,j] and Distance[i+ioff,j+joff] > Distance[i,j]+d and Distance[i,j]>0:
                                    Distance[i+ioff,j+joff]=Distance[i,j]+d
                                if Design[i+ioff,j+joff]<Design[i,j] and Distance[i+ioff,j+joff]==0 and Distance[i,j]>0:
                                    Distance[i+ioff,j+joff]=Distance[i,j]+d
                            
@jit
def Distance_to_spigotGPU2(Design,cellsize,Poly,ID,Distance,x,y):
    diag=(2*cellsize**2)**0.5
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if i <Design.shape[0] and j<Design.shape[1]:
                if Poly[i,j]==ID:
                    for ioff in range (-1,2):
                        for joff in range (-1,2):
                            if i+ioff>0 and i+ioff<Design.shape[0] and j+joff>0 and j+joff<Design.shape[1]:
                                d=diag
                                if ioff==0 or joff==0:
                                    d=cellsize
                                if Design[i+ioff,j+joff]<Design[i,j] and Distance[i+ioff,j+joff]==0 and Distance[i,j]>0:
                                    Distance[i+ioff,j+joff]=(((i+ioff-x)*cellsize)**2+((j+joff-y)*cellsize)**2)**0.5
                            
@jit
def Distance_to_spigotGPU3(Design,cellsize,Poly,ID,Distance,x,y):
    diag=(2*cellsize**2)**0.5
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if i <Design.shape[0] and j<Design.shape[1]:
                if Poly[i,j]==ID:
                    Distance[i,j]=(((i-x)*cellsize)**2+((j-y)*cellsize)**2)**0.5
                            

@jit
def Place_Tailings(Tailings, Distance,Design,slope,elev,volume):
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Distance[i,j]>0:
                if elev-Distance[i,j]/slope>Design[i,j]:
                    volume[0]+=elev-Distance[i,j]/slope-Design[i,j]
                    Tailings[i,j]=elev-Distance[i,j]/slope
            
def Distance_to_spigot(Spigots,Design,cellsize,Poly,ID,Distance,slope,elev):
    
    for i in range (0,Spigots.shape[0]):
        Distance[Spigots[i,0],Spigots[i,1]]=1
    
    
    
    # func_boundarypoly[blockspergrid,threadsperblock](d_W,d_A)
    check = 0
    v=0
    while check==0 and v<1:
        Distance_to_spigotGPU3(Design,cellsize,Poly,ID,Distance,Spigots[i,0],Spigots[i,1])
        # Distance_to_spigotGPU[blockspergrid,threadsperblock](d_Design,cellsize,Poly,ID,d_Distance)
        v+=1
    
    # slope=100
    elev= Design[Spigots[0,0],Spigots[0,1]]+elev
    volume=np.array([0])
    Tailings=np.copy(Design)
    
    Place_Tailings(Tailings, Distance,Design,slope,elev,volume)
    print(volume)
    return Distance,Tailings
        
@jit
def Apply_Benches4(C,Design,Survey,Bench_h,toe_elev,Poly,ID,S,TopE):
    for bench in range (1,50):
        benchlevel=toe_elev+bench*Bench_h
        benchbase=benchlevel-1.0*Bench_h
        benchtop=benchlevel+0.0*Bench_h
        if benchtop>TopE:
            benchtop=TopE
        step=Bench_h*0.5
        dstep=10
        dstepold=0
        # check=0
        for k in range (0,50):
            cut0=1
            fill0=0
            for i in range (0,Design.shape[0]):
                for j in range (0,Design.shape[1]):
                    if  Poly[i,j]==ID:
                        if Design[i,j]<toe_elev:
                            C[i,j]=Design[i,j]
                        if Design[i,j]>TopE:
                            C[i,j]=Design[i,j]    
                        if Design[i,j]>=benchbase and Design[i,j]<=benchtop and Design[i,j]<=TopE:
                            if Design[i,j]>benchbase+step:
                                C[i,j]=benchtop
                            else:
                                C[i,j]=benchbase
                            if C[i,j]<Survey[i,j]:
                                C[i,j]=Survey[i,j]
                            
                            if Design[i,j]>=benchbase and Design[i,j]<=benchtop:
                                dz=C[i,j]-Design[i,j]
                                # dz=min(benchtop,C[i,j])-Design[i,j]
                                if dz>0:
                                    fill0+=dz
                                else:
                                    cut0-=dz
            # if cut0>0:
            
            if (cut0-fill0)/cut0>0.00:
            # if cut0>fill0:
                if dstepold>0:
                    dstep=0.5*dstep
                step-=dstep
                dstepold=-dstep
            else:
                if dstepold<0:
                    dstep=0.5*dstep
                step+=dstep
                dstepold=dstep
                
@jit# (nopython=True)
def func_boundarypoly(W, elev):
    for i in range (0,W.shape[0]):
        for j in range (0,W.shape[1]):
            if i <W.shape[0] and j<W.shape[1]:
                if elev[i,j] !=0:
                    for xoff in range(-1,2):
                        for yoff in range(-1,2):
                            if xoff!=0 or yoff!=0:
                                if i+yoff<W.shape[0] and i+yoff>=0:
                                    if j + xoff<W.shape[1] and j+xoff>=0:
                                        if elev[i+yoff][j+xoff] == 0:
                                            W[i][j]=elev[i][j]
                                        if i+yoff==0 or j +xoff==0 or i+yoff==W.shape[0] or j +xoff==W.shape[1]:
                                            if elev[i,j]>0:
                                                W[i][j]=elev[i][j]
                                                
                    if W[i][j]==0:
                        W[i][j]=10000
                
@jit #(nopython=True)
def func_fill(d_W,d_elev,C):
    for i in range (0,d_W.shape[0]):
        for j in range (0,d_W.shape[1]):
            if i < d_W.shape[0] and j < d_W.shape[1]:
                if d_elev[i,j]>0:
                    if d_W[i,j] >d_elev[i,j]:
                         Terminate =0
                         for roff in range(-1,2):
                             for coff in range(-1,2):
                                 if i+roff<d_W.shape[0] and i+roff>=0:
                                     if j + coff<d_W.shape[1]  and j+coff>=0:
                                         if roff!=0 or coff!=0:
                                             if Terminate == 0:
                                                 if roff == 0 or coff == 0:
                                                     epsi = C[2]
                                                 else:
                                                     epsi = C[3]
                                                 if d_elev[i,j] >= d_W[i+roff,j+coff]+epsi:
                                                     d_W[i,j]=d_elev[i,j]
                                                     C[4]+=1
                                                     Terminate = 1
                                                 if Terminate == 0:
                                                     if d_W[i,j] > d_W[i+roff,j+coff]+epsi:
                                                         d_W[i,j] = d_W[i+roff,j+coff]+epsi
                                                         C[4]+=1
@jit
def set_polyArea(A,Poly,ID,W):
    for i in range (0,A.shape[0]):
        for j in range (0,A.shape[1]):
            W[i,j]=A[i,j]
            if Poly[i,j]==ID:
                W[i,j]=10000
                
def Free_poly(A,cellsize,Poly,ID,slope,W):
    
    set_polyArea(A,Poly,ID,W)
    epsistr = cellsize/slope
    epsidiag = ((2*(cellsize)**2)**0.5)/slope
    arr=np.array([0,0,epsistr,epsidiag,1],dtype=np.float32)
    
    
    
    # func_boundarypoly[blockspergrid,threadsperblock](d_W,d_A)
    check = 0
    v=0
    while check==0 and v<1000:
        func_fill(W,A,arr)
        C=arr
        check=1
        if C[4]>1:
            arr[4]=0
        v+=1
    
    return W

def Draw_contours2(Sf,Surfaces):
        
            
        Sf.notPlotted=False
        transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        transform = mtransforms.Affine2D().translate(Sf.xlim[0],Sf.ylim[0])
        # background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        # background=Sf.f.canvas.copy_from_bbox(Sf.f.bbox)
        # print('draw')
        try:
            for tp in Sf.p[0].collections:
                tp.remove()
        except:
            pass
        try:    
            Sf.p=[Sf.a.contour(Surfaces.Design[int(Sf.ylim[0]):int(Sf.ylim[1]),int(Sf.xlim[0]):int(Sf.xlim[1])], Sf.levels,linewidths=0.3,colors='white',antialiased=True) ]
            # Sf.f.canvas.restore_region(background)
        except:
            return
        for tp in Sf.p[0].collections:
            tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
        # print('done')
        # Sf.f.canvas.blit(Sf.a.bbox)
        Sf.canvas.draw_idle()
        
        
@jit
def Apply_Benches(C,Design,Survey,Bench_h,toe_elev,Poly,ID,S):
    
    
    step=0
    dstep=5
    dstepold=0
    check=0
    for k in range (0,50):
        cut0=0
        fill0=0
        area=0
        
        for i in range (0,Design.shape[0]):
            for j in range (0,Design.shape[1]):
                if  Poly[i,j]==ID:
                    
                    if Design[i,j]>Survey[i,j]:
                       check=1
                       z=toe_elev+round(int(Design[i,j]-toe_elev-step)/Bench_h)*Bench_h
                       # if z<benchtop and z>benchbase:
                       if z>Survey[i,j]:
                            C[i,j]=z
                       else:
                            C[i,j]=Survey[i,j]
                               
                           # if C[i,j]>benchtop:
                           #     C[i,j]=benchtop
                           # if C[i,j]<benchbase:
                           #      C[i,j]=benchbase    
                    else:
                        C[i,j]=Survey[i,j]
                        
                    dz=C[i,j]-Design[i,j]
                    # else:
                    #     dz=0
                    
                    if dz>0:
                        fill0+=dz
                    else:
                        cut0-=dz
        if cut0==0:
            break
        if (cut0-fill0)/cut0>0.00:
        # if cut0>fill0:
            if dstepold>0:
                dstep=0.5*dstep
            step-=dstep
            dstepold=-dstep
        else:
            if dstepold<0:
                dstep=0.5*dstep
            step+=dstep
            dstepold=dstep
 
            
@jit
def Apply_Benches3(C,Design,Survey,Bench_h,toe_elev,Poly,ID,S):
    for bench in range (0,50):
        benchlevel=toe_elev+bench*Bench_h
        benchbase=benchlevel-1.0*Bench_h
        benchtop=benchlevel+0.0*Bench_h
        step=Bench_h*0.5
        dstep=10
        dstepold=0
        check=0
        for k in range (0,50):
            cut0=0
            fill0=0
            for i in range (0,Design.shape[0]):
                for j in range (0,Design.shape[1]):
                    if  Poly[i,j]==ID:
                        # if S[i,j]<50:
                            # if Design[i,j]>Survey[i,j]:
                            if Design[i,j]>=benchbase and Design[i,j]<=benchtop:
                                # bh=benchtop+step
                                # if Design[i,j]>Survey[i,j]:
                                    # if Survey[i,j]<benchlevel:
                                if Design[i,j]>benchbase+step:
                                    C[i,j]=benchtop
                                else:
                                    C[i,j]=benchbase
                                # if Design[i,j]<benchlevel:
                                #     C[i,j]=benchlevel-Bench_h
                                # else:
                                #     C[i,j]=benchlevel
                                if C[i,j]<Survey[i,j]:
                                    C[i,j]=Survey[i,j]
                                    
                                # else:
                                #     C[i,j]=Survey[i,j]
                                # if C[i,j]>benchtop:
                                #     C[i,j]=benchtop
                                dz=min(benchtop,C[i,j])-Design[i,j]
                                if dz>0:
                                    fill0+=dz
                                else:
                                    cut0-=dz
                        # else:
                        #     C[i,j]=Design[i,j]
                        # else: 
                        #     C[i,j]=Survey[i,j]
            if cut0==0:
                break
            if (cut0-fill0)/cut0>0.00:
            # if cut0>fill0:
                if dstepold>0:
                    dstep=0.5*dstep
                step-=dstep
                dstepold=-dstep
            else:
                if dstepold<0:
                    dstep=0.5*dstep
                step+=dstep
                dstepold=dstep
        if check==0:
            bench=51
    maxC1=toe_elev
    maxC=0
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Poly[i,j]==ID:
                dz=C[i,j]-Design[i,j]
                if dz>0:
                    fill0+=dz
                else:
                    cut0-=dz
                if C[i,j]>maxC:
                    maxC=C[i,j]
                   
    for k in range (0,200):
        if cut0>0:
            if (cut0-fill0)/cut0<0.0:
                maxC1+=0.5
                maxC-=0.1
            else:
                maxC1-=0.5
        cut0=0
        fill0=0            
        for i in range (0,Design.shape[0]):
           for j in range (0,Design.shape[1]):
               if Poly[i,j]==ID: 
                   if C[i,j]>Survey[i,j]:
                       if Survey[i,j]<maxC1:
                           C[i,j]=Survey[i,j]
                       if C[i,j]>maxC:
                            C[i,j]=maxC
                   dz=C[i,j]-Design[i,j]
                   if dz>0:
                       fill0+=dz
                   else:
                       cut0-=dz
                   
                        
@jit
def Bench_Volumes(C,Design,cut,fill,Poly,ID):
    cut0=0
    fill0=0
    for i in range (0,Design.shape[0]):
       for j in range (0,Design.shape[1]):
           if Design[i,j]>0 and Poly[i,j]==ID:
               dz=C[i,j]-Design[i,j]
               if dz>0:
                   fill0+=dz
               else:
                   cut0-=dz
    cut[0]=cut0
    fill[0]=fill0
                        
                        
# @jit
# def Fill_Cut(Design,Survey,cut,fill,cellsize):
# #def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
#     sq=cellsize**2
#     cut0=0
#     fill0=0
#     for i in range(0,Design.shape[0]):
#         for j in range(0,Design.shape[1]):
#             if Design[i,j]>0 and Survey[i,j]: 
#                dz=Survey[i,j]-Design[i,j]
#                if dz>0: #cut
#                     cut0+=dz*sq
#                elif dz<0:
#                     fill0+=-dz*sq
                                    
#     cut[0]=cut0
#     fill[0]=fill0
    
@jit
def Set_points(Design,Poly,ID,Scratch):
   
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Poly[i,j]==ID:
                Design[i,j]=Scratch[i,j]
                    



@jit
def Slope_to_points(x,y,Design,cellsize,Poly,ID,slope,Scratch):
    z=Design[x,y]
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Poly[i,j]==ID:
                d=((x*cellsize-i*cellsize)**2+(y*cellsize-j*cellsize)**2)**0.5
                z0=z+d/slope
                if z0>Design[i,j]:
                    if Scratch[i,j]==0:
                        Scratch[i,j]=z0
                    if Scratch[i,j]>0:
                        if z0<Scratch[i,j]:
                            Scratch[i,j]=z0
                else:
                    Scratch[i,j]=Design[i,j]
                          
@jit
def Dome_to_points(Design,cellsize,Poly,ID,slope,Scratch):
    # z=Design[x,y]
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Poly[i,j]==ID:
                check=0
                for ioff in range (-1,2):
                    for joff in range (-1,2):
                        if i+ioff>0 and j+joff>0 and i+ioff<Design.shape[0] and j+joff<Design.shape[1]:
                            if Poly[i+ioff,j+joff]!=ID:
                                check=1
                if check==1:
                    for ii in range (0,Design.shape[0]):
                        for jj in range (0,Design.shape[1]):
                            if Poly[ii,jj]==ID:                
                                d=((ii*cellsize-i*cellsize)**2+(jj*cellsize-j*cellsize)**2)**0.5
                                if Scratch[ii,jj]==0:
                                    Scratch[ii,jj]=Design[i,j]+d/slope
                                if Design[i,j]+d/slope<Scratch[ii,jj]:
                                    Scratch[ii,jj]=Design[i,j]+d/slope

@jit
def Vertical_Offset(Design,cellsize,Poly,ID,Off_V):
    # z=Design[x,y]
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Poly[i,j]==ID:
                Design[i,j]+=Off_V                

@jit
def Set_Surv(Design,cellsize,Poly,ID,Survey):
    # z=Design[x,y]
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Poly[i,j]==ID:
                Design[i,j]= Survey[i,j]    
                    
@jit
def setCanalPoints(Canals,xy,width,cellsize,Design,Dist,ID):
    radius=int(width/cellsize)+1
    # radius=50
    for p in xy:
        x=int(round(p[1]))
        y=int(round(p[0]))
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Canals.shape[0] and x+coloff>0 and y+rowoff<Canals.shape[1] and y+rowoff>0:
                    if Design[x+coloff,y+rowoff]>0:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=width:
                            Canals[x+coloff,y+rowoff]=ID
                            
@jit
def polygon_cut_fill(Design,Survey,Poly,cut,fill,cellsize,ID):
    sq=cellsize**2
    cut0=0
    fill0=0
    for i in range(0,Design.shape[0]):
        for j in range(0,Design.shape[1]):
            if Design[i,j]>0 and Survey[i,j]>0 and Poly[i,j]==ID: 
               dz=Survey[i,j]-Design[i,j]
               if dz>0: #cut
                    cut0+=dz*sq
               elif dz<0:
                    fill0+=-dz*sq
                                    
    cut[0]=cut0
    fill[0]=fill0
    
@jit
def polygon_cut_fillArea(Design,Survey,Poly,area,cellsize,ID):
    sq=cellsize**2
    cut0=0
    fill0=0
    area[0]=0
    for i in range(0,Design.shape[0]):
        for j in range(0,Design.shape[1]):
            if Design[i,j]>0 and Survey[i,j]>0 and Poly[i,j]==ID and Design[i,j]!=Survey[i,j]: 
             area[0]+=1
             
@jit
def polygon_cut_fillAreaS(Design,Survey,Poly,area,cellsize,ID,S):
    sq=cellsize**2
    cut0=0
    fill0=0
    for i in range(0,Design.shape[0]):
        for j in range(0,Design.shape[1]):
            if Design[i,j]>0 and Survey[i,j]>0 and Poly[i,j]==ID and Design[i,j]!=Survey[i,j] and S[i,j]<10: 
             area[0]+=1
   

@jit
def Line_cut_fill(Design,Survey,Canal,cut,fill,cellsize,ID):
    sq=cellsize**2
    cut0=0
    fill0=0
    for i in range(0,Design.shape[0]):
        for j in range(0,Design.shape[1]):
            if Design[i,j]>0 and Survey[i,j]>0 and Canal[i,j]==ID: 
               dz=Survey[i,j]-Design[i,j]
               if dz>0: #cut
                    cut0+=dz*sq
               elif dz<0:
                    fill0+=-dz*sq
                                    
    cut[0]=cut0
    fill[0]=fill0

@jit
def polygon_erosion_deposition(Alldiff,Poly,erosion,depo,cellsize,ID):
    
    for i in range(0,Alldiff.shape[0]):
        for j in range(0,Alldiff.shape[1]):
            if Alldiff[i,j,0]>-100  and Poly[i,j]==ID: 
                for k in range (0,Alldiff.shape[2]):
                    if Alldiff[i,j,k]>0:
                        erosion[k]+=Alldiff[i,j,k]
                    else:
                        depo[k]+=Alldiff[i,j,k]
     
@jit
def get_cut_fill_Polygon(Inpoly,A,Aa,block,Survey,C,TotalFill,TotalCut,cutcentroids,fillcentroids,cut,fill,Volumes,cutcount,fillcount,Allx,Ally,Allcount,cellsize,ID):
    sq=cellsize**2
    for i in range (0,A.shape[0]):
        for j in range (0,A.shape[1]):
            if Inpoly[i,j]==ID:
                Aa[i,j]=int(round((i)/block)*round((Aa.shape[1])/block) + round((j)/block))
                C[i,j]=Survey[i,j]-A[i,j]
            else:
                Aa[i,j]=int(round((i)/block)*round((Aa.shape[1])/block) + round((j)/block))
                C[i,j]=0
            if abs(C[i,j])>1000:
                A[i,j]=max(Survey[i,j],A[i,j])
                Survey[i,j]=A[i,j]
                C[i,j]=0
            Volumes[int(Aa[i,j])]+=C[i,j]*sq
            Allx[int(Aa[i,j])]+=i
            Ally[int(Aa[i,j])]+=j
            Allcount[int(Aa[i,j])]+=1
    
    for j in range (0,Volumes.shape[0]):
        if Volumes[j]>0:
            cutcentroids[cutcount[0],0]=Allx[j]/Allcount[j]
            cutcentroids[cutcount[0],1]=Ally[j]/Allcount[j]
            cut[cutcount[0]]=Volumes[j]
            cutcount[0]+=1
        if Volumes[j]<0:
            fillcentroids[fillcount[0],0]=Allx[j]/Allcount[j]
            fillcentroids[fillcount[0],1]=Ally[j]/Allcount[j]
            fill[fillcount]=-Volumes[j]
            fillcount[0]+=1
    for i in range (0,A.shape[0]):
        for j in range (0,A.shape[1]):
            Aa[i,j]=Volumes[int(Aa[i,j])]

@jit
def get_distances(cutcentroids,fillcentroids,Dist,DistUpDwn,cut,fill,cellsize,A):
    # count=0
    cf=-1
    for c in fillcentroids:
        cf+=1
        cc=0
 
        for f in cutcentroids:
            d=((f[0]*cellsize-c[0]*cellsize)**2+(f[1]*cellsize-c[1]*cellsize)**2)**0.5
            Dist[cc,cf]=d
            slope=-100*(A[int(c[0]),int(c[1])]-A[int(f[0]),int(f[1])])/d
        
            factor=-slope/45+1.0
            factor=1/factor
            # factor=1
            DistUpDwn[cc,cf]=d/factor
            cc+=1
            
    for i in range (0,DistUpDwn.shape[0]):
        for j in range (0,DistUpDwn.shape[1]):
            if j ==DistUpDwn.shape[1]-2:
                if i<cut.shape[0]:
                    DistUpDwn[i,j]=cut[i]
            if i ==DistUpDwn.shape[0]-1:
                DistUpDwn[i,j]=j
            
            if i ==DistUpDwn.shape[0]-2:
                if j<fill.shape[0]:
                    DistUpDwn[i,j]=fill[j]
            if j ==DistUpDwn.shape[1]-1:
                DistUpDwn[i,j]=i

@jit
def VogelApproxNmb(A,B):
    count=0
    v=1
    while np.sum(A[:,-2])>0 and np.sum(A[-2,:])>0 and v==1:
        aold=np.sum(A[:,-2])*np.sum(A[-2,:])
        # k=2
        maxi=0
        maxj=0
        maxival=0
        minval=np.inf
        minval2=np.inf
        count+=1
        for i in range(0,A.shape[0]-2):
            if A[i,-2]>0:
                i2=0
                j2=0
                for j in range(0,A.shape[1]-2):
                    if A[i,j]<minval and A[-2,j]>0:
                        minval=A[i,j]
                        i2=i
                        j2=j
                    if A[i,j]<minval2 and A[i,j]>minval and A[-2,j]>0:
                        minval2=A[i,j]
                # idx=np.argpartition(A[i,:-2],k)
                if abs(minval2-minval)>maxival:
                    maxi=i2
                    maxj=j2
                    maxival=abs(minval2-minval)
        B[maxi,maxj]=min(A[maxi,-2],A[-2,maxj])
        A[maxi,-2]-=B[maxi,maxj]
        A[-2,maxj]-=B[maxi,maxj]
        if aold==np.sum(A[:,-2])*np.sum(A[-2,:]):
            v=0 
def dot(v,w):
    x,y = v
    X,Y = w
    return x*X + y*Y

def length(v):
    x,y = v
    return math.sqrt(x*x + y*y)

def vector(b,e):
    x,y = b
    X,Y = e
    return (X-x, Y-y)

def unit(v):
    x,y = v
    mag = length(v)
    return (x/mag, y/mag)

def distance(p0,p1):
    return length(vector(p0,p1))

def scale(v,sc):
    x,y = v
    return (x * sc, y * sc)

def add(v,w):
    x,y = v
    X,Y = w
    return (x+X, y+Y)

@jit
def Slope_by_Z(S,SlopeBot,expo,TopE,BotE,avg,dist,step):
    #S is x,y of the line... y doesnt matter, x doesnt matter 0.5m steps
    endz=(TopE-BotE)*(1-step)
    length=(TopE-BotE)*avg*(1-step)
    b=1/SlopeBot
    a=(endz-b*length)/(length**expo)
    # c=0
    for i in range (0,S.shape[0]):
        if dist[i]<length:
            S[i]=BotE+a*dist[i]**expo+b*dist[i]
        else:
            S[i]=BotE+endz+a*(dist[i]-length)**expo+b*(dist[i]-length)
        # c+=0.5
        
def Slope_by_ZRVL(S,SlopeBot,expo,TopE,BotE,avg,dist):
    #S is x,y of the line... y doesnt matter, x doesnt matter 0.5m steps
    endz=TopE-BotE
    length=(TopE-BotE)*avg
    b=1/SlopeBot
    a=(endz-b*length)/(length**expo)
    # c=0
    for i in range (0,S.shape[0]):
        S[i]=BotE+a*dist[i]**expo+b*dist[i]
        
    return(S,expo)

@jit
def Profile_Bench(S,BotE,dist,BWidth,BHeight,BOff,BSlope):
    #S is x,y of the line... y doesnt matter, x doesnt matter 0.5m steps
    S[0]=BotE
    Battercounter=0
    # Benchcounter=0
    for i in range (1,S.shape[0]):
        if Battercounter<BHeight-0.5:
            S[i]=S[i-1]+(dist[i]-dist[i-1])/BSlope
            Battercounter+=S[i]-S[i-1]
        else:
            S[i]=S[i-1]+(dist[i]-dist[i-1])/BWidth
            Battercounter+=S[i]-S[i-1]
            if Battercounter>BHeight+0.5:
                Battercounter=0
        # c+=0.5
        
@jit
def Profile_BenchVar(S,BotE,dist,BWidth,BElev,BSlope):
    #S is x,y of the line... y doesnt matter, x doesnt matter 0.5m steps
    S[0]=BotE
    Battercounter=0
    # Benchcounter=0
    for i in range (1,S.shape[0]):
        check=0
        for ii in range(0,BElev.shape[0]-1,2):
            if S[i-1]> BElev[ii] and S[i-1]< BElev[ii+1]:
                slope=((BElev[ii+1]-BElev[ii])/BWidth)
                S[i]=S[i-1]+(dist[i]-dist[i-1])*slope
                check=1
                break
        if check ==0:
            slope=BSlope
            S[i]=S[i-1]+(dist[i]-dist[i-1])/slope
                
@jit
def Profile_linear(S,BotE,dist,S1,S2,S3,S4,C1,C2,C3,C4):
    #S is x,y of the line... y doesnt matter, x doesnt matter 0.5m steps
    S[0]=BotE
    
    # Benchcounter=0
    for i in range (1,S.shape[0]):
        if dist[i]<C1 and C1>0:
            S[i]=S[i-1]+(dist[i]-dist[i-1])/S1
        elif dist[i]<C2 and C2>C1:
            S[i]=S[i-1]+(dist[i]-dist[i-1])/S2
        elif dist[i]<C3 and C3>C2:
            S[i]=S[i-1]+(dist[i]-dist[i-1])/S3
        elif dist[i]<C4 and C4>C3:
            S[i]=S[i-1]+(dist[i]-dist[i-1])/S4
        else:
            Ss=1.0
            if S1>0:
                Ss=S1
            if S2>0:
                Ss=S2
            if S3>0:
                Ss=S3
            if S4>0:
                Ss=S4
            S[i]=S[i-1]+(dist[i]-dist[i-1])/Ss

def compile_tangent_radial_lines():
    line=[[0,0],[100,100]]
    linesize=np.size(line,axis=0)
    line=np.array(line,dtype=np.float64)
    line_new=np.zeros(((linesize-2)*100 + 2,2),dtype=np.float64)
    line_new_temp=np.zeros(((linesize-2)*100 + 2,2),dtype=np.float64)
    temp_k_list=np.zeros((100),dtype=np.float64)
    vectors=np.zeros((11,2),dtype=np.float64)
    integers=np.zeros((4),dtype=np.float64)

    radii=[0.5]
    radii=np.array(radii,dtype=np.float64)
    
   

    tangent_radial_lines_jit(line,line_new,line_new_temp,radii,vectors,temp_k_list,integers)


#@jit 
def tangent_radial_lines_jit(line,line_new,line_new_temp,radii,vectors,temp_k_list,integers):
    for radius in radii:
        #radius=radii[ii]
        integers[1]=0
        integers[2]=0
        
        if line.shape[0]==2:
            line_new[0,0]=line[0,0]
            line_new[0,1]=line[0,1]
            line_new[1,1]=line[1,1]
            line_new[1,0]=line[1,0]
            break
        
        for i in range(0,line.shape[0]-2):
            #vectors from intersect point in focus (point i+1)
            vectors[0,0]=line[i,0]-line[i+1,0]
            vectors[0,1]=line[i,1]-line[i+1,1]
            vectors[1,0]=-line[i+1,0]+line[i+2,0]
            vectors[1,1]=-line[i+1,1]+line[i+2,1]
                 
            #angle between vectors = A.B/(|A||B|)
            vectors[9,0]=np.arccos((vectors[0,0]*vectors[1,0]+vectors[0,1]*vectors[1,1])/(((vectors[0,0]**2+vectors[0,1]**2)**0.5)*((vectors[1,0]**2+vectors[1,1]**2)**0.5)))
            
            vectors[10,0]=radius/np.sin(vectors[9,0]/2)
               

            #Finding the vectors that have direction that points to the two potential points for A (one rotation clockwise and the other anticlockwise)
            #A is the centre point of the circle we create to give the curvature
            vectors[2,0]=vectors[1,0]*np.cos(vectors[9,0]/2) - vectors[1,1]*np.sin(vectors[9,0]/2) 
            vectors[2,1]=vectors[1,0]*np.sin(vectors[9,0]/2) + vectors[1,1]*np.cos(vectors[9,0]/2)
            vectors[3,0]=vectors[1,0]*np.cos(-vectors[9,0]/2) - vectors[1,1]*np.sin(-vectors[9,0]/2)
            vectors[3,1]=vectors[1,0]*np.sin(-vectors[9,0]/2) + vectors[1,1]*np.cos(-vectors[9,0]/2)
            

            #We have two potential points for A, one is on the correct side and the other is not, so need to figure out which one is correct    
            vectors[4,0]=line[i+1,0] + vectors[10,0]*vectors[2,0]/((vectors[2,0]**2 + vectors[2,1]**2)**0.5)         
            vectors[4,1]=line[i+1,1] + vectors[10,0]*vectors[2,1]/((vectors[2,0]**2 + vectors[2,1]**2)**0.5)
            vectors[7,0]=line[i+1,0] + vectors[10,0]*vectors[3,0]/((vectors[3,0]**2 + vectors[3,1]**2)**0.5)
            vectors[7,1]=line[i+1,1] + vectors[10,0]*vectors[3,1]/((vectors[3,0]**2 + vectors[3,1]**2)**0.5)

            
            #Calculations to figure which A point is correct
            vectors[11,0]=0
            vectors[11,1]=0
            for j in range(0,3):
                #Average vectors[11,0] between each potential A point and the points on the straight lines (the smallest avg. dist. is the correct point)
                vectors[11,0]+=((vectors[4,0]-line[i+j,0])**2+(vectors[4,1]-line[i+j,1])**2)**0.5
                vectors[11,1]+=((vectors[7,0]-line[i+j,0])**2+(vectors[7,1]-line[i+j,1])**2)**0.5
            
            alternate_point=False
            if vectors[11,1]<vectors[11,0]:
                alternate_point=True
                vectors[4,0]=vectors[7,0]
                vectors[4,1]=vectors[7,1]
            
            
            #Intersection by calculation
            vectors[9,1]=np.pi/2-vectors[9,0]/2 #vectors[9,0] of rotation
            
            #Vector from the centre of the circle to the join of the straight lines
            vectors[2,0]=line[i+1,0]-vectors[4,0]
            vectors[2,1]=line[i+1,1]-vectors[4,1]
            
            vectors[10,1]=((vectors[2,0]**2+vectors[2,1]**2)**0.5)
            vectors[2,0]=vectors[2,0]/vectors[10,1] #normalising vector to become unit vector
            vectors[2,1]=vectors[2,1]/vectors[10,1]
            
            #rotating vector to intersection point of straight line 1
            vectors[0,0]=vectors[2,0]*np.cos(vectors[9,1]) - vectors[2,1]*np.sin(vectors[9,1])
            vectors[0,1]=vectors[2,0]*np.sin(vectors[9,1]) + vectors[2,1]*np.cos(vectors[9,1])
            #rotating vector to intersection point of straight line 2
            vectors[1,0]=vectors[2,0]*np.cos(-vectors[9,1]) - vectors[2,1]*np.sin(-vectors[9,1])
            vectors[1,1]=vectors[2,0]*np.sin(-vectors[9,1]) + vectors[2,1]*np.cos(-vectors[9,1])
          
            vectors[5,0]=round(vectors[4,0]+vectors[0,0]*radius,2)
            vectors[5,1]=round(vectors[4,1]+vectors[0,1]*radius,2)
            vectors[6,0]=round(vectors[4,0]+vectors[1,0]*radius,2)
            vectors[6,1]=round(vectors[4,1]+vectors[1,1]*radius,2)
            
                    
            
            #Sometimes the rounding of zero can be -0 so need to change that
            if vectors[5,0]==-0:
                vectors[5,0]=float(0)
                
            if vectors[5,1]==-0:
                vectors[5,1]=float(0)
                
            if vectors[6,0]==-0:
                vectors[6,0]=float(0)
                
            if vectors[6,1]==-0:
                vectors[6,1]=float(0)   
            
              
            
            #Creating the arc
            #Finding the vectors[9,0] difference between the two end points of straight line and the orientation of that vectors[9,0] on the unit circle
            if abs(vectors[5,0]-vectors[4,0])!=0:
                vectors[12,0]=np.arctan(abs(vectors[5,1]-vectors[4,1])/abs(vectors[5,0]-vectors[4,0]))
            else:
                vectors[12,0]=np.pi/2   
            if vectors[5,0]-vectors[4,0]>=0:
                if vectors[5,1]-vectors[4,1]>=0:
                    pass
                else: 
                    vectors[12,0]=2*np.pi-vectors[12,0]
            else:
                if vectors[5,1]-vectors[4,1]>=0:
                    vectors[12,0]=np.pi-vectors[12,0]
                else:
                    vectors[12,0]=np.pi+vectors[12,0]

            if abs(vectors[6,0]-vectors[4,0])==0:
                vectors[12,1]=np.pi/2
            else:
                vectors[12,1]=np.arctan(abs(vectors[6,1]-vectors[4,1])/abs(vectors[6,0]-vectors[4,0]))
            
            if vectors[6,0]-vectors[4,0]>=0:
                if vectors[6,1]-vectors[4,1]>=0:      
                    pass
                else: 
                    vectors[12,1]=2*np.pi-vectors[12,1] 
                    
            else:
                if vectors[6,1]-vectors[4,1]>=0:
                    vectors[12,1]=np.pi-vectors[12,1]        
                else:
                    vectors[12,1]=np.pi+vectors[12,1]
                    
                    
            #ensures that each end point of the arc is connected to the right line endpoint
            if alternate_point: 
                if vectors[12,0]<vectors[12,1]:
                    vectors[12,0]=vectors[12,0]+2*np.pi
                angle_list=np.linspace(vectors[12,0],vectors[12,1],100) 
            else:
                if vectors[12,0]<vectors[12,1]:
                    vectors[12,0]=vectors[12,0]+2*np.pi
                angle_list=np.linspace(vectors[12,1],vectors[12,0],100) 
            

            #Creation of the new line array with the arc
            if integers[1]==0:
                line_new[int(integers[2]),0]=line[i,0]
                line_new[int(integers[2]),1]=line[i,1]
                integers[2]=integers[2]+1
                
            else:
                integers[2]=integers[2]-1
            
               
            integers[3]=0
            for kk in range(0,angle_list.shape[0]):
                angle=angle_list[kk]
                line_new_temp[int(integers[2]),0]=vectors[4,0]+radius*np.cos(angle)
                line_new_temp[int(integers[2]),1]=vectors[4,1]+radius*np.sin(angle)
                temp_k_list[int(integers[3])]=integers[2]
                integers[3]=integers[3]+1
                integers[2]=integers[2]+1
                
            
            if integers[0]==0:
                for jj in range(0,temp_k_list.shape[0]):
                    entry=int(temp_k_list[jj])
                    line_new[entry,0]=line_new_temp[entry,0]
                    line_new[entry,1]=line_new_temp[entry,1]
                
                line_new[int(integers[2]),0]=line[i+2,0]
                line_new[int(integers[2]),1]=line[i+2,1]
                integers[2]=integers[2]+1
               
             
            else:
                vectors[0,0]=line_new[int(temp_k_list[0])-1,0]-line_new_temp[int(temp_k_list[0]),0]
                vectors[0,1]=line_new[int(temp_k_list[0])-1,1]-line_new_temp[int(temp_k_list[0]),1]
                vectors[1,0]=-line_new_temp[int(temp_k_list[0]),0]+line_new_temp[int(temp_k_list[1]),0]
                vectors[1,1]=-line_new_temp[int(temp_k_list[0]),1]+line_new_temp[int(temp_k_list[1]),1]
                
                vectors[2,0]=line_new[int(temp_k_list[-1])+1,0]-line_new_temp[int(temp_k_list[-1]),0]
                vectors[2,1]=line_new[int(temp_k_list[-1])+1,1]-line_new_temp[int(temp_k_list[-1]),1]
                vectors[3,0]=-line_new_temp[int(temp_k_list[-1]),0]+line_new_temp[int(temp_k_list[-2]),0]
                vectors[3,1]=-line_new_temp[int(temp_k_list[-1]),1]+line_new_temp[int(temp_k_list[-2]),1]
                 
                
                vectors[8,0]=np.arccos((vectors[0,0]*vectors[1,0]+vectors[0,1]*vectors[1,1])/(((vectors[0,0]**2+vectors[0,1]**2)**0.5)*((vectors[1,0]**2+vectors[1,1]**2)**0.5)))               
                vectors[8,1]=np.arccos((vectors[2,0]*vectors[3,0]+vectors[2,1]*vectors[3,1])/(((vectors[2,0]**2+vectors[2,1]**2)**0.5)*((vectors[3,0]**2+vectors[3,1]**2)**0.5)))
                
           
                if vectors[8,0]<(np.pi+0.2) and vectors[8,0]>(np.pi-0.2) and vectors[8,1]<(np.pi+0.2) and vectors[8,1]>(np.pi-0.2): #approx greater than 5 degrees
                    for iii in range(0,temp_k_list.shape[0]):
                        entry=int(temp_k_list[iii])
                        line_new[entry,0]=line_new_temp[entry,0]
                        line_new[entry,1]=line_new_temp[entry,1]
                        
                    
                integers[2]=integers[2]+1
            integers[1]=integers[1]+1
        integers[0]=integers[0]+1
 


        
class CircleObj(object):
    def __init__(self, Sf, circle):
#        canvas = circle.figure.canvas
        self.canvas = Sf.canvas
        self.circle = circle
        self.ax=Sf.a
        self.rad=20
        self.fig=Sf.f
        self.ax.add_artist(self.circle)
#        Sf.a.add_artist(self.circle)
        self.Active=True
        # print('circle added')
        self.canvas.callbacks.connect('draw_event', self.draw_callback)
#        self.canvas.callbacks.connect('motion_notify_event', self.motion_notify_callback)
#        self.canvas = canvas
    def draw_callback(self, event):
        if self.Active:
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)
            # self.background = self.canvas.copy_from_bbox(self.fig.bbox)
            self.ax.draw_artist(self.circle)
    def motion_notify_callback(self, event):
        'on mouse movement'
#        print('circle added motion')
        if self.Active:
            # self.background = self.canvas.copy_from_bbox(self.ax.bbox)
            x, y = event.xdata, event.ydata
            self.circle.set_center((x,y))
            self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.circle)
            self.canvas.blit(self.fig.bbox)
            # self.canvas.blit(self.ax.bbox)
            # self.canvas.draw()
    def Radius(self, var,cellsize):
        'on mouse movement'
        if self.Active:
            if self.rad+var>2:
                self.rad+=var
                self.circle.set_radius(self.rad/cellsize)
                self.canvas.restore_region(self.background)
                self.ax.draw_artist(self.circle)
                self.canvas.blit(self.fig.bbox)

class PolygonInfo(tk.Toplevel):
    def __init__(self, title='', message=''):
        tk.Toplevel.__init__(self)
        self.geometry('400x200+200+100') # Must change these accordingly
        self.title(title)
        # self.protocol("WM_DELETE_WINDOW",on_closing())
        self.AreaLabel = tk.Label(self, text='Area ha',
                                     bg='#fff', fg='#000', font=('roboto', 10))
        self.AreaLabel.grid(row=0,column=0)
        
        self.DensityLabel = tk.Label(self, text='Drainage Density m/ha',
                                     bg='#fff', fg='#000', font=('roboto', 10))
        self.DensityLabel.grid(row=1,column=0)
        
        self.CutLabel = tk.Label(self, text='Polygon Cut m3',
                                     bg='#fff', fg='#000', font=('roboto', 10))
        self.CutLabel.grid(row=2,column=0)

        self.FillLabel = tk.Label(self, text='Polygon Fill m3',
                                     bg='#fff', fg='#000', font=('roboto', 10))
        self.FillLabel.grid(row=3,column=0)
        
        self.DiffLabel = tk.Label(self, text='Difference m3',
                                     bg='#fff', fg='#000', font=('roboto', 10))
        self.DiffLabel.grid(row=4,column=0)
        
        
        self.Area = tk.Label(self, text=str(0),
                                     bg='#fff', fg='#000', font=('roboto', 10))
        self.Area.grid(row=0,column=1)
        
        self.Density = tk.Label(self, text=str(0),
                                     bg='#fff', fg='#000', font=('roboto', 10))
        self.Density.grid(row=1,column=1)
        
        self.Cut = tk.Label(self, text=str(0),
                                     bg='#fff', fg='#000', font=('roboto', 10))
        self.Cut.grid(row=2,column=1)

        self.Fill = tk.Label(self, text=str(0),
                                     bg='#fff', fg='#000', font=('roboto', 10))
        self.Fill.grid(row=3,column=1)
        
        self.Diff = tk.Label(self, text=str(0),
                                     bg='#fff', fg='#000', font=('roboto', 10))
        self.Diff.grid(row=4,column=1)
        
    def updateInfo(self,P, title='', message=''):
        self.title(title)
        self.Area.configure(text="{0:.2f}".format(P.area/10000))
        self.Density.configure(text="{0:.2f}".format(P.density))
        self.Cut.configure(text=str(int(P.cut)))        
        self.Fill.configure(text=str(int(P.fill)))
        self.Diff.configure(text=str(int(P.cut-P.fill)))
        
    # def on_closing():
    #         self.polyinfo=[]
        
    
        
class DynamicDroplet(object):
    def __init__(self, Sf, line,line2,CS):
#        canvas = circle.figure.canvas
        self.canvas = Sf.canvas
        self.line = line
        self.line2 = line2
        self.ax=Sf.a
        # self.Aspect=Aspect
        self.fig=Sf.f
        self.ax.add_artist(self.line)
        self.ax.add_artist(self.line2)
        self.cellsize=CS
        self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.line)
        self.ax.draw_artist(self.line2)
        self.canvas.blit(self.fig.bbox)
        # self.draw_callback(1)
#        Sf.a.add_artist(self.circle)
        self.Active=True
        self.maxD=float(Sf.sliderDDL.get())
        print('circle added')
        self.canvas.callbacks.connect('draw_event', self.draw_callback)
#        self.canvas.callbacks.connect('motion_notify_event', self.motion_notify_callback)
#        self.canvas = canvas
    def draw_callback(self, event):
        if self.Active:
            # self.background = self.canvas.copy_from_bbox(self.ax.bbox)
            self.background = self.canvas.copy_from_bbox(self.fig.bbox)
            self.ax.draw_artist(self.line)
            self.ax.draw_artist(self.line2)
    def motion_notify_callback2(self, event,Aspect):
        'on mouse movement'
#        print('circle added motion')
        if self.Active:
            x, y = event.xdata, event.ydata
            if int(x)<Aspect.shape[1] and int(y)<Aspect.shape[0]: 
                # print('here')
                if Aspect[int(y),int(x),0]!=0:
                    ii=int(x)
                    jj=int(y)
                    i=ii
                    j=jj
                    lx=[]
                    ly=[]
                    lx2=[]
                    ly2=[]
                    dist=0
                    for bb in range (0,500):
                        if dist<self.maxD:
                            lx.append(ii)
                            ly.append(jj)
                        else:
                            lx2.append(ii)
                            ly2.append(jj)
                        ii-=2*Aspect[j,i,0]
                        jj-=2*Aspect[j,i,1]
                        dx=((self.cellsize*2*Aspect[j,i,0])**2+(self.cellsize*2*Aspect[j,i,1])**2)**0.5
                        dist+=dx
                        i=int(ii)
                        j=int(jj)
                    self.line.set_data([lx,ly])
                    self.line2.set_data([lx2,ly2])
                    self.canvas.restore_region(self.background)
                    self.ax.draw_artist(self.line)
                    self.ax.draw_artist(self.line2)
                    self.canvas.blit(self.fig.bbox)
                    
    def motion_notify_callback(self, event,Aspect,Slope):
        'on mouse movement'
#        print('circle added motion')
        
        if self.Active:
            x, y = event.xdata, event.ydata
            if int(x)<Aspect.shape[1] and int(y)<Aspect.shape[0]: 
                # print('here')
                if Aspect[int(y),int(x),0]!=0:
                    ii=int(x)
                    jj=int(y)
                    i=ii
                    j=jj
                    lx=[]
                    ly=[]
                    lx2=[]
                    ly2=[]
                    dist=0
                    for bb in range (0,500):
                        if dist<self.maxD:
                            lx.append(ii)
                            ly.append(jj)
                        else:
                            lx2.append(ii)
                            ly2.append(jj)
                        stepi=0.5*Aspect[j,i,0]
                        stepj=0.5*Aspect[j,i,1]
                        
                        if 1/Slope[j,i]>100:
                            
                            theta=math.acos((1/50)/(1/Slope[j,i]))
                            stepi=(stepi*math.cos(theta)-stepj*math.sin(theta))
                            stepj=(stepi*math.sin(theta)+stepj*math.cos(theta))
                            print((Slope[j,i],stepi,stepj))
                        ii-=stepi
                        jj-=stepj
                        dx=((self.cellsize*stepi)**2+(self.cellsize*stepj)**2)**0.5
                        dist+=dx
                        i=int(ii)
                        j=int(jj)
                    self.line.set_data([lx,ly])
                    self.line2.set_data([lx2,ly2])
                    self.canvas.restore_region(self.background)
                    self.ax.draw_artist(self.line)
                    self.ax.draw_artist(self.line2)
                    self.canvas.blit(self.fig.bbox)
    def remover(self):
        self.line.remove()
        self.line2.remove()
        self.fig.canvas.restore_region(self.background)
        self.canvas.blit(self.fig.bbox)
                

        
class Le_dot(object):
    def __init__(self, Sf, circle):
        self.canvas = Sf.canvas
        self.circle = Line2D([0,0],[0,0],marker='o',markevery=2)
        self.ax=Sf.a
        self.rad=2
        self.fig=Sf.f
        self.ax.add_artist(self.circle)
        self.canvas.callbacks.connect('draw_event', self.draw_callback)
    def draw_callback(self, event):
        self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        self.ax.draw_artist(self.circle)
    def draw_dot(self,xdata,ydata):
        self.circle.set_data(xdata,ydata)
        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.circle)
        self.canvas.blit(self.fig.bbox)

class Le_point(object):
    def __init__(self, Sf, circle):
        self.canvas = Sf.canvas
        self.circle = circle
        self.ax=Sf.a
        self.rad=0.5
        self.fig=Sf.f
        self.ax.add_artist(self.circle)
        self.canvas.callbacks.connect('draw_event', self.draw_callback)
    def draw_callback(self, event):
        self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        self.ax.draw_artist(self.circle)
    def draw_point(self, x,y):
        self.circle.set_center((x,y))
        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.circle)
        self.canvas.blit(self.fig.bbox)

class ElevationAnnot(object):
    def __init__(self, Sf,Surfaces):
#        canvas = circle.figure.canvas
        self.canvas = Sf.canvas
        self.ax=Sf.a
        self.Surface=Surfaces.Design
        self.Survey=Surfaces.Survey
        # self.Aspect=Aspect
        self.fig=Sf.f
        self.annot = self.ax.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",bbox=dict(boxstyle="round", fc="w"),arrowprops=dict(arrowstyle="->",color='white'))
        # self.ax.add_artist(self.annot)
        self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        self.canvas.callbacks.connect('draw_event', self.draw_callback)
#        self.canvas.callbacks.connect('motion_notify_event', self.motion_notify_callback)
#        self.canvas = canvas
    def draw_callback(self, event):
        self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        
    def on_click(self, event):
        x, y = event.xdata, event.ydata
        pos=[x,y]
        z=self.Surface[int(y),int(x)]
        z2=self.Survey[int(y),int(x)]
        self.annot.xy = pos
        text = str('Design = %.2f\nSurvey = %.2f' % (z,z2))
        # text = str('%.2f\n%.2f' % (z,z2))
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.4)
        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.annot)
        self.canvas.blit(self.fig.bbox)
            
    def motion_notify_callback(self, event):
        'on mouse movement'
        # self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        x, y = event.xdata, event.ydata
        pos=[x,y]
        z=self.Surface[int(y),int(x)]
        z2=self.Survey[int(y),int(x)]
        self.annot.xy = pos
        # text = str('%.2f' % z)
        # text = str('%.2f\n%.2f' % (z,z2))
        text = str('Design = %.2f\nSurvey = %.2f' % (z,z2))
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.4)
        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.annot)
        self.canvas.blit(self.fig.bbox)
    def remover(self):
        print('removed')
        # self.annot.set_visible=False
        self.annot.remove()
        self.fig.canvas.restore_region(self.background)
        self.canvas.blit(self.fig.bbox)

class MeasureAnnot(object):
    def __init__(self, Sf):
#        canvas = circle.figure.canvas
        self.canvas = Sf.canvas
        self.ax=Sf.a
        self.fig=Sf.f
        self.linedrawn=False
        
        self.annots=[]
        self.annots.append(self.ax.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",bbox=dict(boxstyle="round", fc="w"),arrowprops=dict(arrowstyle="->",color='white')))
        # self.annot = self.ax.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",bbox=dict(boxstyle="round", fc="w"),arrowprops=dict(arrowstyle="->",color='white'))
        self.background = self.canvas.copy_from_bbox(self.fig.bbox)
        self.canvas.callbacks.connect('draw_event', self.draw_callback)
        # print('added ruler')
    def draw_callback(self, event):
        self.background = self.canvas.copy_from_bbox(self.fig.bbox)
            
    def motion_notify_callback(self, event,Surfaces):
        if self.linedrawn:
            x, y = event.xdata, event.ydata
            xy=self.line.get_xydata()
            midy=0.5*(xy[-2,0]+x)
            midx=0.5*(xy[-2,1]+y)
            pos=[midy,midx]
            distance=Surfaces.cellsize*((x-xy[-2,0])**2+(y-xy[-2,1])**2)**0.5
            self.annots[-1].xy = pos
            text = str('%.2f' % distance)
            self.annots[-1].set_text(text)
            xy[-1,0]=x
            xy[-1,1]=y
            self.line.set_data(xy.T)
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)
            self.canvas.restore_region(self.background)
            for a in self.annots:
                self.ax.draw_artist(a)
            self.ax.draw_artist(self.line)
            self.canvas.blit(self.ax.bbox)
    def remove_last(self):
        xy=self.line.get_xydata()
        if xy.shape==2:
            self.remover()
            return
        else:
            xy=xy[0:-1]
            self.annots[-1].remove()
            self.annots=self.annots[0:-1]
            self.line.set_data(xy.T)
        self.canvas.restore_region(self.background)
        for a in self.annots:
            self.ax.draw_artist(a)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.fig.bbox)
        
            
    def on_click(self, event):
        'on mouse movement'
        # print('added ruler click')
        x, y = event.xdata, event.ydata
        print(('measure',x,y))
        if not self.linedrawn:
            line = Line2D([x,x], [y,y], animated=False,marker='o', markerfacecolor='g')
            self.line=line
            self.ax.add_artist(self.line)
            self.xy=np.array([[x,y],[x,y]])
        else:    
            # xy=self.line.get_xydata()
            # print(xy)
            self.xy=np.append(self.xy,[[x,y]],axis=0)
            self.xy=np.append(self.xy,[[x,y]],axis=0)
            # xyt = self.line.get_transform().transform(xy)
            # print(xy[-1])
            midy=0.5*(self.xy[-2,0]+x)
            midx=0.5*(self.xy[-2,1]+y)
            self.annots.append(self.ax.annotate("", xy=(midx,midy), xytext=(20,20),textcoords="offset points",bbox=dict(boxstyle="round", fc="w"),arrowprops=dict(arrowstyle="->",color='white')))
            pos=[midy,midx]
            distance=((x-self.xy[-2,0])**2+(y-self.xy[-2,1])**2)**0.5
            print(x)
            self.annots[-1].xy = pos
            text = str('%.2f' % distance)
            self.annots[-1].set_text(text)
            self.line.set_data(self.xy.T)
            # self.annots[-1].get_bbox_patch().set_alpha(0.4)
            self.canvas.restore_region(self.background)
            for a in self.annots:
                # self.ax.draw_artist(self.annots[-1])
                self.ax.draw_artist(a)
            
            self.ax.draw_artist(self.line)
            self.canvas.blit(self.fig.bbox)
        self.linedrawn=True
        
    def remover(self):
        self.line.remove()
        for a in self.annots:
            a.remove()
        # self.annot.remove()
        self.fig.canvas.restore_region(self.background)
        self.canvas.blit(self.fig.bbox)

                
class LineLinear(object):

    showverts = True
    epsilon = 5  # max pixel distance to count as a vertex hit
    epsilon2=20
    def __init__(self, Sf, line,lineSP,lineRT,Surfaces,dot,ID,Linetype,slp,exp):
       
            canvas = Sf.canvas
            print('added')
            self.press = None
            self.cur_xlim = None
            self.cur_ylim = None
            self.x0 = None
            self.y0 = None
            self.x1 = None
            self.y1 = None
            self.xpress = None
            self.ypress = None

            self.CA=0
            self.DrainDense=0
            self.AllLengths=0
            self.AllDensity=0
            self.Sf=Sf
            self.ID=ID
            self.dot=dot
            self.Linetype=Linetype
            self.Surfaces=Surfaces
            # self.CanalPoints=np.zeros_like()
            self.line = line
            self.lineRT=lineRT ###!
            self.lineSP=lineSP
            self.ax=Sf.a
            self.StrtE=None
            self.StrtSlp=None
            self.EndE=None
            self.EndSlp=None
            self.Active=False
            self.Crest=False
            self.Toe=False
            self.Exp=None
            self.Rad=None
            self.Base=None
            
            self.ax.add_artist(self.line)
            self.ax.add_artist(self.lineSP)
            self.ax.add_artist(self.lineRT)
            self.Allpoints=Sf.Allpoints
            self._ind = None  # the active vert
            self.average=None
            self.ExitButton=None
            self.Coord=None
            self.BH=None
            self.LH=None
            self.Topslope=None
            self.plotActive=False
            self.Slope0=slp
            self.Step=0
            self.StartElevation=None
            self.expo=exp
            self.BWidth=5.0
            self.BHeight=20.0
            self.BOff=0
            self.Bslope=5.0
            self.BottomWidth = 0
            self.TotDepth = 0
            self.SideSlope = 0
            self.depthBelow = 0
            
            self.SlopeL = 0
            self.WidthL = 0
            self.SlopeLC = 0
            self.DepthLC = 0
            self.WidthB = 0
            self.SlopeRC = 0
            self.DepthRC = 0
            self.WidthBR = 0
            self.SlopeR = 0
            
            
            self.C1=0
            self.C2=0
            self.C3=0
            self.C4=0
            
            self.S1=0
            self.S2=0
            self.S3=0
            self.S4=0
            self.BenchBB=0
            self.BenchWW=0
            self.BenchSS=0
            # self.Exp=1.0
            self.plotc=None
            self.connectedLines=[]
            canvas.mpl_connect('draw_event', self.draw_callback)
            # canvas.mpl_connect('button_press_event', self.button_press_callback)
            # canvas.mpl_connect('key_press_event', self.key_press_callback)
            # canvas.mpl_connect('button_release_event', self.button_release_callback)
            # canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
            self.canvas = canvas
            # self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.line)
            self.ax.draw_artist(self.lineSP)
            self.ax.draw_artist(self.lineRT)
            self.canvas.blit(self.ax.bbox)
            
    # def set_line_from_file(self,bottom_slp,exp):
    #     self.expo=exp
    #             self.Exp.grid(row=0,column=0)
                
    #             self.Bottom_slp= tk.Scale(self.profilewindow,from_=0,to=200,resolution=0.1,orient='horizontal',length=500,label = "Bottom Slope",command=self.UpdateSlp)
    #             if self.Slope0 is not None:
    #                 self.Bottom_slp.set(self.Slope0)
    def delete_l(self):
        self.line.set_visible(False)
        self.lineSP.set_visible(False)
        self.lineRT.set_visible(False)
        self.Active=False
        
    def draw_callback(self, event):
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.ax.draw_artist(self.line)
       
    def Tie_in(self,allLines):
        xy0 = self.line.get_xydata()
        x0, y0 = xy0[0, 0], xy0[0, 1]
        for line in allLines:
            if line.ID!=self.ID:
                if self.Linetype=='quadratic':
                    xy=line.lineSP.get_xydata()
                if self.Linetype=='radius':
                    xy=line.lineRT.get_xydata()
                x, y = xy[:, 0], xy[:, 1]
                d = np.hypot(x - x0, y - y0)
                indseq, = np.nonzero(d == d.min())
                ind = indseq[0]
                # print(ind,d[ind],x0,y0)
                print(d[ind])
                if d[ind] <= self.epsilon2:
                    xy0[0,0]=x[ind]
                    xy0[0,1]=y[ind]
                    self.StartElevation=line.S[ind]
                    if ind<x.shape[0]-1:
                        ds=((x[ind+1]*self.Surfaces.cellsize-x[ind]*self.Surfaces.cellsize)**2+(y[ind+1]*self.Surfaces.cellsize-y[ind]*self.Surfaces.cellsize)**2)**0.5
                        # self.Slope0=(ds*self.Surfaces.cellsize)/(line.S[ind+1]-line.S[ind])
                        self.Slope0=ds/(line.S[ind+1]-line.S[ind])
                    else:
                        ds=((x[ind-1]*self.Surfaces.cellsize-x[ind]*self.Surfaces.cellsize)**2+(y[ind-1]*self.Surfaces.cellsize-y[ind]*self.Surfaces.cellsize)**2)**0.5
                        # self.Slope0=(ds*self.Surfaces.cellsize)/(line.S[ind]-line.S[ind-1])
                        self.Slope0=ds/(line.S[ind]-line.S[ind-1])
                        
                    self.line.set_data(xy0.T)

                    # self.Bottom_slp.set(self.Slope0)
                    if not self.ID in line.connectedLines:
                        line.connectedLines.append(self.ID)
                        # self.connectedLines.append(line.ID)
                        
                    self.Sf.DrainIDS.delete(0,tk.END)
                    for pp in self.connectedLines:
                        self.Sf.DrainIDS.insert(0,', ')
                        self.Sf.DrainIDS.insert(0,str(pp))
                        
                    self.Update_Tiein()
                    
    
    def get_ind_under_point(self, event):
        'get the index of the vertex under point if within epsilon tolerance'
        xy = self.line.get_xydata()
        xyt = self.line.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.hypot(xt - event.x, yt - event.y)
        indseq, = np.nonzero(d == d.min())
        ind = indseq[0]
        if d[ind] >= self.epsilon:
            ind = None
        return ind

    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        if not self.showverts:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self._ind = self.get_ind_under_point(event)
        
        self.SlopeL = self.Sf.SlopeL.get()
        self.WidthL = self.Sf.WidthL.get()
        self.SlopeLC = self.Sf.SlopeLC.get()
        self.DepthLC = self.Sf.DepthLC.get()
        self.WidthB = self.Sf.WidthB.get()
        self.SlopeRC = self.Sf.SlopeRC.get()
        self.DepthRC = self.Sf.DepthRC.get()
        self.WidthBR = self.Sf.WidthBR.get()
        self.SlopeR = self.Sf.SlopeR.get()
        self.depthBelow=self.Sf.depthBelow.get()
    
    def set_visible(self,VIS):
        # self.line.
        self.line.set_visible(VIS)
        self.lineSP.set_visible(VIS)
        self.lineRT.set_visible(VIS)
        
        # self.line.set_visible(not self.line.get_visible())
        # self.lineSP.set_visible(not self.lineSP.get_visible())
     
    def button_release_callback(self, event):
        'whenever a mouse button is released'
        if self.Active and self._ind!=None:
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)
            # self.ax.draw_artist(self.poly)
            self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.line)
            self.ax.draw_artist(self.lineSP)
            self.ax.draw_artist(self.lineRT)
            self.canvas.blit(self.ax.bbox)
            # self.canvas.flush_events()
            self.canvas.draw_idle()
            if not self.showverts:
                return
            if event.button != 1:
                return
            self._ind = None
            self.vertical_alignmentUpdate()
            # if self.plotc is not None:
            #     self.UpdateS(1)
    def select(self,event):
        if self.line.get_visible()==True:
            self.Active=False
            self.line.set_color('orange')
            self.lineSP.set_color('orange')
            self.lineRT.set_color('orange')
            xys = self.line.get_transform().transform(self.line.get_xydata())
            p = event.x, event.y  # display coords
            for i in range(len(xys) - 1):
                start = xys[i]
                end = xys[i + 1]
               
                line_vec = vector(start, end)
                pnt_vec = vector(start, p)
                line_len = length(line_vec)
                line_unitvec = unit(line_vec)
                pnt_vec_scaled = scale(pnt_vec, 1.0/line_len)
                t = dot(line_unitvec, pnt_vec_scaled)    
                if t < 0.0:
                    t = 0.0
                elif t > 1.0:
                    t = 1.0
                nearest = scale(line_vec, t)
                d = distance(nearest, pnt_vec)
                if d <= self.epsilon:
                    self.Sf.DrainIDS.delete(0,tk.END)
                    for pp in self.connectedLines:
                        self.Sf.DrainIDS.insert(0,', ')
                        self.Sf.DrainIDS.insert(0,str(pp))
                    self.Sf.DrainLength.delete(0,tk.END)
                    self.Sf.DrainLength.insert(0,int(self.distance2[-1]))
                    self.Sf.CatchArea.delete(0,tk.END)
                    self.Sf.CatchArea.insert(0,self.CA)
                    
                    
                    self.Sf.AllLengths.delete(0,tk.END)
                    self.Sf.AllLengths.insert(0,self.AllLengths)
                    
                    self.Sf.AllDensity.delete(0,tk.END)
                    self.Sf.AllDensity.insert(0,self.AllDensity)
                    
                    self.Sf.DrainDens.delete(0,tk.END)
                    self.Sf.DrainDens.insert(0,self.DrainDense)
                    
                    ## Insert drain width, side slope, total depth and depth below
                    self.Sf.SlopeL.delete(0,tk.END)
                    self.Sf.WidthL.delete(0,tk.END)
                    self.Sf.SlopeLC.delete(0,tk.END)
                    self.Sf.DepthLC.delete(0,tk.END)
                    self.Sf.WidthB.delete(0,tk.END)
                    self.Sf.SlopeRC.delete(0,tk.END)
                    self.Sf.DepthRC.delete(0,tk.END)
                    self.Sf.WidthBR.delete(0,tk.END)
                    self.Sf.SlopeR.delete(0,tk.END)
                    self.Sf.depthBelow.delete(0,tk.END)
                    
                    self.Sf.SlopeL.insert(0,self.SlopeL)
                    self.Sf.WidthL.insert(0,self.WidthL)
                    self.Sf.SlopeLC.insert(0,self.SlopeLC)
                    self.Sf.DepthLC.insert(0,self.DepthLC)
                    self.Sf.WidthB.insert(0,self.WidthB)
                    self.Sf.SlopeRC.insert(0,self.SlopeRC)
                    self.Sf.DepthRC.insert(0,self.DepthRC)
                    self.Sf.WidthBR.insert(0,self.WidthBR)
                    self.Sf.SlopeR.insert(0,self.SlopeR)
                    self.Sf.depthBelow.insert(0,self.depthBelow)
                    
                    print(f"Selected Line ID: {self.ID}")

                    
                    self.Active = not self.Active
                    if self.Active:
                        self.line.set_color('red')
                        self.lineSP.set_color('red')
                        self.lineRT.set_color('red')
                    else:
                        self.line.set_color('orange')
                        self.lineSP.set_color('orange')
                        self.lineRT.set_color('orange')
                    break
    def onEntryClick(self,event):
        a=self.SlopeOp.get()
        if a=='Exponential Slope':
            self.UpdateSlp(1)
        if a=='Benched':
            self.UpdateBench()
        if a=='Linear Sections':
            self.C1=float(self.Chainage1.get())
            self.C2=float(self.Chainage2.get())
            self.C3=float(self.Chainage3.get())
            self.C4=float(self.Chainage4.get())
            
            self.S1=float(self.Slope1.get())
            self.S2=float(self.Slope2.get())
            self.S3=float(self.Slope3.get())
            self.S4=float(self.Slope4.get())
            print((self.S1,self.S2,self.S3))
            self.UpdateLinearSection()
        print('entry changed')           
    def onEntryClickVar(self,var,index,mode):
        a=self.SlopeOp.get()
        if a=='Exponential Slope':
            self.UpdateSlp(1)
        # if a=='Benched':
        #     self.UpdateBench()
        # if a=='Varied Benches':
        #     self.UpdateBenchVar()
        if a=='Linear Sections':
            self.C1=float(self.Chainage1.get())
            self.C2=float(self.Chainage2.get())
            self.C3=float(self.Chainage3.get())
            self.C4=float(self.Chainage4.get())
            
            self.S1=float(self.Slope1.get())
            self.S2=float(self.Slope2.get())
            self.S3=float(self.Slope3.get())
            self.S4=float(self.Slope4.get())
            print((self.S1,self.S2,self.S3))
            self.UpdateLinearSection()
        if a=='Set to Design':
            self.Set_to_Design()
        if a=='Set to Survey':
            self.Set_to_Survey()
    def key_press_callback(self, event):
       
        'whenever a key is pressed'
        if not event.inaxes:
            return
        if self.line.get_visible():
            if event.key == 'd':
                ind = self.get_ind_under_point(event)
                if ind is not None:
                    xy=self.line.get_xydata()
                    xy=np.delete(xy,ind, axis=0)
                    self.line.set_data(xy.T)
                   
            elif event.key == 'i':
                xys = self.line.get_transform().transform(self.line.get_xydata())
                p = event.x, event.y  # display coords
                self.StrtE = None
                for i in range(len(xys) - 1):
                    start = xys[i]
                    end = xys[i + 1]
                   
                    line_vec = vector(start, end)
                    pnt_vec = vector(start, p)
                    line_len = length(line_vec)
                    line_unitvec = unit(line_vec)
                    pnt_vec_scaled = scale(pnt_vec, 1.0/line_len)
                    t = dot(line_unitvec, pnt_vec_scaled)    
                    if t < 0.0:
                        t = 0.0
                    elif t > 1.0:
                        t = 1.0
                    nearest = scale(line_vec, t)
                    d = distance(nearest, pnt_vec)
                   
                    if d <= self.epsilon:
                        xy0=np.insert(self.line.get_xydata(), i+1,[event.xdata, event.ydata],axis=0)
                        self.line.set_data(xy0.T)
                        print(self.line.set_data(xy0.T))
                        break
                    # self.draw_callback(1)
                    # self.ax.draw_artist(self.line)
                    # self.ax.draw_artist(self.lineSP)
                    # self.canvas.blit(self.ax.bbox)
                   
            elif event.key == 'a':
                if self.line.get_visible()==True:
                    xys = self.line.get_transform().transform(self.line.get_xydata())
                    p = event.x, event.y  # display coords
                    for i in range(len(xys) - 1):
                        start = xys[i]
                        end = xys[i + 1]
                       
                        line_vec = vector(start, end)
                        pnt_vec = vector(start, p)
                        line_len = length(line_vec)
                        line_unitvec = unit(line_vec)
                        pnt_vec_scaled = scale(pnt_vec, 1.0/line_len)
                        t = dot(line_unitvec, pnt_vec_scaled)    
                        if t < 0.0:
                            t = 0.0
                        elif t > 1.0:
                            t = 1.0
                        nearest = scale(line_vec, t)
                        d = distance(nearest, pnt_vec)
                        if d <= self.epsilon:
                            self.Active = not self.Active
                            if self.Active:
                                self.line.set_color('r')
                                self.lineSP.set_color('r')
                                self.lineRT.set_color('r')
                            else:
                                self.line.set_color('orange')
                                self.lineSP.set_color('orange')
                                self.lineRT.set_color('orange')
                            break
           
            
            elif event.key == 'e' and self.Active:
                self.vertical_alignment()
    
    def spinchanged(self):
        self.a.set_aspect(self.spin.get())
        self.a.set_ylim([-15/int(self.spin.get())+self.miny,15/int(self.spin.get())+self.maxy])
        self.a.set_xlim([self.minx,self.maxx])

        if self.show_perp_section.get()==1:
            self.b.set_aspect(self.spin.get())

        self.canvasp.draw_idle() 
    
    def change_vertical_alignment_frame(self, *args):
        # for s in self.subframes:
        #     s.grid_forget()
        
        option = self.SlopeOp.get()
        
        self.Step_point.grid_forget()
        self.Bottom_slp.grid_forget()
        self.Exp.grid_forget()
        
        self.labelBenchE.grid_forget()
        self.BenchE.grid_forget()
        self.labelBenchW.grid_forget()
        self.BenchW.grid_forget()
        self.labelBenchS.grid_forget()
        self.BenchS.grid_forget()
        self.ApplyBench.grid_forget()
        
        self.labelLSC.grid_forget()
        self.labelLSS.grid_forget()
        self.Chainage1.grid_forget()
        self.Chainage2.grid_forget()
        self.Chainage3.grid_forget()
        self.Chainage4.grid_forget()
        self.Slope1.grid_forget()
        self.Slope2.grid_forget()
        self.Slope3.grid_forget()
        self.Slope4.grid_forget()
        
        
        if option == "Exponential Slope":
            self.Step_point.grid(row=3,column=4,rowspan=2,columnspan=2,sticky="nesw",pady=1,padx=1)
            self.Bottom_slp.grid(row=3,column=2,rowspan=2,columnspan=2,sticky="nesw",pady=1,padx=1)
            self.Exp.grid(row=3,column=0,rowspan=2,columnspan=2,sticky="nesw",pady=1,padx=1)
        
        elif option == "Varied Benches":
            self.labelBenchE.grid(row=3,column=2,sticky="nesw",pady=1,padx=1)
            self.BenchE.grid(row=4,column=2,sticky="nesw",pady=1,padx=1)
            self.labelBenchW.grid(row=3,column=3,sticky="nesw",pady=1,padx=1)
            self.BenchW.grid(row=4,column=3,sticky="nesw",pady=1,padx=1)
            self.labelBenchS.grid(row=3,column=4,sticky="nesw",pady=1,padx=1)
            self.BenchS.grid(row=4,column=4,sticky="nesw",pady=1,padx=1)
            self.ApplyBench.grid(row=3,column=0,sticky="nesw",pady=1,padx=1,rowspan=2,columnspan=2)
        
        elif option == "Linear Sections":
            self.labelLSC.grid(row=3,column=0,sticky="nesw",pady=1,padx=1)
            self.labelLSS.grid(row=4,column=0,sticky="nesw",pady=1,padx=1)
            
            self.Chainage1.grid(row=3,column=1,sticky="nesw",pady=1,padx=1)
            self.Chainage2.grid(row=3,column=2,sticky="nesw",pady=1,padx=1)
            self.Chainage3.grid(row=3,column=3,sticky="nesw",pady=1,padx=1)
            self.Chainage4.grid(row=3,column=4,sticky="nesw",pady=1,padx=1)
            self.Slope1.grid(row=4,column=1,sticky="nesw",pady=1,padx=1)
            self.Slope2.grid(row=4,column=2,sticky="nesw",pady=1,padx=1)
            self.Slope3.grid(row=4,column=3,sticky="nesw",pady=1,padx=1)
            self.Slope4.grid(row=4,column=4,sticky="nesw",pady=1,padx=1)
        
        
        else: #option == "Set to Design" or "Set to Survey"
            pass
        
    
    def show_perp_section_InWindow(self):
        self.show_perpendicular_cross_section('InWindow')
        
    def show_perp_section_OutWindow(self):
        self.show_perpendicular_cross_section('OutWindow')
    

    
    def show_perpendicular_cross_section(self,command):
        if command == 'InWindow' and self.show_perp_section.get()==1:
            if self.show_perp_section_window.get()==1:
                self.remove_perp_window()
            
            #Add InWindow
            gs = gridspec.GridSpec(1,2)
            self.a.set_position(gs[0:1].get_position(self.f))
            self.b = self.f.add_subplot(gs[1])

            self.plot_cross_section(0)    
            self.canvasp.draw()
            
        elif command == 'OutWindow' and self.show_perp_section_window.get()==1:
            if self.show_perp_section.get()==1:
                self.remove_perp_subplot()
            
            ##Add OutWindow
            self.perp_profilewindow = tk.Toplevel(self.Sf)
            self.perp_profilewindow.protocol('WM_DELETE_WINDOW', self.remove_perp_window) #Protocol to delete frame if window closed on top right
            
            self.windowfigure = Figure()
            self.b = self.windowfigure.add_subplot(111)
            self.canvasp1 = FigureCanvasTkAgg(self.windowfigure, self.perp_profilewindow)
            self.canvasp1.get_tk_widget().grid(row=0, column=0,columnspan=10,pady=20,sticky=tk.NSEW)
            self.windowfigure.subplots_adjust(left=0.1, right=0.9, top=0.99, bottom=0.1)
            self.plot_cross_section(0)    
            self.canvasp1.draw()
            
            
        else: ## Close all open windows
            self.remove_perp_subplot() 
            self.remove_perp_window()
            
        
    def remove_perp_window(self):
        try: self.windowfigure.delaxes(self.b)       
        except: pass
        self.perp_profilewindow.destroy()
        # self.perp_profilewindow = None
        self.ShowPerpSectionw.deselect()
   
    def remove_perp_subplot(self):
        try: 
            self.f.delaxes(self.b)   
            gs = gridspec.GridSpec(1,2)
            self.a.set_position(gs[0:2].get_position(self.f))
            self.canvasp.draw_idle()
        except: pass
        
        self.ShowPerpSection.deselect()

 
    def vertical_alignment(self):
        self.profilewindow = tk.Toplevel(self.Sf)
        self.profilewindow.grid_columnconfigure(6,weight=1) # the text and entry frames column
        # self.profilewindow.grid_rowconfigure(5,weight=1) # all frames row_
        
        self.SlopeOp=tk.StringVar()
        self.SlopeOp.set("Exponential Slope")
        self.SlopeOptionsVar=tk.StringVar(value='Exponential Slope')
        self.SlopeOptions=tk.OptionMenu(self.profilewindow,self.SlopeOp,"Exponential Slope","Varied Benches","Linear Sections","Set to Design","Set to Survey",command=self.change_vertical_alignment_frame)
        self.SlopeOptions.config(relief='solid',borderwidth=1,width=50, height=2)
        self.SlopeOptions.grid(row=0,column=0, rowspan=2, columnspan=2,sticky='nesw') #padx=3
        self.SlopeOp.trace("w",self.onEntryClickVar)
        
        self.AnnotESV=tk.StringVar()
        self.AnnotESV.set("Elevations")
        self.AnnotESV=tk.StringVar(value='Elevations')
        self.AnnotES=tk.OptionMenu(self.profilewindow,self.AnnotESV,"Elevations","Slopes")
        self.AnnotES.config(relief='solid',borderwidth=1,width=50, height=2)
        self.AnnotES.grid(row=0,column=2, rowspan=2, columnspan=2,sticky='nesw') #padx=3
        
        self.show_perp_section = tk.IntVar()
        self.ShowPerpSection = tk.Checkbutton(self.profilewindow, variable = self.show_perp_section,text = "Show Perpendicular Cross Section (On this Window)", onvalue = 1, offvalue=0, command=self.show_perp_section_InWindow)
        self.ShowPerpSection.grid(row=0,column=5,rowspan=1)
        
        self.perp_profilewindow = None
        self.show_perp_section_window = tk.IntVar()
        self.ShowPerpSectionw = tk.Checkbutton(self.profilewindow, variable = self.show_perp_section_window,text = "Show Perpendicular Cross Section (External Window)", onvalue = 1, offvalue=0, command=self.show_perp_section_OutWindow)
        self.ShowPerpSectionw.grid(row=1,column=5,rowspan=1)
        
        
        sep = Separator(self.profilewindow, orient="horizontal")
        sep.grid(column=0, row=2, sticky="ew",columnspan=10)
        
        sep1 = Separator(self.profilewindow, orient="horizontal")
        sep1.grid(column=0, row=6, sticky="ew",columnspan=10)
        
        
        
        ### Exponential Slope        
        self.Exp= tk.Scale(self.profilewindow,from_=0,to=10,resolution=0.1,orient='horizontal',length=200,label = "Exponent",command=self.UpdateExp)
        self.Exp.set(self.expo)

        self.Bottom_slp= tk.Scale(self.profilewindow,from_=0,to=400,resolution=0.1,orient='horizontal',length=200,label = "Bottom Slope",command=self.UpdateSlp)
        if self.Slope0 is not None:
            self.Bottom_slp.set(self.Slope0)
        else:
            self.Bottom_slp.set(5.0)
        
        self.Step_point= tk.Scale(self.profilewindow,from_=0,to=1,resolution=0.01,orient='horizontal',length=200,label = "Step Point ratio from top",command=self.UpdateSlp)
        if self.Step is not None:
            self.Step_point.set(self.Step)
        else:
            self.Step_point.set(1.0)
            
        
        self.Step_point.grid(row=3,column=4,rowspan=2,columnspan=2,sticky="nesw",pady=1,padx=1)
        self.Bottom_slp.grid(row=3,column=2,rowspan=2,columnspan=2,sticky="nesw",pady=1,padx=1)
        self.Exp.grid(row=3,column=0,rowspan=2,columnspan=2,sticky="nesw",pady=1,padx=1)
        
        ### Bench old version
        # labelBH = tk.Label(self.profilewindow, text="Batter Height")
        # labelBH.grid(row=4,column=0)
        
    
        # self.BenchHeight=tk.Entry(self.profilewindow)
        # self.BenchHeight.delete(0,tk.END)
        # self.BenchHeight.insert(0,self.BHeight)
        # self.BenchHeight.grid(row=4,column=1)
        # self.BenchHeight.bind("<KeyRelease>",self.onEntryClick)
        
        # labelBW = tk.Label(self.profilewindow, text="Bench Width")
        # labelBW.grid(row=4,column=2)
        # self.BenchWidth=tk.Entry(self.profilewindow)
        # self.BenchWidth.delete(0,tk.END)
        # self.BenchWidth.insert(0,self.BWidth)
        # self.BenchWidth.grid(row=4,column=3)
        # self.BenchWidth.bind("<KeyRelease>",self.onEntryClick)
        
        # labelBO = tk.Label(self.profilewindow, text="Bench vertical Offset")
        # labelBO.grid(row=4,column=4)
        # self.BenchOffset=tk.Entry(self.profilewindow)
        # self.BenchOffset.delete(0,tk.END)
        # self.BenchOffset.insert(0,self.BOff)
        # self.BenchOffset.grid(row=4,column=5)
        # self.BenchOffset.bind("<KeyRelease>",self.onEntryClick)
        
        # labelBS = tk.Label(self.profilewindow, text="Batter Slope")
        # labelBS.grid(row=4,column=6)
        # self.BatterSlope=tk.Entry(self.profilewindow)
        # self.BatterSlope.delete(0,tk.END)
        # self.BatterSlope.insert(0,self.Bslope)
        # self.BatterSlope.grid(row=4,column=7)
        # self.BatterSlope.bind("<KeyRelease>",self.onEntryClick)
        
        


        ### Linear Slope
        self.labelLSS = tk.Label(self.profilewindow, text="Gradient")
        self.labelLSC = tk.Label(self.profilewindow, text="Linear Slope Chainage End")

        
        self.Chainage1=tk.Entry(self.profilewindow)
        self.Chainage1.delete(0,tk.END)
        self.Chainage1.insert(0,self.C1)
        self.Chainage1.bind("<KeyRelease>",self.onEntryClick)
        
        self.Chainage2=tk.Entry(self.profilewindow)
        self.Chainage2.delete(0,tk.END)
        self.Chainage2.insert(0,self.C2)
        self.Chainage2.bind("<KeyRelease>",self.onEntryClick)
        
        self.Chainage3=tk.Entry(self.profilewindow)
        self.Chainage3.delete(0,tk.END)
        self.Chainage3.insert(0,self.C3)
        self.Chainage3.bind("<KeyRelease>",self.onEntryClick)
        
        self.Chainage4=tk.Entry(self.profilewindow)
        self.Chainage4.delete(0,tk.END)
        self.Chainage4.insert(0,self.C4)
        self.Chainage4.bind("<KeyRelease>",self.onEntryClick)
        
        self.Slope1=tk.Entry(self.profilewindow)
        self.Slope1.delete(0,tk.END)
        self.Slope1.insert(0,self.S1)
        self.Slope1.bind("<KeyRelease>",self.onEntryClick)
        
        self.Slope2=tk.Entry(self.profilewindow)
        self.Slope2.delete(0,tk.END)
        self.Slope2.insert(0,self.S2)
        self.Slope2.bind("<KeyRelease>",self.onEntryClick)
        
        self.Slope3=tk.Entry(self.profilewindow)
        self.Slope3.delete(0,tk.END)
        self.Slope3.insert(0,self.S3)
        self.Slope3.bind("<KeyRelease>",self.onEntryClick)
        
        self.Slope4=tk.Entry(self.profilewindow)
        self.Slope4.delete(0,tk.END)
        self.Slope4.insert(0,self.S4)
        self.Slope4.bind("<KeyRelease>",self.onEntryClick)
        
        
        ### Varied Benches
        self.labelBenchE = tk.Label(self.profilewindow, text="Bench Elevation Ranges")
        self.BenchE=tk.Entry(self.profilewindow)
        self.BenchE.delete(0,tk.END)
        self.BenchE.insert(0,self.BenchBB)
        self.BenchE.bind("<KeyRelease>",self.onEntryClick)

        self.labelBenchW = tk.Label(self.profilewindow, text="Bench Width")
        self.BenchW=tk.Entry(self.profilewindow)
        self.BenchW.delete(0,tk.END)
        self.BenchW.insert(0,self.BenchWW)
        self.BenchW.bind("<KeyRelease>",self.onEntryClick)

        self.labelBenchS = tk.Label(self.profilewindow, text="Batter Slope")
        self.BenchS=tk.Entry(self.profilewindow)
        self.BenchS.delete(0,tk.END)
        self.BenchS.insert(0,self.BenchSS)
        self.BenchS.bind("<KeyRelease>",self.onEntryClick)
        
        self.ApplyBench = tk.Button(self.profilewindow, text="Visualise Benches", command=lambda: self.UpdateBenchVar())
        
        
        ### Place holder labe;
        self.blanklabel1 = tk.Label(self.profilewindow, text="                  ")
        self.blanklabel1.grid(row=0,column=6,rowspan=5,columnspan=4)
        
        
        
        self.f = Figure()
        self.a = self.f.add_subplot(111)
        self.canvasp = FigureCanvasTkAgg(self.f, self.profilewindow)
        self.canvasp.get_tk_widget().grid(row=7, column=0,columnspan=10,pady=20,sticky=tk.NSEW)
        self.f.subplots_adjust(left=0.1, right=0.9, top=0.99, bottom=0.1)
       
        
        
        labelspin = tk.Label(self.profilewindow, text="Vertical Exaggeration")
        labelspin.grid(row=0,column=4)
        self.spin=tk.Spinbox(self.profilewindow,from_=1,to=20,command=self.spinchanged)
        self.spin.grid(row=1,column=4)
        self.spin.config(width=25)
        
        if self.StartElevation is None:
            self.StartElevation=self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]
        
        self.plota,=self.a.plot(self.distance2,self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
        self.plotb,=self.a.plot(self.distance2,self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
        self.plotc,=self.a.plot([self.distance2[0],self.distance2[-1]],[self.StartElevation,self.Surfaces.Design[self.interpolated_points.astype(int)[-1,1],self.interpolated_points.astype(int)[-1,0]]])
        self.UpdateS(1)

        self.annot = self.a.annotate("", xy=(self.distance2[0],-5+self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]), xytext=(0,-10),textcoords="data",color='white',bbox=dict(boxstyle="round", fc="blue"),arrowprops=dict(arrowstyle="->",color='blue',alpha=0.9),xycoords='data')
        self.annot2 = self.a.annotate("", xy=(self.distance2[0],-10+self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]), xytext=(0,-15),textcoords="data",color='white',bbox=dict(boxstyle="round", fc="orange"),arrowprops=dict(arrowstyle="->",color='orange',alpha=0.9),xycoords='data')
        self.annot3 = self.a.annotate("", xy=(self.distance2[0],-15+self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]), xytext=(0,-20),textcoords="data",color='white',bbox=dict(boxstyle="round", fc="green"),arrowprops=dict(arrowstyle="->",color='green',alpha=0.9),xycoords='data')
        
        self.annotSlope = self.a.annotate("", xy=(self.distance2[-1],self.Surfaces.Design[self.interpolated_points.astype(int)[-1,1],self.interpolated_points.astype(int)[-1,0]]), xytext=(-20,-50),textcoords="offset points",bbox=dict(boxstyle="round", fc="w"),arrowprops=dict(arrowstyle="->",color='red'))
        self.minx=0
        self.maxx=self.distance2[-1]
        self.miny=min([min(i for i in self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]] if i > 0),min(i for i in self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]] if i > 0)])
        self.maxy=max([max(self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]),max(self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])])
        self.a.set_ylim([-15/int(self.spin.get())+self.miny,15/int(self.spin.get())+self.maxy])
        self.a.grid(True)
        self.a.set_aspect(1)
        self.vertical_alignmentUpdate()

            
        self.resetzoom = True
        self.annot.set_visible(False)
        self.canvasp.draw()
        self.canvasp.mpl_connect('motion_notify_event', self.mouse_move)
        self.canvasp.mpl_connect('scroll_event', self.zoom)
        self.canvasp.mpl_connect('button_press_event',self.onPress)
        self.canvasp.mpl_connect('button_release_event',self.onRelease)
        self.canvasp.mpl_connect('motion_notify_event',self.onMotion)

        
        self.plotActive=True
     
    def vertical_alignmentUpdate(self):
              
        
        #Cross Section
        #Pulling line coordinates
        if self.Linetype=='quadratic':
            xy=self.lineSP.get_xydata()
        if self.Linetype=='radius':
            xy=self.lineRT.get_xydata()
        
        #Width of the displayed cross section    
        SecWid=int(50/self.Surfaces.cellsize)
        self.SecWid=SecWid

        #Resolution of sampling, how many interpolated points per cell
        res=20
        self.res=res
        
        #Creating array for the grid
        #SecWid*res+1 because cross section is from -SecWid/2 to 0 to +Secwid/2
        #crossdata(eachpoint on drain length, cross section points, (x,y) of each point along cross section)
        self.crossdata=np.zeros((int(float(self.Sf.DrainLength.get())/self.Surfaces.cellsize),SecWid*res+1,2))
        
        #Finding max and min of the drain to set up sampling grid for interpolation
        #print(f"Max x:{max(xy[:,0])}, Min x:{min(xy[:,0])}, Max y:{max(xy[:,1])}, Min y:{min(xy[:,1])}")
        upperlimitx = int(max(xy[:,0])+int(SecWid))
        lowerlimitx = int(min(xy[:,0])-int(SecWid))
        upperlimity = int(max(xy[:,1])+int(SecWid))
        lowerlimity = int(min(xy[:,1])-int(SecWid))
        
        #Checking for limits outside the TIF surface
        if upperlimitx > self.Surfaces.Design.shape[1]:
            upperlimitx =self.Surfaces.Design.shape[1]
        if lowerlimitx < 0:
            lowerlimitx = 0
        if upperlimity > self.Surfaces.Design.shape[0]:
            upperlimity = self.Surfaces.Design.shape[0]
        if lowerlimity < 0:
            lowerlimity = 0
         
        print((lowerlimitx,lowerlimity,upperlimitx,upperlimity))
        print((self.Surfaces.maxcol,self.Surfaces.maxrow))
        #Creating Interpolation Grid Limits - made bigger than cross section width to avoid issues with edges of interpolation grid
        xlist = np.array(range(lowerlimitx,upperlimitx))
        ylist = np.array(range(lowerlimity,upperlimity))
        
        #Creating elevation grid
        zlist_survey = self.Surfaces.Survey[lowerlimity:upperlimity,lowerlimitx:upperlimitx]
        zlist_design = self.Surfaces.Design[lowerlimity:upperlimity,lowerlimitx:upperlimitx]
        print(zlist_design.shape)
        print(zlist_survey.shape)
        
        #Creating interpolator functions
        self.survinterp = interpolate.interp2d(xlist,ylist,zlist_survey,kind='linear')
        self.desinterp = interpolate.interp2d(xlist,ylist,zlist_design,kind='linear')
        # self.survinterp = interpolate.RectBivariateSpline(xlist,ylist,zlist_survey)
        # self.desinterp = interpolate.RectBivariateSpline(xlist,ylist,zlist_design)
        self.bvec=np.zeros((int(int(self.Sf.DrainLength.get())/self.Surfaces.cellsize),2))
        
        for k in range(0,int(int(self.Sf.DrainLength.get())/self.Surfaces.cellsize)):
            #Finding the vector that points in the direction of the drain at point k along the drain
            if k==0:
                a=[self.interpolated_points[k,0]-self.interpolated_points[k+1,0],self.interpolated_points[k,1]-self.interpolated_points[k+1,1]]
            elif k==np.size(self.interpolated_points, axis=0)-1:
                a=[-self.interpolated_points[k,0]+self.interpolated_points[k-1,0],-self.interpolated_points[k,1]+self.interpolated_points[k-1,1]]
            else:
                a=[self.interpolated_points[k-1,0]-self.interpolated_points[k+1,0],self.interpolated_points[k-1,1]-self.interpolated_points[k+1,1]]
            
            #Calculating b, the perpendicular vector of a
            b = np.cross([a[0],a[1],0],[0,0,1])
            b =  b/norm(b)
            self.bvec[k] = [b[0],b[1]] #might need to swap the x and y
            
            
            #Flipping of the b vector so that it always points to the same side of the drain
            if k>0:
                b_old=self.bvec[k-1]
            else:
                b_old=[1,1]
                    
            
            #Defining the x and y position lists of the cross section at each point k
            for j in np.arange(0,int(res*SecWid+1)):
                # print(self.crossdata.shape)
                # print(int(res*SecWid+1))
                # print(int(int(self.Sf.DrainLength.get())/self.Surfaces.cellsize))
                dist=-SecWid/2 + j/res
                
                self.crossdata[k,-(j+1),0] = self.interpolated_points[k,0] + dist*b[0]
                self.crossdata[k,-(j+1),1] = self.interpolated_points[k,1] + dist*b[1]
       
        
    def plot_cross_section(self,k):
        SecWid=self.SecWid
        res=self.res
        b=self.bvec[k]
        
        #X-axis values for the plot
        distancecross = np.arange(self.Surfaces.cellsize*SecWid/2,-self.Surfaces.cellsize*SecWid/2-0.00000001,-self.Surfaces.cellsize/res)
        self.distancecross=distancecross
        
        #Interpolating an irregular grid (x spacings varying from y spacing) who's diagonal defines the cross section
        surveycross = self.survinterp(self.crossdata[k,:,0],self.crossdata[k,:,1])
        designcross = self.desinterp(self.crossdata[k,:,0],self.crossdata[k,:,1])
    
        #Only the diagonal entries have the line heights and then squeeze into a 1D array
        #Interpolation output is always ordered from lowest x and y to highest, so the diagonal corresponding to the line depends on the vector of the line b
        #Thus, the output is manipulated so that the correct diagonal and order is extracted
        
        #Vector in 1st quadrant corresponds to diagonal but in reverse direction (don't ask why...) (\)
        if b[0]>=0 and b[1]>=0:
            self.surveysections=np.squeeze(np.diag(np.array(surveycross)))[::-1]
            self.designsections=np.squeeze(np.diag(np.array(designcross)))[::-1]
        #Vector in the 3rd quadrant corresponds to diagonal in forwards direction (\)
        elif b[0]<=0 and b[1]<=0:
            self.surveysections=np.squeeze(np.diag(np.array(surveycross)))
            self.designsections=np.squeeze(np.diag(np.array(designcross)))
        #Vector in 2nd quadrant corresponds to diagonal running from top right of array to bottom left (/)
        elif b[0]<0 and b[1]>0:
            self.surveysections=np.squeeze(np.diag(np.flip(np.array(surveycross),0)))
            self.designsections=np.squeeze(np.diag(np.flip(np.array(designcross),0)))
        #Vector in 4th quadrant corresponds to diagonal running from bottom left of array to top right (/)
        else:
            self.surveysections=np.squeeze(np.diag(np.flip(np.array(surveycross),1)))
            self.designsections=np.squeeze(np.diag(np.flip(np.array(designcross),1)))
        
        #Plotting
        self.b.clear()
        self.plote,=self.b.plot(self.distancecross,self.designsections,marker='o',markevery=int(np.size(self.distancecross,axis=0)))
        self.plotd,=self.b.plot(self.distancecross,self.surveysections,marker='o',markevery=int(np.size(self.distancecross,axis=0)))
        
        self.b.set_xticks([-25,-20,-15,-10,-5,0,5,10,15,20,25], minor=False)
        self.b.invert_xaxis     
        self.b.grid(True)
        self.b.set_ylim([-5/int(self.spin.get())+np.amin(self.designsections),5/int(self.spin.get())+np.amax(self.designsections)])
        self.b.set_aspect(self.spin.get())   
        
        
    
    
    def zoom(self,event):
        # get the current x and y limits
        base_scale=2
        cur_xlim = self.a.get_xlim()
        cur_ylim = self.a.get_ylim()
        cur_xrange = (cur_xlim[1] - cur_xlim[0])*.5
        cur_yrange = (cur_ylim[1] - cur_ylim[0])*.5
        xdata = event.xdata # get event x location
        ydata = event.ydata # get event y location
        if event.button == 'up':
            # deal with zoom in
            self.resetzoom = False
            self.scale_factor = 1/base_scale
            
            self.a.set_xlim([xdata - cur_xrange*self.scale_factor, xdata + cur_xrange*self.scale_factor])
            self.a.set_ylim([ydata - cur_yrange*self.scale_factor, ydata + cur_yrange*self.scale_factor])
            
        elif event.button == 'down' and self.resetzoom==False:
            # deal with zoom out
            self.scale_factor = base_scale
            self.a.set_xlim([xdata - cur_xrange*self.scale_factor, xdata + cur_xrange*self.scale_factor])
            self.a.set_ylim([ydata - cur_yrange*self.scale_factor, ydata + cur_yrange*self.scale_factor])
        else:
            pass        
        
        #If zoom out further than current vertical exaggeration, reset view
        if cur_yrange*self.scale_factor > (15/int(self.spin.get())+self.maxy -  (-15/int(self.spin.get())+self.miny)):
            self.resetzoom = True
            self.a.set_aspect(self.spin.get())
            self.a.set_ylim([-15/int(self.spin.get())+self.miny,15/int(self.spin.get())+self.maxy])
            self.a.set_xlim([self.minx,self.maxx])

        # self.a.figure.canvasp.draw()
        self.canvasp.draw_idle()
        
    def onPress(self,event):
        if event.inaxes != self.a: return
        self.cur_xlim = self.a.get_xlim()
        self.cur_ylim = self.a.get_ylim()
        self.press = self.x0, self.y0, event.xdata, event.ydata
        self.x0, self.y0, self.xpress, self.ypress = self.press
        

    def onRelease(self,event):
        self.press = None
        self.canvasp.draw_idle()

    def onMotion(self,event):
        if self.press is None: return
        if event.inaxes != self.a: return
        dx = event.xdata - self.xpress
        dy = event.ydata - self.ypress
        self.cur_xlim -= dx
        self.cur_ylim -= dy
        self.a.set_xlim(self.cur_xlim)
        self.a.set_ylim(self.cur_ylim)

        self.canvasp.draw_idle()
        
    
    def mouse_move(self,event):
        x, y = event.xdata, event.ydata
        if event.inaxes:
            if x<0:
                x=0.1
            if self.AnnotESV.get()=='Elevations':    
                self.update_annot(x)
            if self.AnnotESV.get()=='Slopes':    
                self.update_annotS(x)
            self.annot.set_visible(True)
            self.annot2.set_visible(True)
            self.annot3.set_visible(True)
            self.canvasp.draw_idle()
            if self.show_perp_section_window.get()==1:  
                self.canvasp1.draw_idle()
        
        # print(x, y)    

    def update_annot(self,x):
        y=np.interp(x,self.distance2,self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
        y2=np.interp(x,self.distance2,self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
        self.Surv=y2
        self.miny=min([min(i for i in self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]] if i > 0),min(i for i in self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]] if i > 0)])
        self.maxy=max([max(self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]),max(self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])])
        y3=np.interp(x,self.distance2,self.S)
        if x is not None:
            index, = np.where((self.distance2<x))
            x1=self.interpolated_points.astype(int)[index[-1],0]
            y1=self.interpolated_points.astype(int)[index[-1],1]
            self.dot.draw_dot([self.crossdata[index[-1],0,0],self.crossdata[index[-1],-1,0]],[self.crossdata[index[-1],0,1],self.crossdata[index[-1],-1,1]])
            if self.show_perp_section.get()==1 or self.show_perp_section_window.get()==1:
                self.plot_cross_section(index[-1])
         
        yy3=self.miny-10/int(self.spin.get())
        yy2=self.miny+(self.maxy-self.miny)*0.5
        yy=self.maxy+10/int(self.spin.get())
        
        self.annot.xy = ((x,y))
        self.annot2.xy = ((x,y2))
        self.annot3.xy = ((x,y3))
        
        if y>=y2 and y>=y3:
            if y2>y3:
                self.annot.set_position([x,yy])
                self.annot2.set_position([x,yy2])
                self.annot3.set_position ([x,yy3])
            else:
                self.annot.set_position([x,yy])
                self.annot2.set_position([x,yy3])
                self.annot3.set_position ([x,yy2])
                
        if y2>=y and y2>=y3:
            if y>y3:
                self.annot.set_position([x,yy2])
                self.annot2.set_position([x,yy])
                self.annot3.set_position ([x,yy3])
            else:
                self.annot.set_position([x,yy3])
                self.annot2.set_position([x,yy])
                self.annot3.set_position ([x,yy2]) 
                
        if y3>=y and y3>=y2:
            if y>y2:
                self.annot.set_position([x,yy2])
                self.annot2.set_position([x,yy3])
                self.annot3.set_position ([x,yy])
            else:
                self.annot.set_position([x,yy3])
                self.annot2.set_position([x,yy2])
                self.annot3.set_position ([x,yy]) 
        text = str('%.2f' % y)
        text2 = str('%.2f' % y2)
        text3 = str('%.2f' % y3)
        self.annot.set_text(text)
        self.annot2.set_text(text2)
        self.annot3.set_text(text3)
        
    def update_annotS(self,x):
        y=np.interp(x,self.distance2,self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
        yb=np.interp(x+1,self.distance2,self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
        if yb-y!=0:
            s1=abs(1/(yb-y))
        else:
            s1=0
        y2=np.interp(x,self.distance2,self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
        y2b=np.interp(x+1,self.distance2,self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
        if y2b-y2!=0:
            s2=abs(1/(y2b-y2))
        else:
            s2=0
        self.Surv=y2
        self.miny=min([min(i for i in self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]] if i > 0),min(i for i in self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]] if i > 0)])
        self.maxy=max([max(self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]),max(self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])])
        y3=np.interp(x,self.distance2,self.S)
        y3b=np.interp(x+1,self.distance2,self.S)
        if y3b-y3!=0:
            s3=abs(1/(y3b-y3))
        else:
            s3=0
        if x is not None:
            index, = np.where((self.distance2<x))
            # self.k=index
            x1=self.interpolated_points.astype(int)[index[-1],0]
            y1=self.interpolated_points.astype(int)[index[-1],1]
            self.dot.draw_dot(x1,y1)
            
            #not working
            # self.crossline = Line2D(self.crossdata[self.k,0],self.crossdata[self.k,-1], animated=False,ls='--',color='y')
            # self.ax.add_artist(self.crossline)
            # self.ax.draw_artist(self.crossline)
            
        yy3=self.miny-10/int(self.spin.get())
        yy2=self.miny+(self.maxy-self.miny)*0.5/int(self.spin.get())
        yy=self.maxy+10/int(self.spin.get())
        
        self.annot.xy = ((x,y))
        self.annot2.xy = ((x,y2))
        self.annot3.xy = ((x,y3))
        
        if y>=y2 and y>=y3:
            if y2>y3:
                self.annot.set_position([x,yy])
                self.annot2.set_position([x,yy2])
                self.annot3.set_position ([x,yy3])
            else:
                self.annot.set_position([x,yy])
                self.annot2.set_position([x,yy3])
                self.annot3.set_position ([x,yy2])
                
        if y2>=y and y2>=y3:
            if y>y3:
                self.annot.set_position([x,yy2])
                self.annot2.set_position([x,yy])
                self.annot3.set_position ([x,yy3])
            else:
                self.annot.set_position([x,yy3])
                self.annot2.set_position([x,yy])
                self.annot3.set_position ([x,yy2]) 
                
        if y3>=y and y3>=y2:
            if y>y2:
                self.annot.set_position([x,yy2])
                self.annot2.set_position([x,yy3])
                self.annot3.set_position ([x,yy])
            else:
                self.annot.set_position([x,yy3])
                self.annot2.set_position([x,yy2])
                self.annot3.set_position ([x,yy]) 
        text = str('%.2f' % s1)
        text2 = str('%.2f' % s2)
        text3 = str('%.2f' % s3)
        self.annot.set_text(text)
        self.annot2.set_text(text2)
        self.annot3.set_text(text3)  
        
    def UpdateExp(self,value):
        a=self.SlopeOp.get()
        if a=='Exponential Slope':
            self.expo=self.Exp.get()    
            self.UpdateS(1)
            s=(self.distance2[-1]-self.distance2[-2])/(self.S[-1]-self.S[-2])
            textS = str('%.2f' % s)
            self.annotSlope.set_text(textS)
            pos=(self.distance2[-1],self.Surfaces.Design[self.interpolated_points.astype(int)[-1,1],self.interpolated_points.astype(int)[-1,0]])
            self.annotSlope.xy = pos
            self.canvasp.draw_idle()
        
    def UpdateSlp(self,value):
        a=self.SlopeOp.get()
        if a=='Exponential Slope':
            try:
                self.Slope0=self.Bottom_slp.get()
                self.Step=self.Step_point.get()
                self.expo=self.Exp.get()
            except:
                pass
            self.UpdateS(1)
            s=(self.distance2[-1]-self.distance2[-2])/(self.S[-1]-self.S[-2])
            
            textS = str('%.2f' % s)
            # try:
            self.annotSlope.set_text(textS)
            pos=(self.distance2[-1],self.Surfaces.Design[self.interpolated_points.astype(int)[-1,1],self.interpolated_points.astype(int)[-1,0]])
            self.annotSlope.xy = pos
            self.canvasp.draw_idle()
    
    def UpdateBench(self):
        self.S=np.zeros_like(self.distance2)
        if self.StartElevation is None:
            self.StartElevation=self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]
        self.BotE=self.StartElevation
        self.BWidth=float(self.BenchWidth.get())
        self.BHeight=float(self.BenchHeight.get())
        self.BOff=float(self.BenchOffset.get())
        self.Bslope=float(self.BatterSlope.get())
        Profile_Bench(self.S,self.BotE,self.distance2,self.BWidth,self.BHeight,self.BOff,self.Bslope)
        self.UpdatePlotDesign(self.S)   
        
    def UpdateBenchVar(self):
        self.S=np.zeros_like(self.distance2)
        if self.StartElevation is None:
            self.StartElevation=self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]
        self.BotE=self.StartElevation
        self.BWidth=float(self.BenchW.get())/self.Surfaces.cellsize
        print(self.BenchE.get().split(","))
        pnts=[]
        for p in self.BenchE.get().split(","):
            pnts.append(float(p))

        self.BElev=np.array(pnts,dtype=np.float32)
        print(self.BElev)
        self.Bslope=float(self.BenchS.get())
        Profile_BenchVar(self.S,self.BotE,self.distance2,self.BWidth,self.BElev,self.Bslope)
        print(self.S)
        self.UpdatePlotDesign(self.S)    
        
    def UpdateLinearSection(self):
        self.S=np.zeros_like(self.distance2)
        if self.StartElevation is None:
            self.StartElevation=self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]
        self.BotE=self.StartElevation
        Profile_linear(self.S,self.BotE,self.distance2,self.S1,self.S2,self.S3,self.S4,self.C1,self.C2,self.C3,self.C4)
        self.UpdatePlotDesign(self.S)
        
    def UpdateS(self,value):
        self.S=np.zeros_like(self.distance2)
        TopE=self.Surfaces.Design[self.interpolated_points.astype(int)[-1,1],self.interpolated_points.astype(int)[-1,0]]
        if self.StartElevation is None:
            self.StartElevation=self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]
        BotE=self.StartElevation
        avg=self.distance2[-1]/(TopE-BotE)
        Slope_by_Z(self.S,self.Slope0,self.expo,TopE,BotE,avg,self.distance2,self.Step)
        self.UpdatePlotDesign(self.S)
        
    def Set_to_Design(self):
        self.S=self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]
        self.UpdatePlotDesign(self.S)
        
    def Set_to_Survey(self):
        self.S=self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]
        self.UpdatePlotDesign(self.S)
        
    def UpdateSinitial(self,value):
        self.Des=self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]
        self.S=np.zeros_like(self.distance2)
        TopE=self.Surfaces.Design[self.interpolated_points.astype(int)[-1,1],self.interpolated_points.astype(int)[-1,0]]
        # if self.StartElevation is None:
        self.StartElevation=self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]
        BotE=self.StartElevation
        avg=self.distance2[-1]/(TopE-BotE)
        Slope_by_Z(self.S,self.Slope0,self.expo,TopE,BotE,avg,self.distance2,self.Step)
        
    def Unlock(self,Surfaces,S):
        Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=1
        self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=1
     
    def UpdateSRVL(self,value):
        self.S=np.zeros_like(self.distance2)
        TopE=self.Surfaces.Design[self.interpolated_points.astype(int)[-1,1],self.interpolated_points.astype(int)[-1,0]]
        if self.StartElevation is None:
            self.StartElevation=self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]
        BotE=self.StartElevation
        avg=self.distance2[-1]/(TopE-BotE)
        (S,expo) = Slope_by_ZRVL(self.S,self.Slope0,self.expo,TopE,BotE,avg,self.distance2)
        return(S,expo,self.Slope0)    
     
    #code for multiple points on a line, will need to plot on the landscape each point too   
    def RockVelLines(self,Surfaces,activeline):
    
        #Obtaining the line design height (S), exponent factor and bottom slope inputs from cross section pop-up
        (S,expo,Slope0) =  self.UpdateSRVL(1)
        
    
       
        if self.Linetype=='quadratic':
            xy=self.lineSP.get_xydata()
        if self.Linetype=='radius':
            xy=self.lineRT.get_xydata()
        
        s=[] 
        points=[]
        
        limit=0
        dist2=[]
        d=[]
        count=0
        point_coord=[]
        
        iiold=xy[0,0]
        jjold=xy[0,1]
    
        for i in xy:
            dist2.append(((iiold-i[0])**2+(jjold-i[1])**2)**0.5)
            
            if np.size(d)>=1:
                d.append(dist2[-1]+d[-1])
                
            else:
                d.append(dist2[-1])
            
            iiold=i[0]
            jjold=i[1]
            
            if d[-1]>=limit:
                limit+=100
                points.append(count)
                point_coord.append([iiold,jjold])
                
                
            count+=1    
        
        
        for i in range(0,np.size(points)):
            y=self.S[points[i]]
            yd=self.S[points[i]+1]
            
            s.append(abs(y-yd/1))
            
                
        #drain width constant so only calculate at the end or beginning
        Widthab=float(activeline.Width.get())/self.Surfaces.cellsize
        
        #returns a 3 lists (drain width, slope and point ID), corresponding entries in lists store info for the same point on the line
        return(xy, Widthab, s, points)
        
    
    #Function that plots the Rock and Velocity Limits given drain width, slope and flow 
    #NOTE: does not plot points from the line (next function does that)
    def RockVelLinesPlot(self,Surfaces,parameters):
        #setting up the pop up window
        self.profilewindow = tk.Toplevel(self.Sf)
        self.profilewindow.grid_columnconfigure(3,weight=1) # the text and entry frames column
        self.profilewindow.grid_rowconfigure(10,weight=1) # all frames row_
        self.profilewindow.title("Plot Rock Size and Velocity Limits")
        
        #setting up the plot on the window?
        self.f = Figure()
        self.a = self.f.add_subplot(111)
#                self.a.axis('scaled')
        self.canvasp = FigureCanvasTkAgg(self.f, self.profilewindow)
        self.canvasp.get_tk_widget().grid(row=10, column=0,columnspan=7,ipadx=40,ipady=20,sticky=tk.NSEW)
        self.f.subplots_adjust(left=0.1, right=0.9, top=0.99, bottom=0.1)
        
        
        #stores data as float to prevent datatype erros in later calculations
        f200=float(parameters[3])
        e200=float(parameters[4])
        c200=float(parameters[5])
        f300=float(parameters[6])
        e300=float(parameters[7])
        c300=float(parameters[8])
        f400=float(parameters[9])
        e400=float(parameters[10])
        c400=float(parameters[11])
        va=float(parameters[12])
        fa=float(parameters[13])
        ea=float(parameters[14])
        ca=float(parameters[15])
        vb=float(parameters[16])
        fb=float(parameters[17])
        eb=float(parameters[18])
        cb=float(parameters[19])
        vc=float(parameters[20])
        fc=float(parameters[21])
        ec=float(parameters[22])
        cc=float(parameters[23])
        vd=float(parameters[24])
        fd=float(parameters[25])
        ed=float(parameters[26])
        cd=float(parameters[27])
        
        
        
        #creating the velocity and rock limit lines
        rockvelx=np.linspace(0.01,0.5,1000)
        rock200=f200*(rockvelx**e200) + c200
        rock300=f300*(rockvelx**e300) + c300
        rock400=f400*(rockvelx**e400) + c400
        vela=fa*(rockvelx**ea) + ca
        velb=fb*(rockvelx**eb) + cb
        velc=fc*(rockvelx**ec) + cc
        veld=fd*(rockvelx**ed) + cd
        
        #Attempt at labelling the point:
        ##xy = (x[0],y[0])
        ##self.a.annotate('(%x, %y)' % xy, xy=xy, textcoords='data')
        
        #plotting the velocity and rock limit lines
        self.plotb=self.a.plot(rockvelx,rock200, c='y', label='Rock size 200mm')
        self.plotc=self.a.plot(rockvelx,rock300, c='r', label='Rock size 300mm')
        self.plotd=self.a.plot(rockvelx,rock400, c='g', label='Rock size 400mm')
        self.plote=self.a.plot(rockvelx,vela, c='orange', ls='--', label='Velocity (m/s)')
        self.plotf=self.a.plot(rockvelx,velb, c='orange', ls='--',)
        self.plotg=self.a.plot(rockvelx,velc, c='orange', ls='--',)
        self.ploth=self.a.plot(rockvelx,veld, c='orange', ls='--',)
        
        #setting up graph extras: legend, labels, grid, title, axis limits
        self.a.grid(True)
        self.a.legend(loc='upper right', labelcolor='white')
        
        #velocity curve label and label position on plot
        #sets permanent x position for labels   
        xpos=0.4
        yposa=fa*(xpos**ea) + ca
        yposb=fb*(xpos**eb) + cb
        yposc=fc*(xpos**ec) + cc
        yposd=fd*(xpos**ed) + cd
        texta=str(va)+' m/s'
        textb=str(vb)+' m/s'
        textc=str(vc)+' m/s'
        textd=str(vd)+' m/s'
        
        self.a.text(xpos, yposa, texta, ha="center", va="bottom", size=9, c='white')
        self.a.text(xpos, yposb, textb, ha="center", va="bottom", size=9, c='white')
        self.a.text(xpos, yposc, textc, ha="center", va="bottom", size=9, c='white')
        self.a.text(xpos, yposd, textd, ha="center", va="bottom", size=9, c='white')
        
        #Other graph options (axis labels, axis range, title)
        self.a.set_ylabel('Flow per Width (m^3/s/m)')
        self.a.set_xlabel('Slope (%)')
        
        self.a.set_title('Flow/m width against rock size and velocity limit')
        
        #limiting the axis ranges
        self.a.set_ylim([0.00,2])
        
        self.a.set_xlim([0.00,0.5])
        
     
    #PLots points from line and velocity and rock size curves    
    def RockVelPlots(self,Surfaces,q,Slope,points,parameters):
        #setting up the pop up window
        self.profilewindow = tk.Toplevel(self.Sf)
        self.profilewindow.grid_columnconfigure(3,weight=1) # the text and entry frames column
        self.profilewindow.grid_rowconfigure(10,weight=1) # all frames row_
        self.profilewindow.title("Plot Rock Size and Velocity Limits")
        
        #setting up the plot on the window?
        self.f = Figure()
        self.a = self.f.add_subplot(111)
#                self.a.axis('scaled')
        self.canvasp = FigureCanvasTkAgg(self.f, self.profilewindow)
        self.canvasp.get_tk_widget().grid(row=10, column=0,columnspan=7,ipadx=40,ipady=20,sticky=tk.NSEW)
        self.f.subplots_adjust(left=0.1, right=0.9, top=0.99, bottom=0.1)
        
        x=Slope
        y=q
        
        #stores data as float to prevent datatype erros in later calculations
        f200=float(parameters[3])
        e200=float(parameters[4])
        c200=float(parameters[5])
        f300=float(parameters[6])
        e300=float(parameters[7])
        c300=float(parameters[8])
        f400=float(parameters[9])
        e400=float(parameters[10])
        c400=float(parameters[11])
        va=float(parameters[12])
        fa=float(parameters[13])
        ea=float(parameters[14])
        ca=float(parameters[15])
        vb=float(parameters[16])
        fb=float(parameters[17])
        eb=float(parameters[18])
        cb=float(parameters[19])
        vc=float(parameters[20])
        fc=float(parameters[21])
        ec=float(parameters[22])
        cc=float(parameters[23])
        vd=float(parameters[24])
        fd=float(parameters[25])
        ed=float(parameters[26])
        cd=float(parameters[27])
           
        
        #creating the velocity and rock limit lines
        rockvelx=np.linspace(0.01,0.5,1000)
        rock200=f200*(rockvelx**e200) + c200
        rock300=f300*(rockvelx**e300) + c300
        rock400=f400*(rockvelx**e400) + c400
        vela=fa*(rockvelx**ea) + ca
        velb=fb*(rockvelx**eb) + cb
        velc=fc*(rockvelx**ec) + cc
        veld=fd*(rockvelx**ed) + cd
        
        #plotting the drain flow/width and slope as a scatter point
        self.plota=self.a.scatter(x,y, c='b', label='Drain Slope and Flow per Width')
        
        
        #plotting the velocity and rock limit lines
        self.plotb=self.a.plot(rockvelx,rock200, c='y', label='Rock size 200mm')
        self.plotc=self.a.plot(rockvelx,rock300, c='r', label='Rock size 300mm')
        self.plotd=self.a.plot(rockvelx,rock400, c='g', label='Rock size 400mm')
        self.plote=self.a.plot(rockvelx,vela, c='orange', ls='--', label='Velocity (m/s)')
        self.plotf=self.a.plot(rockvelx,velb, c='orange', ls='--',)
        self.plotg=self.a.plot(rockvelx,velc, c='orange', ls='--',)
        self.ploth=self.a.plot(rockvelx,veld, c='orange', ls='--',)
        
        #setting up graph extras: legend, labels, grid, title, axis limits
        self.a.grid(True)
        self.a.legend(loc='upper right', labelcolor='white')
        
        #Displaying coordinates of points on plot
        for i in range(0,np.size(points),1):    
            #x,y coordinates in tif for each point
            ycoord=self.interpolated_points.astype(int)[points[i],1]
            xcoord=self.interpolated_points.astype(int)[points[i],0]
            
            #x,y corrdinates on plot 
            xpos=x[i]
            ypos=y[i]
            
            #Rounding numbers for display
            xpos=round(xpos,2)
            ypos=round(ypos,2)
            
            #Display of the coordinates for each point
            words = '(' + str(xcoord) + ',' + str(ycoord) + ')'
            
            self.a.text(xpos, ypos, words, ha="center", va="bottom", size=8, c='white')
            
       
        xpos=0.4
        yposa=fa*(xpos**ea) + ca
        yposb=fb*(xpos**eb) + cb
        yposc=fc*(xpos**ec) + cc
        yposd=fd*(xpos**ed) + cd
        texta=str(va)+' m/s'
        textb=str(vb)+' m/s'
        textc=str(vc)+' m/s'
        textd=str(vd)+' m/s'
        
        self.a.text(xpos, yposa, texta, ha="center", va="bottom", size=9, c='white')
        self.a.text(xpos, yposb, textb, ha="center", va="bottom", size=9, c='white')
        self.a.text(xpos, yposc, textc, ha="center", va="bottom", size=9, c='white')
        self.a.text(xpos, yposd, textd, ha="center", va="bottom", size=9, c='white')
        
        self.a.set_ylabel('Flow per Width (m^3/s/m)')
        self.a.set_xlabel('Slope (%)')
        

        self.a.set_title('Flow/m width against rock size and velocity limit')
        
        #limiting the axis ranges
        if max(y)>1.75:
            ymax=max(y)+0.25
        else:
            ymax=2.00
        self.a.set_ylim([0.00,ymax])
        
        if max(x)>0.45:
            xmax=max(x)+0.04
        else:
            xmax=0.45
        self.a.set_xlim([0.00,xmax])
    
    def DeleteDXF(self,activeline,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR):
        for i in range(0,np.size(idlist),1):
            if self.ID == idlist[i]:
                # EdgeL.pop(i)
                # Berm1.pop(i)
                # Berm2.pop(i)
                # Base1.pop(i)
                # Center.pop(i)
                # Base2.pop(i)
                # Berm3.pop(i)
                # Berm4.pop(i)
                # EdgeR.pop(i)
                
                EdgeL[i]=[]
                Berm1[i]=[]
                Berm2[i]=[]
                Base1[i]=[]
                Center[i]=[]
                Base2[i]=[]
                Berm3[i]=[]
                Berm4[i]=[]
                EdgeR[i]=[]
        
        return(idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR) 
    
    def Createridges(self,Surfaces):
        if self.Linetype=='quadratic':
            xy=self.lineSP.get_xydata()
        # D=np.zeros_like(Surfaces.Design)
        GenRidges(xy,Surfaces.Design,Surfaces.cellsize)
        return Surfaces.Design
        
    
    
    def CreateCanalDendritic(self,Surfaces,S,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR):
        if self.Linetype=='quadratic':
            xy=self.lineSP.get_xydata()
        if self.Linetype=='radius':
            xy=self.lineRT.get_xydata()
        
        
        LineID=self.ID
        appended=False
        for i in range(0,np.size(idlist),1):
            if LineID == idlist[i]:
                linenum=i
                
               
                EdgeL[linenum]=[]
                Berm1[linenum]=[]
                Berm2[linenum]=[]
                Base1[linenum]=[]
                Center[linenum]=[]
                Base2[linenum]=[]
                Berm3[linenum]=[]
                Berm4[linenum]=[]
                EdgeR[linenum]=[]
                
                appended=True
                break
        
        if not appended:
            idlist.append(LineID)
            linenum=np.size(idlist,axis=0)-1
            # idlist.append([])
            EdgeL.append([])
            Berm1.append([])
            Berm2.append([])
            Base1.append([])
            Center.append([])
            Base2.append([])
            Berm3.append([])
            Berm4.append([])
            EdgeR.append([])
                   
        print('LineID')
        print(LineID)
        print('Linenum')
        print(linenum)
        
        self.SlopeL = float(S.SlopeL.get())
        self.WidthL = float(S.WidthL.get())
        self.SlopeLC = float(S.SlopeLC.get())
        self.DepthLC = float(S.DepthLC.get())
        self.WidthB = float(S.WidthB.get())
        self.SlopeRC = float(S.SlopeRC.get())
        self.DepthRC = float(S.DepthRC.get())
        self.WidthBR = float(S.WidthBR.get())
        self.SlopeR = float(S.SlopeR.get())
        
        d=0
        iiold=xy[0,0]
        jjold=xy[0,1]
        # iiold=self.interpolated_points[0,1]
        # jjold=self.interpolated_points[0,0]
        points=[]
        pointsE=[]
        
        depthBelow=float(S.depthBelow.get())
        self.depthBelow=depthBelow
        
        Widthbase=self.WidthB/self.Surfaces.cellsize/2.0
        
        sideLengthL=self.DepthLC*self.SlopeLC
        WidthBerm1=Widthbase+sideLengthL/self.Surfaces.cellsize+self.WidthL/self.Surfaces.cellsize
        WidthBerm2=Widthbase+sideLengthL/self.Surfaces.cellsize
        
        sideLengthR=self.DepthRC*self.SlopeRC
        WidthBerm3=Widthbase+sideLengthR/self.Surfaces.cellsize
        WidthBerm4=Widthbase+sideLengthR/self.Surfaces.cellsize+self.WidthBR/self.Surfaces.cellsize
        
        dist2=1
        cnt=0
        edgea=[]
        edgeb=[]
        EdgeLlocal=[]
        EdgeRlocal=[]
        #Note: if error comes up where S[cnt] is out of bounds for axis size, remember to apply surface cross section via 'E' key
        for i in xy:
            dist2=((iiold-i[0])**2+(jjold-i[1])**2)**0.5
            d+=dist2
            # if dist2>0:
            nx=(iiold-i[0])/dist2
            ny=(jjold-i[1])/dist2
            iiold=i[0]
            jjold=i[1]
            if not np.isnan(nx):
                depthleftTEMP=self.DepthLC
                depthrightTEMP=self.DepthRC
                bermleftTemp=WidthBerm1
                bermrightTemp=WidthBerm4
                bermleftSlopeTemp=WidthBerm2
                bermrightSlopeTemp=WidthBerm3
                 # msp.add_line(Sf.maxcol-(Sf.Design.shape[1]-float(centa[count][k]))*Sf.cellsize+0.5*Sf.cellsize, -(Sf.Design.shape[0]-float(centa[count][k+1]))*Sf.cellsize+Sf.maxrow+0.5*Sf.cellsize
                # centa[linenum].append([i[0],i[1],self.S[cnt]-depthBelow])
                Center[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(i[0]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(i[1]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,self.S[cnt]-depthBelow])
                
                #Berm1
                endelev = self.desinterp((WidthBerm1)*ny+i[0],i[1]-nx*(WidthBerm1))
                if endelev>self.S[cnt]-depthBelow+self.DepthLC:
                    depthleftTEMP=0
                    bermleftTemp=Widthbase
                    bermleftSlopeTemp=Widthbase
                    
                points.append([(i[1]-nx*(bermleftTemp)),(bermleftTemp)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+depthleftTEMP)
                Berm1[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                #Berm2
                points.append([(i[1]-nx*(bermleftSlopeTemp)),(bermleftSlopeTemp)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+depthleftTEMP)
                Berm2[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                #Base1
                points.append([(i[1]-nx*(Widthbase)),(Widthbase)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow)
                Base1[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                #Base2
                points.append([(i[1]+nx*(Widthbase)),-(Widthbase)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow)
                Base2[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                #Berm3
                endelev = self.desinterp(-(WidthBerm4)*ny+i[0],i[1]+nx*(WidthBerm4))
                if endelev>self.S[cnt]-depthBelow+self.DepthRC:
                    depthrightTEMP=0
                    bermrightTemp=Widthbase
                    bermrightSlopeTemp=Widthbase
                
                points.append([(i[1]+nx*(bermrightSlopeTemp)),-(bermrightSlopeTemp)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+depthrightTEMP)
                Berm3[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                #Berm4
                points.append([(i[1]+nx*(bermrightTemp)),-(bermrightTemp)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+depthrightTEMP)
                Berm4[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
    
                step=0
                dstep=0.5
                endelev = self.desinterp((step+bermleftTemp)*ny+i[0],i[1]-nx*(step+bermleftTemp))
                SideSlope1=self.SlopeL
                check=1
                if endelev<self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+depthleftTEMP:
                    SideSlope1=-self.SlopeL
                    check=-1
                for jj in range (0,100):
                    endelev = self.desinterp((step+bermleftTemp)*ny+i[0],i[1]-nx*(step+bermleftTemp))
                    if ((endelev-(self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+depthleftTEMP))*check<0):
                        check=-check
                        dstep=-0.5*dstep
                    step+=dstep
                points.append([(i[1]-nx*(step+bermleftTemp)),(step+bermleftTemp)*ny+i[0]])
                pointsE.append(self.S[cnt]+step*Surfaces.cellsize/SideSlope1-depthBelow+depthleftTEMP) 
                EdgeLlocal.append([(i[1]-nx*(step+bermleftTemp)),(step+bermleftTemp)*ny+i[0]])
                EdgeL[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                step=0
                dstep=0.5
                endelev = self.desinterp(-(step+bermrightTemp)*ny+i[0],i[1]+nx*(step+bermrightTemp))
                SideSlope1=self.SlopeR
                check=1
                if endelev<self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+depthrightTEMP:
                    SideSlope1=-self.SlopeR
                    check=-1
                for jj in range (0,100):
                    endelev = self.desinterp(-(step+bermrightTemp)*ny+i[0],i[1]+nx*(step+bermrightTemp))
                    if ((endelev-(self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+depthrightTEMP))*check<0):
                        check=-check
                        dstep=-0.5*dstep
                    step+=dstep
                points.append([(i[1]+nx*(step+bermrightTemp)),-(step+bermrightTemp)*ny+i[0]])
                pointsE.append(self.S[cnt]+step*Surfaces.cellsize/SideSlope1-depthBelow+depthrightTEMP) 
                EdgeRlocal.append([(i[1]+nx*(step+bermrightTemp)),-(step+bermrightTemp)*ny+i[0]])
                EdgeR[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                # print("points appened")
            cnt+=1
        # wallarev=walla[linenum].reverse()
        polygonlist=[]
        print('pointEL')
        print(EdgeL)
        print('pointR')
        print(EdgeR)
        for p in reversed(EdgeLlocal):
            polygonlist.append([p[1],p[0]])
        for p in EdgeRlocal:
            polygonlist.append([p[1],p[0]])
        self.poly = Polygon(polygonlist,animated=False, alpha=0.2)
        self.ax.add_artist(self.poly)        
        
        inv = self.ax.transData.inverted()
        poly_extents = inv.transform(self.poly.get_extents().get_points())
        min_x, min_y = np.floor(poly_extents[0]).astype(int)
        max_x, max_y = np.floor(poly_extents[1]).astype(int)
        bbox = np.where((self.Allpoints[:,0]>=min_x) & (self.Allpoints[:,0]<=max_x) & (self.Allpoints[:,1]>=min_y) & (self.Allpoints[:,1]<=max_y))
        self.Inside = np.zeros(self.Allpoints.shape[0], dtype=bool)
        self.Inside[bbox]=self.poly.contains_points(self.ax.transData.transform(self.Allpoints[bbox]))
        inside_indices = np.where(self.Inside)
        self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=0
        self.Surfaces.Canals[self.Allpoints[inside_indices, 1], self.Allpoints[inside_indices, 0]] = self.ID
        # self.Surfaces.Canals[self.Inside]=self.ID
       
        points=np.array(points)
        pointsE=np.array(pointsE)
        # print(points)
        interp = LinearNDInterpolator(points, pointsE)
        
        # self.CanalPoints.fill(0)
        
        Temp_Array=np.zeros_like(self.Surfaces.Canals)
        Temp_Canals=np.copy(self.Surfaces.Canals)
        Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=1
        self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=0
        # setCanalPoints(Temp_Canals,xy,WidthT*self.Surfaces.cellsize,self.Surfaces.cellsize,self.Surfaces.Design,self.Surfaces.Dist,self.ID)
        Temp_Array[np.where(Temp_Canals==self.ID)]=interp(np.where(Temp_Canals==self.ID))
        where_are_Nans=np.isnan(Temp_Array)
        Temp_Canals[where_are_Nans]=0
        # print(np.where(np.isnan(Temp_Array)))
        self.Surfaces.Canals[np.where(Temp_Canals==self.ID)]=self.ID
        # print(self.ID)
        Surfaces.Design[np.where(self.Surfaces.Canals==self.ID)]=interp(np.where(self.Surfaces.Canals==self.ID))
        Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=0
        cut=np.array([0])
        fill=np.array([0])
        Line_cut_fill(self.Surfaces.Design,self.Surfaces.Survey,self.Surfaces.Canals,cut,fill,self.Surfaces.cellsize,self.ID)
        print('cut')
        print(cut)
        print('fill')
        print(fill)
        # print(np.where(self.Surfaces.Canals==self.ID))
        return(idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR)
    
    
    
    
    def CreateCanalCUTFILL(self,Surfaces,S,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR,lineOptV):
        # print(lineOptV)
        if self.Linetype=='quadratic':
            xy=self.lineSP.get_xydata()
        if self.Linetype=='radius':
            xy=self.lineRT.get_xydata()
        
        
        LineID=self.ID
        appended=False
        for i in range(0,np.size(idlist),1):
            if LineID == idlist[i]:
                linenum=i
                
               
                EdgeL[linenum]=[]
                Berm1[linenum]=[]
                Berm2[linenum]=[]
                Base1[linenum]=[]
                Center[linenum]=[]
                Base2[linenum]=[]
                Berm3[linenum]=[]
                Berm4[linenum]=[]
                EdgeR[linenum]=[]
                
                appended=True
                break
        
        if not appended:
            idlist.append(LineID)
            linenum=np.size(idlist,axis=0)-1
            # idlist.append([])
            EdgeL.append([])
            Berm1.append([])
            Berm2.append([])
            Base1.append([])
            Center.append([])
            Base2.append([])
            Berm3.append([])
            Berm4.append([])
            EdgeR.append([])
                   
        print('LineID')
        print(LineID)
        print('Linenum')
        print(linenum)
        
        self.SlopeL = float(S.SlopeL.get())
        self.WidthL = float(S.WidthL.get())
        self.SlopeLC = float(S.SlopeLC.get())
        self.DepthLC = float(S.DepthLC.get())
        self.WidthB = float(S.WidthB.get())
        self.SlopeRC = float(S.SlopeRC.get())
        self.DepthRC = float(S.DepthRC.get())
        self.WidthBR = float(S.WidthBR.get())
        self.SlopeR = float(S.SlopeR.get())
        
        d=0
        iiold=xy[0,0]
        jjold=xy[0,1]
        # iiold=self.interpolated_points[0,1]
        # jjold=self.interpolated_points[0,0]
        points=[]
        pointsE=[]
        
        depthBelow=float(S.depthBelow.get())
        self.depthBelow=depthBelow
        
        Widthbase=self.WidthB/self.Surfaces.cellsize/2.0
        
        sideLengthL=self.DepthLC*self.SlopeLC
        WidthBerm1=Widthbase+sideLengthL/self.Surfaces.cellsize+self.WidthL/self.Surfaces.cellsize
        WidthBerm2=Widthbase+sideLengthL/self.Surfaces.cellsize
        
        sideLengthR=self.DepthRC*self.SlopeRC
        WidthBerm3=Widthbase+sideLengthR/self.Surfaces.cellsize
        WidthBerm4=Widthbase+sideLengthR/self.Surfaces.cellsize+self.WidthBR/self.Surfaces.cellsize
        
        dist2=1
        cnt=0
        edgea=[]
        edgeb=[]
        EdgeLlocal=[]
        EdgeRlocal=[]
        
        Berm1local=[]
        Berm4local=[]
        #Note: if error comes up where S[cnt] is out of bounds for axis size, remember to apply surface cross section via 'E' key
        for i in xy:
            dist2=((iiold-i[0])**2+(jjold-i[1])**2)**0.5
            d+=dist2
            # if dist2>0:
            nx=(iiold-i[0])/dist2
            ny=(jjold-i[1])/dist2
            iiold=i[0]
            jjold=i[1]
            if not np.isnan(nx):
                 # msp.add_line(Sf.maxcol-(Sf.Design.shape[1]-float(centa[count][k]))*Sf.cellsize+0.5*Sf.cellsize, -(Sf.Design.shape[0]-float(centa[count][k+1]))*Sf.cellsize+Sf.maxrow+0.5*Sf.cellsize
                # centa[linenum].append([i[0],i[1],self.S[cnt]-depthBelow])
                Center[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(i[0]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(i[1]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,self.S[cnt]-depthBelow])
                
                #Berm1
                points.append([(i[1]-nx*(WidthBerm1)),(WidthBerm1)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+self.DepthLC)
                Berm1local.append([(i[1]-nx*(WidthBerm1)),(WidthBerm1)*ny+i[0]])
                Berm1[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                #Berm2
                points.append([(i[1]-nx*(WidthBerm2)),(WidthBerm2)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+self.DepthLC)
                Berm2[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                #Base1
                points.append([(i[1]-nx*(Widthbase)),(Widthbase)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow)
                Base1[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                #Base2
                points.append([(i[1]+nx*(Widthbase)),-(Widthbase)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow)
                Base2[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                #Berm3
                points.append([(i[1]+nx*(WidthBerm3)),-(WidthBerm3)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+self.DepthRC)
                Berm3[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                #Berm4
                points.append([(i[1]+nx*(WidthBerm4)),-(WidthBerm4)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+self.DepthRC)
                Berm4local.append([(i[1]+nx*(WidthBerm4)),-(WidthBerm4)*ny+i[0]])
                Berm4[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
    
                step=0
                dstep=0.5
                endelev = self.desinterp((step+WidthBerm1)*ny+i[0],i[1]-nx*(step+WidthBerm1))
                SideSlope1=self.SlopeL
                check=1
                if endelev<self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthLC:
                    SideSlope1=-self.SlopeL
                    check=-1
                for jj in range (0,100):
                    endelev = self.desinterp((step+WidthBerm1)*ny+i[0],i[1]-nx*(step+WidthBerm1))
                    if ((endelev-(self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthLC))*check<0):
                        check=-check
                        dstep=-0.5*dstep
                    step+=dstep
                points.append([(i[1]-nx*(step+WidthBerm1)),(step+WidthBerm1)*ny+i[0]])
                pointsE.append(self.S[cnt]+step*Surfaces.cellsize/SideSlope1-depthBelow+self.DepthLC) 
                EdgeLlocal.append([(i[1]-nx*(step+WidthBerm1)),(step+WidthBerm1)*ny+i[0]])
                EdgeL[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                step=0
                dstep=0.5
                endelev = self.desinterp(-(step+WidthBerm4)*ny+i[0],i[1]+nx*(step+WidthBerm4))
                SideSlope1=self.SlopeR
                check=1
                if endelev<self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthRC:
                    SideSlope1=-self.SlopeR
                    check=-1
                for jj in range (0,100):
                    endelev = self.desinterp(-(step+WidthBerm4)*ny+i[0],i[1]+nx*(step+WidthBerm4))
                    if ((endelev-(self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthRC))*check<0):
                        check=-check
                        dstep=-0.5*dstep
                    step+=dstep
                points.append([(i[1]+nx*(step+WidthBerm4)),-(step+WidthBerm4)*ny+i[0]])
                pointsE.append(self.S[cnt]+step*Surfaces.cellsize/SideSlope1-depthBelow+self.DepthRC) 
                EdgeRlocal.append([(i[1]+nx*(step+WidthBerm4)),-(step+WidthBerm4)*ny+i[0]])
                EdgeR[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                # print("points appened")
            cnt+=1
        # wallarev=walla[linenum].reverse()
        polygonlist=[]
        for p in reversed(EdgeLlocal):
            polygonlist.append([p[1],p[0]])
        for p in EdgeRlocal:
            polygonlist.append([p[1],p[0]])
        self.poly = Polygon(polygonlist,animated=False, alpha=0.0)
        self.ax.add_artist(self.poly)
        
        polygonlistBerm=[]
        for p in reversed(Berm1local):
            # print(p)
            polygonlistBerm.append([p[1],p[0]])
        for p in Berm4local:
            polygonlistBerm.append([p[1],p[0]])
        self.polyBerm = Polygon(polygonlistBerm,animated=False, alpha=0.4)
        self.ax.add_artist(self.polyBerm)        
        
        inv = self.ax.transData.inverted()
        poly_extents = inv.transform(self.poly.get_extents().get_points())
        min_x, min_y = np.floor(poly_extents[0]).astype(int)
        max_x, max_y = np.floor(poly_extents[1]).astype(int)
        bbox = np.where((self.Allpoints[:,0]>=min_x) & (self.Allpoints[:,0]<=max_x) & (self.Allpoints[:,1]>=min_y) & (self.Allpoints[:,1]<=max_y))
        self.Inside = np.zeros(self.Allpoints.shape[0], dtype=bool)
        self.Inside[bbox]=self.poly.contains_points(self.ax.transData.transform(self.Allpoints[bbox]))
        inside_indices = np.where(self.Inside)
        self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=0
        self.Surfaces.Canals[self.Allpoints[inside_indices, 1], self.Allpoints[inside_indices, 0]] = self.ID
        # self.Surfaces.Canals[self.Inside]=self.ID
       
        points=np.array(points)
        pointsE=np.array(pointsE)
        # print(points)
        interp = LinearNDInterpolator(points, pointsE)
        
        # self.CanalPoints.fill(0)
        
        Temp_Array=np.zeros_like(self.Surfaces.Canals)
        Temp_Canals=np.copy(self.Surfaces.Canals)
        Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=1
        self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=0
        # setCanalPoints(Temp_Canals,xy,WidthT*self.Surfaces.cellsize,self.Surfaces.cellsize,self.Surfaces.Design,self.Surfaces.Dist,self.ID)
        Temp_Array[np.where(Temp_Canals==self.ID)]=interp(np.where(Temp_Canals==self.ID))
        where_are_Nans=np.isnan(Temp_Array)
        Temp_Canals[where_are_Nans]=0
        # print(np.where(np.isnan(Temp_Array)))
        self.Surfaces.Canals[np.where(Temp_Canals==self.ID)]=self.ID
        # print(self.ID)
        # Surfaces.Design[np.where(self.Surfaces.Canals==self.ID)]=interp(np.where(self.Surfaces.Canals==self.ID))
        print(lineOptV)
        if lineOptV=='Lock Base Only':
           poly_extents = inv.transform(self.polyBerm.get_extents().get_points())
           min_x, min_y = np.floor(poly_extents[0]).astype(int)
           max_x, max_y = np.floor(poly_extents[1]).astype(int)
           bbox = np.where((self.Allpoints[:,0]>=min_x) & (self.Allpoints[:,0]<=max_x) & (self.Allpoints[:,1]>=min_y) & (self.Allpoints[:,1]<=max_y))
           self.Inside = np.zeros(self.Allpoints.shape[0], dtype=bool)
           self.Inside[bbox]=self.polyBerm.contains_points(self.ax.transData.transform(self.Allpoints[bbox]))
           inside_indices = np.where(self.Inside)
           self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=0
           self.Surfaces.Canals[self.Allpoints[inside_indices, 1], self.Allpoints[inside_indices, 0]] = self.ID
           Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=0
        if lineOptV=='Lock to Edge':
            Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=0
        cut=np.array([0])
        fill=np.array([0])
        Line_cut_fill(self.Surfaces.Design,self.Surfaces.Survey,self.Surfaces.Canals,cut,fill,self.Surfaces.cellsize,self.ID)
        print('cut')
        print(cut[0])
        print('fill')
        print(fill[0])
        # print(np.where(self.Surfaces.Canals==self.ID))
        return(idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR)
    
    def CreateCanal(self,Surfaces,S,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR,lineOptV):
        # print(lineOptV)
        if self.Linetype=='quadratic':
            xy=self.lineSP.get_xydata()
        if self.Linetype=='radius':
            xy=self.lineRT.get_xydata()
        
        
        LineID=self.ID
        appended=False
        print(EdgeL)
        print(len(EdgeL))
        for i in range(0,np.size(idlist),1):
            if LineID == idlist[i]:
                linenum=i
                
               
                EdgeL[linenum]=[]
                Berm1[linenum]=[]
                Berm2[linenum]=[]
                Base1[linenum]=[]
                Center[linenum]=[]
                Base2[linenum]=[]
                Berm3[linenum]=[]
                Berm4[linenum]=[]
                EdgeR[linenum]=[]
                
                appended=True
                break
        
        if not appended:
            idlist.append(LineID)
            linenum=np.size(idlist,axis=0)-1
            # idlist.append([])
            EdgeL.append([])
            Berm1.append([])
            Berm2.append([])
            Base1.append([])
            Center.append([])
            Base2.append([])
            Berm3.append([])
            Berm4.append([])
            EdgeR.append([])
                   
        print('LineID')
        print(LineID)
        print('Linenum')
        print(linenum)
        
        self.SlopeL = float(S.SlopeL.get())
        self.WidthL = float(S.WidthL.get())
        self.SlopeLC = float(S.SlopeLC.get())
        self.DepthLC = float(S.DepthLC.get())
        self.WidthB = float(S.WidthB.get())
        self.SlopeRC = float(S.SlopeRC.get())
        self.DepthRC = float(S.DepthRC.get())
        self.WidthBR = float(S.WidthBR.get())
        self.SlopeR = float(S.SlopeR.get())
        
        d=0
        iiold=xy[0,0]
        jjold=xy[0,1]
        # iiold=self.interpolated_points[0,1]
        # jjold=self.interpolated_points[0,0]
        points=[]
        pointsE=[]
        
        depthBelow=float(S.depthBelow.get())
        self.depthBelow=depthBelow
        
        Widthbase=self.WidthB/self.Surfaces.cellsize/2.0
        
        sideLengthL=self.DepthLC*self.SlopeLC
        WidthBerm1=Widthbase+sideLengthL/self.Surfaces.cellsize+self.WidthL/self.Surfaces.cellsize
        WidthBerm2=Widthbase+sideLengthL/self.Surfaces.cellsize
        
        sideLengthR=self.DepthRC*self.SlopeRC
        WidthBerm3=Widthbase+sideLengthR/self.Surfaces.cellsize
        WidthBerm4=Widthbase+sideLengthR/self.Surfaces.cellsize+self.WidthBR/self.Surfaces.cellsize
        
        dist2=1
        cnt=0
        edgea=[]
        edgeb=[]
        EdgeLlocal=[]
        EdgeRlocal=[]
        
        Berm1local=[]
        Berm4local=[]
        #Note: if error comes up where S[cnt] is out of bounds for axis size, remember to apply surface cross section via 'E' key
        for i in xy:
            dist2=((iiold-i[0])**2+(jjold-i[1])**2)**0.5
            d+=dist2
            # if dist2>0:
            nx=(iiold-i[0])/dist2
            ny=(jjold-i[1])/dist2
            iiold=i[0]
            jjold=i[1]
            if not np.isnan(nx):
                 # msp.add_line(Sf.maxcol-(Sf.Design.shape[1]-float(centa[count][k]))*Sf.cellsize+0.5*Sf.cellsize, -(Sf.Design.shape[0]-float(centa[count][k+1]))*Sf.cellsize+Sf.maxrow+0.5*Sf.cellsize
                # centa[linenum].append([i[0],i[1],self.S[cnt]-depthBelow])
                Center[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(i[0]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(i[1]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,self.S[cnt]-depthBelow])
                
                #Berm1
                points.append([(i[1]-nx*(WidthBerm1)),(WidthBerm1)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+self.DepthLC)
                Berm1local.append([(i[1]-nx*(WidthBerm1)),(WidthBerm1)*ny+i[0]])
                Berm1[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                #Berm2
                points.append([(i[1]-nx*(WidthBerm2)),(WidthBerm2)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+self.DepthLC)
                Berm2[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                #Base1
                points.append([(i[1]-nx*(Widthbase)),(Widthbase)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow)
                Base1[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                #Base2
                points.append([(i[1]+nx*(Widthbase)),-(Widthbase)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow)
                Base2[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                #Berm3
                points.append([(i[1]+nx*(WidthBerm3)),-(WidthBerm3)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+self.DepthRC)
                Berm3[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                #Berm4
                points.append([(i[1]+nx*(WidthBerm4)),-(WidthBerm4)*ny+i[0]])
                pointsE.append(self.S[cnt]-depthBelow+self.DepthRC)
                Berm4local.append([(i[1]+nx*(WidthBerm4)),-(WidthBerm4)*ny+i[0]])
                Berm4[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
    
                step=0
                dstep=0.5
                endelev = self.desinterp((step+WidthBerm1)*ny+i[0],i[1]-nx*(step+WidthBerm1))
                SideSlope1=self.SlopeL
                check=1
                if endelev<self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthLC:
                    SideSlope1=-self.SlopeL
                    check=-1
                for jj in range (0,100):
                    endelev = self.desinterp((step+WidthBerm1)*ny+i[0],i[1]-nx*(step+WidthBerm1))
                    if ((endelev-(self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthLC))*check<0):
                        check=-check
                        dstep=-0.5*dstep
                    step+=dstep
                points.append([(i[1]-nx*(step+WidthBerm1)),(step+WidthBerm1)*ny+i[0]])
                pointsE.append(self.S[cnt]+step*Surfaces.cellsize/SideSlope1-depthBelow+self.DepthLC) 
                EdgeLlocal.append([(i[1]-nx*(step+WidthBerm1)),(step+WidthBerm1)*ny+i[0]])
                EdgeL[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                step=0
                dstep=0.5
                endelev = self.desinterp(-(step+WidthBerm4)*ny+i[0],i[1]+nx*(step+WidthBerm4))
                SideSlope1=self.SlopeR
                check=1
                if endelev<self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthRC:
                    SideSlope1=-self.SlopeR
                    check=-1
                for jj in range (0,100):
                    endelev = self.desinterp(-(step+WidthBerm4)*ny+i[0],i[1]+nx*(step+WidthBerm4))
                    if ((endelev-(self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthRC))*check<0):
                        check=-check
                        dstep=-0.5*dstep
                    step+=dstep
                points.append([(i[1]+nx*(step+WidthBerm4)),-(step+WidthBerm4)*ny+i[0]])
                pointsE.append(self.S[cnt]+step*Surfaces.cellsize/SideSlope1-depthBelow+self.DepthRC) 
                EdgeRlocal.append([(i[1]+nx*(step+WidthBerm4)),-(step+WidthBerm4)*ny+i[0]])
                EdgeR[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                
                # print("points appened")
            cnt+=1
        # wallarev=walla[linenum].reverse()
        polygonlist=[]
        for p in reversed(EdgeLlocal):
            polygonlist.append([p[1],p[0]])
        for p in EdgeRlocal:
            polygonlist.append([p[1],p[0]])
        self.poly = Polygon(polygonlist,animated=False, alpha=0.0)
        self.ax.add_artist(self.poly)
        
        polygonlistBerm=[]
        for p in reversed(Berm1local):
            # print(p)
            polygonlistBerm.append([p[1],p[0]])
        for p in Berm4local:
            polygonlistBerm.append([p[1],p[0]])
        self.polyBerm = Polygon(polygonlistBerm,animated=False, alpha=0.0)
        self.ax.add_artist(self.polyBerm)        
        
        inv = self.ax.transData.inverted()
        poly_extents = inv.transform(self.poly.get_extents().get_points())
        min_x, min_y = np.floor(poly_extents[0]).astype(int)
        max_x, max_y = np.floor(poly_extents[1]).astype(int)
        bbox = np.where((self.Allpoints[:,0]>=min_x) & (self.Allpoints[:,0]<=max_x) & (self.Allpoints[:,1]>=min_y) & (self.Allpoints[:,1]<=max_y))
        self.Inside = np.zeros(self.Allpoints.shape[0], dtype=bool)
        self.Inside[bbox]=self.poly.contains_points(self.ax.transData.transform(self.Allpoints[bbox]))
        inside_indices = np.where(self.Inside)
        self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=0
        self.Surfaces.Canals[self.Allpoints[inside_indices, 1], self.Allpoints[inside_indices, 0]] = self.ID
        # self.Surfaces.Canals[self.Inside]=self.ID
       
        points=np.array(points)
        pointsE=np.array(pointsE)
        # print(points)
        interp = LinearNDInterpolator(points, pointsE)
        
        # self.CanalPoints.fill(0)
        
        Temp_Array=np.zeros_like(self.Surfaces.Canals)
        Temp_Canals=np.copy(self.Surfaces.Canals)
        Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=1
        self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=0
        # setCanalPoints(Temp_Canals,xy,WidthT*self.Surfaces.cellsize,self.Surfaces.cellsize,self.Surfaces.Design,self.Surfaces.Dist,self.ID)
        Temp_Array[np.where(Temp_Canals==self.ID)]=interp(np.where(Temp_Canals==self.ID))
        where_are_Nans=np.isnan(Temp_Array)
        Temp_Canals[where_are_Nans]=0
        # print(np.where(np.isnan(Temp_Array)))
        self.Surfaces.Canals[np.where(Temp_Canals==self.ID)]=self.ID
        # print(self.ID)
        Surfaces.Design[np.where(self.Surfaces.Canals==self.ID)]=interp(np.where(self.Surfaces.Canals==self.ID))
        print(lineOptV)
        if lineOptV=='Lock Base Only':
           poly_extents = inv.transform(self.polyBerm.get_extents().get_points())
           min_x, min_y = np.floor(poly_extents[0]).astype(int)
           max_x, max_y = np.floor(poly_extents[1]).astype(int)
           bbox = np.where((self.Allpoints[:,0]>=min_x) & (self.Allpoints[:,0]<=max_x) & (self.Allpoints[:,1]>=min_y) & (self.Allpoints[:,1]<=max_y))
           self.Inside = np.zeros(self.Allpoints.shape[0], dtype=bool)
           self.Inside[bbox]=self.polyBerm.contains_points(self.ax.transData.transform(self.Allpoints[bbox]))
           inside_indices = np.where(self.Inside)
           self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=0
           self.Surfaces.Canals[self.Allpoints[inside_indices, 1], self.Allpoints[inside_indices, 0]] = self.ID
           Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=0
        if lineOptV=='Lock to Edge':
            Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=0
        cut=np.array([0])
        fill=np.array([0])
        Line_cut_fill(self.Surfaces.Design,self.Surfaces.Survey,self.Surfaces.Canals,cut,fill,self.Surfaces.cellsize,self.ID)
        print('cut')
        print(cut)
        print('fill')
        print(fill)
        # print(np.where(self.Surfaces.Canals==self.ID))
        return(idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR)

    def CreateCanalBalanced(self,Surfaces,S,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR):
            if self.Linetype=='quadratic':
                xy=self.lineSP.get_xydata()
            if self.Linetype=='radius':
                xy=self.lineRT.get_xydata()
            
            
            LineID=self.ID
            appended=False
            for i in range(0,np.size(idlist),1):
                if LineID == idlist[i]:
                    linenum=i
                    
                   
                    EdgeL[linenum]=[]
                    Berm1[linenum]=[]
                    Berm2[linenum]=[]
                    Base1[linenum]=[]
                    Center[linenum]=[]
                    Base2[linenum]=[]
                    Berm3[linenum]=[]
                    Berm4[linenum]=[]
                    EdgeR[linenum]=[]
                    
                    appended=True
                    break
            
            if not appended:
                idlist.append(LineID)
                linenum=np.size(idlist,axis=0)-1
                # idlist.append([])
                EdgeL.append([])
                Berm1.append([])
                Berm2.append([])
                Base1.append([])
                Center.append([])
                Base2.append([])
                Berm3.append([])
                Berm4.append([])
                EdgeR.append([])
                       
            # print('LineID')
            # print(LineID)
            # print('Linenum')
            # print(linenum)
            
            self.SlopeL = float(S.SlopeL.get())
            self.WidthL = float(S.WidthL.get())
            self.SlopeLC = float(S.SlopeLC.get())
            self.DepthLC = float(S.DepthLC.get())
            self.WidthB = float(S.WidthB.get())
            self.SlopeRC = float(S.SlopeRC.get())
            self.DepthRC = float(S.DepthRC.get())
            self.WidthBR = float(S.WidthBR.get())
            self.SlopeR = float(S.SlopeR.get())
            
            d=0
            iiold=xy[0,0]
            jjold=xy[0,1]
            # iiold=self.interpolated_points[0,1]
            # jjold=self.interpolated_points[0,0]
            points=[]
            pointsE=[]
            
            depthBelow=float(S.depthBelow.get())
            self.depthBelow=depthBelow
            
            Widthbase=self.WidthB/self.Surfaces.cellsize/2.0
            
            sideLengthL=self.DepthLC*self.SlopeLC
            WidthBerm1=Widthbase+sideLengthL/self.Surfaces.cellsize+self.WidthL/self.Surfaces.cellsize
            WidthBerm2=Widthbase+sideLengthL/self.Surfaces.cellsize
            
            sideLengthR=self.DepthRC*self.SlopeRC
            WidthBerm3=Widthbase+sideLengthR/self.Surfaces.cellsize
            WidthBerm4=Widthbase+sideLengthR/self.Surfaces.cellsize+self.WidthBR/self.Surfaces.cellsize
            
            dist2=1
            cnt=0
            edgea=[]
            edgeb=[]
            EdgeLlocal=[]
            EdgeRlocal=[]
            #Note: if error comes up where S[cnt] is out of bounds for axis size, remember to apply surface cross section via 'E' key
            for i in xy:
                dist2=((iiold-i[0])**2+(jjold-i[1])**2)**0.5
                d+=dist2
                # if dist2>0:
                nx=(iiold-i[0])/dist2
                ny=(jjold-i[1])/dist2
                iiold=i[0]
                jjold=i[1]
                if not np.isnan(nx):
                     # msp.add_line(Sf.maxcol-(Sf.Design.shape[1]-float(centa[count][k]))*Sf.cellsize+0.5*Sf.cellsize, -(Sf.Design.shape[0]-float(centa[count][k+1]))*Sf.cellsize+Sf.maxrow+0.5*Sf.cellsize
                    # centa[linenum].append([i[0],i[1],self.S[cnt]-depthBelow])
                    Center[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(i[0]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(i[1]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,self.S[cnt]-depthBelow])
                    
                    #Berm1
                    points.append([(i[1]-nx*(WidthBerm1)),(WidthBerm1)*ny+i[0]])
                    pointsE.append(self.S[cnt]-depthBelow+self.DepthLC)
                    Berm1[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                    
                    #Berm2
                    points.append([(i[1]-nx*(WidthBerm2)),(WidthBerm2)*ny+i[0]])
                    pointsE.append(self.S[cnt]-depthBelow+self.DepthLC)
                    Berm2[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                    #Base1
                    points.append([(i[1]-nx*(Widthbase)),(Widthbase)*ny+i[0]])
                    pointsE.append(self.S[cnt]-depthBelow)
                    Base1[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                    #Base2
                    points.append([(i[1]+nx*(Widthbase)),-(Widthbase)*ny+i[0]])
                    pointsE.append(self.S[cnt]-depthBelow)
                    Base2[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                    
                    #Berm3
                    points.append([(i[1]+nx*(WidthBerm3)),-(WidthBerm3)*ny+i[0]])
                    pointsE.append(self.S[cnt]-depthBelow+self.DepthRC)
                    Berm3[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])

                    #Berm4
                    points.append([(i[1]+nx*(WidthBerm4)),-(WidthBerm4)*ny+i[0]])
                    pointsE.append(self.S[cnt]-depthBelow+self.DepthRC)
                    Berm4[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
        
                    step=0
                    dstep=0.5
                    endelev = self.desinterp((step+WidthBerm1)*ny+i[0],i[1]-nx*(step+WidthBerm1))
                    SideSlope1=self.SlopeL
                    check=1
                    if endelev<self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthLC:
                        SideSlope1=-self.SlopeL
                        check=-1
                    for jj in range (0,100):
                        endelev = self.desinterp((step+WidthBerm1)*ny+i[0],i[1]-nx*(step+WidthBerm1))
                        if ((endelev-(self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthLC))*check<0):
                            check=-check
                            dstep=-0.5*dstep
                        step+=dstep
                    points.append([(i[1]-nx*(step+WidthBerm1)),(step+WidthBerm1)*ny+i[0]])
                    pointsE.append(self.S[cnt]+step*Surfaces.cellsize/SideSlope1-depthBelow+self.DepthLC) 
                    EdgeLlocal.append([(i[1]-nx*(step+WidthBerm1)),(step+WidthBerm1)*ny+i[0]])
                    EdgeL[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                    
                    step=0
                    dstep=0.5
                    endelev = self.desinterp(-(step+WidthBerm4)*ny+i[0],i[1]+nx*(step+WidthBerm4))
                    SideSlope1=self.SlopeR
                    check=1
                    if endelev<self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthRC:
                        SideSlope1=-self.SlopeR
                        check=-1
                    for jj in range (0,100):
                        endelev = self.desinterp(-(step+WidthBerm4)*ny+i[0],i[1]+nx*(step+WidthBerm4))
                        if ((endelev-(self.S[cnt]-depthBelow+step*Surfaces.cellsize/SideSlope1+self.DepthRC))*check<0):
                            check=-check
                            dstep=-0.5*dstep
                        step+=dstep
                    points.append([(i[1]+nx*(step+WidthBerm4)),-(step+WidthBerm4)*ny+i[0]])
                    pointsE.append(self.S[cnt]+step*Surfaces.cellsize/SideSlope1-depthBelow+self.DepthRC) 
                    EdgeRlocal.append([(i[1]+nx*(step+WidthBerm4)),-(step+WidthBerm4)*ny+i[0]])
                    EdgeR[linenum].append([Surfaces.maxcol-(Surfaces.Design.shape[1]-float(points[-1][1]))*Surfaces.cellsize+0.5*Surfaces.cellsize, -(Surfaces.Design.shape[0]-float(points[-1][0]))*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize,pointsE[-1]])
                    
                    # print("points appened")
                cnt+=1
            # wallarev=walla[linenum].reverse()
            polygonlist=[]
            # print('pointEL')
            # print(EdgeL)
            # print('pointR')
            # print(EdgeR)
            for p in reversed(EdgeLlocal):
                polygonlist.append([p[1],p[0]])
            for p in EdgeRlocal:
                polygonlist.append([p[1],p[0]])
            self.poly = Polygon(polygonlist,animated=False, alpha=0.2)
            p=self.ax.add_artist(self.poly)        
            
            inv = self.ax.transData.inverted()
            poly_extents = inv.transform(self.poly.get_extents().get_points())
            min_x, min_y = np.floor(poly_extents[0]).astype(int)
            max_x, max_y = np.floor(poly_extents[1]).astype(int)
            bbox = np.where((self.Allpoints[:,0]>=min_x) & (self.Allpoints[:,0]<=max_x) & (self.Allpoints[:,1]>=min_y) & (self.Allpoints[:,1]<=max_y))
            self.Inside = np.zeros(self.Allpoints.shape[0], dtype=bool)
            self.Inside[bbox]=self.poly.contains_points(self.ax.transData.transform(self.Allpoints[bbox]))
            inside_indices = np.where(self.Inside)
            self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=0
            self.Surfaces.Canals[self.Allpoints[inside_indices, 1], self.Allpoints[inside_indices, 0]] = self.ID
            # self.Surfaces.Canals[self.Inside]=self.ID
            p.remove()        
            points=np.array(points)
            pointsE=np.array(pointsE)
            # print(points)
            interp = LinearNDInterpolator(points, pointsE)
            
            # self.CanalPoints.fill(0)
            
            Temp_Array=np.zeros_like(self.Surfaces.Canals)
            Temp_Canals=np.copy(self.Surfaces.Canals)
            Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=1
            self.Surfaces.Canals[np.where(self.Surfaces.Canals==self.ID)]=0
            # setCanalPoints(Temp_Canals,xy,WidthT*self.Surfaces.cellsize,self.Surfaces.cellsize,self.Surfaces.Design,self.Surfaces.Dist,self.ID)
            Temp_Array[np.where(Temp_Canals==self.ID)]=interp(np.where(Temp_Canals==self.ID))
            where_are_Nans=np.isnan(Temp_Array)
            Temp_Canals[where_are_Nans]=0
            # print(np.where(np.isnan(Temp_Array)))
            self.Surfaces.Canals[np.where(Temp_Canals==self.ID)]=self.ID
            # print(self.ID)
            Designtest=np.copy(Surfaces.Design)
            Designtest[np.where(self.Surfaces.Canals==self.ID)]=interp(np.where(self.Surfaces.Canals==self.ID))
            Surfaces.Active[np.where(self.Surfaces.Canals==self.ID)]=0
            cut=np.array([0])
            fill=np.array([0])
            Line_cut_fill(Designtest,self.Surfaces.Survey,self.Surfaces.Canals,cut,fill,self.Surfaces.cellsize,self.ID)
            # print('cut')
            # print(cut)
            # print('fill')
            # print(fill)
            # print(np.where(self.Surfaces.Canals==self.ID))
            return(idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR,cut,fill)
    
    def UpdatePlot(self):
            self.plota.set_ydata(self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
            self.plotb.set_ydata(self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
            self.Surv=self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]
            # self.plotc.set_ydata(S)
            # self.plotc.set_xdata(self.distance2)
            
            # self.plotc.set_ydata([self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]],self.Surfaces.Design[self.interpolated_points.astype(int)[-1,1],self.interpolated_points.astype(int)[-1,0]]])
            self.plota.set_xdata(self.distance2)
            self.plotb.set_xdata(self.distance2)
            self.plotc.set_xdata([self.distance2[0],self.distance2[-1]])
            miny=min([min(i for i in self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]] if i > 0),min(i for i in self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]] if i > 0)])
            maxy=max([max(self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]),max(self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])])
            self.a.set_ylim([-15+miny,15+maxy])
            self.a.set_xlim([self.distance2[0],self.distance2[-1]+10])
            self.StartElevation=self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]
            self.UpdateSlp(1)
            # self.StartElevation=self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]]
            # self.canvasp.draw()
    def UpdatePlot2(self):
            self.plota.set_ydata(self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
            self.plotb.set_ydata(self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])
            self.Surv=self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]
            # self.plotc.set_ydata(S)
            # self.plotc.set_xdata(self.distance2)
            
            # self.plotc.set_ydata([self.Surfaces.Design[self.interpolated_points.astype(int)[0,1],self.interpolated_points.astype(int)[0,0]],self.Surfaces.Design[self.interpolated_points.astype(int)[-1,1],self.interpolated_points.astype(int)[-1,0]]])
            self.plota.set_xdata(self.distance2)
            self.plotb.set_xdata(self.distance2)
            self.plotc.set_xdata([self.distance2[0],self.distance2[-1]])
            miny=min([min(i for i in self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]] if i > 0),min(i for i in self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]] if i > 0)])
            maxy=max([max(self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]),max(self.Surfaces.Survey[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]])])
            self.a.set_ylim([-15+miny,15+maxy])
            self.a.set_xlim([self.distance2[0],self.distance2[-1]+10])
            
    def UpdatePlotDesign(self,S):
            self.plotc.set_ydata(S)
            self.plotc.set_xdata(self.distance2)
            self.canvasp.draw()
    
    def initial_distance(self):
        
            xy=self.line.get_xydata()
            
            if self.Linetype=='radius':
                line_new=self.tangent_radial_lines(self.line.get_xydata())
                distance = np.cumsum( np.sqrt(np.sum( np.diff(line_new, axis=0)**2, axis=1 )) )
                TotalD=distance[-1]*self.Surfaces.cellsize
                distance = np.insert(distance, 0, 0)/distance[-1]
                
                alpha = np.linspace(0, 1, int(TotalD/self.Surfaces.cellsize))
                interpolator = interp1d(distance, line_new, kind='linear', axis=0)
                interpolated_points= interpolator(alpha)
                
                self.interpolated_points=interpolated_points
                self.distance=distance
                self.distance2=np.linspace(0, TotalD, int(TotalD/self.Surfaces.cellsize))
                self.alpha=alpha
                self.Sf.DrainLength.delete(0,tk.END)
                self.Sf.DrainLength.insert(0,int(TotalD))
                
#            xy = self.line.get_transform().transform(self.line.get_xydata())
            else: 
                if self.Linetype=='quadratic' and xy.shape[0]==2:
                    xxyy=[[xy[0,0],xy[0,1]],[(xy[0,0]+xy[1,0])/2,(xy[0,1]+xy[1,1])/2],[xy[1,0],xy[1,1]]]
                    xy=np.array(xxyy)
                    # print('initial distance')
                distance = np.cumsum( np.sqrt(np.sum( np.diff(xy, axis=0)**2, axis=1 )) )
                TotalD=distance[-1]*self.Surfaces.cellsize
                distance = np.insert(distance, 0, 0)/distance[-1]
                
                alpha = np.linspace(0, 1, int(TotalD/self.Surfaces.cellsize))
                interpolator =  interp1d(distance, xy, kind=self.Linetype, axis=0)
                interpolated_points= interpolator(alpha)
               
                self.interpolated_points=interpolated_points
                self.distance=distance
                self.distance2=np.linspace(0, TotalD, int(TotalD/self.Surfaces.cellsize))
                self.alpha=alpha
                           
                self.Sf.DrainLength.delete(0,tk.END)
                self.Sf.DrainLength.insert(0,int(TotalD))
            
            
                  
           
    def tangent_radial_lines(self,line):   
        linesize=np.size(line,axis=0)
        line=np.array(line,dtype=np.float64)
        line_new=np.zeros(((linesize-2)*100 + 2,2),dtype=np.float64)
        line_new_temp=np.zeros(((linesize-2)*100 + 2,2),dtype=np.float64)
        temp_k_list=np.zeros((100),dtype=np.float64)
        vectors=np.zeros((13,2),dtype=np.float64)
        integers=np.zeros((4),dtype=np.float64)
        #dxfinfo=np.zeros((np.size(line,axis=0)-2,2),dtype=np.float64)

        radii=np.array(range(1,int(self.Sf.maxrad.get()),int(self.Sf.steprad.get())),dtype=np.float64)
        #radii=np.array([0.1,0.2,0.3,0.4,0.5,0.6],dtype=np.float64)

        tangent_radial_lines_jit(line,line_new,line_new_temp,radii,vectors,temp_k_list,integers)
        
        
        return(line_new)

    #def prewritedxf(self):
        
        
        
    
    def Initial_setup(self):
        
        xy=self.line.get_xydata()
        
        if self.Linetype=='radius':
            line_new=self.tangent_radial_lines(self.line.get_xydata())
            
            distance = np.cumsum( np.sqrt(np.sum( np.diff(line_new, axis=0)**2, axis=1 )) )
            TotalD=distance[-1]*self.Surfaces.cellsize
            distance = np.insert(distance, 0, 0)/distance[-1]
            
            alpha = np.linspace(0, 1, int(TotalD/self.Surfaces.cellsize))
            interpolator = interp1d(distance, line_new, kind='linear', axis=0)
            interpolated_points= interpolator(alpha)
            
            
            self.interpolated_points=interpolated_points
            self.distance=distance
            self.distance2=np.linspace(0, TotalD, int(TotalD/self.Surfaces.cellsize))
            self.alpha=alpha
            self.lineRT.set_data(interpolated_points.T)
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)            
            self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.line)
            self.ax.draw_artist(self.lineRT)
            self.ax.draw_artist(self.lineSP)
            self.canvas.blit(self.ax.bbox)
        
        
        else:
            if self.Linetype=='quadratic' and xy.shape[0]==2:
                xxyy=[[xy[0,0],xy[0,1]],[(xy[0,0]+xy[1,0])/2,(xy[0,1]+xy[1,1])/2],[xy[1,0],xy[1,1]]]
                xy=np.array(xxyy)
    #            xy = self.line.get_transform().transform(self.line.get_xydata())
            distance = np.cumsum( np.sqrt(np.sum( np.diff(xy, axis=0)**2, axis=1 )) )
            TotalD=distance[-1]*self.Surfaces.cellsize
            distance = np.insert(distance, 0, 0)/distance[-1]
            
            alpha = np.linspace(0, 1, int(TotalD/self.Surfaces.cellsize))
            interpolator =  interp1d(distance, xy, kind=self.Linetype, axis=0)
            interpolated_points= interpolator(alpha)
            # print(interpolated_points)
            self.interpolated_points=interpolated_points
            self.distance=distance
            self.distance2=np.linspace(0, TotalD, int(TotalD/self.Surfaces.cellsize))
            self.alpha=alpha
            self.lineSP.set_data(interpolated_points.T)
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)            
            self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.line)
            self.ax.draw_artist(self.lineRT)
            self.ax.draw_artist(self.lineSP)
            self.canvas.blit(self.ax.bbox)
        
    
    def motion_notify_callback(self, event):
        if self.line.get_visible():
            'on mouse movement'
            if not self.showverts:
                return
            if self._ind is None:
                return
            if event.inaxes is None:
                return
            if event.button != 1:
                return
            x, y = event.xdata, event.ydata
   
            xy=self.line.get_xydata()
            xy[self._ind,0]=x
            xy[self._ind,1]=y
            #print(xy[self._ind]) ### 
            #print(self.line)
            
            self.line.set_data(xy.T)

            
            if self.Linetype=='radius':
                line_new=self.tangent_radial_lines(self.line.get_xydata())
                
                distance = np.cumsum( np.sqrt(np.sum( np.diff(line_new, axis=0)**2, axis=1 )) )
                TotalD=distance[-1]*self.Surfaces.cellsize
                distance = np.insert(distance, 0, 0)/distance[-1]
                
                alpha = np.linspace(0, 1, int(TotalD/self.Surfaces.cellsize))
                interpolator = interp1d(distance, line_new, kind='linear', axis=0)
                interpolated_points= interpolator(alpha)
                
                
                self.interpolated_points=interpolated_points
                self.distance=distance
                self.distance2=np.linspace(0, TotalD, int(TotalD/self.Surfaces.cellsize))
                self.alpha=alpha
                self.lineRT.set_data(interpolated_points.T)
                self.background = self.canvas.copy_from_bbox(self.ax.bbox)            
                self.canvas.restore_region(self.background)
                self.ax.draw_artist(self.line)
                self.ax.draw_artist(self.lineRT)
                self.ax.draw_artist(self.lineSP)
                self.canvas.blit(self.ax.bbox)
                
                
                
                 
#            xy = self.line.get_transform().transform(self.line.get_xydata())
            else:   
                if self.Linetype=='quadratic' and xy.shape[0]==2:
                    xxyy=[[xy[0,0],xy[0,1]],[(xy[0,0]+xy[1,0])/2,(xy[0,1]+xy[1,1])/2],[xy[1,0],xy[1,1]]]
                    xy=np.array(xxyy)
    #            xy = self.line.get_transform().transform(self.line.get_xydata())
                distance = np.cumsum( np.sqrt(np.sum( np.diff(xy, axis=0)**2, axis=1 )) )
                TotalD=distance[-1]*self.Surfaces.cellsize
                distance = np.insert(distance, 0, 0)/distance[-1]
                # alpha = np.linspace(0, 1, int(TotalD/self.Surfaces.cellsize))
                alpha = np.linspace(0, 1, int(TotalD/self.Surfaces.cellsize))
                interpolator =  interp1d(distance, xy, kind=self.Linetype, axis=0)
                interpolated_points= interpolator(alpha)
               
                self.interpolated_points=interpolated_points
                self.distance=distance
                self.distance2=np.linspace(0, TotalD, int(TotalD/self.Surfaces.cellsize))
                self.Des=self.Surfaces.Design[self.interpolated_points.astype(int)[:,1],self.interpolated_points.astype(int)[:,0]]
                self.alpha=alpha
                self.lineSP.set_data(interpolated_points.T) ###!
            
            
            # self.background = self.canvas.copy_from_bbox(self.ax.bbox)            
            self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.line)
            self.ax.draw_artist(self.lineRT)
            self.ax.draw_artist(self.lineSP)
            self.canvas.blit(self.ax.bbox)
            if self.plotActive:
                a=self.SlopeOp.get()
                if a=='Exponential Slope':
                    self.UpdatePlot()
                if a=='Benched':
                    self.UpdateBench()
                if a=='Linear Sections':
                    self.UpdatePlot()
                    self.UpdateLinearSection()
                
            self.Sf.DrainLength.delete(0,tk.END)
            self.Sf.DrainLength.insert(0,int(TotalD))
                
    def Update_Tiein(self):
        if self.line.get_visible():
            if self.Linetype=='radius':
                line_new=self.tangent_radial_lines(self.line.get_xydata())
                
                distance = np.cumsum( np.sqrt(np.sum( np.diff(line_new, axis=0)**2, axis=1 )) )
                TotalD=distance[-1]*self.Surfaces.cellsize
                distance = np.insert(distance, 0, 0)/distance[-1]
                
                alpha = np.linspace(0, 1, int(TotalD/self.Surfaces.cellsize))
                interpolator = interp1d(distance, line_new, kind='linear', axis=0)
                interpolated_points= interpolator(alpha)
                
                
                self.interpolated_points=interpolated_points
                self.distance=distance
                self.distance2=np.linspace(0, TotalD, int(TotalD/self.Surfaces.cellsize))
                self.alpha=alpha
                self.lineRT.set_data(interpolated_points.T)
                self.background = self.canvas.copy_from_bbox(self.ax.bbox)            
                self.canvas.restore_region(self.background)
                self.ax.draw_artist(self.line)
                self.ax.draw_artist(self.lineRT)
                self.ax.draw_artist(self.lineSP)
                self.canvas.blit(self.ax.bbox)
                
            if self.Linetype=='quadratic':
                xy=self.line.get_xydata()
                distance = np.cumsum( np.sqrt(np.sum( np.diff(xy, axis=0)**2, axis=1 )) )
                TotalD=distance[-1]
                distance = np.insert(distance, 0, 0)/distance[-1]
                
                alpha = np.linspace(0, 1, int(TotalD/self.Surfaces.cellsize))
                interpolator =  interp1d(distance, xy, kind=self.Linetype, axis=0)
                interpolated_points= interpolator(alpha)
               
                self.interpolated_points=interpolated_points
                self.distance=distance
                self.distance2=np.linspace(0, TotalD, int(TotalD/self.Surfaces.cellsize))
                self.alpha=alpha
                
                self.lineSP.set_data(interpolated_points.T)
                
            
                
            self.canvas.restore_region(self.background)
            
           
           
            self.ax.draw_artist(self.line)
            self.ax.draw_artist(self.lineRT)
            self.ax.draw_artist(self.lineSP)
            self.canvas.blit(self.ax.bbox)
            
            
            if self.plotActive:
                self.UpdateS(1)
                
                
class PolygonInteractor(object):
    showverts = True
    epsilon = 5  # max pixel distance to count as a vertex hit

    def __init__(self, Sf, poly,ID):
        # if poly.figure is None:
        #     raise RuntimeError('You must first add the polygon to a figure '
        #                        'or canvas before defining the interactor')
        self.ax = Sf.a
        self.f=Sf.f
        self.ID=ID
        self.poly = poly
        self.ax.add_artist(self.poly)
        canvas = poly.figure.canvas
        
        x, y = zip(*self.poly.xy)
        self.line = Line2D(x, y,marker='o', markerfacecolor='r',animated=False)
        self.ax.add_line(self.line)
        
        self.Boundary=None
        self.StrtSlp=None
        self.EndE=None
        self.EndSlp=None
        self.MaxE=None
        self.toeElev=None
        self.Volumes=None
        self.Domecontours=None
        self._ind = None  # the active vert
        self.label=None
        self.points=np.array([0,0])
        self.C=None
        self.Active=False
        self.Allpoints=Sf.Allpoints
        self.Lock=False
        self.cut=np.array([0.0])
        self.fill=np.array([0.0])
        self.area=np.array([0.0])
        self.density=0
        self.point=Sf.point
        canvas.mpl_connect('draw_event', self.draw_callback)
        # canvas.mpl_connect('button_press_event', self.button_press_callback)
        # canvas.mpl_connect('key_press_event', self.key_press_callback)
        # canvas.mpl_connect('button_release_event', self.button_release_callback)
        # canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        self.canvas = canvas
    
    def delete_p(self):
        self.line.set_visible(False)
        self.poly.set_visible(False)
        self.Active=False
    
    def draw_callback(self, event):
        
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.ax.draw_artist(self.poly)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)
        


    def poly_disconnect(self):
        self.poly.figure.canvas.mpl_disconnect
    
    def set_visible(self,VIS):
        self.line.set_visible(VIS)
        self.poly.set_visible(VIS)
        # self.line.set_visible(not self.line.get_visible())
        # self.poly.set_visible(not self.poly.get_visible())
        
    def get_ind_under_point(self, event):
        'get the index of the vertex under point if within epsilon tolerance'

        # display coords
        xy = np.asarray(self.poly.xy)
        xyt = self.poly.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.hypot(xt - event.x, yt - event.y)
        indseq, = np.nonzero(d == d.min())
        ind = indseq[0]

        if d[ind] >= self.epsilon:
            ind = None
        if ind is not None:
            self.points=np.array([0])
        return ind
    
    # def get_movement_polygon(self):
    #     'get the index of the vertex under point if within epsilon tolerance'
    #     if self.Active:
    #         # display coords
    #         inpoly=np.zeros_like(Aobj.arrClip)
    #         for p in self.points:
    #             inpoly[p[1],p[0]]=1
    #         material_opt_polygon(inpoly,Aobj.arrClip,AOobj.arrClip,cellsize,ax)
    #         ax.figure.canvas.draw()
            

    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        
        if not self.showverts:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self._ind = self.get_ind_under_point(event)
    
    def button_release_callback(self, event,Surfaces,Sf):
        'whenever a mouse button is released'
        if not self.showverts:
            return
        if event.button != 1:
            return
        if self._ind != None:
            # self.Inside=self.poly.contains_points(self.ax.transData.transform(self.Allpoints))
            # Surfaces.Poly.fill(0)
            # for p,t in zip (self.Allpoints,self.Inside):
            #     if t:
            #         Surfaces.Poly[p[1],p[0]]=self.ID
                    
            # self.cut=np.array([0.0])
            # self.fill=np.array([0.0])
            # polygon_cut_fill(Surfaces.Design,Surfaces.Survey,Surfaces.Poly,self.cut,self.fill,Surfaces.cellsize,self.ID)
            # Sf.CutP.delete(0,tk.END)
            # Sf.FillP.delete(0,tk.END)
            # Sf.CutP.insert(0,int(self.cut))
            # Sf.FillP.insert(0,int(self.fill))
            
            
            # self.area=np.count_nonzero(self.Inside)*Surfaces.cellsize**2
            # Sf.AreaPoly.delete(0,tk.END)
            # Sf.AreaPoly.insert(0,int(self.area))
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)
            self.ax.draw_artist(self.poly)
            self.ax.draw_artist(self.line)
            self.canvas.blit(self.ax.bbox)
            self.canvas.draw_idle()
            # Draw_Update(SF,Surfaces)
            # self.draw_callback( 1)
            # print(np.count_nonzero(self.Inside))
            
            
        self._ind = None
        
                
    def updateCF(self, Surfaces,Sf):
        print("released")
        # 'whenever a mouse button is released'
        # self.Inside=self.poly.contains_points(self.ax.transData.transform(self.Allpoints))
        # Surfaces.Poly.fill(0)
        # for p,t in zip (self.Allpoints,self.Inside):
        #     if t:
        #         Surfaces.Poly[p[1],p[0]]=self.ID
                    
        # self.cut=np.array([0.0])
        # self.fill=np.array([0.0])
        # polygon_cut_fill(Surfaces.Design,Surfaces.Survey,Surfaces.Poly,self.cut,self.fill,Surfaces.cellsize,self.ID)
        # Sf.CutP.delete(0,tk.END)
        # Sf.FillP.delete(0,tk.END)
        # Sf.CutP.insert(0,int(self.cut))
        # Sf.FillP.insert(0,int(self.fill))


        
    def key_press_callback(self, event):
        'whenever a key is pressed'
        if not event.inaxes:
            return
        if event.key == 't':
            self.showverts = not self.showverts
            self.line.set_visible(self.showverts)
            if not self.showverts:
                self._ind = None
        elif event.key == 'd':
            ind = self.get_ind_under_point(event)
            if ind is not None:
                self.poly.xy = np.delete(self.poly.xy,
                                         ind, axis=0)
                self.line.set_data(zip(*self.poly.xy))
        elif event.key == 'i':
            xys = self.poly.get_transform().transform(self.poly.xy)
            p = event.x, event.y  # display coords
            for i in range(len(xys) - 1):
                start = xys[i]
                end = xys[i + 1]
                
                line_vec = vector(start, end)
                pnt_vec = vector(start, p)
                line_len = length(line_vec)
                line_unitvec = unit(line_vec)
                pnt_vec_scaled = scale(pnt_vec, 1.0/line_len)
                t = dot(line_unitvec, pnt_vec_scaled)    
                if t < 0.0:
                    t = 0.0
                elif t > 1.0:
                    t = 1.0
                nearest = scale(line_vec, t) 

                d = distance(nearest, pnt_vec)
                if d <= self.epsilon:
                    self.poly.xy = np.insert(
                        self.poly.xy, i+1,
                        [event.xdata, event.ydata],
                        axis=0)
                    self.line.set_data(zip(*self.poly.xy))
                    break
                
                
                
    def deselect(self,event,Surfaces,Sf):
        if self.poly.get_visible()==True:
            # print('select polygons')
            self.Active=False
            self.poly.set_color('b')
            
    def updatePolygonPoints(self,Sf,Surfaces):
        # Get polygon bounding box to reduce computations on larger arrays
        inv = self.ax.transData.inverted()
        poly_extents = inv.transform(self.poly.get_extents().get_points())
        min_x, min_y = np.floor(poly_extents[0]).astype(int)
        max_x, max_y = np.floor(poly_extents[1]).astype(int)
        bbox = np.where((self.Allpoints[:,0]>=min_x) & (self.Allpoints[:,0]<=max_x) & (self.Allpoints[:,1]>=min_y) & (self.Allpoints[:,1]<=max_y))

        # Create a boolean array with False values everywhere
        self.Inside = np.zeros(self.Allpoints.shape[0], dtype=bool)

        # Check points for inside polygon within its bounding box 
        self.Inside[bbox]=self.poly.contains_points(self.ax.transData.transform(self.Allpoints[bbox]))
        
        Surfaces.Poly.fill(0)
        
        inside_indices = np.where(self.Inside)
        Surfaces.Poly[self.Allpoints[inside_indices, 1], self.Allpoints[inside_indices, 0]] = self.ID
                
        self.getpolycutfill(Sf,Surfaces)
    
    def UpdateElevDiff(self,Surfaces):
        Tk().withdraw()
        filename = asksaveasfilename(title = "Save design",filetypes = (("csv files","*.csv"),("all files","*.*")))
        path = filename
        Output=[]
        Surfaces.Poly.fill(0)
        inside_indices = np.where(self.Inside)
        Surfaces.Poly[self.Allpoints[inside_indices, 1], self.Allpoints[inside_indices, 0]] = self.ID
        
        self.erosion=np.zeros((Surfaces.Alldiff.shape[2]))
        self.deposition=np.zeros((Surfaces.Alldiff.shape[2]))
        self.erosionDiff=np.zeros_like(self.deposition)
        polygon_erosion_deposition(Surfaces.Alldiff,Surfaces.Poly,self.erosion,self.deposition,Surfaces.cellsize,self.ID)
        self.erosionDiff[0]=self.erosion[0]
        for i in range (1, self.erosion.shape[0]-1):
            self.erosionDiff[i]=self.erosion[i+1]-self.erosion[i]
        fig,(ax1,ax2)=plt.subplots(2,1,sharex=True)
        # ax=plt.axes()
        ax1.plot(self.erosion)
        ax1.plot(self.deposition)
        ax2.plot(self.erosionDiff)
        fig.show()
        for i in range (0,self.erosion.shape[0]):
            Output.append([self.erosion[i],self.deposition[i]])
        if len(filename)>3:
            if filename[-4]!=".":
                filename=filename +".csv"
            else:
                filename=filename +".csv"
        with open(filename,'w') as output:
            writr=csv.writer(output, lineterminator='\n')
            writr.writerows(Output)
        
    def updatecutfill(self,Surfaces,Lines):
        Surfaces.Poly.fill(0)
        inside_indices = np.where(self.Inside)
        Surfaces.Poly[self.Allpoints[inside_indices, 1], self.Allpoints[inside_indices, 0]] = self.ID
        
        self.cut=np.array([0.0])
        self.fill=np.array([0.0])
        polygon_cut_fill(Surfaces.Design,Surfaces.Survey,Surfaces.Poly,self.cut,self.fill,Surfaces.cellsize,self.ID)
        self.area=np.count_nonzero(self.Inside)*Surfaces.cellsize**2
        length=0.0
        for l in Lines:
            length+=Surfaces.cellsize*np.count_nonzero(self.poly.contains_points(self.ax.transData.transform(l.interpolated_points)))
        self.density=length/(self.area/10000)
        
    def select(self,event,Surfaces,Sf):
        if self.poly.get_visible()==True:
            # print('select polygons')
            self.Active=False
            self.poly.set_color('b')
            if self.poly.contains_point([event.x,event.y]):
                self.Active = not self.Active
                if self.Active:
                      self.poly.set_color('r')
                
                start_time = time.time()
               
                # Get polygon bounding box to reduce computations on larger arrays
                inv = self.ax.transData.inverted()
                poly_extents = inv.transform(self.poly.get_extents().get_points())
                min_x, min_y = np.floor(poly_extents[0]).astype(int)
                max_x, max_y = np.floor(poly_extents[1]).astype(int)
                bbox = np.where((self.Allpoints[:,0]>=min_x) & (self.Allpoints[:,0]<=max_x) & (self.Allpoints[:,1]>=min_y) & (self.Allpoints[:,1]<=max_y))

                
                # Create a boolean array with False values everywhere
                self.Inside = np.zeros(self.Allpoints.shape[0], dtype=bool)
                
                
                # Check points for inside polygon within its bounding box 
                self.Inside[bbox]=self.poly.contains_points(self.ax.transData.transform(self.Allpoints[bbox]))
                
                end_time = time.time()
                elapsed_time0 = end_time - start_time

                

                start_time = time.time()
                Surfaces.Poly.fill(0)
                
                inside_indices = np.where(self.Inside)
                Surfaces.Poly[self.Allpoints[inside_indices, 1], self.Allpoints[inside_indices, 0]] = self.ID
                
                end_time = time.time()
                elapsed_time2 = end_time - start_time
                
                print(f"Time taken for matplotlib function: {elapsed_time0} and for numpy operation: {elapsed_time2} (seconds)")
                
                self.cut=np.array([0.0])
                self.fill=np.array([0.0])
                self.cutfillArea=np.array([0.0])
                
                
                
                from Landformer_Functions import RunSlope2
                S=RunSlope2(Surfaces)
                self.SlopeArea=np.array([0.0])
                polygon_cut_fillAreaS(Surfaces.Design,Surfaces.Survey,Surfaces.Poly,self.SlopeArea,Surfaces.cellsize,self.ID,S)
                print(self.SlopeArea[0]*Surfaces.cellsize**2)
                self.getpolycutfill(Sf,Surfaces)
                self.checkpolylock(Sf)
                
                    
                # Surfaces.Poly[self.Allpoints[np.where(self.Inside)]]=self.ID
                # print(self.Allpoints[np.where(self.Inside)])
                # plt.imshow(Surfaces.Poly)
   
    def getpolycutfill(self,Sf,Surfaces):
        polygon_cut_fill(Surfaces.Design,Surfaces.Survey,Surfaces.Poly,self.cut,self.fill,Surfaces.cellsize,self.ID)
        polygon_cut_fillArea(Surfaces.Design,Surfaces.Survey,Surfaces.Poly,self.cutfillArea,Surfaces.cellsize,self.ID)
        Sf.CutP.delete(0,tk.END)
        Sf.FillP.delete(0,tk.END)
        Sf.AreaPoly.delete(0,tk.END)
        
        Sf.CutP.insert(0,int(self.cut))
        Sf.FillP.insert(0,int(self.fill))
        self.area=np.count_nonzero(self.Inside)*Surfaces.cellsize**2
        Sf.AreaPoly.insert(0,int(self.area))
        self.cutfillArea[0]=self.cutfillArea[0]*Surfaces.cellsize**2
        Sf.DrainPoly.delete(0,tk.END)
        Sf.DrainPoly.insert(0,int(self.cutfillArea))
        
        try:
            Sf.CutPw.delete(0,tk.END)
            Sf.FillPw.delete(0,tk.END)
            Sf.AreaPolyw.delete(0,tk.END)
            
            Sf.CutPw.insert(0,int(self.cut))
            Sf.FillPw.insert(0,int(self.fill))
            Sf.AreaPolyw.insert(0,int(self.area))
            Sf.DrainPolyw.delete(0,tk.END)
            Sf.DrainPolyw.insert(0,int(self.cutfillArea))
        except:
            pass
   
    def checkpolylock(self,Sf):
        if self.label is not None:
            Sf.buttonPolyLock.config(text=self.label) 
            try: Sf.buttonPolyLockw.config(text=self.label) 
            except: pass

        else:
            Sf.buttonPolyLock.config(text='Toggle (Unlocked)')
            try: Sf.buttonPolyLockw.config(text='Toggle (Unlocked)')
            except: pass

                
    def Free_Drain(self,Surfaces,Sf,Elevpoints,slope):
        self.Scratch=np.zeros_like(Surfaces.Design)
        self.Scratch=Free_poly(Surfaces.Design,Surfaces.cellsize,Surfaces.Poly,self.ID,slope,self.Scratch)
        transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        try:
            for tp in Sf.l[0].collections:
                tp.remove()
        except:
            pass
        Sf.l=[Sf.a.contour(self.Scratch[int(Sf.a.get_ylim()[0]):int(Sf.a.get_ylim()[1]),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])], Sf.levels,linewidths=0.3,colors='red',antialiased=True) ]   
        Sf.f.canvas.restore_region(background)
        for tp in Sf.l[0].collections:
            tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
        Sf.f.canvas.blit(Sf.a.bbox)
        
    def Benches(self,Surfaces,Sf,BenchH,BenchBottom,BenchTop):
        self.Scratch=np.zeros_like(Surfaces.Design)
        cut1=np.array([0])
        fill1=np.array([0])
        from Landformer_Functions import RunSlope2
        S=RunSlope2(Surfaces)
        Apply_Benches4(self.Scratch,Surfaces.Design,Surfaces.Survey,BenchH,BenchBottom,Surfaces.Poly,self.ID,S,BenchTop)
        Bench_Volumes(self.Scratch,Surfaces.Design,cut1,fill1,Surfaces.Poly,self.ID)
        # print(('cut,fill',cut1[0]*Surfaces.cellsize**2,fill1[0]*Surfaces.cellsize**2))
        transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        try:
            for tp in Sf.l[0].collections:
                tp.remove()
        except:
            pass
        Sf.l=[Sf.a.contour(self.Scratch[int(Sf.a.get_ylim()[0]):int(Sf.a.get_ylim()[1]),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])], Sf.levels,linewidths=0.3,colors='red',antialiased=True) ]   
        Sf.f.canvas.restore_region(background)
        for tp in Sf.l[0].collections:
            tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
        Sf.f.canvas.blit(Sf.a.bbox)
        Sf.f.canvas.draw_idle()
        # Draw_Update(Sf,Surfaces)
    
    def Distance_to(self,Surfaces,Sf,Elevpoints,slope,elev):
            self.Distance=np.zeros_like(Surfaces.Design)
            l=[]
            for p in Elevpoints:
                x=int(p.annot.xy[1])
                y=int(p.annot.xy[0])
                l.append([x,y])
            spigots=np.array(l)
            self.Distance,Tailings=Distance_to_spigot(spigots,Surfaces.Design,Surfaces.cellsize,Surfaces.Poly,self.ID,self.Distance,slope,elev)
            self.Scratch=Tailings
            DrawDistance(Surfaces,Sf,self.Distance,Tailings)
            
                        
    def Slope_to(self,Surfaces,Sf,Elevpoints,slope):
        self.Scratch=np.zeros_like(Surfaces.Design)
        for p in Elevpoints:
            x=int(p.annot.xy[1])
            y=int(p.annot.xy[0])
            Slope_to_points(x,y,Surfaces.Design,Surfaces.cellsize,Surfaces.Poly,self.ID,slope,self.Scratch)
            # print('run')
            # print((x,y))
        transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        try:
            for tp in Sf.l[0].collections:
                tp.remove()
        except:
            pass
        Sf.l=[Sf.a.contour(self.Scratch[int(Sf.a.get_ylim()[0]):int(Sf.a.get_ylim()[1]),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])], Sf.levels,linewidths=0.3,colors='red',antialiased=True) ]   
        Sf.f.canvas.restore_region(background)
        for tp in Sf.l[0].collections:
            tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
        Sf.f.canvas.blit(Sf.a.bbox)
        # Draw_Update(Sf,Surfaces)
    
    def VerticalOffset(self,Surfaces,Sf):
        offV=float(Sf.VOff.get())
        Vertical_Offset(Surfaces.Design,Surfaces.cellsize,Surfaces.Poly,self.ID,offV)
        # background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        Draw_contours2(Sf,Surfaces)
        
        Sf.CutFill()
        
  
                    
    def RunPolyConstant(self,Surfaces,Sf,constant):
        Set_to_constant(Surfaces.Design,Surfaces.Poly,self.ID,constant)
        Draw_contours2(Sf,Surfaces)
        
        Sf.CutFill()
        

    
    def SetSurv(self,Surfaces,Sf):
        
        Set_Surv(Surfaces.Design,Surfaces.cellsize,Surfaces.Poly,self.ID,Surfaces.Survey)
        # background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        Draw_contours2(Sf,Surfaces)
        
        Sf.CutFill()
        
    def Settlement(self,Surfaces,Sf):
        
        Invert_Settlement(Surfaces.Design,Surfaces.Survey,Surfaces.Poly,self.ID)
        # Create_Settlement(Surfaces.Design,Surfaces.Survey,Surfaces.Poly,self.ID)
        # background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        Draw_contours2(Sf,Surfaces)
        
        Sf.CutFill()
        
    
    def Dome_to(self,Surfaces,Sf,Elevpoints,slope):
        self.Scratch=np.zeros_like(Surfaces.Design)
        Dome_to_points(Surfaces.Design,Surfaces.cellsize,Surfaces.Poly,self.ID,slope,self.Scratch)
        transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        try:
            for tp in Sf.l[0].collections:
                tp.remove()
        except:
            pass
        Sf.l=[Sf.a.contour(self.Scratch[int(Sf.a.get_ylim()[0]):int(Sf.a.get_ylim()[1]),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])], Sf.levels,linewidths=0.3,colors='red',antialiased=True) ]   
        Sf.f.canvas.restore_region(background)
        for tp in Sf.l[0].collections:
            tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
        Sf.f.canvas.blit(Sf.a.bbox)
    
    
    def polygonpoints(self,Sf,Surfaces):
        self.Scratch=np.zeros_like(Surfaces.Design)
        for i in range(0,Surfaces.Design.shape[0]):
            for j in range(0,Surfaces.Design.shape[1]):
                self.Scratch[i,j]=Surfaces.Design[i,j]
        polyvertex=self.poly.get_xy()
        poly_path = mplPath.Path(np.array(polyvertex))
        polymesh=[]
        for i in range(int(np.min(polyvertex[:,0])),int(np.max(polyvertex[:,0]+1))):
            for j in range(int(np.min(polyvertex[:,1])),int(np.max(polyvertex[:,1]+1))):
                point=(i,j)
                a=poly_path.contains_point(point)
                if a is True:
                    polymesh.append([i,j])
        boundary=[]
        boundaryZ=[]        
        for p in polymesh:
            check=0
            for ii in range (-1,2):
                for jj in range (-1,2):
                    if p[0]+ii>0 and p[0]+ii<Surfaces.Design.shape[1] and p[1]+jj>0 and p[1]+jj<Surfaces.Design.shape[0]:
                        point=(p[0]+ii,p[1]+jj)
                        if not poly_path.contains_point(point):
                           check=1
            if check==1:
                boundary.append([p[1],p[0]])
                boundaryZ.append(Surfaces.Design[p[1],p[0]])
        boundary=np.array(boundary)
        boundaryZ=np.array(boundaryZ)
        polymesh=np.array(polymesh)
        interp = interpolate.LinearNDInterpolator(boundary,boundaryZ)      
        Z=interp(polymesh[:,1],polymesh[:,0])
        for i in range (0,polymesh.shape[0]):
            self.Scratch[polymesh[i,1],polymesh[i,0]]=Z[i]
                    
        transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        try:
            for tp in Sf.l[0].collections:
                tp.remove()
        except:
            pass
        Sf.l=[Sf.a.contour(self.Scratch[int(Sf.a.get_ylim()[0]):int(Sf.a.get_ylim()[1]),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])], Sf.levels,linewidths=0.3,colors='red',antialiased=True) ]   
        Sf.f.canvas.restore_region(background)
        for tp in Sf.l[0].collections:
            tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
        Sf.f.canvas.blit(Sf.a.bbox)
        
    def Remove_contours(self,Sf,Surfaces):
        
        transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        try:
            self.pointmarkers.remove()
        except:
            pass
        try:
            for tp in Sf.l[0].collections:
                tp.remove()
        except:
            pass
        
        Sf.f.canvas.blit(Sf.a.bbox)
        # Draw_Update(Sf,Surfaces)
        
    def Apply_Poly(self,Surfaces,Sf):
        Set_points(Surfaces.Design,Surfaces.Poly,self.ID,self.Scratch)
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        try:
            for tp in Sf.l[0].collections:
                tp.remove()
        except:
            pass
        try:
            for tp in Sf.p[0].collections:
                tp.remove()
        except:
            pass
        try:    
            Sf.p=[Sf.a.contour(Surfaces.Design[int(Sf.a.get_ylim()[0]):int(Sf.a.get_ylim()[1]),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])], Sf.levels,linewidths=0.3,colors='white',antialiased=True) ]
            Sf.f.canvas.restore_region(background)
        except:
            return
        
        Sf.f.canvas.restore_region(background)
        Sf.f.canvas.blit(Sf.a.bbox)
        
        
    def ToggleLock(self,Surfaces,Sf):
        print("Changing Lock")
        if self.Lock==False:
            self.label = 'Toggle (Locked)'
            Surfaces.Active[np.where(Surfaces.Poly==self.ID)]=0
            Sf.buttonPolyLock.config(text=self.label)
            try: Sf.buttonPolyLockw.config(text=self.label)
            except: pass

        else:
            self.label = 'Toggle (unlocked)'
            Surfaces.Active[np.where(Surfaces.Poly==self.ID)]=1
            Sf.buttonPolyLock.config(text=self.label)
            try: Sf.buttonPolyLockw.config(text=self.label)
            except: pass
            #self.Lock=False
        self.Lock=not self.Lock

    def motion_notify_callback(self, event):
        'on mouse movement'
        if not self.showverts:
            return
        if self._ind is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        x, y = event.xdata, event.ydata

        self.poly.xy[self._ind] = x, y
        if self._ind == 0:
            self.poly.xy[-1] = x, y
        elif self._ind == len(self.poly.xy) - 1:
            self.poly.xy[0] = x, y
        self.line.set_data(zip(*self.poly.xy))

        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.poly)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)
        
    def DistanceExceeded (self,Surfaces,Se,D):
        D=D.split(',')
        # print(D)
        # print(len(D))
        if len(D)<2:
            D.append(1000)
        if self.Volumes is not None:
            Se.RemoveArrows()
            for p in self.DistanceLsorted:
                i=self.CostInd[p,0]
                j=self.CostInd[p,1]
                widthV=((self.maxvol-self.Volumes[i,j])/(self.maxvol-0))
                widthV=(1-widthV)*10
                xc=int(self.cutcentroids[i][0])
                yc=int(self.cutcentroids[i][1])
                xf=int(self.fillcentroids[j][0])
                yf=int(self.fillcentroids[j][1])
                if self.Distances[i,j]<float(D[0]) and self.Volumes[i,j]>10:
                    self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='green',fc='green',width=widthV,lw=0.1)
                if self.Distances[i,j]>float(D[0]) and self.Distances[i,j]<float(D[1]) and self.Volumes[i,j]>10:
                    self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='blue',fc='blue',width=widthV,lw=0.1)
                if self.Distances[i,j]>float(D[1]) and self.Volumes[i,j]>10:
                    self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='orange',fc='orange',width=widthV,lw=0.1)
                    # cnt+=1
        cmap = colors.ListedColormap(['green','blue','orange'])
        bounds=[0,float(D[0]),float(D[1]),1000]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        img = self.ax.imshow(np.array([[0,1]]), cmap=cmap, norm=norm)
        img.set_visible(False)
        CB=self.f.colorbar(img,ticks=[0,float(D[0]),float(D[1]),1000],shrink=0.5)
        # CB.ax.set_yticklabels([0,float(D[0]),float(D[1]),1000],color='white')
        CB.ax.set_yticklabels([0,float(D[0]),float(D[1]),1000],color='white')
        CB.ax.set_ylabel('Distance',color='white')
        CB.ax.set_title('Movement Distance',color='white')
        self.canvas.draw_idle()  
        
    def ArrowConstraints (self,Surfaces,Se,dmin,dmax,vmin,vmax):
        if self.Volumes is not None:
            Se.RemoveArrows()
            for p in self.DistanceLsorted:
                i=self.CostInd[p,0]
                j=self.CostInd[p,1]
                widthV=((self.maxvol-self.Volumes[i,j])/(self.maxvol-0))
                widthV=(1-widthV)*10
                xc=int(self.cutcentroids[i][0])
                yc=int(self.cutcentroids[i][1])
                xf=int(self.fillcentroids[j][0])
                yf=int(self.fillcentroids[j][1])
                if self.Distances[i,j]>float(dmin) and self.Distances[i,j]<float(dmax)  and self.Volumes[i,j]>float(vmin) and self.Distances[i,j]<float(vmax):
                    self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='blue',fc='blue',width=widthV,lw=0.1)
                    
        self.canvas.draw_idle()
            
    def AllArrows (self,Surfaces,Se):
        if self.Volumes is not None:
            Se.RemoveArrows()
            # argInd=self.DistanceLsorted
            for p in self.DistanceLsorted:
                i=self.CostInd[p,0]
                j=self.CostInd[p,1]
                        
                widthV=((self.maxvol-self.Volumes[i,j])/(self.maxvol-0))
                widthV=(1-widthV)*10
                xc=int(self.cutcentroids[i][0])
                yc=int(self.cutcentroids[i][1])
                        
                xf=int(self.fillcentroids[j][0])
                yf=int(self.fillcentroids[j][1])
                
                if self.Distances[i,j]>0 and self.Volumes[i,j]>50:
                    self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='k',width=widthV,lw=0.1)
                
                    # cnt+=1
            self.canvas.draw_idle()
            
    def Fraction(self,Surfaces,Se,percent):
        if self.Volumes is not None:
            percent=100-percent
            if percent>100:
                percent=100
            if percent<0:
                percent=0
            number=self.Cost.shape[0]
            number=int(number*percent/100)
            argInd=np.argpartition(self.Cost,number)
        
            Se.RemoveArrows()
            for p in argInd[number:-1]:
                i=self.CostInd[p,0]
                j=self.CostInd[p,1]
                widthV=((self.maxvol-self.Volumes[i,j])/(self.maxvol-0))
                widthV=(1-widthV)*10
                xc=int(self.cutcentroids[i][0])
                yc=int(self.cutcentroids[i][1])
                xf=int(self.fillcentroids[j][0])
                yf=int(self.fillcentroids[j][1])
                slope=-100*(Surfaces.Design[xc,yc]-Surfaces.Design[xf,yf])/self.Distances[i,j]
                if self.Distances[i,j]<800 and self.Volumes[i,j]>0:
                        self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='k',width=widthV,lw=0.1)
                if self.Distances[i,j]>800 and self.Volumes[i,j]>0:
                    self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='red',width=widthV,lw=0.1)
                
                    # cnt+=1
            self.canvas.draw_idle()
            
    def Uphill(self,Surfaces,Se):
        if self.Volumes is not None:
            Se.RemoveArrows()
            for i in range (0,self.Volumes.shape[0]-2):
                for j in range (0,self.Volumes.shape[1]-2):
                    if self.Volumes[i,j]>0:# and DistUpDwn[i,j]<350:
                        
                        widthV=((self.maxvol-self.Volumes[i,j])/(self.maxvol-0))
                        widthV=(1-widthV)*10
                        xc=int(self.cutcentroids[i][0])
                        yc=int(self.cutcentroids[i][1])
                                
                        xf=int(self.fillcentroids[j][0])
                        yf=int(self.fillcentroids[j][1])
                        slope=-100*(Surfaces.Design[xc,yc]-Surfaces.Design[xf,yf])/self.Distances[i,j]
                        # if slope<0 and self.Volumes[i,j]>50:
                        #     ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='k',width=widthV)
                        if slope>0 and self.Volumes[i,j]>50:
                            self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='red',width=widthV,lw=0.1)
                        
                    # cnt+=1
            self.canvas.draw_idle()
        
    def material_opt_polygon(self,Surfaces,Se,block):            
        block=block/Surfaces.cellsize
        x= Surfaces.Design.shape[0]
        y= Surfaces.Design.shape[1]
        sq=Surfaces.cellsize**2
        Aa= np.zeros_like(Surfaces.Design)
        Areas=np.zeros((int(x/block)+1,int(y/block)+1))
        fillcentroids=np.zeros((Areas.shape[0]*Areas.shape[1],2))
        cutcentroids=np.zeros((Areas.shape[0]*Areas.shape[1],2))
        fill=np.zeros((Areas.shape[0]*Areas.shape[1]))
        cut=np.zeros((Areas.shape[0]*Areas.shape[1]))
        C=np.zeros_like(Surfaces.Design)
        TotalCut=0
        TotalFill=0
        Volumes=np.zeros((int(Surfaces.Design.shape[0])*int(Surfaces.Design.shape[1])))
        Allx=np.zeros((int(Surfaces.Design.shape[0])*int(Surfaces.Design.shape[1])))
        Ally=np.zeros((int(Surfaces.Design.shape[0])*int(Surfaces.Design.shape[1])))
        Allcount=np.zeros((int(Surfaces.Design.shape[0])*int(Surfaces.Design.shape[1])))
        cutcount=np.array([0])
        fillcount=np.array([0])
        
        get_cut_fill_Polygon(Surfaces.Poly,Surfaces.Design,Aa,block,Surfaces.Survey,C,TotalFill,TotalCut,cutcentroids,fillcentroids,cut,fill,Volumes,cutcount,fillcount,Allx,Ally,Allcount,Surfaces.cellsize,self.ID)
        cut=cut[0:cutcount[0]]
        fill=fill[0:fillcount[0]]
        cutcentroids=cutcentroids[0:cutcount[0],:]
        fillcentroids=fillcentroids[0:fillcount[0],:]
        Dist=np.zeros((cutcount[0]+2,fillcount[0]+2))
        DistUpDwn=np.zeros((cutcount[0]+2,fillcount[0]+2))
                        
        get_distances(cutcentroids,fillcentroids,Dist,DistUpDwn,cut,fill,Surfaces.cellsize,Surfaces.Design)
        
        Distances=np.copy(Dist)
        DistancesUpDwn=np.copy(DistUpDwn)
        
        B=np.zeros_like(Dist)     
        # plt.imshow(Aa)
        print('start optimization')
        VogelApproxNmb(DistUpDwn,B)
        print(DistUpDwn.shape)
        print(Dist.shape)
        print('optimization done')
        cnt=0
        sumcost=0
        sumdistance=0
        sumvolume=0
        maxcost=0
        maxvol=0
        sumcostUpDwn=0
        sumdistanceUpDwn=0
        UpDistanceLinear=0
        UpDistanceNonLinear=0
        UpCostLinear=0
        UpCostNonLinear=0
        UphillVolume=0
        self.Cost=[]
        self.CostInd=[]
        self.DistanceL=[]
        self.DistanceLUpDwn=[]
        for i in range (0,B.shape[0]-2):
            for j in range (0,B.shape[1]-2):
                if B[i,j]>10:
                    self.DistanceL.append(Dist[i,j])
                    self.DistanceLUpDwn.append(DistUpDwn[i,j])
                    self.Cost.append(B[i,j]*Dist[i,j])
                    self.CostInd.append([i,j])
                    if B[i,j]*Dist[i,j]>maxcost:
                        maxcost=B[i,j]*Dist[i,j]
                    if B[i,j]>maxvol:
                        maxvol=B[i,j]
        
        self.DistanceLsorted=np.argsort(self.DistanceL)
        self.DistanceLsortedUpDwn=np.argsort(self.DistanceLUpDwn)
        self.DistanceLsorted=self.DistanceLsorted[::-1]
        self.DistanceLsortedUpDwn=self.DistanceLsortedUpDwn[::-1]

        cut0=0
        fill0=0
        for i in range (0,Surfaces.Design.shape[0]):
            for j in range (0,Surfaces.Design.shape[1]):
                if Surfaces.Poly[i,j]==self.ID:
                    dz=Surfaces.Design[i,j]-Surfaces.Survey[i,j]
                    if dz>0:
                        fill0+=dz*sq
                    else:
                        cut0-=dz*sq
        # Outlist=[]
        self.Cost=np.array(self.Cost)
        self.CostInd=np.array(self.CostInd)
        self.maxvol=maxvol
        self.maxcost=maxcost
        self.Volumes=B
        self.averageV=np.mean(B[np.where(B>0)])
        self.StdV=np.std(B[np.where(B>0)])
        print((self.averageV,self.StdV))
        self.cutcentroids=cutcentroids
        self.fillcentroids=fillcentroids
        self.Distances=Distances    
        self.DistancesUpDwn=DistancesUpDwn  
        Vertical_Change_Names=['<-10','[-10,-8)','[-8,-6)','[-6,-5)','[-5,-4)','[-4,-3)','[-3,-2)','[-2,-1)','[-1,0)','[0,1)','[1,2)','[2,3)','[3,4)','[4,5)','[5,6)','[6,8)','[8,10)','>10']
        Vertical_Change_Bins=[-10,-8,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,8,10]
        Vertical_Change_Data=np.zeros((np.size(Vertical_Change_Names,axis=0)))
        Distance_Bins=['Distance (m)'] + list(range(0,5001,50)) + ['>5000']
        
        Grade2percentdown=['Slope2percentdown (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade5percentdown=['Slope5percentdown (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade10percentdown=['Slope10percentdown (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade20percentdown=['Slope20percentdown (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade30percentdown=['Slope30percentdown (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade40percentdown=['Slope40percentdown (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade50percentdown=['Slope50percentdown (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        
        Grade2percentup=['Slope2percentup (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade5percentup=['Slope5percentup (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade10percentup=['Slope10percentup (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade20percentup=['Slope20percentup (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade30percentup=['Slope30percentup (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade40percentup=['Slope40percentup (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        Grade50percentup=['Slope50percentup (m)'] + list(np.zeros((len(Distance_Bins)-1)))
        
        Gradehorizontal=['Slopehorizontal (m)'] + list(np.zeros((len(Distance_Bins)-1)))
                
        Volume_Bins=['Volume (m3)'] + list(np.zeros((len(Distance_Bins)-1)))
        Volume_Bins_Up=['Uphill Volume (m3)'] + list(np.zeros((len(Distance_Bins)-1)))
        Volume_Bins_Down=['Downhill Volume (m3)'] + list(np.zeros((len(Distance_Bins)-1)))
        
        Downhill_less_100m=['Downhill < 100m (m3,average%)'] + list(np.zeros((2)))
        Downhill_100m_to_200m=['Downhill 100m-200m (m3,average%)'] + list(np.zeros((2)))
        Downhill_200m_to_300m=['Downhill 200m-300m (m3,average%)'] + list(np.zeros((2)))
        Downhill_greater_300m=['Downhill >300m (m3,average%)'] + list(np.zeros((2)))
        Uphill_less_100m=['Uphill < 100m (m3,average%)'] + list(np.zeros((2)))
        Uphill_100m_to_200m=['Uphill 100m-200m (m3,average%)'] + list(np.zeros((2)))
        Uphill_200m_to_300m=['Uphill 200m-300m (m3,average%)'] + list(np.zeros((2)))
        Uphill_greater_300m=['Uphill >300m (m3,average%)'] + list(np.zeros((2)))
        ArrowAttributes=[['x1','y1','x2','y2','dx','dy','Polygon ID','ShapeID','length','volume']]
        Load_Haul_Cutoff=250
        for i in range (0,self.Volumes.shape[0]-2):
            for j in range (0,self.Volumes.shape[1]-2):
                if B[i,j]>0:
                    
                    widthV=((maxvol-self.Volumes[i,j])/(maxvol-0))
                    widthV=(1-widthV)*10
                    xc=int(self.cutcentroids[i][0])
                    yc=int(self.cutcentroids[i][1])
                            
                    xf=int(self.fillcentroids[j][0])
                    yf=int(self.fillcentroids[j][1])
                    slope=-100*(Surfaces.Design[xc,yc]-Surfaces.Design[xf,yf])/Distances[i,j]
                    # Outlist.append([Distances[i,j],B[i,j],slope])
                    # plt.arrow(xc,yc,xf-xc,yf-yc,head_width=3, length_includes_head=True)
                    # if Distances[i,j]<800 and slope<0 and B[i,j]>50:
                    #     ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='k',width=widthV)
                    # if Distances[i,j]<800 and slope>0 and B[i,j]>50:
                    #     ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='red',width=widthV)
                    ArrowAttributes.append([xc,yc,xf,yf,xf-xc,yf-yc,self.ID,(str(self.ID)+str(i)+str(j)),Distances[i,j],self.Volumes[i,j]])    
                    if Distances[i,j]<200 and self.Volumes[i,j]>0 and Distances[i,j]<Load_Haul_Cutoff:
                        self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='k',width=widthV)
                    if Distances[i,j]>200 and self.Volumes[i,j]>0 and Distances[i,j]<Load_Haul_Cutoff:
                        self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='red',width=widthV)
                    if slope>0 and self.Volumes[i,j]>0:
                        UpDistanceLinear+=Distances[i,j]
                        UpDistanceNonLinear+=DistancesUpDwn[i,j]
                        UpCostLinear+=B[i,j]*Distances[i,j]
                        UpCostNonLinear+=B[i,j]*DistancesUpDwn[i,j]
                        UphillVolume+=B[i,j]
                        
                    #Binning volumes by their movement distances
                    Binfound=False  
                    if slope<0 and self.Volumes[i,j]>0:
                        if Distances[i,j]<=100:
                            Downhill_less_100m[1]+=B[i,j]
                            Downhill_less_100m[2]+=B[i,j]*slope
                        if Distances[i,j]<=200 and Distances[i,j]>100:
                            Downhill_100m_to_200m[1]+=B[i,j]
                            Downhill_100m_to_200m[2]+=B[i,j]*slope
                        if Distances[i,j]<=300 and Distances[i,j]>200:
                            Downhill_200m_to_300m[1]+=B[i,j]
                            Downhill_200m_to_300m[2]+=B[i,j]*slope
                        if Distances[i,j]>300:
                            Downhill_greater_300m[1]+=B[i,j]
                            Downhill_greater_300m[2]+=B[i,j]*slope
                            
                    if slope>0 and self.Volumes[i,j]>0:
                        if Distances[i,j]<=100:
                            Uphill_less_100m[1]+=B[i,j]
                            Uphill_less_100m[2]+=B[i,j]*slope
                        if Distances[i,j]<=200 and Distances[i,j]>100:
                            Uphill_100m_to_200m[1]+=B[i,j]
                            Uphill_100m_to_200m[2]+=B[i,j]*slope
                        if Distances[i,j]<=300 and Distances[i,j]>200:
                            Uphill_200m_to_300m[1]+=B[i,j]
                            Uphill_200m_to_300m[2]+=B[i,j]*slope
                        if Distances[i,j]*0.5>300:
                            Uphill_greater_300m[1]+=B[i,j]
                            Uphill_greater_300m[2]+=B[i,j]*slope
                    for k in range(1,np.size(Distance_Bins,axis=0)-1):
                       
                        
                        if Distances[i,j]<=Distance_Bins[k]:
                            
                            Volume_Bins[k]+=B[i,j]
                            if slope>0 and self.Volumes[i,j]>0:
                                Volume_Bins_Up[k]+=B[i,j]
                            if slope<0 and self.Volumes[i,j]>0:
                                Volume_Bins_Down[k]+=B[i,j]  
                                
                            if slope>0 and slope<=2:
                                Grade2percentup[k]+=B[i,j]
                            if slope>2 and slope<=5:
                                Grade5percentup[k]+=B[i,j]
                            if slope>5 and slope<=10:
                                Grade10percentup[k]+=B[i,j]
                            if slope>10 and slope<=20:
                                Grade20percentup[k]+=B[i,j]
                            if slope>20 and slope<=30:
                                Grade30percentup[k]+=B[i,j]
                            if slope>30 and slope<=40:
                                Grade40percentup[k]+=B[i,j]
                            if slope>=50 :
                                Grade50percentup[k]+=B[i,j]
                                
                            if slope<0 and slope>=-2:
                                Grade2percentdown[k]+=B[i,j]
                            if slope<-2 and slope>=-5:
                                Grade5percentdown[k]+=B[i,j]
                            if slope<-5 and slope>=-10:
                                Grade10percentdown[k]+=B[i,j]
                            if slope<-10 and slope>=-20:
                                Grade20percentdown[k]+=B[i,j]
                            if slope<-20 and slope>=-30:
                                Grade30percentdown[k]+=B[i,j]
                            if slope<-30 and slope>=-40:
                                Grade40percentdown[k]+=B[i,j]
                            if slope<=-50 :
                                Grade50percentdown[k]+=B[i,j]
                                
                            Binfound=True
                            break
                    if Binfound==False:
                        Volume_Bins[-1]+=B[i,j]
                        Volume_Bins_Up[-1]+=B[i,j]
                        Volume_Bins_Down[-1]+=B[i,j]
                        
                    # if Distances[i,j]>=150:
                    #     plt.arrow(yc,xc,yf-yc,xf-xc,head_width=3*widthV,width=widthV, length_includes_head=True,ec='r')
                    # plt.arrow(locations[cnt][0][1],locations[cnt][0][0],locations[cnt][0][1]-locations[cnt][1][1],locations[cnt][0][0]-locations[cnt][1][0],head_width=3, length_includes_head=True)
        #            print(locations[cnt])
                    sumcost+=B[i,j]*Distances[i,j]
                    sumcostUpDwn+=B[i,j]*DistancesUpDwn[i,j]
                    sumdistance+=Distances[i,j]
                    sumdistanceUpDwn+=DistancesUpDwn[i,j]
                    sumvolume+=B[i,j]
                cnt+=1
        self.ArrowAttributes=ArrowAttributes
        print(TotalCut,sumvolume)
        Downhill_less_100m[2]=Downhill_less_100m[2]/Downhill_less_100m[1]
        Downhill_100m_to_200m[2]=Downhill_100m_to_200m[2]/Downhill_100m_to_200m[1]
        Downhill_200m_to_300m[2]=Downhill_200m_to_300m[2]/Downhill_200m_to_300m[1]
        Downhill_greater_300m[2]=Downhill_greater_300m[2]/Downhill_greater_300m[1]
        Uphill_less_100m[2]=Uphill_less_100m[2]/Uphill_less_100m[1]
        Uphill_100m_to_200m[2]=Uphill_100m_to_200m[2]/Uphill_100m_to_200m[1]
        Uphill_200m_to_300m[2]=Uphill_200m_to_300m[2]/Uphill_200m_to_300m[1]
        Uphill_greater_300m[2]=Uphill_greater_300m[2]/Uphill_greater_300m[1]
        
        Downhill_less_100m[1]+=cut0-sumvolume
        #Change in height for each block (cut for block cutcentroid[i] is B[i,:], fill for block fillcentroid[j] is B[:,j])
        #A block can only have cut removed or fill added not both
       
        #Change in height in cut blocks
        for i in range(0,self.Volumes.shape[0]-2):
            Binfound=False
            dh=-sum(B[i,:]/(block**2))
            if dh<-10:
                Vertical_Change_Data[0]+=1
                Binfound=True
            if Binfound==False:
                for k in range(1,np.size(Vertical_Change_Bins,axis=0)-1):
                    if dh<int(Vertical_Change_Bins[k]):
                        Vertical_Change_Data[k]+=1
                        Binfound=True
                        break
            if Binfound==False:
                Vertical_Change_Data[-1]+=1
                Binfound=True
            
        #Change in height in fill blocks
        for j in range(0,self.Volumes.shape[1]-2):
            Binfound=False
            dh=sum(B[:,j]/(block**2))
            for k in range(0,np.size(Vertical_Change_Bins,axis=0)):
                    if dh<int(Vertical_Change_Bins[k]):
                        Vertical_Change_Data[k]+=1
                        Binfound=True
                        break
            if Binfound==False:
                Vertical_Change_Data[-1]+=1
                Binfound=True
                
            
        self.canvas.draw_idle()
        
        TotalCut=np.sum(cut)
        TotalFill=np.sum(fill)
        inCellCut=cut0-TotalCut
        Volume_Bins[1]=inCellCut
        Grade2percentdown[1]=inCellCut
        Volume_Bins_Down[1]=inCellCut
        #List of statistics for output to csv
        output_list1=[['Blocksize (m2)', block*Surfaces.cellsize],
                      ['Total Cut (m3)', cut0],
                      ['Cut retained in Cells (m3)', cut0-TotalCut],
                      ['Total Fill (m3)', fill0],
                      ['Fill retained in Cells (m3)', fill0-TotalFill],
                      [' ',' '],
                      ['Total Uphill Cost (linear)', UpCostLinear],
                      ['Total Uphill Cost (non-linear)', UpCostLinear],
                      ['Average Uphill Distance (linear) (m)', UpCostLinear/UphillVolume],
                      ['Average Uphill Distance (non-linear) (m)', UpCostNonLinear/UphillVolume],
                      [' ',' '],
                      ['Total Cost (linear)', sumcost+inCellCut*(block*Surfaces.cellsize)],
                      ['Average Distance (linear) (m)', (sumcost+inCellCut*(block*Surfaces.cellsize))/TotalCut],
                      ['Total Cost (non-linear)', sumcostUpDwn+inCellCut*(block*Surfaces.cellsize)],
                      ['Average Distance (non-linear) (m)', (sumcostUpDwn+inCellCut*(block*Surfaces.cellsize))/TotalCut],
                      ['Maximum Distance (m)', np.amax(Distances)],
                      [' ',' '],
                      ['Distance Volume Bins'],
                      Distance_Bins,
                      Volume_Bins,
                      Volume_Bins_Up,
                      Volume_Bins_Down,
                      Grade2percentdown,
                      Grade5percentdown,
                      Grade10percentdown,
                      Grade20percentdown,
                      Grade30percentdown,
                      Grade40percentdown,
                      Grade50percentdown,
                      Grade2percentup,
                      Grade5percentup,
                      Grade10percentup,
                      Grade20percentup,
                      Grade30percentup,
                      Grade40percentup,
                      Grade50percentup,
                      ['Vertical Change per Block Bins'],
                      Vertical_Change_Names,
                      Vertical_Change_Data,
                      Downhill_less_100m,
                      Downhill_100m_to_200m,
                      Downhill_200m_to_300m,
                      Downhill_greater_300m,
                      Uphill_less_100m,
                      Uphill_100m_to_200m,
                      Uphill_200m_to_300m,
                      Uphill_greater_300m]
        
        #CSV writing
        outfilename = asksaveasfilename(title = "Save Movement Report, Enter file name",filetypes = (("csv files","*.csv"),("all files","*.*")))
        if len(outfilename)>3:
             if outfilename[-4]!=".":
                 outfilename=outfilename +".csv"
        with open(outfilename, 'w', newline='') as csv_file:  
            writer = csv.writer(csv_file)
            writer.writerows(output_list1)
        print('CSV Report Generated')   
        
        
       
    
    
    def LimitVolumes(self,Surfaces,Se):
        if self.Volumes is not None:
            Se.RemoveArrows()
            for i in range (0,self.Volumes.shape[0]-2):
                for j in range (0,self.Volumes.shape[1]-2):
                    if self.Volumes[i,j]>self.averageV*0.5:# and DistUpDwn[i,j]<350:
                        
                        widthV=((self.maxvol-self.Volumes[i,j])/(self.maxvol-0))
                        widthV=(1-widthV)*10
                        xc=int(self.cutcentroids[i][0])
                        yc=int(self.cutcentroids[i][1])
                                
                        xf=int(self.fillcentroids[j][0])
                        yf=int(self.fillcentroids[j][1])
                        slope=-100*(Surfaces.Design[xc,yc]-Surfaces.Design[xf,yf])/self.Distances[i,j]
                        # if slope<0 and self.Volumes[i,j]>50:
                        #     ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='k',width=widthV)
                        # if slope>0 and self.Volumes[i,j]>50:
                        self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='blue',fc='blue',width=widthV)    
    def Uphill(self,Surfaces,Se):
        if self.Volumes is not None:
            Se.RemoveArrows()
            for i in range (0,self.Volumes.shape[0]-2):
                for j in range (0,self.Volumes.shape[1]-2):
                    if self.Volumes[i,j]>0:# and DistUpDwn[i,j]<350:
                        
                        widthV=((self.maxvol-self.Volumes[i,j])/(self.maxvol-0))
                        widthV=(1-widthV)*10
                        xc=int(self.cutcentroids[i][0])
                        yc=int(self.cutcentroids[i][1])
                                
                        xf=int(self.fillcentroids[j][0])
                        yf=int(self.fillcentroids[j][1])
                        slope=-100*(Surfaces.Design[xc,yc]-Surfaces.Design[xf,yf])/self.Distances[i,j]
                        # if slope<0 and self.Volumes[i,j]>50:
                        #     ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='k',width=widthV)
                        if slope>0 and self.Volumes[i,j]>50:
                            self.ax.arrow(yc,xc,yf-yc,xf-xc,head_width=3,length_includes_head=True,ec='red',width=widthV)
                        
                    # cnt+=1
            self.canvas.draw_idle()
    
    def OutputArrowShapefile(self,Surfaces,Se):
        if self.ArrowAttributes is not None:
            ArrowAttributes=[['x1','y1','x2','y2','dx','dy','Polygon ID','ShapeID','length','volume']]
            data=self.ArrowAttributes[1:]
            outfilename = asksaveasfilename(title = "Save Arrows, Enter file name",filetypes = (("shp files","*.shp"),("all files","*.*")))
            # path='Arrows Shapefile Data/Arrow_'+str(self.ID)
            t=shapefile.Writer(outfilename)
            t.field('PolygonID', 'N', 10)
            t.field('LineID', 'N', 10)
            t.field('Length', 'N', 30)
            t.field('Volume', 'N', 30)
            for entry in data:
                x1=float(entry[0])
                y1=float(entry[1])
                x2=float(entry[2])
                y2=float(entry[3])
                PID=float(entry[6])
                LID=float(entry[7])
                L=float(entry[8])
                V=float(entry[9])
               
                y1 = Surfaces.maxcol-(Surfaces.Design.shape[1]-y1)*Surfaces.cellsize+0.5*Surfaces.cellsize
                x1 = -(Surfaces.Design.shape[0]-x1)*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize
                y2 = Surfaces.maxcol-(Surfaces.Design.shape[1]-y2)*Surfaces.cellsize+0.5*Surfaces.cellsize
                x2 = -(Surfaces.Design.shape[0]-x2)*Surfaces.cellsize+Surfaces.maxrow+0.5*Surfaces.cellsize
                t.line([[[y1,x1],[y2,x2]]])
                t.record(PID,LID,L,V)

            t.close()
    
                
        
            
    
        
