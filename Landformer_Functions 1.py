#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  2 21:04:03 2021

@author: sven
"""
# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'qt4' 
import os
# os.environ['ETS_TOOLKIT'] = 'qt4'

from scipy.spatial import Delaunay
import IPython.display as display
import scipy.interpolate
from scipy.interpolate import RegularGridInterpolator
import scipy.spatial
from statistics import mean
from numba import jit
import numpy as np
import math
from Landformer_classesBerms import *
from tkinter import Tk
import matplotlib.transforms as mtransforms
# from osgeo import gdal
from pathlib import Path
from tkinter.filedialog import askopenfilename, asksaveasfilename
import tkinter.messagebox
from matplotlib.patches import Circle
# from mayavi import mlab
import plotly.graph_objects as go
# import plotly.io as pio
# pio.renderers.default='browser'
import matplotlib.pyplot as plt

# from tvtk.api import tvtk
from matplotlib.colors import LightSource
import glob
from matplotlib.lines import Line2D
from PIL import Image
import csv
import shapefile as shp
from matplotlib import colors as mcolors
from matplotlib.patches import Polygon
from skimage import io
import re

# from vispy import plot as vp
# from vispy.util.filter import gaussian_filter
# from vispy import color
# import vispy

import ezdxf
import time
import datetime
Image.MAX_IMAGE_PIXELS = None

def check_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def triangulate_rasters(cellS,progress,Sf):
    Tk().withdraw() 
    filename = askopenfilename()
    path = filename
    path_in_str = str(path)
    input_dir = os.path.dirname(filename)
    
    search_criteria = "*.xyz"
    query = os.path.join(input_dir, search_criteria)
    tiff_files = glob.glob(query)

    # List to hold the opened rasters
    src_files_to_mosaic = []
    
    for fp in tiff_files:
        Temp = []
        
        c=0
        progress['value']=10
        Sf.update_idletasks()
        for line in open (fp):
            c+=1    
            line = line.replace('"',' ')
            row=re.split(",| ",line)
            # row=re.split("\t",line)
            rowV=[]
            # print('try')
            if c%5==0:
                for r in row:
                    try:
                        rowV.append(float(r))
                    except:
                        pass
                try:
                    if float(rowV[2])!=0:
                        Temp.append([float(rowV[0]), float(rowV[1]),float(rowV[2])])
                        # print(rowV)
                except:
                    print (row,rowV)
        Points=np.array(Temp,dtype=np.float32)
        progress['value']=20
        Sf.update_idletasks()
        minx = min(float(x[0]) for x in Temp)
        maxx = max(float(x[0]) for x in Temp)
        miny = min(float(x[1]) for x in Temp)
        maxy = max(float(x[1]) for x in Temp)
        
        meanx = mean(float(x[0]) for x in Temp)
        meany = mean(float(x[1]) for x in Temp)
        
        points = []
        values=[]
        Temp = []
        for p in Points:
        
            x = float(p[0]-meanx)
            y = float(p[1]-meany)
            z = float(p[2])
            points.append([x,y])
            values.append(z)
            
        points=np.array(points)
        values=np.array(values)
        progress['value']=30
        Sf.update_idletasks()
        Points = []
        Outlist = []
        delaunay = scipy.spatial.Delaunay(points)
        ip = scipy.interpolate.LinearNDInterpolator(delaunay, values)
        progress['value']=40
        Sf.update_idletasks()
        points1=[]
        points2=[]
        A=[]
        B=[]
        
        c=minx
        while c<maxx:
            A.append(c)
            c+=cellS
        c=miny
        while c<maxy:
            B.append(c)
            c+=cellS
        for i in A:
            for j in B:
                points1.append([i-meanx,j-meany])
                points2.append([i,j])
                
        points1=np.array(points1)
        out=ip(points1)
        progress['value']=50
        Sf.update_idletasks()
        for coord,p in zip(points2,out):
            if not np.isnan(p):
                Outlist.append([coord[0],coord[1],p])  #x,y and returned z   
        progress['value']=60
        Sf.update_idletasks()
        Points=np.array(Outlist)
        
        maxcol=np.max(Points[:,0])
        maxrow=np.max(Points[:,1])
        mincol=np.min(Points[:,0])
        minrow=np.min(Points[:,1])
        
        rows=int((maxrow-minrow)/cellS)
        cols=int((maxcol-mincol)/cellS)
        
        A=np.zeros((rows,cols))
        progress['value']=70
        Sf.update_idletasks()    
        create_Array(maxrow,maxcol,cellS,A,Points)
        progress['value']=80
        Sf.update_idletasks()
        filename2=fp[0:-4]
        if cellS>=1:
            filename2=filename2+' cellsize%dm2.tif'%cellS
        else:
            filename2=filename2+' cellsizesub1m.tif'
        tag={}
        tag[33922]=(0.0,0.0,0.0,1.0*maxcol+0.5*cellS-cols*cellS,1.0*maxrow+0.5*cellS,0.0)
        tag[33550]=(cellS,cellS,0.0)
        A=np.flip(A,axis=1)
        im=Image.fromarray(A)  
        im.save(filename2,tiffinfo=tag)
        im.close
        progress['value']=100

def import_LEM(Sf,Surfaces):
    Tk().withdraw()
    filename = askopenfilename(title = "Select elevdiff",filetypes = (("txt files","*.txt"),("all files","*.*")))
    path = filename
    Directory = os.path.dirname(filename)
    im=np.loadtxt(path,skiprows=6)
    # plt.imshow(im)
    outfiles=[]
    outfilesN=[]
    for file in os.listdir(Directory):
        if re.match("elevdiff\d+\.txt",file):
            # print(file)
            outfiles.append(file)
            outfilesN.append(re.findall(r'\d+',file))
            # outfilesN.append([int(s) for s in file.split() if s.isdigit()])
    outfilesN=np.array(outfilesN,dtype=np.float32)
      
    P=np.argsort(outfilesN,axis=0)
    outsorted=[]
    for p in P:
        outsorted.append(outfiles[p[0]])    
    Alldiff=np.zeros((im.shape[0],im.shape[1],len(outsorted)))
    Sf.sliderLem.configure(to=len(outsorted)-1)
    count=0
    for p in outsorted:
        path=os.path.join(Directory,p)
        im=np.loadtxt(path,skiprows=6)
        im=np.flip(im,axis=0)
        Alldiff[:,:,count]=im
        count+=1
    Surfaces.Alldiff=Alldiff
    
    for tp in Sf.p[0].collections:
        tp.set_color(['gray'])
        Sf.a.draw_artist(tp)
        
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
    Draw_Update(Sf,Surfaces)
    
    Sf.im=Sf.a.imshow(Alldiff[:,:,10],vmax=0.5,vmin=-0.5,cmap=plt.get_cmap('Spectral_r'))
    Sf.f.canvas.restore_region(background)
    Sf.a.draw_artist(Sf.im)
    Sf.f.canvas.blit(Sf.f.bbox)   

def import_LEMTiff(Sf,Surfaces):
    Tk().withdraw()
    filename = askopenfilename(title = "Select Surface",filetypes = (("Output files","*.tif"),("all files","*.*")))
    path = filename
    Directory = os.path.dirname(filename)
    # im=np.loadtxt(path,skiprows=6)
    im = Image.open(path)
    Arr=np.array(im)
    Arr=np.flip(Arr,axis=1)
    Arr=np.flip(Arr,axis=0)
    # plt.imshow(im)
    outfiles=[]
    outfilesN=[]
    for file in os.listdir(Directory):
        print(('unmatched',file))
        if file.endswith(".tif"):
        # if re.match("\.tif",file):
            print(file)
            outfiles.append(file)
            A=re.findall(r'\d+',file)
            outfilesN.append(A[-1])
            print(outfilesN[-1])
            # outfilesN.append([int(s) for s in file.split() if s.isdigit()])
    outfilesN=np.array(outfilesN,dtype=np.float32)
      
    P=np.argsort(outfilesN,axis=0)
    outsorted=[]
    for p in P:
        # print(p[0])
        outsorted.append(outfiles[p])    
    Alldiff=np.zeros((Arr.shape[0],Arr.shape[1],len(outsorted)))
    Sf.sliderLem.configure(to=len(outsorted)-1)
    count=0
    for p in outsorted:
        path=os.path.join(Directory,p)
        im = Image.open(path)
        im=np.array(im)
        im=np.flip(im,axis=1)
        im=np.flip(im,axis=0)
        # Alldiff[:,:,count]=im
        Subtract_Array(Arr,im,Alldiff[:,:,count])
        count+=1
    Surfaces.Alldiff=Alldiff
    
    for tp in Sf.p[0].collections:
        tp.set_color(['gray'])
        Sf.a.draw_artist(tp)
        
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
    Draw_Update(Sf,Surfaces)
    
    Sf.im=Sf.a.imshow(Alldiff[:,:,10],vmax=0.5,vmin=-0.5,cmap=plt.get_cmap('Spectral_r'))
    Sf.f.canvas.restore_region(background)
    Sf.a.draw_artist(Sf.im)
    Sf.f.canvas.blit(Sf.f.bbox)   
    
@jit
def create_Array(maxrow,maxcol,cellsize,Arr,Points):
    for i in range(0,Points.shape[0]):
        # p=Points[i]
        row=(maxrow-Points[i,1])/cellsize
        col=(maxcol-Points[i,0])/cellsize
        row = round(row,0)
        col = round(col,0)
        row=int(row)
        col=int(col)
        if row<Arr.shape[0] and col<Arr.shape[1] and row>=0 and col>=0:
            Arr[row,col]=Points[i,2]
    # return Arr
@jit
def Subtract_Array(Arr1,Arr2,diff):
    for i in range (0,Arr1.shape[0]):
        for j in range (0,Arr1.shape[1]):
            diff[i,j]=Arr1[i,j]-Arr2[i,j]
            
def import_LEM_SIBERIA(Sf,Surfaces):
    Tk().withdraw()
    filename = askopenfilename(title = "Select SIBERIA Output",filetypes = (("csv files","*.csv"),("all files","*.*")))
    path = filename
    Directory = os.path.dirname(filename)
    with open(path, 'r') as f:
        reader = csv.reader(f)
        Temp = list(reader)
    Arr=np.zeros_like(Surfaces.Design)
    Arr1=np.zeros_like(Surfaces.Design)
    Points=np.array(Temp,dtype='float64')
    create_Array(Surfaces.maxrow+0.1,Surfaces.maxcol+0.1,Surfaces.cellsize,Arr,Points)
    outfiles=[]
    outfilesN=[]
    for file in os.listdir(Directory):
        if re.match("out-\d+\. converted.csv",file):
            print(file)
            outfiles.append(file)
            outfilesN.append(re.findall(r'\d+',file))
            # outfilesN.append([int(s) for s in file.split() if s.isdigit()])
    outfilesN=np.array(outfilesN,dtype=np.float32)
      
    P=np.argsort(outfilesN,axis=0)
    outsorted=[]
    for p in P:
        outsorted.append(outfiles[p[0]])    
    Alldiff=np.zeros((Arr.shape[0],Arr.shape[1],len(outsorted)))
    Sf.sliderLem.configure(to=len(outsorted)-1)
    count=0
    for p in outsorted:
        path=os.path.join(Directory,p)
        with open(path, 'r') as f:
            print('reading')
            print(path)
            reader = csv.reader(f)
            Temp = list(reader)
        Points=np.array(Temp,dtype='float64')
        create_Array(Surfaces.maxrow+0.1,Surfaces.maxcol+0.1,Surfaces.cellsize,Arr1,Points)
        Subtract_Array(Arr,Arr1,Alldiff[:,:,count])
        count+=1
        
    Alldiff=np.flip(Alldiff,axis=0)
    Alldiff=np.flip(Alldiff,axis=1)
    Surfaces.Alldiff=Alldiff
    
    for tp in Sf.p[0].collections:
        tp.set_color(['gray'])
        Sf.a.draw_artist(tp)
        
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
    Draw_Update(Sf,Surfaces)
    
    Sf.im=Sf.a.imshow(Alldiff[:,:,10],vmax=0.5,vmin=-0.5,cmap=plt.get_cmap('Spectral_r'))
    Sf.f.canvas.restore_region(background)
    Sf.a.draw_artist(Sf.im)
    Sf.f.canvas.blit(Sf.f.bbox)       
    
def LemUp(Num,Sf,Surfaces):
    # print(Num)
    background = Sf.f.canvas.copy_from_bbox(Sf.f.bbox)
    Sf.im.set_array(Surfaces.Alldiff[:,:,int(Num)])  
    Draw_Update(Sf,Surfaces)
    Sf.f.canvas.restore_region(background)
    Sf.a.draw_artist(Sf.im)
    Sf.f.canvas.blit(Sf.f.bbox)      
    
@jit
def Render(px,py, phi, height, horizon, scale_height, distance, screen_width, screen_height,heightmap,ybuffer,colormap,Out):
    # precalculate viewing angle parameters
    
    
    sinphi = math.sin(phi);
    cosphi = math.cos(phi);
    
    # initialize visibility array. Y position for each column on screen 
    
    for i in range(0, screen_width):
        ybuffer[i] = screen_height

    # Draw from front to the back (low z coordinate to high z coordinate)
    dz = 1.
    z = 2.
    while z < distance:

        # Find line on map. This calculation corresponds to a field of view of 90°
        pleftx = (-cosphi*z - sinphi*z) + px
        plefty = (sinphi*z - cosphi*z) + py
        prightx = ( cosphi*z - sinphi*z) + px
        prighty = (-sinphi*z - cosphi*z) + py

        # segment the line
        dx = ((prightx - pleftx) / screen_width)
        dy = ((prighty - plefty) / screen_height)

        # Raster line and draw a vertical line for each segment
        
        for i in range(0, screen_width):
            if pleftx<heightmap.shape[0] and plefty<heightmap.shape[1] and pleftx> 0 and plefty>0: 
                height_on_screen = (height - heightmap[int(pleftx), int(plefty)]) / z * scale_height + horizon
                            
                for j in range (0,screen_height):
                    if j>height_on_screen and j<ybuffer[i]:
                        Out[j,i,:]=colormap[int(pleftx), int(plefty),:]
                
                if height_on_screen < ybuffer[i]:
                    ybuffer[i] = height_on_screen
                # DrawVerticalLine(i, height_on_screen, ybuffer[i], colormap[pleftx, plefty],Out)
            
            pleftx += dx
            plefty += dy

        # Go to next line and increase step size when you are far away
        z += dz
        dz += 0.0

def gen_fig(Surfaces,x,y,x0,y0,eh,scale_height):
    
    ls = LightSource(200, 45)
    rgb = ls.shade(Surfaces.Design, plt.cm.copper,vert_exag=2,vmin=Surfaces.minval,vmax=Surfaces.maxval,fraction=1.0)
    
    height=Surfaces.Design[int(x0),int(y0)]+eh
    print(height)
    # horizon = height+50
    horizon =height
    # scale_height=2000
    distance=2000
    screen_width=2000
    screen_height=2000
    # phi=math.atan((x-x0)/(y-y0))
    print((x,x0,y,y0))
    phi=math.atan2((y-x0),(x-y0))+3.14159
    print(('phi',phi))
    # phi=0
    A=np.zeros((screen_width,screen_height,4))
    A[:,:,0]=135/255
    A[:,:,1]=206/255
    A[:,:,2]=235/255
    A[:,:,3]=1
    # A.fill([135,206,235,0])
    # p=np.array([320,370],dtype=np.float64)
    
    
    # pL=np.array([0,0],dtype=np.float64)
    # pR=np.array([0,0],dtype=np.float64)
    ybuffer = np.zeros(screen_width)
    # px,py, phi, height, horizon, scale_height, distance, screen_width, screen_height,heightmap,ybuffer,colormap,Out
    Render(x0,y0, phi, height, horizon, scale_height, distance, screen_width, screen_height,Surfaces.Design,ybuffer,rgb,A)
    # RenderOpt(p, phi, height, horizon, scale_height, distance, screen_width, screen_height,elevation,rgb,A,pR,pL)
    # A=np.flip(A,axis=1)
    plt.imshow(A)
    # fig2=plt.figure()
    # ax2=plt.gca()        
    # img=ax2.imshow(A)
    
def gen_figSurv(Surfaces,x,y,x0,y0,eh,scale_height):
    
    ls = LightSource(200, 45)
    rgb = ls.shade(Surfaces.Survey, plt.cm.copper,vert_exag=2,vmin=Surfaces.minval,vmax=Surfaces.maxval,fraction=1.0)
    
    height=Surfaces.Design[int(x0),int(y0)]+eh
    print(height)
    # horizon = height+50
    horizon =height
    # scale_height=2000
    distance=2000
    screen_width=2000
    screen_height=2000
    # phi=math.atan((x-x0)/(y-y0))
    print((x,x0,y,y0))
    phi=math.atan2((y-x0),(x-y0))+3.14159
    print(('phi',phi))
    # phi=0
    A=np.zeros((screen_width,screen_height,4))
    # p=np.array([320,370],dtype=np.float64)
    A[:,:,0]=135/255
    A[:,:,1]=206/255
    A[:,:,2]=235/255
    A[:,:,3]=1
    
    # pL=np.array([0,0],dtype=np.float64)
    # pR=np.array([0,0],dtype=np.float64)
    ybuffer = np.zeros(screen_width)
    # px,py, phi, height, horizon, scale_height, distance, screen_width, screen_height,heightmap,ybuffer,colormap,Out
    Render(x0,y0, phi, height, horizon, scale_height, distance, screen_width, screen_height,Surfaces.Survey,ybuffer,rgb,A)
    # RenderOpt(p, phi, height, horizon, scale_height, distance, screen_width, screen_height,elevation,rgb,A,pR,pL)
    # A=np.flip(A,axis=1)
    plt.imshow(A)
    # fig2=plt.figure()
    # ax2=plt.gca()        
    # img=ax2.imshow(A) 
       
def ThreeD(Sf,Surfaces):
    pass
    # plotS=np.flip(Surfaces.Design,0)    
    # y0=plotS.shape[0]-Sf.a.get_ylim()[1]
    # y1=plotS.shape[0]-Sf.a.get_ylim()[0]
    # plotS=plotS[int(y0):int(y1),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])]
    # # cnorm=(plotS-Surfaces.minval)/(Surfaces.maxval-Surfaces.minval)
    # # c = color.get_colormap("coolwarm").map(cnorm).reshape(plotS.shape + (-1,))
    # # c = c.flatten().tolist()
    # # c=list(map(lambda x,y,z,w:(x,y,z,w), c[0::4],c[1::4],c[2::4],c[3::4]))
    
    # fig = vp.Fig(size=(1200, 800), show=False)
    # p1=fig[0, 0].surface(plotS/Surfaces.cellsize)
    
    # # p1.mesh_data.set_vertex_colors(c)
    # fig.show(run=True)
    
    
    # y0=plotS.shape[0]-Sf.a.get_ylim()[1]
    # y1=plotS.shape[0]-Sf.a.get_ylim()[0]
    # mlab.figure(size=(400, 320), bgcolor=(0.16, 0.28, 0.46))
    # minval = round(np.nanmin(plotS[int(y0):int(y1),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])][np.nonzero(plotS[int(y0):int(y1),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])])]))
    # maxval = round(np.nanmax(plotS[int(y0):int(y1),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])][np.nonzero(plotS[int(y0):int(y1),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])])]))
    # mlab.surf(plotS[int(y0):int(y1),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])], colormap='gist_earth', warp_scale=1/Surfaces.cellsize,vmin=Surfaces.minval, vmax=Surfaces.maxval)
    # levels=list(np.linspace(minval+1,maxval-1,int((maxval-minval)/Sf.interval)))
    # mlab.contour_surf(plotS[int(y0):int(y1),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])],color=(0,0,0),contours=levels, warp_scale=1/Surfaces.cellsize,line_width=0.8)
    # fig = mlab.gcf()
    # fig.scene.interactor.interactor_style = tvtk.InteractorStyleTerrain()
    
# def ThreeD(Sf,Surfaces):
#     # pass
#     fig = go.Figure(data=[go.Surface(z=Surfaces.Design, colorscale='earth',cmin=Surfaces.minval,cmax=Surfaces.maxval)])
#     fig.update_layout(title='3D',autosize=False,
#                   width=2000, height=2000,
#                   margin=dict(l=65, r=50, b=65, t=90))
#     fig.show()
# #     # plotS=np.flip(Surfaces.Design,0)
# #     # y0=plotS.shape[0]-Sf.a.get_ylim()[1]
# #     # y1=plotS.shape[0]-Sf.a.get_ylim()[0]
# #     # mlab.figure(size=(400, 320), bgcolor=(0.16, 0.28, 0.46))
# #     # mlab.surf(plotS[int(y0):int(y1),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])], colormap='gist_earth', warp_scale=1/Surfaces.cellsize,vmin=Surfaces.minval, vmax=Surfaces.maxval)
# #     # levels=list(np.linspace(Surfaces.minval,Surfaces.maxval,int((Surfaces.maxval-Surfaces.minval)/Sf.interval)))
# #     # mlab.contour_surf(plotS[int(y0):int(y1),int(Sf.a.get_xlim()[0]):int(Sf.a.get_xlim()[1])],color=(0,0,0),contours=levels, warp_scale=1/Surfaces.cellsize,line_width=0.8)
# #     # fig = mlab.gcf()
# #     # fig.scene.interactor.interactor_style = tvtk.InteractorStyleTerrain()

@jit
def Visibility(x0,y0,y,x,Design,Visible,cellsize,TH,OH):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    Z0=Design[int(x0),int(y0)]+OH
    L=((x0-x)**2+(y0-y)**2)**0.5
    Vxn=(x-x0)/L
    Vyn=(y-y0)/L
    Vxt=Vyn
    Vyt=-Vxn
    width=100/cellsize
    startx=x+width*Vxt
    starty=y+width*Vyt
    L=((startx-x)**2+(starty-y)**2)**0.5
    Vxt=(x-startx)/L
    Vyt=(y-starty)/L
    # print((x,y,x0,y0,startx,starty,Vxn,Vyn,Vxt,Vyt))
    for i in range (0,2*int(width)):
        x=startx+i*Vxt
        y=starty+i*Vyt
        L=((x-x0)**2+(y-y0)**2)**0.5
        Vxn=(x-x0)/L
        Vyn=(y-y0)/L
        minS=2
        for step in range (10,int(L)):
            xnew=x0+step*Vxn
            ynew=y0+step*Vyn
            if xnew>0 and ynew>0 and xnew<Design.shape[0] and ynew<Design.shape[1]:
                Z=Design[int(xnew),int(ynew)]
                grad=(Z0-Z)/step
                if grad<minS:
                    minS=grad
                    Visible[int(xnew),int(ynew)]=1
                else:
                    grad=(Z0-Z+TH)/step
                    if grad<minS:
                        Visible[int(xnew),int(ynew)]=1
        

def Import_lines(Se,Sf,linetype):
    Tk().withdraw()
    filename = askopenfilename(title = "Select points",filetypes = (("csv files","*.csv"),("all files","*.*")))
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        K=list(reader)
        c=0
        d=0
        while d<len(K):
            ID=float(K[d][0])
            exp=float(K[d+1][0])
            slp=float(K[d+2][0])
            StartE=float(K[d+3][0])
            print(K[d+4])
            xy=np.array(K[d+4],dtype=np.float64)
            x=xy[0::2]
            y=xy[1::2]
            d+=5
            for i in range(0,x.shape[0]):
                x0 = [(i-Sf.maxcol-0.5*Sf.cellsize)/Sf.cellsize+Sf.Design.shape[1] for i in x]
                y0 = [(i-Sf.maxrow-0.5*Sf.cellsize)/Sf.cellsize+Sf.Design.shape[0] for i in y]
            line = Line2D(x0, y0, animated=False,marker='o', markerfacecolor='r')
            linesp = Line2D(x0, y0, animated=False,lw=0.3,color='k')
            linesrt = Line2D(x0, y0, animated=False,lw=0.3,color='g')
            print((x0,y0))
            p = LineLinear(Se, line,linesp,linesrt,Sf,Se.dot,ID,linetype,slp,exp)
            p.StartElevation=StartE
            Se.Lines.append(p)
            Se.LineID=ID 
            p.Initial_setup()
        Draw_Update(Se,Sf)
        
def alpha_shape(points, alpha, only_outer=True):
    """
    Compute the alpha shape (concave hull) of a set of points.
    :param points: np.array of shape (n,2) points.
    :param alpha: alpha value.
    :param only_outer: boolean value to specify if we keep only the outer border
    or also inner edges.
    :return: set of (i,j) pairs representing edges of the alpha-shape. (i,j) are
    the indices in the points array.
    """
    assert points.shape[0] > 3, "Need at least four points"
    def add_edge(edges, i, j):
        """
        Add an edge between the i-th and j-th points,
        if not in the list already
        """
        if (i, j) in edges or (j, i) in edges:
            # already added
            assert (j, i) in edges, "Can't go twice over same directed edge right?"
            if only_outer:
                # if both neighboring triangles are in shape, it's not a boundary edge
                edges.remove((j, i))
            return
        edges.add((i, j))
    tri = Delaunay(points[:,0:2])
    edges = set()
    # Loop over triangles:
    # ia, ib, ic = indices of corner points of the triangle
    for ia, ib, ic in tri.vertices:
        pa = points[ia]
        pb = points[ib]
        pc = points[ic]
        # Computing radius of triangle circumcircle
        # www.mathalino.com/reviewer/derivation-of-formulas/derivation-of-formula-for-radius-of-circumcircle
        a = np.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
        b = np.sqrt((pb[0] - pc[0]) ** 2 + (pb[1] - pc[1]) ** 2)
        c = np.sqrt((pc[0] - pa[0]) ** 2 + (pc[1] - pa[1]) ** 2)
        s = (a + b + c) / 2.0
        area = np.sqrt(s * (s - a) * (s - b) * (s - c))
        if area>0:
            circum_r = a * b * c / (4.0 * area)
        else: 
            circum_r=1000
        if circum_r < alpha:
            add_edge(edges, ia, ib)
            add_edge(edges, ib, ic)
            add_edge(edges, ic, ia)
    return edges,tri

def find_edges_with(i, edge_set):
    i_first = [j for (x,j) in edge_set if x==i]
    i_second = [j for (j,x) in edge_set if x==i]
    return i_first,i_second

def stitch_boundaries(edges,points):
    edge_set = edges.copy()
    boundary_lst = []
    while len(edge_set) > 0:
        boundary = []
        edge0 = edge_set.pop()
        # boundary.append(edge0)
        boundary.append([points[edge0[0],0],points[edge0[0],1]])
        last_edge = edge0
        while len(edge_set) > 0:
            i,j = last_edge
            j_first, j_second = find_edges_with(j, edge_set)
            if j_first:
                edge_set.remove((j, j_first[0]))
                edge_with_j = (j, j_first[0])
                # boundary.append(edge_with_j)
                boundary.append([points[edge_with_j[0],0],points[edge_with_j[0],1]])
                last_edge = edge_with_j
            elif j_second:
                edge_set.remove((j_second[0], j))
                edge_with_j = (j, j_second[0])  # flip edge rep
                # boundary.append(edge_with_j)
                boundary.append([points[edge_with_j[0],0],points[edge_with_j[0],1]])
                last_edge = edge_with_j
            if edge0[0] == last_edge[1]:
                break
        boundary_lst.append(boundary)
    return boundary

def Import_Points2(Se,Sf,alphaEdge):
    Tk().withdraw()
    filename = askopenfilename(title = "Select Points to Import",filetypes = (("CSV files","*.csv"),("all files","*.*")))
    path = filename
    with open(path, 'r') as f:
        reader = csv.reader(f)
        Temp = list(reader)
    Points=np.array(Temp,dtype='float64')
    for i in range(0,Points.shape[0]):
        # print(i)
        Points[i,0]=(Points[i,0]-Sf.maxcol-0.5*Sf.cellsize)/Sf.cellsize+Sf.Design.shape[1]
        Points[i,1]=(Points[i,1]-Sf.maxrow-0.5*Sf.cellsize)/Sf.cellsize+Sf.Design.shape[0]
        if Sf.Offset:
           Points[i,2]=Points[i,2]+1000
    edges,tri = alpha_shape(Points, alpha=alphaEdge, only_outer=True)
    ip = scipy.interpolate.LinearNDInterpolator(tri, Points[:,2])
    boundary=stitch_boundaries(edges,Points)
    # print(boundary)
    boundary.append(boundary[0])
    # print(boundary)
    boundary=np.array(boundary)
    Se.Mergepoly = Polygon(boundary, animated=False,alpha=0.5)
    Se.a.add_artist(Se.Mergepoly)
    Se.MergeScat=Se.a.scatter(Points[:,0],Points[:,1])    
    Inside=Se.Mergepoly.contains_points(Se.a.transData.transform(Se.Allpoints))
    out=ip(Se.Allpoints)
    for i,p,truth in zip(out,Se.Allpoints,Inside):
        if truth:
            # print((truth,p[1],p[0],i))
            Sf.Design[p[1],p[0]]=i
            # Sf.Design[p[1],p[0]]=100
    Draw_contours(Se,Sf)    
    Draw_Update(Se,Sf)    
    # Se.a.add_artist(poly)
    


    
def ShapeFile_plot(Se,Sf):
    
    Tk().withdraw()
    filename = askopenfilename(title = "Select design edge shapefile",filetypes = (("shp files","*.shp"),("all files","*.*")))
    Directory = os.path.dirname(filename)
    Name = Path(filename).stem
    path = filename
    sf = shp.Reader(path)
    background=Se.f.canvas.copy_from_bbox(Se.a.bbox)
    # t=[]
    for shape in sf.shapeRecords():
        for i in range(len(shape.shape.parts)):
            i_start = shape.shape.parts[i]
            if i==len(shape.shape.parts)-1:
                i_end = len(shape.shape.points)
            else:
                i_end = shape.shape.parts[i+1]
           
            x = [(i[0]-Sf.maxcol-0.5*Sf.cellsize)/Sf.cellsize+Sf.Design.shape[1] for i in shape.shape.points[i_start:i_end]]
            y = [(i[1]-Sf.maxrow-0.5*Sf.cellsize)/Sf.cellsize+Sf.Design.shape[0] for i in shape.shape.points[i_start:i_end]]
            l=Se.a.plot(x,y)
            Se.shape.append(l)
            # Se.a.draw_artist(t[-1])
    Draw_Update(Se,Sf)
    # Se.f.canvas.blit(Se.a.bbox)
            

def Save_Lines(Se,Sf):
    outfilename = asksaveasfilename(title = "Save, Enter file name",filetypes = (("csv files","*.csv"),("all files","*.*")))
    if len(outfilename)>3:
        if outfilename[-4]!=".":
            outfilename=outfilename +".csv"
    out=[]
    for p in Se.Lines:
        pointsC=[]
        xycentre=p.line.get_xydata()
        try:
            for i in range (0,xycentre.shape[0]):
                pointsC.append(Sf.maxcol-(Sf.Design.shape[1]-xycentre[i,0])*Sf.cellsize+0.5*Sf.cellsize)
                pointsC.append(-(Sf.Design.shape[0]-xycentre[i,1])*Sf.cellsize+Sf.maxrow+0.5*Sf.cellsize)
                # pointsC.append([Sf.maxcol-(Sf.Design.shape[1]-xycentre[i,0])*Sf.cellsize+0.5*Sf.cellsize,-(Sf.Design.shape[0]-xycentre[i,1])*Sf.cellsize+Sf.maxrow+0.5*Sf.cellsize])
            out.append([p.ID])
            out.append([p.expo])
            out.append([p.Slope0])
            out.append([p.StartElevation])
            out.append(pointsC[:])
        except:
            pass
    with open(outfilename,'w') as output:
        writr=csv.writer(output, lineterminator='\n')
        writr.writerows(out)


            
        # print(K)
        
def write_DXF(idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR,Sf):
    
    # Create a new DXF document.
    filename = asksaveasfilename(title = "Save design",filetypes = (("dxf files","*.dxf"),("all files","*.*")))
    
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    count=0
    layername=1
    Off=0
    if Sf.Offset:
        Off=-1000
    for i in range(0,5*np.size(Center,axis=0),5):
        
        
        EdgeL_points=[]
        for k in range(0,np.size(EdgeL[count], axis=0),1):
            EdgeL_points.append((EdgeL[count][k][0],EdgeL[count][k][1],Off+EdgeL[count][k][2]))
        msp.add_polyline3d(EdgeL_points, dxfattribs={"color": 5, "layer":layername})
    
        Berm1_points=[]
        for k in range(0,np.size(Berm1[count], axis=0),1):
            Berm1_points.append((Berm1[count][k][0],Berm1[count][k][1],Off+Berm1[count][k][2]))
        msp.add_polyline3d(Berm1_points, dxfattribs={"color": 5, "layer":layername})
        
        Berm2_points=[]
        for k in range(0,np.size(Berm2[count], axis=0),1):
            Berm2_points.append((Berm2[count][k][0],Berm2[count][k][1],Off+Berm2[count][k][2]))
        msp.add_polyline3d(Berm2_points, dxfattribs={"color": 5, "layer":layername})
        
        Base1_points=[]
        for k in range(0,np.size(Base1[count], axis=0),1):
            Base1_points.append((Base1[count][k][0],Base1[count][k][1],Off+Base1[count][k][2]))
        msp.add_polyline3d(Base1_points, dxfattribs={"color": 5, "layer":layername})
        
        Center_points=[]
        for k in range(0,np.size(Center[count], axis=0),1):
            Center_points.append((Center[count][k][0],Center[count][k][1],Off+Center[count][k][2]))
        msp.add_polyline3d(Center_points, dxfattribs={"color": 5, "layer":layername})
        
        Base2_points=[]
        for k in range(0,np.size(Base2[count], axis=0),1):
            Base2_points.append((Base2[count][k][0],Base2[count][k][1],Off+Base2[count][k][2]))
        msp.add_polyline3d(Base2_points, dxfattribs={"color": 5, "layer":layername})
        
        Berm3_points=[]
        for k in range(0,np.size(Berm3[count], axis=0),1):
            Berm3_points.append((Berm3[count][k][0],Berm3[count][k][1],Off+Berm3[count][k][2]))
        msp.add_polyline3d(Berm3_points, dxfattribs={"color": 5, "layer":layername})
        
        Berm4_points=[]
        for k in range(0,np.size(Berm4[count], axis=0),1):
            Berm4_points.append((Berm4[count][k][0],Berm4[count][k][1],Off+Berm4[count][k][2]))
        msp.add_polyline3d(Berm4_points, dxfattribs={"color": 5, "layer":layername})
        
        EdgeR_points=[]
        for k in range(0,np.size(EdgeR[count], axis=0),1):
            EdgeR_points.append((EdgeR[count][k][0],EdgeR[count][k][1],Off+EdgeR[count][k][2]))
        msp.add_polyline3d(EdgeR_points, dxfattribs={"color": 5, "layer":layername})
        
        count+=1
        
       
    doc.saveas(filename+'.dxf')
    print('Exported')


           
def write_shapefile(Se,Sf):
    outfilename = asksaveasfilename(title = "Save, Enter file name",filetypes = (("SHP files","*.shp"),("all files","*.*")))
    if len(outfilename)>3:
        if outfilename[-4]!=".":
            outfilename=outfilename +".shp"
    w = shp.Writer(outfilename)
    w.field('Rock_Size','N')
    for p in Se.Lines:
        pointsC=[]
        if p.Linetype=='radius':
            xycentre=p.lineRT.get_xydata()
        else:
            xycentre=p.lineSP.get_xydata()
        
        try:
            for i in range (0,len(p.interpolated_points)-1):
    # Output.append([Surfaces.maxcol-(Surfaces.Design.shape[1]-j)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.maxrow-(Surfaces.Design.shape[0]-i)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.Design[i,j]])
                # if not np.isnan(xyleftb[i,0]):
                    pointsC.append([Sf.maxcol-(Sf.Design.shape[1]-xycentre[i,0])*Sf.cellsize+0.5*Sf.cellsize,-(Sf.Design.shape[0]-xycentre[i,1])*Sf.cellsize+Sf.maxrow+0.5*Sf.cellsize,p.S[i]-p.depthBelow,1])
            w.record(Rock_Size=100)
            w.linez([pointsC])
            pointsC=[]
        except:
            pass
    w.close()
    
    
    
    
    
    
def write_shapefileSurvey(Se,Sf):
    outfilename = asksaveasfilename(title = "Save, Enter file name",filetypes = (("SHP files","*.shp"),("all files","*.*")))
    if len(outfilename)>3:
        if outfilename[-4]!=".":
            outfilename=outfilename +".shp"
    w = shp.Writer(outfilename)
    w.field('Rock_Size','N')
    for p in Se.Lines:
        pointsC=[]
        if p.Linetype=='radius':
            xycentre=p.lineRT.get_xydata()
        else:
            xycentre=p.lineSP.get_xydata()
        try:
            for i in range (0,len(p.interpolated_points)-1):
    # Output.append([Surfaces.maxcol-(Surfaces.Design.shape[1]-j)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.maxrow-(Surfaces.Design.shape[0]-i)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.Design[i,j]])
                # if not np.isnan(xyleftb[i,0]):
                    pointsC.append([Sf.maxcol-(Sf.Design.shape[1]-xycentre[i,0])*Sf.cellsize+0.5*Sf.cellsize,-(Sf.Design.shape[0]-xycentre[i,1])*Sf.cellsize+Sf.maxrow+0.5*Sf.cellsize,p.Surv[i],1])
            w.record(Rock_Size=100)
            w.linez([pointsC])
            pointsC=[]
        except:
            pass
    w.close()

def write_shapefileDesign(Se,Sf):
    outfilename = asksaveasfilename(title = "Save, Enter file name",filetypes = (("SHP files","*.shp"),("all files","*.*")))
    if len(outfilename)>3:
        if outfilename[-4]!=".":
            outfilename=outfilename +".shp"
    w = shp.Writer(outfilename)
    w.field('ID','N')
    cnt=0
    for p in Se.Lines:
        pointsC=[]
        if p.Linetype=='radius':
            xycentre=p.lineRT.get_xydata()
        else:
            xycentre=p.lineSP.get_xydata()
        # try:
        for i in range (0,len(p.interpolated_points)-1):
# Output.append([Surfaces.maxcol-(Surfaces.Design.shape[1]-j)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.maxrow-(Surfaces.Design.shape[0]-i)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.Design[i,j]])
            # if not np.isnan(xyleftb[i,0]):
                pointsC.append([Sf.maxcol-(Sf.Design.shape[1]-xycentre[i,0])*Sf.cellsize+0.5*Sf.cellsize,-(Sf.Design.shape[0]-xycentre[i,1])*Sf.cellsize+Sf.maxrow+0.5*Sf.cellsize,p.Des[i],1])
        w.record(ID=cnt)
        w.linez([pointsC])
        pointsC=[]
        cnt+=1
        # except:
            # pass
    w.close()

    
def write_shapefileP(Se,Sf,Polygons):
    outfilename = asksaveasfilename(title = "Save, Enter file name",filetypes = (("SHP files","*.shp"),("all files","*.*")))
    if len(outfilename)>3:
        if outfilename[-4]!=".":
            outfilename=outfilename +".shp"
    w = shp.Writer(outfilename)
    w.field('Rock_Size','N')
    for p in Polygons:
        pointsC=[]
        xycentre=np.asarray(p.poly.xy)
        for i in range (0,xycentre.shape[0]):
            pointsC.append([Sf.maxcol-(Sf.Design.shape[1]-xycentre[i,0])*Sf.cellsize+0.5*Sf.cellsize,-(Sf.Design.shape[0]-xycentre[i,1])*Sf.cellsize+Sf.maxrow+0.5*Sf.cellsize,0,1])
        w.record(Rock_Size=100)
        w.linez([pointsC])
        pointsC=[]
    w.close()   
    

    
    

def Draw_Surf(Sf,Surfaces):
    Sf.notPlotted=False
#    Sf.a.cla()
    minval = round(np.nanmin(Surfaces.Design[np.where(Surfaces.Design>0)]))
    maxval = round(np.nanmax(Surfaces.Design[np.nonzero(Surfaces.Design)]))
    levels=np.linspace(minval,maxval,int((maxval-minval)/2))
    Sf.p=[Sf.a.contour(Surfaces.Design, levels,linewidths=0.4,colors='gray') ]
    Sf.a.axis('off')
    Sf.a.axis('scaled')
    Sf.a.set_facecolor('black')
    Sf.f.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    Cl=Circle((20, 20), radius = 20/2, fill = False,animated=True,color='white')
    dot=Circle((20, 20), radius = 2/2, fill = True,animated=True,color='yellow')
    point=Circle((20, 20), radius = 1/2, fill = True,animated=True,color='red')
    DyDroplet= Line2D([0,0], [10,10], animated=True, markerfacecolor='blue')
    DyDropletMax= Line2D([0,0], [10,10], animated=True, color='red')
    
    Sf.a.add_artist(Cl)
    Sf.a.add_artist(dot)
    Sf.a.add_artist(point)
    Sf.a.add_artist(DyDroplet)
    Sf.a.add_artist(DyDropletMax)
    Circ = CircleObj(Sf,Cl)
    ledot = Le_dot(Sf,dot)
    lepoint = Le_point(Sf,point)
    drop=[]
    drop.append(DynamicDroplet(Sf,DyDroplet,DyDropletMax,Surfaces.cellsize))
    Sf.circle=Circ
    Sf.dot=ledot
    Sf.point=lepoint
    Sf.drop=drop
    
    x,y=np.meshgrid(np.arange(Surfaces.Design.shape[0]),np.arange(Surfaces.Design.shape[1]))
    x,y=x.flatten(),y.flatten()
    Sf.Allpoints=np.vstack((y,x)).T
    for tp in Sf.p[0].collections:
            # tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
    Sf.canvas.draw()

def Draw_contours(Sf,Surfaces):
        if Sf.notPlotted:
            align_Surfaces(Surfaces)
            Draw_Surf(Sf,Surfaces)
        # if int(Sf.a.get_xlim()[0]) !=Sf.xlim[0] or int(Sf.a.get_xlim()[1]) !=Sf.xlim[1]:
        #         Sf.xlim=[max(0,int(Sf.a.get_xlim()[0])),min(Surfaces.Design.shape[1],int(Sf.a.get_xlim()[1]))]
        #         Sf.a.set_xlim(int(Sf.a.get_xlim()[0]),int(Sf.a.get_xlim()[1]))
        #         Sf.ylim=[max(0,int(Sf.a.get_ylim()[0])),min(Surfaces.Design.shape[0],int(Sf.a.get_ylim()[1]))]
        #         Sf.a.set_ylim(int(Sf.a.get_ylim()[0]),int(Sf.a.get_ylim()[1]))
            
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
        
def Draw_Survey_contours(Sf,Surfaces):
        
        # transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        # transform = mtransforms.Affine2D().translate(Sf.xlim[0],Sf.ylim[0])
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        # background=Sf.f.canvas.copy_from_bbox(Sf.f.bbox)
        try:
            for tp in Sf.S[0].collections:
                tp.remove()
        except:
            pass
        try:    
            Sf.S=[Sf.a.contour(Surfaces.Survey, Sf.levels,linewidths=0.5,colors='green',antialiased=True) ]
            Sf.f.canvas.restore_region(background)
        except:
            return
        for tp in Sf.S[0].collections:
            # tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
        Sf.f.canvas.blit(Sf.a.bbox)
        Sf.canvas.draw_idle()      
        
def Draw_Design_Labels(Sf,Surfaces):
        
        # transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        # transform = mtransforms.Affine2D().translate(Sf.xlim[0],Sf.ylim[0])
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        # background=Sf.f.canvas.copy_from_bbox(Sf.f.bbox)
        
        try:    
            for tp in Sf.p[0].collections:
                Sf.pL=Sf.a.clabel(tp,Sf.levels,inline=True)
                Sf.f.canvas.restore_region(background)
        except:
            return
        for tp in Sf.pL[0].collections:
            # tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
        Sf.f.canvas.blit(Sf.a.bbox)
        Sf.canvas.draw_idle() 
        
def Remove_Design_Labels(Sf,Surfaces):
        
        # transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        # transform = mtransforms.Affine2D().translate(Sf.xlim[0],Sf.ylim[0])
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        # background=Sf.f.canvas.copy_from_bbox(Sf.f.bbox)
        
        try:    
            for tp in Sf.p[0].collections:
                Sf.pL=Sf.a.clabel(tp,Sf.levels,inline=True)
                Sf.f.canvas.restore_region(background)
        except:
            return
        for tp in Sf.pL[0].collections:
            # tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
        Sf.f.canvas.blit(Sf.a.bbox)
        Sf.canvas.draw_idle() 
        
def Remove_Survey_contours(Sf,Surfaces):
        
        # transform = mtransforms.Affine2D().translate(Sf.a.get_xlim()[0],Sf.a.get_ylim()[0])
        # transform = mtransforms.Affine2D().translate(Sf.xlim[0],Sf.ylim[0])
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        # background=Sf.f.canvas.copy_from_bbox(Sf.f.bbox)
        try:
            for tp in Sf.S[0].collections:
                tp.remove()
        except:
            pass
        Sf.f.canvas.blit(Sf.a.bbox)
        Sf.canvas.draw_idle()      
        
        
def Draw_Update(Sf,Surfaces):
        Sf.canvas.draw_idle()
        
        
def Draw_Figure(Sf):
        background=Sf.f.canvas.copy_from_bbox(Sf.a.bbox)
        Sf.f.canvas.restore_region(background)
  
        for tp in Sf.p[0].collections:
            tp.set_transform(transform+Sf.a.transData)
            Sf.a.draw_artist(tp)
        Sf.f.canvas.blit(Sf.a.bbox)
        Sf.canvas.draw_idle()


def import_SurveyPil(Surfaces,TE1,TE2,TE3,TE4):
    Tk().withdraw()
    filepath = askopenfilename(title = "Select gridded survey",filetypes = (("tif files","*.tif"),("all files","*.*")))
    
    #create tiff stuff
    im = Image.open(filepath)
    print(im)
    elevation=np.array(im)
    print(['Survey',im.tag[33922],im.tag[33550]])
    if im.tag[33550][0]>0:# and im.tag[33550][1]>0:
        Surfaces.Survey_maxcol=im.tag[33922][3]+elevation.shape[1]*im.tag[33550][0]
        Surfaces.Survey_maxrow=im.tag[33922][4]
        elevation=np.flip(elevation,0)
    else:
        Surfaces.Survey_maxcol=im.tag[33922][3]
        Surfaces.Survey_maxrow=im.tag[33922][4]
        elevation=np.flip(elevation,1)
        elevation=np.flip(elevation,0)
    print(['Survey',Surfaces.Survey_maxcol])
    
    #return filename only
    filename = os.path.basename(filepath)
    print(filename)
    
    TE1.insert(tk.END, filename)
    
    #return Date Modified
    modTimesinceEpoc = os.path.getmtime(filepath)
    modificationTime = datetime.datetime.fromtimestamp(modTimesinceEpoc).strftime('%Y-%m-%d %H:%M')
    print(modificationTime)

    TE2.insert(tk.END, modificationTime)

    #return number of points
    point_count = elevation.size
    
    TE3.insert(tk.END, point_count)
    
    #return Min/Max Z
    maxZ=round(np.max(elevation), 1)
    minZ=round(np.min(elevation), 1)
    ZStats=(str(minZ)+" / "+str(maxZ))
    
    TE4.insert(tk.END, ZStats)
    
    # maxcol=im.tag[33922][3]
    # maxrow=im.tag[33922][4]
    # cellsize=-1*im.tag[33550][0]
    # elevation=np.flip(elevation,1)
    # elevation=np.flip(elevation,0)
    Surfaces.Survey_cellsize=abs(im.tag[33550][0])
    Surfaces.Survey=elevation

def ElevOffset():
    result=tkinter.messagebox.askquestion("Offset","Negative Elevations Detected, Add 1000m to Survey and Design?",icon="warning")
    return result

def CellsizeMismatch():
    result=tkinter.messagebox.askquestion("Cellsize","Mishmatch between cellsizes detected, resample surface with larger cellsize to the smaller cellsize?",icon="warning")
    return result

def import_SurveyPil2(Surfaces):
    Tk().withdraw()
    filepath = askopenfilename(title = "Select gridded survey",filetypes = (("tif files","*.tif"),("all files","*.*")))
    im = Image.open(filepath)
    elevation=np.array(im)
    if im.tag[33550][0]>0:# and im.tag[33550][1]>0:
        Surfaces.Survey_maxcol=im.tag[33922][3]+elevation.shape[1]*im.tag[33550][0]
        Surfaces.Survey_maxrow=im.tag[33922][4]
        print((Surfaces.Survey_maxcol,Surfaces.Survey_maxcol))
        elevation=np.flip(elevation,0)
    else:
        Surfaces.Survey_maxcol=im.tag[33922][3]
        Surfaces.Survey_maxrow=im.tag[33922][4]
        print((Surfaces.Survey_maxcol,Surfaces.Survey_maxcol))
        elevation=np.flip(elevation,1)
        elevation=np.flip(elevation,0)
    
    Surfaces.Survey=elevation
    if Surfaces.Offset:
        Surfaces.Survey[np.where(Surfaces.Survey!=0)]+=1000
    align_Surfaces(Surfaces)
        
def import_DesignPil2(Surfaces,Sf):
    Tk().withdraw()
    filepath = askopenfilename(title = "Select gridded Design",filetypes = (("tif files","*.tif"),("all files","*.*")))
    im = Image.open(filepath)
    elevation=np.array(im)
    if im.tag[33550][0]>0:# and im.tag[33550][1]>0:
        Surfaces.maxcol=im.tag[33922][3]+elevation.shape[1]*im.tag[33550][0]
        Surfaces.maxrow=im.tag[33922][4]
        elevation=np.flip(elevation,0)
    else:
        Surfaces.maxcol=im.tag[33922][3]
        Surfaces.maxrow=im.tag[33922][4]
        elevation=np.flip(elevation,1)
        elevation=np.flip(elevation,0)
    Surfaces.Design=elevation
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000
    Surfaces.Design[np.where(Surfaces.Design>10000)]=0
    Surfaces.Design[np.where(Surfaces.Design<-10000)]=0
    Surfaces.minval = round(np.nanmin(elevation[np.nonzero(elevation)]))-20
    Surfaces.maxval = round(np.nanmax(elevation[np.nonzero(elevation)]))+20
    align_Surfaces(Surfaces)
    Draw_contours(Sf,Surfaces)    

def import_DesignPil(Surfaces,TD1,TD2,TD3,TD4):
    Tk().withdraw()
    filepath = askopenfilename(title = "Select gridded design",filetypes = (("tif files","*.tif"),("all files","*.*")))

    im = Image.open(filepath)
    elevation=np.array(im)
    Surfaces.tag=im.tag
    if im.tag[33550][0]>0:# and im.tag[33550][1]>0:
        Surfaces.maxcol=im.tag[33922][3]+elevation.shape[1]*im.tag[33550][0]
        Surfaces.maxrow=im.tag[33922][4]
        elevation=np.flip(elevation,0)
    else:
        Surfaces.maxcol=im.tag[33922][3]
        Surfaces.maxrow=im.tag[33922][4]
        elevation=np.flip(elevation,1)
        elevation=np.flip(elevation,0)
        
    # elevation=np.flip(elevation,1)
    Surfaces.Design=elevation
    Surfaces.Design[np.where(Surfaces.Design>10000)]=0
    Surfaces.Design[np.where(Surfaces.Design<-10000)]=0
    Surfaces.minval = round(np.nanmin(elevation[np.nonzero(elevation)]))-20
    Surfaces.maxval = round(np.nanmax(elevation[np.nonzero(elevation)]))+20
    
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000
        Surfaces.minval+=1000
        Surfaces.maxval+=1000
    else:
        if Surfaces.minval+20<0:
            result=ElevOffset()
            print(result)
            if result=='yes':
                Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000
                Surfaces.minval+=1000
                Surfaces.maxval+=1000
                Surfaces.Offset=True
                if Surfaces.Survey !=[]:
                    Surfaces.Survey[np.where(Surfaces.Survey!=0)]+=1000
    # print(Surfaces.minval,Surfaces.maxval)
    Surfaces.cellsize=abs(im.tag[33550][0])
    # print(Surfaces.cellsize)
    Surfaces.Dist=np.zeros((400,400))
    Surfaces.Active=np.zeros_like(elevation)
    Surfaces.Canals=np.zeros_like(elevation)
    Surfaces.Poly=np.zeros_like(elevation)
    
    Surfaces.Active.fill(1)
    for i in range (0,400):
        for j in range (0,400):
            Surfaces.Dist[i,j]=((i*Surfaces.cellsize)**2+(j*Surfaces.cellsize)**2)**0.5
    Surfaces.Dist[0,0]=0
    
    #return filename only
    filename = os.path.basename(filepath)
    print(filename)
    
    TD1.insert(tk.END, filename)
    
    #return Date Modified
    modTimesinceEpoc = os.path.getmtime(filepath)
    modificationTime = datetime.datetime.fromtimestamp(modTimesinceEpoc).strftime('%Y-%m-%d %H:%M')
    print(modificationTime)

    TD2.insert(tk.END, modificationTime)

    #return number of points
    point_count = elevation.size
    
    TD3.insert(tk.END, point_count)
    
    #return Min/Max Z
    maxZ=round(np.max(elevation), 1)
    minZ=round(np.min(elevation), 1)
    ZStats=(str(minZ)+" / "+str(maxZ))
    
    TD4.insert(tk.END, ZStats)


def recastCellsize(Array,current_cellsize,new_cellsize):
    x = np.linspace(0,Array.shape[1]-1,Array.shape[1])
    y = np.linspace(0,Array.shape[0]-1,Array.shape[0])

    Interp = RegularGridInterpolator((y,x),Array)
    
    factor = current_cellsize/new_cellsize
    xx = np.linspace(0,Array.shape[1]-1,int(Array.shape[1]*factor))
    yy = np.linspace(0,Array.shape[0]-1,int(Array.shape[0]*factor))
    YY, XX = np.meshgrid(yy, xx, indexing='ij')
    
    New_Array = Interp((YY,XX))
    
    return New_Array

def save_DesignPilReducedSize(Surfaces):
    # Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save design",filetypes = (("tif files","*.tif"),("all files","*.*")))
    path = filename
    
    new_cellsize=3.0
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]-=1000
    New_Array_cellize=recastCellsize(Surfaces.Design,Surfaces.cellsize,new_cellsize)
    im=Image.fromarray(np.flip(np.flip(New_Array_cellize,0),1))
    tag={}
    tag[33922]=(0.0,0.0,0.0,Surfaces.maxcol+0*Surfaces.cellsize,Surfaces.maxrow+0*Surfaces.cellsize,0.0)
    tag[33550]=(-1*new_cellsize,1*new_cellsize,0.0)
    
    
    # im=Image.fromarray(np.flip(Surfaces.Design,0))
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".tif"
    else:
        filename=filename +".tif"
    im.save(filename,tiffinfo=tag)
    im.close
    
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000    

def resampleRaster(LargerArray,mincol,maxcol,minrow,maxrow):
    #Sample LargerArray outside min and max extents
    mincol_sample = int(mincol)-10
    if mincol_sample<0:
        mincol_sample = 0
    maxcol_sample = int(maxcol)+10
    if maxcol_sample>=LargerArray.shape[1]:
        maxcol_sample = LargerArray.shape[1]
    minrow_sample = int(minrow)-10
    if minrow_sample<0:
        minrow_sample = 0
    maxrow_sample = int(maxrow)+10
    if maxrow_sample>=LargerArray.shape[0]:
        maxrow_sample = LargerArray.shape[0]
        
    #Interpolate LargerArray
    # print(mincol_sample,maxcol_sample,minrow_sample,maxrow_sample)
    x = np.array(range(mincol_sample,maxcol_sample))
    y = np.array(range(minrow_sample,maxrow_sample))

    Interp = RegularGridInterpolator((y,x),LargerArray[minrow_sample:maxrow_sample,mincol_sample:maxcol_sample])
    
    
    #Define offset grid relative to LargerArray
    xx = np.linspace(mincol,maxcol-1,int(maxcol-mincol))
    yy = np.linspace(minrow,maxrow-1,int(maxrow-minrow))
    print(xx)
    print(yy)
    YY, XX = np.meshgrid(yy, xx, indexing='ij')
    
    New_Array = Interp((YY,XX))
    
    return(New_Array)


def align_Surfaces(Surfaces):
    if Surfaces.maxcol>Surfaces.Survey_maxcol:
        colpad=(Surfaces.maxcol-Surfaces.Survey_maxcol)/Surfaces.cellsize
        Surfaces.Survey= np.pad(Surfaces.Survey,((0,0),(0,int(colpad))),'constant', constant_values=((0,0),(0, 0)))
    if Surfaces.maxrow>Surfaces.Survey_maxrow:
        rowpad=(Surfaces.maxrow-Surfaces.Survey_maxrow)/Surfaces.cellsize
        Surfaces.Survey= np.pad(Surfaces.Survey,((0,int(rowpad)),(0,0)),'constant', constant_values=((0,0),(0, 0)))
    if Surfaces.maxcol<Surfaces.Survey_maxcol:
        colpad=-(Surfaces.maxcol-Surfaces.Survey_maxcol)/Surfaces.cellsize
        if int(colpad)>0:
            Surfaces.Survey=Surfaces.Survey[::1,0:-int(colpad)]
    if Surfaces.maxrow<Surfaces.Survey_maxrow:
        rowpad=-(Surfaces.maxrow-Surfaces.Survey_maxrow)/Surfaces.cellsize
        if int(rowpad)>0:
            Surfaces.Survey=Surfaces.Survey[0:-int(rowpad),:]
    if Surfaces.Design.shape[0]>Surfaces.Survey.shape[0]:
        rowout=Surfaces.Design.shape[0]-Surfaces.Survey.shape[0]
        Surfaces.Survey=np.pad(Surfaces.Survey,((int(rowout),0),(0,0)),'constant', constant_values=((0,0),(0, 0)))
    if Surfaces.Design.shape[1]>Surfaces.Survey.shape[1]:
        colout=Surfaces.Design.shape[1]-Surfaces.Survey.shape[1]
        Surfaces.Survey=np.pad(Surfaces.Survey,((0,0),(int(colout),0)),'constant', constant_values=((0,0),(0, 0)))
    if Surfaces.Design.shape[0]<Surfaces.Survey.shape[0]:
        rowout=-(Surfaces.Design.shape[0]-Surfaces.Survey.shape[0])
        Surfaces.Survey=Surfaces.Survey[int(rowout):,:]
    if Surfaces.Design.shape[1]<Surfaces.Survey.shape[1]:
        colout=-(Surfaces.Design.shape[1]-Surfaces.Survey.shape[1])
        Surfaces.Survey=Surfaces.Survey[:,int(colout):]
        

    

@jit
def Merge_Array(maxrow,maxcol,cellsize,Arr,Points):
    for i in range(0,Points.shape[0]):
        p=Points[i]
        row=(maxrow-p[1])/cellsize
        col=(maxcol-p[0])/cellsize
        row = round(row,0)
        col = round(col,0)
        row=int(row)
        col=int(col)
        if row<Arr.shape[0] and col<Arr.shape[1] and row>=0 and col>=0:
            Arr[row,col]=p[2]
            
@jit
def Import_Points(maxrow,maxcol,cellsize,Arr,Points):
    for i in range(0,Points.shape[0]):
        p=Points[i]
        row=(maxrow-p[1])/cellsize
        col=(maxcol-p[0])/cellsize
        row = round(row,0)
        col = round(col,0)
        row=int(row)
        col=int(col)
        if row<Arr.shape[0] and col<Arr.shape[1] and row>=0 and col>=0:
            Arr[row,col]=p[2]
            
@jit   
def settlement(Survey,Design):
    for i in range (0,Survey.shape[0]):
        for j in range (0,Survey.shape[1]):
            if Design[i,j]>Survey[i,j]:
                dx=Design[i,j]-Survey[i,j]
                Design[i,j]-=dx*0.5
                
# @jit
def create_Array(maxrow,maxcol,cellsize,Arr,Points):
    for i in range(0,Points.shape[0]):
        # p=Points[i]
        row=(maxrow-Points[i,1])/cellsize
        col=(maxcol-Points[i,0])/cellsize
        row = round(row,0)
        col = round(col,0)
        row=int(row)
        col=int(col)
        if row<Arr.shape[0] and col<Arr.shape[1] and row>=0 and col>=0:
            Arr[row,col]=Points[i,2]
            
def convert_points_to_tiff():
    Tk().withdraw()
    filename = askopenfilename(title = "Select points",filetypes = (("csv files","*.csv"),("all files","*.*")))
    Temp=[]
    c=0
    for line in open (filename):
        c+=1    
        line = line.replace('"', ' ')
        row=re.split(",| ",line)
        if c%1==0:
            try: 
                if float(row[2])>0:
                    Temp.append([float(row[0]), float(row[1]),float(row[2])])
            except:
                print (row)
    Points=np.array(Temp,dtype=np.float32)            
    # with open(filename, 'r') as f:
    #     reader = csv.reader(f)
    #     Points = np.array(list(reader),dtype=np.float64)
        
    cellsize = 1000
    for i in range (0,50):
        if math.fabs(Points[i,0]- Points[i+1,0])<cellsize and math.fabs(Points[i,0]- Points[i+1,0])>0:
            cellsize=math.fabs(Points[i,0]- Points[i+1,0])
        if math.fabs(Points[i,1]- Points[i+1,1])<cellsize and math.fabs(Points[i,1]- Points[i+1,1])>0:
            cellsize=math.fabs(Points[i,1]- Points[i+1,1])
    # cellsize=int(cellsize)
    # print(cellsize)
    maxcol=np.max(Points[:,0])
    maxrow=np.max(Points[:,1])
    
    mincol=np.min(Points[:,0])
    minrow=np.min(Points[:,1])
    
    rows=int((maxrow-minrow)/cellsize)
    cols=int((maxcol-mincol)/cellsize)
    # print((maxrow,minrow))
    # print(rows)
    # print((maxrow-minrow)/cellsize)

    A=np.zeros((rows,cols))    
    create_Array(maxrow,maxcol,cellsize,A,Points)
    
    Tk().withdraw()
    # filename2 = asksaveasfilename(title = "Save design",filetypes = (("tif files","*.tif"),("all files","*.*")))
    filename2=filename[0:-4]
    filename2=filename2+'.tif'
    tag={}
    tag[33922]=(0.0,0.0,0.0,1.0*maxcol+0.5*cellsize,1.0*maxrow+0.5*cellsize,0.0)
    # tag[33922]=(0.0,0.0,0.0,1.0*maxcol-2.5*cellsize,1.0*maxrow-2.5*cellsize,0.0)
    # tag[33922]=(0.0,0.0,0.0,627494.0,6039494.0,0.0)
    # print(tag[33922])
    # tag[33550]=(-1.0*cellsize,1.0*cellsize,0.0)
    tag[33550]=(-cellsize,cellsize,0.0)
    im=Image.fromarray(A)  
    im.save(filename2,tiffinfo=tag)
    im.close

def save_DesignLOCKED(Surfaces):
    # Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save Locked Areas",filetypes = (("tif files","*.tif"),("all files","*.*")))
    path = filename
    tag={}
    tag[33922]=(0.0,0.0,0.0,Surfaces.maxcol+0*Surfaces.cellsize,Surfaces.maxrow-0*Surfaces.cellsize,0.0)
    tag[33550]=(-1*Surfaces.cellsize,1*Surfaces.cellsize,0.0)
    # if Surfaces.Offset:
    #     Surfaces.Design[np.where(Surfaces.Design!=0)]-=1000
    im=Image.fromarray(np.flip(np.flip(Surfaces.Active,0),1))
    
    # im=Image.fromarray(np.flip(Surfaces.Design,0))
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".tif"
    else:
        filename=filename +".tif"
    im.save(filename,tiffinfo=tag)
    im.close
    
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000

def save_DesignPil(Surfaces):
    # Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save design",filetypes = (("tif files","*.tif"),("all files","*.*")))
    path = filename
    tag={}
    tag[33922]=(0.0,0.0,0.0,Surfaces.maxcol+0*Surfaces.cellsize,Surfaces.maxrow-0*Surfaces.cellsize,0.0)
    tag[33550]=(-1*Surfaces.cellsize,1*Surfaces.cellsize,0.0)
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]-=1000
    im=Image.fromarray(np.flip(np.flip(Surfaces.Design,0),1))
    
    # im=Image.fromarray(np.flip(Surfaces.Design,0))
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".tif"
    else:
        filename=filename +".tif"
    im.save(filename,tiffinfo=tag)
    im.close
    
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000

def save_CutFill(Surfaces):
    C=np.zeros_like(Surfaces.Design)
    cutfillim(Surfaces.Design,Surfaces.Survey,C)
    
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save design",filetypes = (("tif files","*.tif"),("all files","*.*")))
    path = filename
    tag={}
    tag[33922]=(0.0,0.0,0.0,Surfaces.maxcol+0*Surfaces.cellsize,Surfaces.maxrow+0*Surfaces.cellsize,0.0)
    tag[33550]=(-1*Surfaces.cellsize,1*Surfaces.cellsize,0.0)
    im=Image.fromarray(np.flip(np.flip(C,0),1))
    # im=Image.fromarray(np.flip(Surfaces.Design,0))
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".tif"
    else:
        filename=filename +".tif"
    im.save(filename,tiffinfo=tag)
    im.close
    
        
def Convert_Raster_to_Points(Surfaces):
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save design",filetypes = (("csv files","*.csv"),("all files","*.*")))
    path = filename
    Output=[]
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]-=1000
    
    for i in range (0,Surfaces.Design.shape[0]):
        for j in range (0,Surfaces.Design.shape[1]):
            if Surfaces.Design[i,j]!=0:
                Output.append([Surfaces.maxcol-(Surfaces.Design.shape[1]-j)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.maxrow-(Surfaces.Design.shape[0]-i)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.Design[i,j]])
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".csv"
    else:
        filename=filename +".csv"
    with open(filename,'w') as output:
        writr=csv.writer(output, lineterminator='\n')
        writr.writerows(Output)
    if Surfaces.Offset:
            Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000


def Stage_Capacity(Surfaces):
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save Stage Capacity of locked points",filetypes = (("csv files","*.csv"),("all files","*.*")))
    Output=[]
    MinVal=np.min(Surfaces.Design[np.where(Surfaces.Active==0)])
    MaxVal=np.max(Surfaces.Design[np.where(Surfaces.Active==0)])
    print(MinVal)
    print(MaxVal)
    elevC=MinVal
    VolC=0
    step=(MaxVal-MinVal)/1000
    for i in range (0,1000):
        Area=np.where(Surfaces.Design[np.where(Surfaces.Active==0)]<=elevC)
        # print(Area[0].shape[0])
        Area=Area[0].shape[0]
        # print(Area)
        # print(len(Area))
        # Area=Area[0].shape[0]
        Output.append([elevC,VolC])
        VolC+=Area*step
        elevC+=step
        if elevC>MaxVal:
            break
    
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".csv"
    else:
        filename=filename +".csv"
    with open(filename,'w') as output:
        writr=csv.writer(output, lineterminator='\n')
        writr.writerows(Output)
        
def Export_Grains(Surfaces,G1,G2,G3,G4,G5,G6,G7,G8,G9):
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save Grains",filetypes = (("csv files","*.csv"),("all files","*.*")))
    path = filename
    Output=[]
    Gs=[G1,G2,G3,G4,G5,G6,G7,G8,G9]
    Des=np.flip(Surfaces.Design,axis=0)
    Act=np.flip(Surfaces.Active,axis=0)
    for i in range (0,Des.shape[0]):
        for j in range (0,Des.shape[1]):
            if Des[i,j]>0 and Act[i,j]==0:
                l=[j,i,0,0]
                for jj in range (0,9):
                        l.append(Gs[jj])
                l.append(0)
                for k in range (0,10):
                    for jj in range (0,9):
                        l.append(Gs[jj])
                Output.append(l)
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".csv"
    else:
        filename=filename +".csv"
    with open(filename,'w') as output:
        writr=csv.writer(output, lineterminator='\n')
        writr.writerows(Output)
    
def Save_Visible(Surfaces,Visible,Elevs):
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save Visibility",filetypes = (("tif files","*.tif"),("all files","*.*")))
    path = filename
    tag={}
    tag[33922]=(0.0,0.0,0.0,Surfaces.maxcol+0*Surfaces.cellsize,Surfaces.maxrow+0*Surfaces.cellsize,0.0)
    tag[33550]=(-1*Surfaces.cellsize,1*Surfaces.cellsize,0.0)
    im=Image.fromarray(np.flip(np.flip(Visible,0),1))
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".tif"
    else:
        filename=filename +".tif"
    im.save(filename,tiffinfo=tag)
    im.close

    Tk().withdraw()
    filename = asksaveasfilename(title = "Save Elev Points",filetypes = (("csv files","*.csv"),("all files","*.*")))
    path = filename
    Output=[]
    
    for p in Elevs:
        j=p.annot.xy[0]
        i=p.annot.xy[1]
        Output.append([Surfaces.maxcol-(Surfaces.Design.shape[1]-j)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.maxrow-(Surfaces.Design.shape[0]-i)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.Design[int(i),int(j)]])
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".csv"
    else:
        filename=filename +".csv"
    with open(filename,'w') as output:
        writr=csv.writer(output, lineterminator='\n')
        writr.writerows(Output)

        
def save_DesignPoints(Surfaces):
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save design",filetypes = (("csv files","*.csv"),("all files","*.*")))
    path = filename
    Output=[]
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]-=1000
    
    for i in range (0,Surfaces.Design.shape[0]):
        for j in range (0,Surfaces.Design.shape[1]):
            if Surfaces.Design[i,j]!=0:
                Output.append([Surfaces.maxcol-(Surfaces.Design.shape[1]-j)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.maxrow-(Surfaces.Design.shape[0]-i)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.Design[i,j]])
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".csv"
    else:
        filename=filename +".csv"
    with open(filename,'w') as output:
        writr=csv.writer(output, lineterminator='\n')
        writr.writerows(Output)
    if Surfaces.Offset:
            Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000

def save_DesignPointsLocked(Surfaces):
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save design",filetypes = (("csv files","*.csv"),("all files","*.*")))
    path = filename
    Output=[]
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]-=1000
    
    for i in range (0,Surfaces.Design.shape[0]):
        for j in range (0,Surfaces.Design.shape[1]):
            if Surfaces.Design[i,j]!=0 and Surfaces.Active[i,j]==0:
                Output.append([Surfaces.maxcol-(Surfaces.Design.shape[1]-j)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.maxrow-(Surfaces.Design.shape[0]-i)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.Design[i,j]])
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".csv"
    else:
        filename=filename +".csv"
    with open(filename,'w') as output:
        writr=csv.writer(output, lineterminator='\n')
        writr.writerows(Output) 
    if Surfaces.Offset:
            Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000
            
def save_DesignPointsMod(Surfaces):
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save design",filetypes = (("csv files","*.csv"),("all files","*.*")))
    path = filename
    Output=[]
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]-=1000
    
    for i in range (0,Surfaces.Design.shape[0]):
        for j in range (0,Surfaces.Design.shape[1]):
            if Surfaces.Design[i,j]!=0 and Surfaces.Survey[i,j]!=0 and Surfaces.Design[i,j]!=Surfaces.Survey[i,j]:
                Output.append([Surfaces.maxcol-(Surfaces.Design.shape[1]-j)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.maxrow-(Surfaces.Design.shape[0]-i)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.Design[i,j]])
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".csv"
    else:
        filename=filename +".csv"
    with open(filename,'w') as output:
        writr=csv.writer(output, lineterminator='\n')
        writr.writerows(Output)           
    if Surfaces.Offset:
        Surfaces.Design[np.where(Surfaces.Design!=0)]+=1000
        
def import_Design(Surfaces,text):
    Tk().withdraw()
    filename = askopenfilename(title = "Select gridded survey",filetypes = (("tif files","*.tif"),("all files","*.*")))
    path = filename
    text.insert(tk.END, filename)
    gdal.UseExceptions()
    ds = gdal.Open(path)
    ulx, xres, xskew, uly, yskew, yres  = ds.GetGeoTransform()
    band = ds.GetRasterBand(1)
    elevation = band.ReadAsArray()
    elevation=np.flip(elevation,1)
    elevation=np.flip(elevation,0)
    Surfaces.Design=elevation
    Surfaces.minval = round(np.min(elevation[np.where(elevation>0)]))-20
    Surfaces.maxval = round(np.max(elevation[np.nonzero(elevation)]))+20
    Surfaces.cellsize=abs(xres)
    # print(xres)
    Surfaces.Dist=np.zeros((400,400))
    Surfaces.Active=np.zeros_like(elevation)
    Surfaces.Canals=np.zeros_like(elevation)
    Surfaces.Active.fill(1)
    for i in range (0,400):
        for j in range (0,400):
            Surfaces.Dist[i,j]=((i*xres)**2+(j*xres)**2)**0.5
    Surfaces.Dist[0,0]=10
    
    
def import_Surface1(Surfaces,text):
    Tk().withdraw()
    filename = askopenfilename(title = "Select gridded survey",filetypes = (("tif files","*.tif"),("all files","*.*")))
    path = filename
    text.insert(tk.END, filename)
    gdal.UseExceptions()
    ds = gdal.Open(path)
    ulx, xres, xskew, uly, yskew, yres  = ds.GetGeoTransform()
    band = ds.GetRasterBand(1)
    elevation = band.ReadAsArray()
    elevation=np.flip(elevation,1)
    Surfaces.Surface1=elevation
    
def import_Surface2(Surfaces,text):
    Tk().withdraw()
    filename = askopenfilename(title = "Select gridded survey",filetypes = (("tif files","*.tif"),("all files","*.*")))
    path = filename
    text.insert(tk.END, filename)
    gdal.UseExceptions()
    ds = gdal.Open(path)
    ulx, xres, xskew, uly, yskew, yres  = ds.GetGeoTransform()
    band = ds.GetRasterBand(1)
    elevation = band.ReadAsArray()
    elevation=np.flip(elevation,1)
    Surfaces.Surface2=elevation

@jit
def Fill_Cut(Design,Survey,cut,fill,cellsize):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    sq=cellsize**2
    cut0=0
    fill0=0
    for i in range(0,Design.shape[0]):
        for j in range(0,Design.shape[1]):
            if Design[i,j]>0 and Survey[i,j]>0: 
               dz=Survey[i,j]-Design[i,j]
               if dz>0: #cut
                    cut0+=dz*sq
               elif dz<0:
                    fill0-=dz*sq
                                    
    cut[0]=-cut0
    fill[0]=fill0

@jit
def Shape_Balanced(x,y,rad,Slope,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    Slope=1/Slope
    #x,y=centre of brush
    #Iter=# of iterations
    for i in range (0,Iter):
        #loop through all points in brush radius
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0: #BOUNDS CHECK
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0: #Active array defines areas where points may be be locked
                        d=Dist[abs(rowoff),abs(coloff)] #distance lookup table
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)#this is the decay function from centre of brush
                            
                            #local loop around the point
                            for xoff in range(-1,2):
                                for yoff in range(-1,2):
                                   
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                       
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                            d2=Dist[abs(yoff),abs(xoff)] #distasnce lookup again
                                            delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                            sl=delev/d2
                                            if sl>Slope: #it gets interesting when we make limiting slope a function of elevation, we can make concave slopes, even benches

                                                Design[y+rowoff,x+coloff]-=c*0.05 # if we comment this out it would be fill only to a certain slope
                                                Design[y+rowoff+yoff,x+coloff+xoff]+=c*0.05 # if we comment this out it would be cut only to a certain slope

@jit
def Close_Gaps(Design):

    for i in range (0,500):
        for x in range (0,Design.shape[1]):
            for y in range (0,Design.shape[0]):
                if Design[y,x]==0:
                    count = 0
                    sumE=0
                    for rowoff in range (-1,2):
                        for coloff in range (-1,2):
                            if rowoff!=0 or coloff!=0:
                                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                                    if Design[y+rowoff,x+coloff]>0:
                                        count+=1
                                        sumE+=Design[y+rowoff,x+coloff]
                    if count>1:
                        Design[y,x]=sumE/count

@jit
def Shape_Poly(Design,Active,Slope,cellsize,Dist):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):

    Slope=1/Slope

    for i in range (0,1000):
        for x in range (0,Design.shape[1]):
            for y in range (0,Design.shape[0]):
                if Active[y,x]==0:
                    for rowoff in range (-1,2):
                        for coloff in range (-1,2):
                            if rowoff!=0 or coloff!=0:
                                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                                    if Design[y+rowoff,x+coloff]>0:
                                        d2=Dist[abs(rowoff),abs(coloff)]
                                        delev=Design[y,x]-Design[y+rowoff,x+coloff]
                                        sl=delev/d2
                                        if sl>Slope:
                                            Design[y,x]-=0.05
                                            Design[y+rowoff,x+coloff]+=0.05


@jit
def Shape_Poly_Profile(Design,Active,Slope,cellsize,Dist,S):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):

    Slope=1/Slope

    for i in range (0,5000):
        for x in range (0,Design.shape[1]):
            for y in range (0,Design.shape[0]):
                if Active[y,x]==0 and Design[y,x]>0:
                    if Design[y,x]<S[0]:
                        Slope=(S[1]-S[0])/cellsize
                    elif Design[y,x]>S[-1]:
                        Slope=(S[-1]-S[-2])/cellsize
                    else:
                        for ii in range (0,S.shape[0]-1):
                            if S[ii]<=Design[y,x] and S[ii+1]>=Design[y,x]:
                                Slope=(S[ii+1]-S[ii])/cellsize
                                break

                    for rowoff in range (-1,2):
                        for coloff in range (-1,2):
                            if rowoff!=0 or coloff!=0:
                                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                                    if Design[y+rowoff,x+coloff]>0:

                                        d2=Dist[abs(rowoff),abs(coloff)]
                                        delev=Design[y,x]-Design[y+rowoff,x+coloff]
                                        sl=delev/d2
                                        if sl>Slope:
                                            Design[y,x]-=0.05
                                            Design[y+rowoff,x+coloff]+=0.05

@jit
def Shape_Cut(x,y,rad,Slope,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    Slope=1/Slope

    for i in range (0,Iter):
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)

                            for xoff in range(-2,3):
                                for yoff in range(-2,3):
                                   
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                       
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                            d2=Dist[abs(yoff),abs(xoff)]
                                            delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                            sl=delev/d2
                                            if sl>Slope:

                                                Design[y+rowoff,x+coloff]-=c*0.002



@jit
def Shape_Balanced_Above(x,y,rad,Slope,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    Slope=1/Slope

    for i in range (0,Iter):
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)

                            for xoff in range(-1,2):
                                for yoff in range(-1,2):
                                   
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                       
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                            d2=Dist[abs(yoff),abs(xoff)]
                                            delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                            sl=delev/d2
                                            if sl>Slope:
                                                if Design[y+rowoff,x+coloff]-c*0.01>=Survey[y+rowoff,x+coloff]:
 
                                                    Design[y+rowoff,x+coloff]-=c*0.002
                                                      
                                                    Design[y+rowoff+yoff,x+coloff+xoff]+=c*0.002
                                                 

@jit
def Close_gaps(Design):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    

    for i in range (0, Design.shape[0]):
        for j in range (0, Design.shape[1]):
            if Design[i,j]==0 or Design[i,j]<20:
                count=0
                sumE=0
                for rowoff in range (-1,2):
                    for coloff in range (-1,2):
                        if j+coloff<Design.shape[1] and j+coloff>0 and i+rowoff<Design.shape[0] and i+rowoff>0:
                            if Design[i+rowoff,j+coloff]>0:
                                count+=1
                                sumE+=Design[i+rowoff,j+coloff]
                if count>2:
                    Design[i,j]=sumE/count
                                
                                
                                                    
@jit
def Shape_Cut_Above(x,y,rad,Slope,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    Slope=1/Slope

    for i in range (0,Iter):
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)

                            for xoff in range(-2,3):
                                for yoff in range(-2,3):
                                   
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                       
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                            d2=Dist[abs(yoff),abs(xoff)]
                                            delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                            sl=delev/d2
                                            if sl>Slope:
                                                if Design[y+rowoff,x+coloff]-c*0.01>=Survey[y+rowoff,x+coloff]:
                                                    Design[y+rowoff,x+coloff]-=c*0.01

@jit
def Shape_Fill_AboveS(x,y,rad,Slope,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    Slope=1/Slope
   
    for i in range (0,Iter):
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0 and Design[y+rowoff,x+coloff]>Survey[y+rowoff,x+coloff]:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)

                            for xoff in range(-1,2):
                                for yoff in range(-1,2):
                                   
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                       
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                            d2=Dist[abs(yoff),abs(xoff)]
                                            delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                            sl=delev/d2
                                            if sl>Slope:
                                                                                                                                              
                                                Design[y+rowoff+yoff,x+coloff+xoff]+=c*0.002                                                       
                                                    
@jit
def Shape_Fill(x,y,rad,Slope,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    Slope=1/Slope
   
    for i in range (0,Iter):
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)

                            for xoff in range(-1,2):
                                for yoff in range(-1,2):
                                   
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                       
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                            d2=Dist[abs(yoff),abs(xoff)]
                                            delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                            sl=delev/d2
                                            if sl>Slope:
                                                                                                                                              
                                                Design[y+rowoff+yoff,x+coloff+xoff]+=c*0.002


@jit
def Shape_Fill_All(x,y,rad,Slope,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    # radius=int(rad/cellsize)
    Slope=1/Slope
   
    for i in range (0,Iter):
        for rowoff in range (0,Design.shape[0]):
            for coloff in range (0,Design.shape[1]):
                if Design[rowoff,coloff]>0 and Active[rowoff,coloff]>0:
                    for xoff in range(-1,2):
                        for yoff in range(-1,2):
                           
                            if coloff+xoff<Design.shape[1] and coloff+xoff>0 and rowoff+yoff<Design.shape[0] and rowoff+yoff>0:
                               
                                if Design[rowoff+yoff,coloff+xoff]>0 and Active[rowoff+yoff,coloff+xoff]>0 and Design[rowoff+yoff,coloff+xoff]<Design[rowoff,coloff] and Design[rowoff+yoff,coloff+xoff]<Survey[rowoff+yoff,coloff+xoff]:
                                    d2=Dist[abs(yoff),abs(xoff)]
                                    delev=Design[rowoff,coloff]-Design[rowoff+yoff,coloff+xoff]
                                    sl=delev/d2
                                    if sl>Slope:
                                                                                                                                      
                                        Design[rowoff+yoff,coloff+xoff]+=1.0*0.002
                                            
@jit
def Shape_Fillbench(x,y,rad,Slope,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    Slope=1/Slope
   
    for i in range (0,Iter):
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                        kz=(Design[y+rowoff,x+coloff]-4.5)%10
                        if kz>0.25:
                            Slope=0.25
                        else:
                            Slope=0.02
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)

                            for xoff in range(-1,2):
                                for yoff in range(-1,2):
                                   
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                       
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                            d2=Dist[abs(yoff),abs(xoff)]
                                            delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                            sl=delev/d2
                                            if sl>Slope:
                                                                                                                                              
                                                Design[y+rowoff+yoff,x+coloff+xoff]+=c*0.005


@jit
def Shape_Fill_Below(x,y,rad,Slope,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active,Cutoff):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    Slope=1/Slope
    
    for i in range (0,Iter):
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0 and Design[y+rowoff,x+coloff]<=Cutoff:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)

                            for xoff in range(-1,2):
                                for yoff in range(-1,2):
                                   
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                       
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                            d2=Dist[abs(yoff),abs(xoff)]
                                            delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                            sl=delev/d2
                                            if sl>Slope:
                                               
                                                Design[y+rowoff+yoff,x+coloff+xoff]+=c*0.01
                                             
@jit
def Shape_Bench(x,y,rad,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active,BElev,BWidth,Bslope,fillp,cutp):
    radius=int(rad/cellsize)

    for i in range (0,Iter):
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)

                            Slope = 1/Bslope
                            check=0
                            for ii in range (0,BElev.shape[0]-1,2):
                                if Design[y+rowoff,x+coloff]>BElev[ii] and Design[y+rowoff,x+coloff]<BElev[ii+1]:
                                    Slope=(BElev[ii+1]-BElev[ii])/BWidth
                                    check=1
                            if check == 0:        
                                for xoff in range(-1,2):
                                    for yoff in range(-1,2):

                                        if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:

                                            if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                                d2=Dist[abs(yoff),abs(xoff)]
                                                delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                                sl=delev/d2
                                                if sl>Slope:

                                                    Design[y+rowoff,x+coloff]-=c*cutp

                                                    Design[y+rowoff+yoff,x+coloff+xoff]+=c*fillp

                            if check == 1:        
                                for xoff in range(-1,2):
                                    for yoff in range(-1,2):

                                        if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:

                                            if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                                d2=Dist[abs(yoff),abs(xoff)]
                                                delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                                sl=delev/d2
                                                if sl>Slope:

                                                    Design[y+rowoff,x+coloff]-=c*cutp

                                                    Design[y+rowoff+yoff,x+coloff+xoff]+=c*fillp
                                            if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]>Design[y+rowoff,x+coloff]:
                                                d2=Dist[abs(yoff),abs(xoff)]
                                                delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                                sl=-delev/d2
                                                if sl>Slope:

                                                    Design[y+rowoff,x+coloff]+=c*cutp

                                                    Design[y+rowoff+yoff,x+coloff+xoff]-=c*fillp





# @cuda.jit
# def Shape_BenchGPU(Design,Dist,cellsize,Active,BElev,BWidth,Bslope):
#             y,x = cuda.grid(2)
#             fillp=0.01
#             cutp=0.01
#             if x<Design.shape[1] and x>0 and y<Design.shape[0] and y>0:
#                 if Design[y,x]>0 and Active[y,x]==0:

#                         Slope = 1/Bslope
#                         check=0
#                         for ii in range (0,BElev.shape[0]-1,2):
#                             if Design[y,x]>BElev[ii] and Design[y,x]<BElev[ii+1]:
#                                 Slope=(BElev[ii+1]-BElev[ii])/BWidth
#                                 check=1
#                         if check == 0:        
#                             for xoff in range(-1,2):
#                                 for yoff in range(-1,2):

#                                     if x+xoff<Design.shape[1] and x+xoff>0 and y+yoff<Design.shape[0] and y+yoff>0:

#                                         if Design[y+yoff,x+xoff]>0 and Active[y+yoff,x+xoff]==0 and Design[y+yoff,x+xoff]<Design[y,x]:
#                                             d2=Dist[abs(yoff),abs(xoff)]
#                                             delev=Design[y,x]-Design[y+yoff,x+xoff]
#                                             sl=delev/d2
#                                             if sl>Slope:
#                                                 cuda.atomic.add(Design,(y,x),-cutp)
#                                                 cuda.atomic.add(Design,(y+yoff,x+xoff),fillp)

#                         if check == 1:        
#                             for xoff in range(-1,2):
#                                 for yoff in range(-1,2):

#                                     if x+xoff<Design.shape[1] and x+xoff>0 and y+yoff<Design.shape[0] and y+yoff>0:

#                                         if Design[y+yoff,x+xoff]>0 and Active[y+yoff,x+xoff]==0 and Design[y+yoff,x+xoff]<Design[y,x]:
#                                             d2=Dist[abs(yoff),abs(xoff)]
#                                             delev=Design[y,x]-Design[y+yoff,x+xoff]
#                                             sl=delev/d2
#                                             if sl>Slope:

#                                                 cuda.atomic.add(Design,(y,x),-cutp)
#                                                 cuda.atomic.add(Design,(y+yoff,x+xoff),fillp)

#                                         if Design[y+yoff,x+xoff]>0 and Active[y+yoff,x+xoff]==0 and Design[y+yoff,x+xoff]>Design[y,x]:
#                                             d2=Dist[abs(yoff),abs(xoff)]
#                                             delev=Design[y,x]-Design[y+yoff,x+xoff]
#                                             sl=-delev/d2
#                                             if sl>Slope:

#                                                 cuda.atomic.add(Design,(y,x),+cutp)
#                                                 cuda.atomic.add(Design,(y+yoff,x+xoff),-fillp) 
                                                
# @cuda.jit
# def Shape_BenchGPUSurvey(Design,Dist,cellsize,Active,BElev,BWidth,Bslope,Survey):
#             y,x = cuda.grid(2)
#             fillp=0.005
#             cutp=0.005
#             if x<Design.shape[1] and x>0 and y<Design.shape[0] and y>0:
#                 if Design[y,x]>0 and Active[y,x]==0 and Design[y,x]>Survey[y,x]:

#                         Slope = 1/Bslope
#                         check=0
#                         for ii in range (0,BElev.shape[0]-1,2):
#                             if Design[y,x]>BElev[ii] and Design[y,x]<BElev[ii+1]:
#                                 Slope=(BElev[ii+1]-BElev[ii])/BWidth
#                                 bench_base=BElev[ii]
#                                 check=1
#                         if check == 0:        
#                             for xoff in range(-1,2):
#                                 for yoff in range(-1,2):

#                                     if x+xoff<Design.shape[1] and x+xoff>0 and y+yoff<Design.shape[0] and y+yoff>0:

#                                         if Design[y+yoff,x+xoff]>0 and Active[y+yoff,x+xoff]==0 and Design[y+yoff,x+xoff]<Design[y,x]:
#                                             d2=Dist[abs(yoff),abs(xoff)]
#                                             delev=Design[y,x]-Design[y+yoff,x+xoff]
#                                             sl=delev/d2
#                                             if sl>Slope:
#                                                 cuda.atomic.add(Design,(y,x),-cutp)
#                                                 cuda.atomic.add(Design,(y+yoff,x+xoff),fillp)

#                         if check == 1:        
#                             for xoff in range(-3,4):
#                                 for yoff in range(-3,4):

#                                     if x+xoff<Design.shape[1] and x+xoff>0 and y+yoff<Design.shape[0] and y+yoff>0:

#                                         if Design[y+yoff,x+xoff]>0 and Active[y+yoff,x+xoff]==0 and Design[y+yoff,x+xoff]<Design[y,x]:
#                                             d2=Dist[abs(yoff),abs(xoff)]
#                                             delev=Design[y,x]-Design[y+yoff,x+xoff]
#                                             sl=delev/d2
#                                             if sl>Slope:

#                                                 cuda.atomic.add(Design,(y,x),-cutp)
#                                                 cuda.atomic.add(Design,(y+yoff,x+xoff),fillp)

#                                         # if Design[y+yoff,x+xoff]>0 and Active[y+yoff,x+xoff]==0 and Design[y+yoff,x+xoff]>Design[y,x]:
#                                         #     d2=Dist[abs(yoff),abs(xoff)]
#                                         #     delev=Design[y,x]-Design[y+yoff,x+xoff]
#                                         #     sl=-delev/d2
#                                         #     if sl>Slope:

#                                         #         cuda.atomic.add(Design,(y,x),+cutp)
#                                         #         cuda.atomic.add(Design,(y+yoff,x+xoff),-fillp) 


@jit
def Shape_profile(x,y,rad,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active,S,fillp,cutp):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    
    for i in range (0,Iter):
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)
                            
                            if Design[y+rowoff,x+coloff]<S[0]:
                                Slope=(S[1]-S[0])/cellsize
                            elif Design[y+rowoff,x+coloff]>S[-1]:
                                Slope=(S[-1]-S[-2])/cellsize
                            else:
                                for ii in range (0,S.shape[0]-1):
                                    if S[ii]<=Design[y+rowoff,x+coloff] and S[ii+1]>=Design[y+rowoff,x+coloff]:
                                        Slope=(S[ii+1]-S[ii])/cellsize
                                        break
                                
                            for xoff in range(-1,2):
                                for yoff in range(-1,2):
                                   
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                       
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                            d2=Dist[abs(yoff),abs(xoff)]
                                            delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                            sl=delev/d2
                                            if sl>Slope:
                                               
                                                Design[y+rowoff,x+coloff]-=c*cutp
                                                                                               
                                                Design[y+rowoff+yoff,x+coloff+xoff]+=c*fillp
                                             
@jit
def Shape_profile_Above(x,y,rad,Exp,Iter,Design,Survey,Dist,cut,fill,cellsize,Active,S,fillp,cutp):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    
    for i in range (0,Iter):
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            c=(math.cos((d/rad)*(3.14159/2))**Exp)
                            
                            if Design[y+rowoff,x+coloff]<S[0]:
                                Slope=(S[1]-S[0])/cellsize
                            elif Design[y+rowoff,x+coloff]>S[-1]:
                                Slope=(S[-1]-S[-2])/cellsize
                            else:
                                for ii in range (0,S.shape[0]-1):
                                    if S[ii]<=Design[y+rowoff,x+coloff] and S[ii+1]>=Design[y+rowoff,x+coloff]:
                                        Slope=(S[ii+1]-S[ii])/cellsize
                                        break
                                
                            for xoff in range(-1,2):
                                for yoff in range(-1,2):
                                   
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                       
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0 and Active[y+rowoff+yoff,x+coloff+xoff]>0 and Design[y+rowoff+yoff,x+coloff+xoff]<Design[y+rowoff,x+coloff]:
                                            d2=Dist[abs(yoff),abs(xoff)]
                                            delev=Design[y+rowoff,x+coloff]-Design[y+rowoff+yoff,x+coloff+xoff]
                                            sl=delev/d2
                                            if sl>Slope:
                                                if Design[y+rowoff,x+coloff]-c*cutp>Survey[y+rowoff,x+coloff]:
                                                    Design[y+rowoff,x+coloff]-=c*cutp                                                                                               
                                                    Design[y+rowoff+yoff,x+coloff+xoff]+=c*fillp
    
@jit
def Set_ConstantAll(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        
                        Design[y+rowoff,x+coloff]=C

@jit
def Survey_above_Design(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)

    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:

                       if Survey[y+rowoff,x+coloff]>Design[y+rowoff,x+coloff]:
                           Design[y+rowoff,x+coloff]=Survey[y+rowoff,x+coloff]
    
@jit
def Add_to_Survey(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        
                        Design[y+rowoff,x+coloff]=Survey[y+rowoff,x+coloff]+C
                        
@jit
def Set_to_Lowest(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        
                        if Design[y+rowoff,x+coloff]>Survey[y+rowoff,x+coloff]:
                            Design[y+rowoff,x+coloff]=Survey[y+rowoff,x+coloff]
                            
@jit
def Set_to_Highest(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        
                        if Design[y+rowoff,x+coloff]<Survey[y+rowoff,x+coloff]:
                            Design[y+rowoff,x+coloff]=Survey[y+rowoff,x+coloff]
                            
                        
@jit
def Set_ConstantAbove(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
    
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        
                        if C>Design[y+rowoff,x+coloff]:
                            Design[y+rowoff,x+coloff]=C
                          
    
@jit
def Set_ConstantBelow(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)

    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        
                        if C<Design[y+rowoff,x+coloff]:
                            Design[y+rowoff,x+coloff]=C
                            # if C<Survey[y+rowoff,x+coloff]:
                            #     Design[y+rowoff,x+coloff]=Survey[y+rowoff,x+coloff]
                        
    
@jit
def Set_ConstantBelowSurvey(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
  
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        
                        if C<Survey[y+rowoff,x+coloff]:
                            Design[y+rowoff,x+coloff]=C
                        else: Design[y+rowoff,x+coloff]=Survey[y+rowoff,x+coloff]
                        
@jit
def Set_ConstantAboveSurvey(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
       
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        
                        if C>Survey[y+rowoff,x+coloff]:
                            Design[y+rowoff,x+coloff]=C
                        else: Design[y+rowoff,x+coloff]=Survey[y+rowoff,x+coloff]

@jit
def Set_to_SurveyBelow(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
       
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        if Survey[y+rowoff,x+coloff]<C:
                            Design[y+rowoff,x+coloff]=Survey[y+rowoff,x+coloff]
                            if Design[y+rowoff,x+coloff]>C:
                                Design[y+rowoff,x+coloff]=C

                        if Design[y+rowoff,x+coloff]<C:
                            Design[y+rowoff,x+coloff]=Survey[y+rowoff,x+coloff]
                            if Design[y+rowoff,x+coloff]>C:
                                Design[y+rowoff,x+coloff]=C

                        
@jit
def Undo(x,y,rad,Design,Design2,Dist,cellsize):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
       
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        Design[y+rowoff,x+coloff]=Design2[y+rowoff,x+coloff]
                        
@jit
def Set_zero_to_one(x,y,rad,C,Design,Survey,Dist,cut,fill,cellsize,Active):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):
    radius=int(rad/cellsize)
       
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]<0.1 :
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        Design[y+rowoff,x+coloff]=1

    
@jit    
def Smooth(x,y,rad,sliderdwn,sliderup,sliderNeigh,SmoothExp,SmoothIter,Design,Survey,Dist,cut,fill,cellsize,Active):
    radius=int(rad/cellsize)
    
    for i in range (0,int(SmoothIter)):
        
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            sumP=0
                            cnt=0
                            c=(math.cos((d/rad)*(3.14159/2))**SmoothExp)
                            for xoff in range(-int(sliderNeigh),int(sliderNeigh+1)):
                                for yoff in range(-int(sliderNeigh),int(sliderNeigh+1)):
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0:
                                            sumP+=Design[y+rowoff+yoff,x+coloff+xoff]
                                            cnt+=1
                            z=Design[y+rowoff,x+coloff]-sumP/cnt
                                                       
                            if z>0:
                                Design[y+rowoff,x+coloff]-=sliderdwn*c*z
                            elif z<0:
                                Design[y+rowoff,x+coloff]-=sliderup*c*z
                          
@jit    
def Smooth_fill_edge(Design,Survey,Design2):
       
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            # print((i,j))
            Design2[i,j]=Design[i,j]
            if Design[i,j]>0 and Design[i,j]==Survey[i,j]:
                check=0
                for xoff in range(-1,2):
                    for yoff in range(-1,2):
                        if j+xoff<Design.shape[1] and j+xoff>0 and i+yoff<Design.shape[0] and i+yoff>0:
                            if Design[i+yoff,j+xoff]>Survey[i+yoff,j+xoff]+0.05:
                                check=1
                                
                if check==1:
                    # for it in range (0,5):
                    sumP=0
                    cnt=0
                    for xoff in range(-1,2):
                        for yoff in range(-1,2):
                            if j+xoff<Design.shape[1] and j+xoff>0 and i+yoff<Design.shape[0] and i+yoff>0:
                                if Design[i+yoff,j+xoff]>Survey[i+yoff,j+xoff]+0.05:
                                    sumP+=Design[i+yoff,j+xoff]
                                    cnt+=1
                    z=Design[i,j]-sumP/cnt
                    Design2[i,j]-=0.95*z
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Design2[i,j]>Design[i,j]:
                Design[i,j]=Design2[i,j]
                  

        
@jit    
def Smooth_above_Survey(x,y,rad,sliderdwn,sliderup,sliderNeigh,SmoothExp,SmoothIter,Design,Survey,Dist,cut,fill,cellsize,Active):
    radius=int(rad/cellsize)
    
    for i in range (0,int(SmoothIter)):
               
        for rowoff in range (-radius,radius+1):
            for coloff in range (-radius,radius+1):
                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                    if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                        d=Dist[abs(rowoff),abs(coloff)]
                        if d<=rad:
                            sumP=0
                            cnt=0
                            c=(math.cos((d/rad)*(3.14159/2))**SmoothExp)
                            for xoff in range(-int(sliderNeigh),int(sliderNeigh+1)):
                                for yoff in range(-int(sliderNeigh),int(sliderNeigh+1)):
                                    if x+coloff+xoff<Design.shape[1] and x+coloff+xoff>0 and y+rowoff+yoff<Design.shape[0] and y+rowoff+yoff>0:
                                        if Design[y+rowoff+yoff,x+coloff+xoff]>0:
                                            sumP+=Design[y+rowoff+yoff,x+coloff+xoff]
                                            cnt+=1
                            z=Design[y+rowoff,x+coloff]-sumP/cnt
                            
                            if z>0 and Design[y+rowoff,x+coloff]-sliderdwn*c*z>Survey[y+rowoff,x+coloff]:
                                Design[y+rowoff,x+coloff]-=sliderdwn*c*z
                            elif z<0:
                                Design[y+rowoff,x+coloff]-=sliderup*c*z
                               
                            
# @jit        
        
@jit        
def Modify(x,y,rad,ModifyExp,slidermodup,Design,Survey,Dist,cut,fill,cellsize,Active):
    radius=int(rad/cellsize)
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0 and Active[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    z=0
                    if d<=rad:
                        z=slidermodup*(math.cos((d/rad)*(3.14159/2))**ModifyExp)
                        Design[y+rowoff,x+coloff]+=z
                        
@jit        
def CutFillStrt(x,y,rad,Design,Survey,Dist,cut0,fill0,cellsize):
    cut0[0]=0.0
    fill0[0]=0.0
    radius=int(rad/cellsize)
    sq=cellsize**2
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        dz=Survey[y+rowoff,x+coloff]-Design[y+rowoff,x+coloff]
                        if dz>0: #cut
                            cut0[0]+=dz*sq
                        else:
                            fill0[0]-=dz*sq

@jit        
def CutFillEnd(x,y,rad,Design,Survey,Dist,cut0,fill0,cut,fill,cellsize):
    cut1=0.0
    fill1=0.0
    radius=int(rad/cellsize)
    sq=cellsize**2
    for rowoff in range (-radius,radius+1):
        for coloff in range (-radius,radius+1):
            if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                if Design[y+rowoff,x+coloff]>0:
                    d=Dist[abs(rowoff),abs(coloff)]
                    if d<=rad:
                        dz=Survey[y+rowoff,x+coloff]-Design[y+rowoff,x+coloff]
                        if dz>0: #cut
                            cut1+=dz*sq
                        else:
                            fill1-=dz*sq
    cut[0]-=cut1-cut0[0]
    fill[0]+=fill1-fill0[0]
    
@jit
def Aspect(A,AS,S):
    cellsize=2
    for i in range (0, A.shape[0]):
        for j in range (0,A.shape[1]):
    
            check=0
            if i-1>=0 and i-1<A.shape[0] and j-1>=0 and j-1<A.shape[1]:
                if A[i-1,j-1]>0:
                    a=A[i-1,j-1]
                else:
                    check=1
            else:
                check=1
            #i-1,j
            if i-1>=0 and i-1<A.shape[0] and j>=0 and j<A.shape[1]:
                if A[i-1,j]>0:
                    b=A[i-1,j]
                else:
                    check=1
            else:
                check=1
            #i-1,j+1
            if i-1>=0 and i-1<A.shape[0] and j+1>=0 and j+1<A.shape[1]:
                if A[i-1,j+1]>0:
                    c=A[i-1,j+1]
                else:
                    check=1
            else:
                check=1
            #i,j-1
            if i>=0 and i<A.shape[0] and j-1>=0 and j-1<A.shape[1]:
                if A[i,j-1]>0:
                    d=A[i,j-1]
                else:
                    check=1
            else:
                check=1
            #i,j
            if i>=0 and i<A.shape[0] and j>=0 and j<A.shape[1]:
                if A[i,j]>0:
                    e=0
                else:
                    check=1
            else:
                check=1
            #i,j+1
            if i>=0 and i<A.shape[0] and j+1>=0 and j+1<A.shape[1]:
                if A[i,j+1]>0:
                    f=A[i,j+1]
                else:
                    check=1
            else:
                check=1
            #i+1,j-1
            if i+1>=0 and i+1<A.shape[0] and j-1>=0 and j-1<A.shape[1]:
                if A[i+1,j-1]>0:
                    g=A[i+1,j-1]
                else:
                    check=1
            else:
                check=1
            #i+1,j
            if i+1>=0 and i+1<A.shape[0] and j>=0 and j<A.shape[1]:
                if A[i+1,j]>0:
                    h=A[i+1,j]
                else:
                    check=1
            else:
                check=1
            #i+1,j+1
            if i+1>=0 and i+1<A.shape[0] and j+1>=0 and j+1<A.shape[1]:
                if A[i+1,j+1]>0:
                    ii=A[i+1,j+1]
                else:
                    check=1
            else:
                check=1
            if check==0:
                dzdx=((c+2*f+ii)-(a+2*d+g))/(8*cellsize)
                dzdy=((g+2*h+ii)-(a+2*b+c))/(8*cellsize)
                
                l=(dzdx**2+dzdy**2)**0.5
                
                AS[i,j,0]=dzdx/l
                AS[i,j,1]=dzdy/l
                if abs(l)<0.001:
                    l=0.001
            #        S[i,j]=math.atan(l)*57.29578
                S[i,j]=1/l
            else:
                S[i,j]=1000
                
def RunAspect2(A):
    S=np.zeros_like(A,dtype=np.float32)
    AS=np.zeros((A.shape[0],A.shape[1],2),dtype=np.float32)
    
    Aspect(A,AS,S)
    
    # return AS, S

@jit# (nopython=True)
def func_boundary(W, elev):
    for i in range (0, W.shape[0]):
        for j in range (0,W.shape[1]):
            if i <W.shape[0] and j<W.shape[1]:
                if elev[i,j] !=0:
                    if i%70==0 and j%70==0:
                        W[i,j]=elev[i,j]
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
                
                
@jit# (nopython=True)
def func_boundary2(W, elev):
    for i in range (0, W.shape[0]):
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
    for i in range (0, d_W.shape[0]):
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
                                                    
                                                    
def RunAspect(A,cellsize):
    Slope1in=100.0
    epsistr = cellsize/Slope1in
    epsidiag = ((2*(cellsize)**2)**0.5)/Slope1in
    arr=np.array([0,0,epsistr,epsidiag,1],dtype=np.float32)

    S=np.zeros_like(A,dtype=np.float32)
    AS=np.zeros((A.shape[0],A.shape[1],2),dtype=np.float32)
    W=np.zeros_like(A)

    
    # func_boundary2[blockspergrid,threadsperblock](d_W,d_A)
    # check = 0
    # v=0
    # while check==0 and v<1000:
    #     func_fill[blockspergrid,threadsperblock](d_W,d_A,Constants)
    #     C=Constants.copy_to_host()
    #     check=1
    #     if C[4]>1:
    #         check=0
    #         cuda.to_device(arr, to=Constants)
    #     v+=1
    # # print('v')
    # print(v)

    Aspect(A,AS,S)
   
    return AS,S


@jit
def D8_Directions(A,D8):
    for i in range (0, A.shape[0]):
        for j in range (0,A.shape[1]):
            maxslope=0
            if i>=0 and i<A.shape[0] and j>=0 and j<A.shape[1]:
                for offr in range (-1,2):
                    for offc in range (-1,2):
                        if offr!=0 or offc!=0:
                            if i+offr>=0 and i+offr<A.shape[0] and j+offc>=0 and j+offc<A.shape[1]:
                                if A[i,j]>0:
                                    if A[i,j]-A[i+offr,j+offc]>0:
                                        d=(offc**2+offr**2)**0.5
                                        if (A[i,j]-A[i+offr,j+offc])/d>maxslope:
                                            maxslope=(A[i,j]-A[i+offr,j+offc])/d
                                            D8[i,j,0]=offr
                                            D8[i,j,1]=offc
                            
@jit
def D8_Catchment(A,D8,Catchment):
    for i in range (0, A.shape[0]):
        for j in range (0,A.shape[1]):
            if i>=0 and i<A.shape[0] and j>=0 and j<A.shape[1]:
                if Catchment[i,j]<0:
                    for offr in range (-1,2):
                        for offc in range (-1,2):
                            if offr!=0 or offc!=0:
                                if i+offr>=0 and i+offr<A.shape[0] and j+offc>=0 and j+offc<A.shape[1]:
                                    if D8[i+offr,j+offc,0]==-offr and D8[i+offr,j+offc,1]==-offc: 
                                        Catchment[i+offr,j+offc]=-1

# @cuda.jit
# def D8_Catchment(A,D8,Catchment):
#     i,j=cuda.grid(2)
#     if i>=0 and i<A.shape[0] and j>=0 and j<A.shape[1]:
#         if Catchment[i,j]<0:
#             for offr in range (-1,2):
#                 for offc in range (-1,2):
#                     if i+offr>=0 and i+offr<A.shape[0] and j+offc>=0 and j+offc<A.shape[1]:
#                         if A[i,j]>0:
#                             d=(4.0*offc**2+4.0*offr**2)**0.5
#                             if (A[i,j]-A[i+offr,j+offc])/d<-0.001:
#                             # if A[i,j]-A[i+offr,j+offc]<0.00:
#                                 Catchment[i+offr,j+offc]=-1
                                    
                            
def RunD8(A,Catchment,cellsize):
    Slope1in=500.0
    epsistr = cellsize/Slope1in
    epsidiag = ((2*(cellsize)**2)**0.5)/Slope1in
    Constants=np.array([0,0,epsistr,epsidiag,1],dtype=np.float32)
    D8=np.zeros((A.shape[0],A.shape[1],2),dtype=np.float32)
    W=np.zeros_like(A)
    
    # Constants=cuda.device_array((5),dtype=np.float32)

   
    func_boundary(W,A)

    check = 0
    v=0
    while check==0 and v<10000:
        func_fill(W,A,Constants)
        
        check=1
        if Constants[4]>1:
            check=0
            Constants[4]=0
        v+=1
    
    
    D8_Directions(W,D8)
    for i in range (0,4000):
        D8_Catchment(W,D8,Catchment)
    
    Catchment=np.ma.masked_where(Catchment==0,Catchment)
    return Catchment,W

@jit
def Aspect2(A,W,S,cellsize):
    # cellsize
    for i in range (0, A.shape[0]):
        for j in range (0,A.shape[1]):
            check=0
            if i-1>=0 and i+1<A.shape[0] and j-1>=0 and j+1<A.shape[1]:
                if A[i-1,j-1]>0:
                    a=A[i-1,j-1]
                else:
                    check=1
        
                if A[i-1,j]>0:
                    b=A[i-1,j]
                else:
                    check=1
            
                if A[i-1,j+1]>0:
                    c=A[i-1,j+1]
                else:
                    check=1
            
                if A[i,j-1]>0:
                    d=A[i,j-1]
                else:
                    check=1
            
                if A[i,j+1]>0:
                    f=A[i,j+1]
                else:
                    check=1
           
                if A[i+1,j-1]>0:
                    g=A[i+1,j-1]
                else:
                    check=1
            
                if A[i+1,j]>0:
                    h=A[i+1,j]
                else:
                    check=1
            
                if A[i+1,j+1]>0:
                    ii=A[i+1,j+1]
                else:
                    check=1
            
                if check==0:
                    dzdx=-((c+2*f+ii)-(a+2*d+g))/(8*cellsize)
                    dzdy=-((g+2*h+ii)-(a+2*b+c))/(8*cellsize)
                    
                    l=(dzdx**2+dzdy**2)**0.5
                    if l*l<0.001:
                        l=0.001
                    angle=-math.atan2(dzdy/l,dzdx/l)
                    if angle<0:
                        angle+=2*3.14159
                    W[i,j]=angle
                    S[i,j]=1/l
                else:
                    S[i,j]=1000
        
            
@jit
def Aspect3(Surv,A,W,S,cellsize):
    # cellsize=cs[0]
    for i in range (0, A.shape[0]):
        for j in range (0,A.shape[1]):
            check=0
            if i-1>=0 and i+1<A.shape[0] and j-1>=0 and j+1<A.shape[1]:
                if A[i-1,j-1]>0:
                    a=A[i-1,j-1]
                else:
                    check=1
        
                if A[i-1,j]>0:
                    b=A[i-1,j]
                else:
                    check=1
            
                if A[i-1,j+1]>0:
                    c=A[i-1,j+1]
                else:
                    check=1
            
                if A[i,j-1]>0:
                    d=A[i,j-1]
                else:
                    check=1
            
                if A[i,j+1]>0:
                    f=A[i,j+1]
                else:
                    check=1
           
                if A[i+1,j-1]>0:
                    g=A[i+1,j-1]
                else:
                    check=1
            
                if A[i+1,j]>0:
                    h=A[i+1,j]
                else:
                    check=1
            
                if A[i+1,j+1]>0:
                    ii=A[i+1,j+1]
                else:
                    check=1
            
                if check==0:
                    dzdx=-((c+2*f+ii)-(a+2*d+g))/(8*cellsize)
                    dzdy=-((g+2*h+ii)-(a+2*b+c))/(8*cellsize)
                    
                    l=(dzdx**2+dzdy**2)**0.5
                    if abs(l)<0.001:
                        l=0.001
                    angle=-math.atan2(dzdy/l,dzdx/l)
                    if angle<0:
                        angle+=2*3.14159
                    W[i,j]=angle
                    S[i,j]=1/l
                else:
                    S[i,j]=1000
                if Surv[i,j]==A[i,j]:
                    S[i,j]=100

@jit    
def Unit_to_total(C,cellsize):
    # cellsize=cs[0]   
    for i in range (0, C.shape[0]):
        for j in range (0,C.shape[1]):
            if i < C.shape[0] and j <C.shape[1]: # and Slopes[x,y]>7:
                if C[i,j]>0:           
                    C[i,j]=C[i,j]/cellsize
@jit
def accumulate(B,C,W,A,D):
    for i in range (0, A.shape[0]):
        for j in range (0,A.shape[1]):
            pi=3.14159
            if i < B.shape[0] and j <B.shape[1]: # and Slopes[x,y]>7:
                if B[i,j]>0 and A[i,j]>0:           
                    alpha=W[i,j]
                    check =1
                    angle=pi/4
                   
                    ax=0
                    ay=0
                    bx=0
                    by=0
                    w1=0
                    w2=0
                    #1
                    if alpha<angle and check==1:
                       w1=(angle-alpha)/(pi/4)
                       w2=(alpha-(angle-pi/4))/(pi/4)
                       ax=0
                       ay=1
                       bx=-1
                       by=1
                       check=0
                    angle+=pi/4
                    #2
                    if alpha<angle and check==1:
                       w1=(angle-alpha)/(pi/4)
                       w2=(alpha-(angle-pi/4))/(pi/4)
                       ax=-1
                       ay=1
                       bx=-1
                       by=0
                       check=0
                    angle+=pi/4
                    #3
                    if alpha<angle and check==1:
                       w1=(angle-alpha)/(pi/4)
                       w2=(alpha-(angle-pi/4))/(pi/4)
                       ax=-1
                       ay=0
                       bx=-1
                       by=-1
                       check=0
                    angle+=pi/4
                    #4
                    if alpha<angle and check==1:
                       w1=(angle-alpha)/(pi/4)
                       w2=(alpha-(angle-pi/4))/(pi/4)
                       ax=-1
                       ay=-1
                       bx=0
                       by=-1
                       check=0
                    angle+=pi/4
                    #5
                    if alpha<angle and check==1:
                       w1=(angle-alpha)/(pi/4)
                       w2=(alpha-(angle-pi/4))/(pi/4)
                       ax=0
                       ay=-1
                       bx=1
                       by=-1
                       check=0
                    angle+=pi/4
                    #6
                    if alpha<angle and check==1:
                       w1=(angle-alpha)/(pi/4)
                       w2=(alpha-(angle-pi/4))/(pi/4)
                       ax=1
                       ay=-1
                       bx=1
                       by=0
                       check=0
                    angle+=pi/4
                    #7
                    if alpha<angle and check==1:
                       w1=(angle-alpha)/(pi/4)
                       w2=(alpha-(angle-pi/4))/(pi/4)
                       ax=1
                       ay=0
                       bx=1
                       by=1
                       check=0
                    angle+=pi/4
                    
                    #8
                    if alpha<angle and check==1:
                       w1=(angle-alpha)/(pi/4)
                       w2=(alpha-(angle-pi/4))/(pi/4)
                       ax=1
                       ay=1
                       bx=0
                       by=1
                       check=0
                    angle+=pi/4
                    
                    if i+ax<B.shape[0] and j+ay<B.shape[1] and i+bx<B.shape[0] and j+by<B.shape[1]:
                        if i+ax>0 and j+ay>0 and i+bx>0 and j+by>0:
                              if A[i+ax,j+ay]==0:
                                   B[i+ax,j+ay]=0
                                   B[i,j]=0
                              if A[i+bx,j+by]==0:
                                   B[i+bx,j+by]=0
                                   B[i,j]=0
        
                              D[i+ax,j+ay]+=w1*B[i,j]
                              D[i+bx,j+by]+=w2*B[i,j]
      
@jit    
def SumFlows(B,C,A,D):    
    for i in range (0, A.shape[0]):
        for j in range (0,A.shape[1]):
            if i < B.shape[0] and j <B.shape[1]: # and Slopes[x,y]>7:
                if B[i,j]>0 and A[i,j]>0:           
                    C[i,j]+=D[i,j]
                    B[i,j]=D[i,j]
                    D[i,j]=0
           
@jit    
def TopoF(C,S,TF,E):    
    for i in range (0, C.shape[0]):
        for j in range (0,C.shape[1]):
            if i < C.shape[0] and j <C.shape[1]: # and Slopes[x,y]>7:
                if C[i,j]>0 and S[i,j]>0: 
                    # TF[i,j]=2500*E[1]*E[0]*(C[i,j]/22.13)**0.4*(math.sin(1/S[i,j])/0.0896)**1.3
                    TF[i,j]=C[i,j]**E[1]*(1/S[i,j])**E[0]
            
            
@jit
def Shape_Poly_ProfileGPU_3(Design,Active,cellsize,Dist,Survey):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):

    for y in range (0, A.shape[0]):
        for x in range (0,A.shape[1]):
            if y<Active.shape[0] and x<Active.shape[1]:
                if Active[y,x]==0 and Design[y,x]>0:
                    Slope=1/3
        
                    for rowoff in range (-1,2):
                        for coloff in range (-1,2):
                            if rowoff!=0 or coloff!=0:
                                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                                    if Design[y+rowoff,x+coloff]>0 and Design[y,x]>Survey[y,x]:
        
                                        d2=Dist[abs(rowoff),abs(coloff)]
                                        delev=Design[y,x]-Design[y+rowoff,x+coloff]
                                        sl=delev/d2
                                        if sl>Slope:
                                            # cuda.atomic.add(Design,(y,x),-0.05)
                                            Design[y+rowoff,x+coloff]+=0.05
                                            # Design[y,x]-=0.05
                                            # Design[y+rowoff,x+coloff]+=0.05     
                                    
@jit
def Shape_Poly_ProfileGPU(Design,Active,cellsize,Dist,S):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fill,AO,S,iterations):

    for y in range (0, A.shape[0]):
        for x in range (0,A.shape[1]):
            if y<Active.shape[0] and x<Active.shape[1]:
                if Active[y,x]==0 and Design[y,x]>0:
                    if Design[y,x]<S[0]:
                        Slope=(S[1]-S[0])/cellsize
                    elif Design[y,x]>S[-1]:
                        Slope=(S[-1]-S[-2])/cellsize
                    else:
                        for ii in range (0,S.shape[0]-1):
                            if S[ii]<=Design[y,x] and S[ii+1]>=Design[y,x]:
                                Slope=(S[ii+1]-S[ii])/cellsize
                                break
        
                    for rowoff in range (-1,2):
                        for coloff in range (-1,2):
                            if rowoff!=0 or coloff!=0:
                                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                                    if Design[y+rowoff,x+coloff]>0:
        
                                        d2=Dist[abs(rowoff),abs(coloff)]
                                        delev=Design[y,x]-Design[y+rowoff,x+coloff]
                                        sl=delev/d2
                                        if sl>Slope:
                                            Design[y,x]-=0.05
                                            Design[y+rowoff,x+coloff]+=0.05
                                            # Design[y,x]-=0.05
                                            # Design[y+rowoff,x+coloff]+=0.05     
                                    
                                    
def RunShapePoly(Surfaces,Sf,S):

    

    
    for i in range (0,5000):
        Shape_Poly_ProfileGPU(Surfaces.Design,Surfaces.Active,Surfaces.cellsize,Surfaces.Dist,S)
        # Shape_Poly_ProfileGPU_3[blockspergrid,threadsperblock](d_Design,d_Active,Surfaces.cellsize,d_Dist,d_Survey)
    
    Draw_contours(Sf,Surfaces)

@jit
def Shape_Poly_ProfileGPUSurvey(Design,Active,cellsize,Dist,S,Surv):
#def Shape_point2(A,row,col,r,expo,cellsize,cut,fDesignill,AO,S,iterations):

    for y in range (0, Design.shape[0]):
        for x in range (0,Design.shape[1]):
            if y<Active.shape[0] and x<Active.shape[1]:
                if Active[y,x]==0 and Design[y,x]>0 and Design[y,x]>Surv[y,x]:
                    if Design[y,x]<S[0]:
                        Slope=(S[1]-S[0])/cellsize
                    elif Design[y,x]>S[-1]:
                        Slope=(S[-1]-S[-2])/cellsize
                    else:
                        for ii in range (0,S.shape[0]-1):
                            if S[ii]<=Design[y,x] and S[ii+1]>=Design[y,x]:
                                Slope=(S[ii+1]-S[ii])/cellsize
                                break
        
                    for rowoff in range (-1,2):
                        for coloff in range (-1,2):
                            if rowoff!=0 or coloff!=0:
                                if x+coloff<Design.shape[1] and x+coloff>0 and y+rowoff<Design.shape[0] and y+rowoff>0:
                                    if Design[y+rowoff,x+coloff]>0:
        
                                        d2=Dist[abs(rowoff),abs(coloff)]
                                        delev=Design[y,x]-Design[y+rowoff,x+coloff]
                                        sl=delev/d2
                                        if sl>Slope and Design[y,x]>Surv[y,x]:
                                            Design[y,x]-=0.05
                                            Design[y+rowoff,x+coloff]+=0.05
                                            # Design[y,x]-=0.05
                                            # Design[y+rowoff,x+coloff]+=0.05     
                                            
                                    
def RunShapePolySurvey(Surfaces,Sf,S):

    
    for i in range (0,5000):
        Shape_Poly_ProfileGPUSurvey(Surfaces.Design,Surfaces.Active,Surfaces.cellsize,Surfaces.Dist,S,Surfaces.Survey)
    
    Draw_contours(Sf,Surfaces)
    
def RunShapePolyBench(Surfaces,Sf,BE,BW,BS):
    
    for i in range (0,5000):
        Shape_BenchGPU(Surfaces.Design,Surfaces.Dist,Surfaces.cellsize,Surfaces.Active,BE,BW,BS)
    
    Draw_contours(Sf,Surfaces)
    
def RunShapePolyBenchSurvey(Surfaces,Sf,BE,BW,BS):
   

    for i in range (0,50000):
        Shape_BenchGPUSurvey(Surfaces.Design,Surfaces.Dist,Surfaces.cellsize,Surfaces.Active,BE,BW,BS,d_Survey)
    
    Draw_contours(Sf,Surfaces)
    
    
def RunSlope(Surfaces,Sf,Include_Survey):
    # listSlopes=Sf.SlopeCat
    listSlopes=[]
    for p in Sf.SlopeCat.get().split(","):
        listSlopes.append(float(p))
    S=np.zeros_like(Surfaces.Design)
    W=np.zeros_like(Surfaces.Design)
    # Cs=np.array([Surfaces.cellsize],dtype=np.float32)
    
    
    if Include_Survey==0:
        Aspect2(Surfaces.Design,W,S,float(Surfaces.cellsize))
    else:
        Aspect3(Surfaces.Survey,Surfaces.Design,W,S,float(Surfaces.cellsize))
    
    
    bounds=[0,2.5,3,3.5,4,4.5,5]
    bounds=listSlopes
    # bounds=[boundsL[0],boundsL[1],boundsL[2],boundsL[3],boundsL[4],boundsL[5]]
    # norm = colors.BoundaryNorm(bounds, cmap.N)
    norm = colors.BoundaryNorm(bounds, ncolors=256)
    background = Sf.f.canvas.copy_from_bbox(Sf.f.bbox)
    # for l in range (0,1):
    for im in Sf.a.images:
        Sf.a.images.remove(im)
        try:
            im.colorbar.remove()
        except:
            pass
        try:
            Sf.a.colorbar.remove()
        except:
            pass
        try:
            Sf.CB.remove()
        except:
            pass
            
    Sf.f.canvas.restore_region(background)
    Sf.f.canvas.blit(Sf.f.bbox)
    Draw_Update(Sf,Surfaces)
    
    ax2 = Sf.f.add_axes([0.9,0.1,0.05,0.8])
    im=Sf.a.imshow(S,interpolation='none', cmap='RdBu', norm=norm)
    
    Sf.f.canvas.restore_region(background)
    Sf.a.draw_artist(im)
    
    Sf.CB=Sf.f.colorbar(im,ticks=listSlopes,shrink=0.5,cax=ax2)
    Sf.CB.ax.set_yticklabels(listSlopes,color='white')
    Sf.CB.ax.set_ylabel('Slope (1:H)',color='white')
    Sf.CB.ax.set_title('Design Slope',color='white')
    
    Sf.f.canvas.blit(Sf.f.bbox)
    
def RunSlope3(Surfaces,Sf,Include_Survey):
        vmin_g=float(Sf.MinSlope.get())
        vmax_g=float(Sf.MaxSlope.get())
        
        S=np.zeros_like(Surfaces.Design)
        W=np.zeros_like(Surfaces.Design)
        Cs=np.array([Surfaces.cellsize],dtype=np.float32)
        # print('launch slope')
        # print(Surfaces.Design.dtype)
        
        
        if Include_Survey==0:
            Aspect2(Surfaces.Design,W,S,Surfaces.cellsize)
        else:
            Aspect3(Surfaces.Survey,Surfaces.Design,W,S,Surfaces.cellsize)
        
        
        background = Sf.f.canvas.copy_from_bbox(Sf.f.bbox)
        for l in range (0,3):
            for im in Sf.a.images:
                Sf.a.images.remove(im)
                try:
                    im.colorbar.remove()
                except:
                    pass
                try:
                    Sf.a.colorbar.remove()
                except:
                    pass
                try:
                    Sf.CB.remove()
                except:
                    pass
        Sf.f.canvas.restore_region(background)
        Sf.f.canvas.blit(Sf.f.bbox)
        Draw_Update(Sf,Surfaces)
        
        im=Sf.a.imshow(S,interpolation='nearest', cmap='nipy_spectral_r', vmin=vmin_g,vmax=vmax_g )
        ax2 = Sf.f.add_axes([0.9,0.1,0.05,0.8])
        
        Sf.f.canvas.restore_region(background)
        Sf.a.draw_artist(im)
        ticksList=np.linspace(vmin_g,vmax_g,11)
        CB=Sf.f.colorbar(im,shrink=0.5,ticks=ticksList,cax=ax2)
        CB.ax.set_yticklabels(ticksList,color='white')
        # CB.ax.set_yticklabels([vmin_g,vmax_g],color='white')
        CB.ax.set_ylabel('Slope (1:H)',color='white')
        # CB.ax.set_title('Design Slope',color='white')
        Sf.f.canvas.blit(Sf.f.bbox)
    
    
def RunSlope2(Surfaces):
    S=np.zeros_like(Surfaces.Design)
    W=np.zeros_like(Surfaces.Design)
    Cs=np.array([Surfaces.cellsize],dtype=np.float32)
    # print('launch slope')
    # print(Surfaces.Design.dtype)
    # d_A=cuda.device_array(Surfaces.Design.shape, dtype=np.float32)
    # d_S=cuda.device_array(Surfaces.Design.shape, dtype=np.float32)
    # d_W=cuda.device_array(Surfaces.Design.shape, dtype=np.float32)
    # d_Cs=cuda.device_array(((1)), dtype=np.float32)
    
    # cuda.to_device(Surfaces.Design, to=d_A)
    # cuda.to_device(S, to=d_S)
    # cuda.to_device(W, to=d_W)
    # cuda.to_device(Cs, to=d_Cs)
    
    # threadsperblock=(16,16)
    # blockspergrid_x = math.ceil(Surfaces.Design.shape[0] / threadsperblock[0])
    # blockspergrid_y = math.ceil(Surfaces.Design.shape[1] / threadsperblock[1])
    # blockspergrid = (blockspergrid_x, blockspergrid_y)
    
    Aspect2(Surfaces.Design,W,S,Surfaces.cellsize)
    # S=d_S.copy_to_host()
    return S

@jit
def get_averageSlope(S,ID,P,av):
    countc=0
    sumC=0
    for i in range (0,S.shape[0]):
        for j in range (0,S.shape[1]):
          if P[i,j]==ID:  
              if S[i,j]<30:
                  sumC+=S[i,j]
                  countc+=1
              if S[i,j]>30:
                  sumC+=30
                  countc+=1
    av[0,0]=sumC/countc
    
def AverageSlope(P,Surfaces,Se):
        S=RunSlope2(Surfaces)
        av=np.zeros((1,1))
        get_averageSlope(S,P.ID,Surfaces.Poly,av)
        # avg=np.mean(S[np.where(Surfaces.Poly==P.ID)])
        Se.PolySlopeReq.delete(0,tk.END)
        Se.PolySlopeReq.insert(0,av[0,0])
        
def RunTF(Surfaces,Sf,slopeexp,catchexp,topomax):
    S=np.zeros_like(Surfaces.Design)
    W=np.zeros_like(Surfaces.Design)
    TF=np.zeros_like(Surfaces.Design)
    B=np.zeros_like(Surfaces.Design)
    C=np.zeros_like(Surfaces.Design)
    D=np.zeros_like(Surfaces.Design)
    cellsize=np.array([Surfaces.cellsize],dtype=np.float32)
    Exponents=np.array([slopeexp,catchexp],dtype=np.float32)
    for i in range (0,Surfaces.Design.shape[0]):
        for j in range (0,Surfaces.Design.shape[1]):
            if Surfaces.Design[i,j]>0:
                B[i,j]=Surfaces.cellsize**2

    
    Aspect2(Surfaces.Design,W,S,Surfaces.cellsize)
    v=0
    # for j in range(0,1):
    while v<500:
        accumulate(B,C,W,Surfaces.Design,D)
        SumFlows(B,C,Surfaces.Design,D)
        v+=1
    Unit_to_total(C,Surfaces.cellsize)
    TopoF(C,S,TF,Exponents)
    
    
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
    Draw_Update(Sf,Surfaces)
    
    im=Sf.a.imshow(TF,interpolation='none', cmap=plt.get_cmap('Spectral_r'),vmin = 0,vmax=topomax)
    ax2 = Sf.f.add_axes([0.9,0.1,0.05,0.8])
    
    Sf.f.canvas.restore_region(background)
    Sf.a.draw_artist(im)
    
    ticksList=np.linspace(0,topomax,11)
    
    CB=Sf.f.colorbar(im,ticks=ticksList,shrink=0.5,cax=ax2)
    CB.ax.set_yticklabels(ticksList,color='white')
    
    # CB=Sf.f.colorbar(im,ticks=[0,5,10,15,20,25,30,35,40,45,50],shrink=0.5)
    # CB.ax.set_yticklabels([0,5,10,15,20,25,30,35,40,45,50],color='white')
    
    CB.ax.set_ylabel('Topographic Factor',color='white')
    CB.ax.set_title('Erosion Risk',color='white')
    Sf.f.canvas.blit(Sf.f.bbox)

def SaveTF(Surfaces,Sf,slopeexp,catchexp,topomax):
    S=np.zeros_like(Surfaces.Design)
    W=np.zeros_like(Surfaces.Design)
    TF=np.zeros_like(Surfaces.Design)
    B=np.zeros_like(Surfaces.Design)
    C=np.zeros_like(Surfaces.Design)
    D=np.zeros_like(Surfaces.Design)
    cellsize=np.array([Surfaces.cellsize],dtype=np.float32)
    Exponents=np.array([slopeexp,catchexp],dtype=np.float32)
    for i in range (0,Surfaces.Design.shape[0]):
        for j in range (0,Surfaces.Design.shape[1]):
            if Surfaces.Design[i,j]>0:
                B[i,j]=Surfaces.cellsize**2

    
    Aspect2(Surfaces.Design,W,S,Surfaces.cellsize)
    v=0
    # for j in range(0,1):
    while v<500:
        accumulate(B,C,W,Surfaces.Design,D)
        SumFlows(B,C,Surfaces.Design,D)
        v+=1
    Unit_to_total(C,Surfaces.cellsize)
    TopoF(C,S,TF,Exponents)
    
    Tk().withdraw()
    filename = asksaveasfilename(title = "Save Topofactor",filetypes = (("tif files","*.tif"),("all files","*.*")))
   
    tag={}
    tag[33922]=(0.0,0.0,0.0,Surfaces.maxcol+0*Surfaces.cellsize,Surfaces.maxrow+0*Surfaces.cellsize,0.0)
    tag[33550]=(-1*Surfaces.cellsize,1*Surfaces.cellsize,0.0)
    
    im=Image.fromarray(np.flip(np.flip(TF,0),1))
    
    # im=Image.fromarray(np.flip(Surfaces.Design,0))
    if len(filename)>3:
        if filename[-4]!=".":
            filename=filename +".tif"
    else:
        filename=filename +".tif"
    im.save(filename,tiffinfo=tag)
    im.close

@jit
def cutfillim(Design,Survey,C):
    for i in range (0,Design.shape[0]):
        for j in range (0,Design.shape[1]):
            if Survey[i,j]>0 and Design[i,j]>0:
                if abs(Survey[i,j]-Design[i,j])<500:
                    C[i,j]=Survey[i,j]-Design[i,j]




def Import_Polygon_Shapefile(Sf,Surfaces):
    
    Tk().withdraw()
    filename = askopenfilename(title = "Select design edge shapefile",filetypes = (("shp files","*.shp"),("all files","*.*")))
    Directory = os.path.dirname(filename)
    Name = Path(filename).stem
    path = filename
    sf = shp.Reader(path)
    # background=Se.f.canvas.copy_from_bbox(Se.a.bbox)
    # t=[]
    for shape in sf.shapeRecords():
        for i in range(len(shape.shape.parts)):
            i_start = shape.shape.parts[i]
            if i==len(shape.shape.parts)-1:
                i_end = len(shape.shape.points)
            else:
                i_end = shape.shape.parts[i+1]
           
            x = [(i[0]-Surfaces.maxcol-0.5*Surfaces.cellsize)/Surfaces.cellsize+Surfaces.Design.shape[1] for i in shape.shape.points[i_start:i_end]]
            y = [(i[1]-Surfaces.maxrow-0.5*Surfaces.cellsize)/Surfaces.cellsize+Surfaces.Design.shape[0] for i in shape.shape.points[i_start:i_end]]
            polylist=[]
            for j in range (0, len(x)):
                polylist.append([x[j],y[j]])
            poly=Polygon(polylist,animated=False,alpha=0.2)
            p = PolygonInteractor(Sf, poly, Sf.polyID)
            Sf.Polygons.append(p)
            Sf.polyID+=1 
    Draw_Update(Sf,Surfaces)        
    Sf.Set_to_none()










def Import_Polygon_Shapefile2(Sf,Surfaces):
    Tk().withdraw()
    filename = askopenfilename(title = "Select polygon shapefile",filetypes = (("shp files","*.shp"),("all files","*.*")))
    Directory = os.path.dirname(filename)
    Name = Path(filename).stem
    path = filename
    polys = shapefile.Reader(path)
    #first feature of the shapefile
    polynum=len(polys)
    polygons=[]
    polygon_id=[]
    # fields=noticeareas.fields
    
    for i in range(0,polynum): 
        feature = polys.shapeRecords()[i]
        feature=feature.shape.__geo_interface__
        #print(feature['coordinates'])
        polygon_list=[]
        
        
        #################
        key='coordinates'
        #################
        
        
        try:
            for entry in feature[key]:
                for tup in entry:
                    polygon_list.append(list(tup))
        except:
            print('Error: Line 3188. The current key "' + str(key) + '" for the geometric data is wrong. Check data and change key accordingly.')
                
        if len(polygon_list)>2:
                polygons.append(polygon_list)
                poly=Polygon(polygon_list,animated=False,alpha=0.2)
                p = PolygonInteractor(Sf, poly, Sf.polyID)
                Sf.Polygons.append(p)
                Sf.ID+=1 
                Draw_Update(Sf,Surfaces)        
                Sf.Set_to_none()



def Import_Aerial(Sf,Surfaces):
    
    
    
    maxcol=Surfaces.tag[33922][3]-Surfaces.Design.shape[1]*Surfaces.cellsize
    maxrow=Surfaces.tag[33922][4]
    # cell=1*Surfaces.tag[33550][0]
    # mincol=maxcol-cell*Surfaces.Design.shape[1]
    # minrow=maxrow-cell*Surfaces.Design.shape[0]
    # maxrow=minrow

    background = Sf.f.canvas.copy_from_bbox(Sf.f.bbox)
    
    Tk().withdraw()
    filename = askopenfilename(title = "Select gridded Aerial",filetypes = (("tif files","*.tif"),("all files","*.*")))
    img=io.imread(filename)
    im2 = Image.open(filename)
    # img=np.flip(img,axis=0)
    # img=np.flip(img,axis=1)
    maxcol2=im2.tag[33922][3]
    maxrow2=im2.tag[33922][4]
    cell2=1*im2.tag[33550][0]
    
    # mincol2=maxcol2-cell2*img.shape[1]
    # minrow2=maxrow2-cell2*img.shape[0]
    # left=(maxcol2-maxcol)/cell
    # right=(maxcol2-maxcol)/cell+(img.shape[1]*cell2)/cell
    # top=(maxrow2-maxrow)/cell
    # bottom=(maxrow2-maxrow)/cell-(img.shape[0]*cell2)/cell
    
    left=(maxcol2-maxcol)/Surfaces.cellsize
    right=(maxcol2-maxcol)/Surfaces.cellsize+(img.shape[1]*cell2)/Surfaces.cellsize
    top=Surfaces.Design.shape[0]+(maxrow2-maxrow)/Surfaces.cellsize
    bottom=-(maxrow2-maxrow)/Surfaces.cellsize+(img.shape[0]*cell2)/Surfaces.cellsize
    bottom =Surfaces.Design.shape[0]-bottom
    print(maxcol2,maxcol,maxrow2,maxrow,left,right,top,bottom)
    # im=Sf.a.imshow(np.ma.masked_values(C, 0),interpolation='none', cmap=plt.get_cmap('jet'),vmin = minC,vmax=maxC)
    im=Sf.a.imshow(img,extent=[left,right,bottom,top])
    Sf.f.canvas.restore_region(background)
    
    Sf.a.draw_artist(im)
    
    Sf.f.canvas.blit(Sf.f.bbox)


 
    # Draw_Update(Sf,Surfaces)            
def CutFill(Surfaces,Sf,cutmax,fillmax):
    C=np.zeros_like(Surfaces.Design)
    cutfillim(Surfaces.Design,Surfaces.Survey,C)
    # maxC=np.max(C)
    # minC=np.min(C)
    
    maxC=cutmax
    minC=-fillmax
    maxC=max(maxC,-minC)
    minC=-1*max(maxC,-minC)
    
    colors1 = plt.cm.winter(np.linspace(0., 1, 128))
    colors2 = plt.cm.autumn_r(np.linspace(0, 1, 128))
    colors = np.vstack((colors1, colors2))
    mymap = mcolors.LinearSegmentedColormap.from_list('my_colormap', colors)

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
    Draw_Update(Sf,Surfaces)
    
    # im=Sf.a.imshow(np.ma.masked_values(C, 0),interpolation='none', cmap=plt.get_cmap('jet'),vmin = minC,vmax=maxC)
    im=Sf.a.imshow(np.ma.masked_values(C, 0),interpolation='none', cmap=mymap,vmin = minC,vmax=maxC)
    ax2 = Sf.f.add_axes([0.9,0.1,0.05,0.8])
    Sf.f.canvas.restore_region(background)
    for tp in Sf.p[0].collections:
        tp.set_color(['gray'])
        Sf.a.draw_artist(tp)
    Sf.a.draw_artist(im)
    CB=Sf.f.colorbar(im,ticks=[minC,0,maxC],shrink=0.5,cax=ax2)
    CB.ax.set_yticklabels(['%dm Fill' %round(minC,1),0,'%dm Cut' %round(maxC,1)],color='white')
    CB.ax.set_ylabel('Elevation Difference',color='white')
    CB.ax.set_title('Cut/Fill',color='white')
    
    # CB.ax.set_yticklabels(['%dm Fill' %round(minC,1),0,'%dm Cut' %round(maxC,1)],color='black')
    # CB.ax.set_ylabel('Elevation Difference',color='black')
    # CB.ax.set_title('Cut/Fill',color='black')
    
    Sf.f.canvas.blit(Sf.f.bbox)
    Draw_contours(Sf,Surfaces) 
    # Draw_Update(Sf,Surfaces)

    
def CutFillContours(Surfaces,Sf,cutmax,fillmax):
    C=np.zeros_like(Surfaces.Design)
    cutfillim(Surfaces.Design,Surfaces.Survey,C)
    # maxC=np.max(C)
    # minC=np.min(C)
    
    maxC=cutmax
    minC=-fillmax
    maxC=max(maxC,-minC)
    minC=-1*max(maxC,-minC)
    
def CutFillContoursRemove(Surfaces,Sf,cutmax,fillmax):
    C=np.zeros_like(Surfaces.Design)
    cutfillim(Surfaces.Design,Surfaces.Survey,C)
    # maxC=np.max(C)
    # minC=np.min(C)
    
    maxC=cutmax
    minC=-fillmax
    maxC=max(maxC,-minC)
    minC=-1*max(maxC,-minC)
    
    
           
def DrawVisible(Visible,Sf,Surfaces):
    
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
    Draw_Update(Sf,Surfaces)
    
    # im=Sf.a.imshow(np.ma.masked_values(C, 0),interpolation='none', cmap=plt.get_cmap('jet'),vmin = minC,vmax=maxC)
    im=Sf.a.imshow(np.ma.masked_values(Visible, 0),interpolation='none', cmap=plt.get_cmap('Spectral_r'))
    Sf.f.canvas.restore_region(background)
    Sf.a.draw_artist(im)
    Sf.f.canvas.blit(Sf.f.bbox)            

#functions related to REduce surface tools

@jit
def Plan_CurveR(A,PC,cellsize):
    # cellsize=2
    for i in range (0,A.shape[0]):
        for j in range (0,A.shape[1]):
            check=0
            if i-1>=0 and i-1<A.shape[0] and j-1>=0 and j-1<A.shape[1]:
                if A[i-1,j-1]!=0:
                    z1=A[i-1,j-1]-A[i,j]
                else:
                    check=1
            else:
                check=1
            #i-1,j
            if i-1>=0 and i-1<A.shape[0] and j>=0 and j<A.shape[1]:
                if A[i-1,j]!=0:
                    z2=A[i-1,j]-A[i,j]
                else:
                    check=1
            else:
                check=1
            #i-1,j+1
            if i-1>=0 and i-1<A.shape[0] and j+1>=0 and j+1<A.shape[1]:
                if A[i-1,j+1]!=0:
                    z3=A[i-1,j+1]-A[i,j]
                else:
                    check=1
            else:
                check=1
            #i,j-1
            if i>=0 and i<A.shape[0] and j-1>=0 and j-1<A.shape[1]:
                if A[i,j-1]!=0:
                    z4=A[i,j-1]-A[i,j]
                else:
                    check=1
            else:
                check=1
            #i,j
            if i>=0 and i<A.shape[0] and j>=0 and j<A.shape[1]:
                if A[i,j]!=0:
                    z5=0
                else:
                    check=1
            else:
                check=1
            #i,j+1
            if i>=0 and i<A.shape[0] and j+1>=0 and j+1<A.shape[1]:
                if A[i,j+1]!=0:
                    z6=A[i,j+1]-A[i,j]
                else:
                    check=1
            else:
                check=1
            #i+1,j-1
            if i+1>=0 and i+1<A.shape[0] and j-1>=0 and j-1<A.shape[1]:
                if A[i+1,j-1]!=0:
                    z7=A[i+1,j-1]-A[i,j]
                else:
                    check=1
            else:
                check=1
            #i+1,j
            if i+1>=0 and i+1<A.shape[0] and j>=0 and j<A.shape[1]:
                if A[i+1,j]!=0:
                    z8=A[i+1,j]-A[i,j]
                else:
                    check=1
            else:
                check=1
            #i+1,j+1
            if i+1>=0 and i+1<A.shape[0] and j+1>=0 and j+1<A.shape[1]:
                if A[i+1,j+1]!=0:
                    z9=A[i+1,j+1]-A[i,j]
                else:
                    check=1
            else:
                check=1
            if check==0:
                AA = ((z1 + z3 + z7 + z9) / 4  - (z2 + z4 + z6 + z8) / 2 + z5) / cellsize**4 
                BB = ((z1 + z3 - z7 - z9) /4 - (z2 - z8) /2) / cellsize**3 
                CC = (((-z1 + z3 - z7 + z9) /4 + (z4 - z6)) /2) / cellsize**3 
                DD = ((z4 + z6) /2 - z5) / cellsize**2 
                EE = ((z2 + z8) /2 - z5) / cellsize**2 
                FF = (-z1 + z3 + z7 - z9) / 4*cellsize**2 
                GG = (-z4 + z6) / 2*cellsize
                HH = (z2 - z8) / 2*cellsize
                II = z5
        #        AA = ((z1 + z3 + z4 + z6 + z7 + z9) / 6 - (z2 +  z8) / 3) / cellsize**2;
        #        BB = ((z1 + z2 + z3 + z7 + z8 + z9) / 6 - (z4 +  z6) / 3) / cellsize**2;
        #        CC = (z3 + z7 -z1 - z9) / 4  / cellsize**2;
        #        DD = (z3 + z6 + z9 - z1 - z4 - z7) / 6 / cellsize;
        #        EE = (z1 + z2 + z3 - z7 - z8 - z9) / 6 / cellsize;
        #            FF = (2 * ( z2 + z4 + z6 - z8) - (z1 + z3 + z7 + z9) ) / 9
        #            SqABC = math.sqrt((AA-BB)**2 + CC**2)
                PC[i,j]=-2*(DD+EE)*100
        #        SqED = (EE**2 + DD**2)
        #        if SqED>0:
        #            PC[i,j]=200 * (BB * DD**2 + AA * EE**2 - CC * DD * EE) / SqED**1.5
        #            PC[i,j]=AA
            


@jit
def Aspect2R(A,W,S,cellsize):
    # cellsize=2
    for i in range (0,A.shape[0]):
        for j in range (0,A.shape[1]):
            check=0
            if i-1>=0 and i-1<A.shape[0] and j-1>=0 and j-1<A.shape[1]:
                if A[i-1,j-1]!=0:
                    a=A[i-1,j-1]
                else:
                    check=1
            else:
                check=1
            #i-1,j
            if i-1>=0 and i-1<A.shape[0] and j>=0 and j<A.shape[1]:
                if A[i-1,j]!=0:
                    b=A[i-1,j]
                else:
                    check=1
            else:
                check=1
            #i-1,j+1
            if i-1>=0 and i-1<A.shape[0] and j+1>=0 and j+1<A.shape[1]:
                if A[i-1,j+1]!=0:
                    c=A[i-1,j+1]
                else:
                    check=1
            else:
                check=1
            #i,j-1
            if i>=0 and i<A.shape[0] and j-1>=0 and j-1<A.shape[1]:
                if A[i,j-1]!=0:
                    d=A[i,j-1]
                else:
                    check=1
            else:
                check=1
        
            if i>=0 and i<A.shape[0] and j+1>=0 and j+1<A.shape[1]:
                if A[i,j+1]!=0:
                    f=A[i,j+1]
                else:
                    check=1
            else:
                check=1
            #i+1,j-1
            if i+1>=0 and i+1<A.shape[0] and j-1>=0 and j-1<A.shape[1]:
                if A[i+1,j-1]!=0:
                    g=A[i+1,j-1]
                else:
                    check=1
            else:
                check=1
            #i+1,j
            if i+1>=0 and i+1<A.shape[0] and j>=0 and j<A.shape[1]:
                if A[i+1,j]!=0:
                    h=A[i+1,j]
                else:
                    check=1
            else:
                check=1
            #i+1,j+1
            if i+1>=0 and i+1<A.shape[0] and j+1>=0 and j+1<A.shape[1]:
                if A[i+1,j+1]!=0:
                    ii=A[i+1,j+1]
                else:
                    check=1
            else:
                check=1
            if check==0:
                dzdx=-((c+2*f+ii)-(a+2*d+g))/(8*cellsize)
                dzdy=-((g+2*h+ii)-(a+2*b+c))/(8*cellsize)
                
                l=(dzdx**2+dzdy**2)**0.5
                angle=-math.atan2(dzdy/l,dzdx/l)
                if angle<0:
                    angle+=2*3.14159
                W[i,j]=angle
                S[i,j]=l
        
@jit
def accumulateR(B,C,W,A,D):
    for i in range (0,B.shape[0]):
        for j in range (0,B.shape[1]):
            pi=3.14159
            if i < B.shape[0] and j <B.shape[1]: # and Slopes[x,y]>7:
                if B[i,j]!=0 and A[i,j]!=0:           
                    alpha=W[i,j]
                    check =1
                    angle=pi/4
                   
                    ax=0
                    ay=0
                    bx=0
                    by=0
                    w1=0
                    w2=0
                    #1
                    if alpha<angle and check==1:
                        w1=(angle-alpha)/(pi/4)
                        w2=(alpha-(angle-pi/4))/(pi/4)
                        ax=0
                        ay=1
                        bx=-1
                        by=1
                        check=0
                    angle+=pi/4
                    #2
                    if alpha<angle and check==1:
                        w1=(angle-alpha)/(pi/4)
                        w2=(alpha-(angle-pi/4))/(pi/4)
                        ax=-1
                        ay=1
                        bx=-1
                        by=0
                        check=0
                    angle+=pi/4
                    #3
                    if alpha<angle and check==1:
                        w1=(angle-alpha)/(pi/4)
                        w2=(alpha-(angle-pi/4))/(pi/4)
                        ax=-1
                        ay=0
                        bx=-1
                        by=-1
                        check=0
                    angle+=pi/4
                    #4
                    if alpha<angle and check==1:
                        w1=(angle-alpha)/(pi/4)
                        w2=(alpha-(angle-pi/4))/(pi/4)
                        ax=-1
                        ay=-1
                        bx=0
                        by=-1
                        check=0
                    angle+=pi/4
                    #5
                    if alpha<angle and check==1:
                        w1=(angle-alpha)/(pi/4)
                        w2=(alpha-(angle-pi/4))/(pi/4)
                        ax=0
                        ay=-1
                        bx=1
                        by=-1
                        check=0
                    angle+=pi/4
                    #6
                    if alpha<angle and check==1:
                        w1=(angle-alpha)/(pi/4)
                        w2=(alpha-(angle-pi/4))/(pi/4)
                        ax=1
                        ay=-1
                        bx=1
                        by=0
                        check=0
                    angle+=pi/4
                    #7
                    if alpha<angle and check==1:
                        w1=(angle-alpha)/(pi/4)
                        w2=(alpha-(angle-pi/4))/(pi/4)
                        ax=1
                        ay=0
                        bx=1
                        by=1
                        check=0
                    angle+=pi/4
                    
                    #8
                    if alpha<angle and check==1:
                        w1=(angle-alpha)/(pi/4)
                        w2=(alpha-(angle-pi/4))/(pi/4)
                        ax=1
                        ay=1
                        bx=0
                        by=1
                        check=0
                    angle+=pi/4
                    
                    if i+ax<B.shape[0] and j+ay<B.shape[1] and i+bx<B.shape[0] and j+by<B.shape[1]:
                        if i+ax>0 and j+ay>0 and i+bx>0 and j+by>0:
                              if A[i+ax,j+ay]==0:
                                    B[i+ax,j+ay]=0
                                    B[i,j]=0
                              if A[i+bx,j+by]==0:
                                    B[i+bx,j+by]=0
                                    B[i,j]=0
                              D[i+ax,j+ay]+=w1*B[i,j]
                              D[i+bx,j+by]+=w2*B[i,j]

@jit    
def SumFlowsR(B,C,check,A,D):    
    for i in range (0,A.shape[0]):
        for j in range (0,A.shape[1]):
            if i < B.shape[0] and j <B.shape[1]: # and Slopes[x,y]>7:
                if B[i,j]!=0 and A[i,j]!=0:           
                    C[i,j]+=D[i,j]
                    B[i,j]=D[i,j]
                    if D[i,j]>4:
                        check[0]=1
                    D[i,j]=0
@jit    
def Unit_to_totalR(C,cellsize):
    # cellsize=2    
    for i in range (0,A.shape[0]):
        for j in range (0,A.shape[1]):
            if i < C.shape[0] and j <C.shape[1]: # and Slopes[x,y]>7:
                if C[i,j]>0:           
                    C[i,j]=C[i,j]/cellsize
            
def RunTopoR(A,cellsize):
    S=np.zeros_like(A)
    W=np.zeros_like(A)
    TF=np.zeros_like(A)
    B=np.zeros_like(A)
    C=np.zeros_like(A)
    D=np.zeros_like(A)
    check=np.array([1],dtype=np.float32)
    for i in range (0,A.shape[0]):
        for j in range (0,A.shape[1]):
            if A[i,j]!=0:
                B[i,j]=cellsize**2

    
    
    Aspect2R(A,W,S,cellsize)
    v=0
    while v<1000:
        accumulateR(B,C,W,A,D)
        SumFlowsR(B,C,check,A,D)
        v+=1
    Unit_to_totalR(C,cellsize)
    
    return C

def ReduceSurface (Surfaces,elevation_change):            
    xr=Surfaces.Design.shape[0]
    yr=Surfaces.Design.shape[1]
    W=np.zeros_like(Surfaces.Design)
    
    
    PC=np.zeros_like(Surfaces.Design)
    S=np.zeros_like(Surfaces.Design)
    AS=np.zeros((xr,yr,2),dtype=np.float32)
    
   
    
    Plan_CurveR(A,PC,Surfaces.cellsize)
    #Aspect[blockspergrid,threadsperblock](d_A,d_AS,d_S)
    
    
    C=RunTopoR(Surfaces.Design,Surfaces.cellsize)
    #plt.imshow(PC)
    
    Outlist=[]
    for i in range (0,Surfaces.Design.shape[0]):
        for j in range(0,Surfaces.Design.shape[1]):
            if Surfaces.Design[i,j]!=0:
                if abs(PC[i,j])>2 or abs(Surfaces.Design[i,j]-round(Surfaces.Design[i,j]))<0.1 or i%10+j%10==0 or C[i,j]>1000:
                        # if A[i,j]!=1000:
                        Outlist.append([Surfaces.maxcol-(Surfaces.Design.shape[1]-j)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.maxrow-(Surfaces.Design.shape[0]-i)*Surfaces.cellsize+0.5*Surfaces.cellsize,Surfaces.Design[i,j]+elevation_change])
                            # Outlist.append([lefti+i*cellsize,topi-(j)*cellsize,A[i,j]-1000])
    #                Outlist.append([lefti+j*cellsize,-i*cellsize+topi,Aobj.arr[i,j]])
    outfilename1 = asksaveasfilename(title = "Save, Enter file name",filetypes = (("CSV files","*.csv"),("all files","*.*")))
    if len(outfilename1)>3:
        if outfilename1[-4]!=".":
            outfilename1=outfilename1 +".csv"
    with open(outfilename1,'w') as output:
        writr=csv.writer(output, lineterminator='\n')
        writr.writerows(Outlist)

#####################################################################################################################################################################
#############################################_________End of REduce Surface Block____________########################################################################
#####################################################################################################################################################################