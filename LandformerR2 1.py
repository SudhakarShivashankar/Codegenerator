#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:56:29 2020

@author: sven
"""
# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'qt4' 
import os
# os.environ['ETS_TOOLKIT'] = 'qt4'
import matplotlib
from Landformer_Functions import *
# from Landformer_FunctionsnoGPU import *
from Landformer_classesBerms import *

# matplotlib.use("TKAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import Tk
from tkinter import Menu
#import os
from pathlib import Path
from tkinter.filedialog import askopenfilename
from tkinter import ttk
from tkinter.ttk import Separator


import numpy as np
#import math
# from osgeo import gdal
from matplotlib.colors import LightSource, Normalize
import matplotlib.image as mpimg
import matplotlib.animation
import matplotlib.transforms as mtransforms
from matplotlib.patches import Circle
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D

from queue import Queue
import threading
import sys
import ezdxf
import ctypes
# Image.MAX_IMAGE_PIXELS = None
ctypes.windll.shcore.SetProcessDpiAwareness(1)


plt.rcParams['axes.facecolor'] = 'black'


plt.ion()
TITLE_FONT=("Verdana", 20)
LARGE_FONT= ("Verdana", 9)


class Data:
    def __init__(self):
        self.Survey=[]
        self.Design=[]
        self.Design2=[]
        self.Surface1=[]
        self.Surface2=[]
        self.minval=0
        self.maxval=0
        self.Dist=[]
        self.cellsize=0
        self.Active=[]
        self.maxcol=0
        self.maxrow=0
        self.Survey_maxcol=0
        self.Survey_maxrow=0
        self.Survey_cellsize=0
        self.Offset=False
        

Surfaces=Data() 
   
class Landformer(tk.Tk):

    def __init__(self, *args, **kwargs):
       
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "Landform Design Toolkit")
        tk.Tk.option_add(self,"*Button.Relief","solid")
        tk.Tk.option_add(self,"*borderWidth",0.5)


        # tk.Tk.option_add(self,"*Button.Background","#c2d6d6")
        tk.Tk.option_add(self,"*Button.Background","#d1e0e0")
        # tk.Tk.option_add(self,"*Button.Background","#e6e6e6")
        

        tk.Tk.option_add(self,"*Button.Foreground","#1f2022")
        # tk.Tk.option_add(self,"*Button.Foreground","white")

        tk.Tk.option_add(self,"*epadY",3)

        tk.Tk.option_add(self,"*OptionMenu.Relief","solid")
        tk.Tk.option_add(self,"*Entry.Relief","flat")
        tk.Tk.option_add(self,"*Entry.Background","#B0E2FF")




      
        container = tk.Frame(self)
        
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        
        self.frames = {}
        for F in (StartPage, PageOne, PageTwo):
            frame = F(container, self,Surfaces)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        if cont==PageTwo:
            self['menu'] = frame.menubar
            PageTwo.UpdateInterval(frame)
        else:
            self['menu']=''
        frame.tkraise()

class StartPage(tk.Frame):

    def __init__(self, parent, controller,Surfaces):
        tk.Frame.__init__(self,parent)
        
#        print(b)
        label1 = tk.Label(self, text="Welcome to the Landform Design Toolkit", font=TITLE_FONT)
        label1.pack(pady=20,padx=10)
    
        button=tk.Button(self, text="Start", font="Verdana", bg="#B0E2FF",relief='solid',
                               command=lambda: controller.show_frame(PageOne))
        button.pack(ipadx=20)
        button.config(width=15, height=1)


class PageOne(tk.Frame):

    def __init__(self, parent, controller,Surfaces):
#        print(b)
        tk.Frame.__init__(self, parent)
        
        label = tk.Label(self, text="Import Surfaces", font=LARGE_FONT)
        label.grid(row=0,columnspan=4,padx=0,pady=5,)

        label2 = tk.Label(self, text="Surface Metrics", font=LARGE_FONT,padx=5, pady=10)
        label2.grid(row=4,columnspan=4,padx=0,pady=5,)
             
        label3 = tk.Label(self, text="Last Modified", )
        label3.grid(row=6,column=0,padx=0,pady=5,)
        
        label4 = tk.Label(self, text="Number of Points", )
        label4.grid(row=7,column=0,padx=0,pady=5,)
       
        label5 = tk.Label(self, text="Min / Max Z", )
        label5.grid(row=8,column=0,padx=0,pady=5,)
        
        label6 = tk.Label(self, text="Survey", )
        label6.grid(row=5,column=1,padx=0,pady=5,)
        
        label7 = tk.Label(self, text="Design", )
        label7.grid(row=5,column=2,padx=0,pady=5,)
        
        button1 = tk.Button(self, text="Back",
                            command=lambda: controller.show_frame(StartPage))
        button1.grid(row=3,column=0,padx=20,pady=5)
        button1.config(width=30, height=2)

#        PageTwo.UpdateValue1(PageTwo)
        
        
        button2 = tk.Button(self, text="Next",
                            command=lambda: controller.show_frame(PageTwo))
        button2.grid(row=3,column=2,padx=20,pady=5)
        button2.config(width=30, height=2)
        
        TE1 = tk.Text(self, height=1.15, width=60, bg="#B0E2FF",relief='flat')              
        TE1.grid(row=1,column=1,padx=3)
        
        TE2 = tk.Text(self, height=1.15, width=30, bg="#B0E2FF",relief='flat' )              
        TE2.grid(row=6,column=1,padx=3)
        
        TE3 = tk.Text(self, height=1.15, width=30, bg="#B0E2FF",relief='flat' )              
        TE3.grid(row=7,column=1,padx=3)
        
        TE4 = tk.Text(self, height=1.15, width=30, bg="#B0E2FF",relief='flat' )              
        TE4.grid(row=8,column=1,padx=3)
        
        button3 = tk.Button(self, text="Import Survey",
                            command=lambda: import_SurveyPil(Surfaces,TE1,TE2,TE3,TE4))
        button3.grid(row=1,column=0,padx=20,pady=5)
        button3.config(width=30, height=2)
        
                    
        checkbutton1 = tk.Checkbutton(self, text = "+1000", onvalue = 1, offvalue=0).grid(row=1,column=2)
        
        TD1 = tk.Text(self, height=1.15, width=60, bg="#B0E2FF",relief='flat', )              
        TD1.grid(row=2,column=1,padx=3)
        
        TD2 = tk.Text(self, height=1.15, width=30, bg="#B0E2FF",relief='flat' )              
        TD2.grid(row=6,column=2,padx=3)
        
        TD3 = tk.Text(self, height=1.15, width=30, bg="#B0E2FF",relief='flat' )              
        TD3.grid(row=7,column=2,padx=3)
        
        TD4 = tk.Text(self, height=1.15, width=30, bg="#B0E2FF",relief='flat' )              
        TD4.grid(row=8,column=2,padx=3)
        
        button4 = tk.Button(self, text="Import Design",
                            command=lambda: import_DesignPil(Surfaces,TD1,TD2,TD3,TD4))
        button4.grid(row=2,column=0,padx=20,pady=5)
        button4.config(width=30, height=2)

        
        checkbutton2 = tk.Checkbutton(self, text = "+1000", onvalue = 1, offvalue=0).grid(row=2,column=2)
        
        button5 = tk.Button(self, text="Convert Gridded CSV Points to TIFF",
                            command=lambda: convert_points_to_tiff())
        button5.grid(row=14,column=0,padx=20,pady=5)
        button5.config(width=30, height=2)

        label8 = tk.Label(self, text="Data Preparation", font=LARGE_FONT,padx=5, pady=10)
        label8.grid(row=10,columnspan=4,padx=0,pady=5,)   
          
        label9 = tk.Label(self, text="Cell size (m)", font=LARGE_FONT)
        label9.grid(row=12,column=1,padx=20,pady=0)
        
        self.Cellsize=tk.Entry(self)
        self.Cellsize.insert(0,1.0)
        self.Cellsize.grid(row=14,column=1)
        
        self.progress=ttk.Progressbar(self,orient='horizontal',length=100,mode='determinate')
        self.progress.grid(row=14,column=2)
        button8 = tk.Button(self, text="Triangulate points to tiff",
                            command=lambda: triangulate_rasters(float(self.Cellsize.get()),self.progress,self))
        button8.grid(row=15,column=0,padx=20,pady=5)
        button8.config(width=30, height=2)

        # progress=tk.progressbar(self,orient=horizontal,length=100,mode='determinate')        
        
        label10 = tk.Label(self, text="Function", )
        label10.grid(row=12,column=0,padx=0,pady=5,)
        
        label11 = tk.Label(self, text="Progress", )
        label11.grid(row=12,column=2,padx=0,pady=5,)
        
        controller['menu'] = ''
        
        
class PageTwo(tk.Frame):

    def __init__(self, parent, controller,Surfaces):
        window=tk.Frame.__init__(self, parent)
        
        # self.protocol("WM_DELETE_WINDOW",lambda: self.on_closing2())
        self.focus_set()
        self.popup_menu=Menu(master=self,tearoff=0,background='#1c1b1a',fg='white',activebackground='#534c5c', activeforeground='Yellow')
        self.m1=Menu(self.popup_menu,tearoff=0,background='#1c1b1a',fg='white',activebackground='#534c5c', activeforeground='Yellow')
        self.popup_menu.add_command(label="None                     ",command=self.Set_to_none)
        self.m1.add_command(label="Shape                     ",command=self.Set_to_shape)
        self.m1.add_command(label="Modify                     ",command=self.Set_to_modify)
        self.m1.add_command(label="Smooth                     ",command=self.Set_to_smooth)
        self.m1.add_command(label="Set to Constant            ",command=self.Set_to_constant)
        self.m1.add_command(label="Set Design Undo Point      ",command=lambda: self.Set_Design2(Surfaces))
        self.m1.add_command(label="Undo to Previous Design    ",command=self.Set_to_Undo)
        self.m1.add_command(label="Unlock all            ",command=lambda: self.Unlock_all(Surfaces))
        self.m1.add_command(label="Close gaps            ",command=lambda: Close_gaps(Surfaces.Design))
        self.m1.add_command(label="Smooth fill edge up            ",command=lambda: Smooth_fill_edge(Surfaces.Design,Surfaces.Survey,Surfaces.Design2))
        self.popup_menu.add_cascade(label="Edit Surface",menu=self.m1)
        
        self.m2=Menu(self.popup_menu,tearoff=0,background='#1c1b1a',fg='white',activebackground='#534c5c', activeforeground='Yellow')
        self.m2.add_command(label="Measure Cut Fill                     ",command=lambda: self.CutFill())
        self.m2.add_command(label="Dynamic Droplet                     ",command=self.Set_to_DyDrop)
        self.m2.add_command(label="Clear Droplet                     ",command=self.Clear_DyDrop)
        self.m2.add_command(label="Read Elevation                     ",command=self.Set_to_Elev)
        self.m2.add_command(label="Clear Elevations                     ",command=self.Clear_Elev)
        self.m2.add_command(label="Measure                     ",command=self.Set_to_Measure)
        self.m2.add_command(label="Clear Measure                     ",command=self.Clear_Measure)
        self.popup_menu.add_cascade(label="Inspect Surface",menu=self.m2)
        
        self.m3=Menu(self.popup_menu,tearoff=0,background='#1c1b1a',fg='white',activebackground='#534c5c', activeforeground='Yellow')
        self.m3.add_command(label="Add Line                     ",command=self.Set_to_AddLine)
        self.m3.add_command(label="Add Polygon                     ",command=self.Set_to_AddPolygon)
        self.m3.add_command(label="Toggle Lines                     ",command=lambda: self.ToggleLines())
        self.m3.add_command(label="Toggle Polygons                     ",command=lambda: self.TogglePolygons())
        self.popup_menu.add_cascade(label="Geometries",menu=self.m3)
        
        self.m4=Menu(self.popup_menu,tearoff=0,background='#1c1b1a',fg='white',activebackground='#534c5c', activeforeground='Yellow')
        self.m4.add_command(label="Import shapefile                     ",command=lambda: ShapeFile_plot(self,Surfaces))
        self.m4.add_command(label="Import points                        ",command=lambda:  self.draw_MergeFrame())
        self.m4.add_command(label="Import Quadratic Lines               ",command=lambda: Import_lines(self,Surfaces,'quadratic'))
        self.m4.add_command(label="Import Radial & Tangent Lines        ",command=lambda: Import_lines(self,Surfaces,'radius'))
        self.m4.add_command(label="Import Polygons from shapefile       ",command=lambda: Import_Polygon_Shapefile(self, Surfaces))
        self.m4.add_command(label="Import Survey                        ",command=lambda: import_SurveyPil2(Surfaces))
        self.m4.add_command(label="Import Design                        ",command=lambda: import_DesignPil2(Surfaces,self))          
        # self.m4.add_command(label="Import Image                     ",command=lambda: Import_Image(self))
        self.popup_menu.add_cascade(label="Import",menu=self.m4)
        
        self.m5=Menu(self.popup_menu,tearoff=0,background='#1c1b1a',fg='white',activebackground='#534c5c', activeforeground='Yellow')
        self.m5.add_command(label="Toggle Circle                     ",command=self.ToggleCircle)
        self.m5.add_command(label="Draw Contours                     ",command=lambda: self.UpdateInterval())
        self.m5.add_command(label="Import Aerial Image                     ",command=lambda: Import_Aerial(self,Surfaces))
        self.m5.add_command(label="3D Model                     ",command=self.Gen_3D)
        self.m5.add_command(label="Draw Slope                     ",command=lambda: self.draw_SlopeFrame(Surfaces))
        self.m5.add_command(label="Draw Topofactor                     ",command=lambda: self.draw_TFFrame(Surfaces))
        self.m5.add_command(label="Draw Cut/Fill                     ",command=lambda: self.draw_CutFFrame(Surfaces))
        
        self.m5.add_command(label="Remove Images                     ",command=lambda: self.RemoveImages())
        self.m5.add_command(label="Remove Arrows                     ",command=lambda: self.RemoveArrows())
        self.m5.add_command(label="Remove Shapefile                     ",command=lambda: self.RemoveShape())
        self.m5.add_command(label="Draw Survey Contours                     ",command=lambda: Draw_Survey_contours(self,Surfaces))
        self.m5.add_command(label="Remove Survey Contours                     ",command=lambda: Remove_Survey_contours(self,Surfaces))
        self.m5.add_command(label="Recenter Plot                     ",command=lambda: self.recenter())
        self.m5.add_command(label="Set Labels to Black                     ",command=lambda: self.Set_text_to_black())
        self.m5.add_command(label="Close Gaps                     ",command=lambda: Close_Gaps(Surfaces.Design))
        self.popup_menu.add_cascade(label="Visualization",menu=self.m5)
        
        self.m6=Menu(self.popup_menu,tearoff=0,background='#1c1b1a',fg='white',activebackground='#534c5c', activeforeground='Yellow')
        self.m6.add_command(label="Save Raster                     ",command=lambda: save_DesignPil(Surfaces))
        self.m6.add_command(label="Save Locked Raster                     ",command=lambda: save_DesignLOCKED(Surfaces))
        self.m6.add_command(label="Save Points                     ",command=lambda: save_DesignPoints(Surfaces))
        self.m6.add_command(label="Save Raster New Cellsize                    ",command=lambda: save_DesignPilReducedSize(Surfaces))
        self.m6.add_command(label="Save All Locked Points                     ",command=lambda: save_DesignPointsLocked(Surfaces))
        self.m6.add_command(label="Save All Modified Points                     ",command=lambda: save_DesignPointsMod(Surfaces))
        self.m6.add_command(label="Save CutFill                     ",command=lambda: save_CutFill(Surfaces))
        self.m6.add_command(label="Write Lines to DXF                     ",command=lambda: write_dxf())
        self.m6.add_command(label="Write Lines to shapefile                     ",command=lambda: write_shapefile(self,Surfaces))
        self.m6.add_command(label="Write Survey Section to shapefile                     ",command=lambda: write_shapefileSurvey(self,Surfaces))
        self.m6.add_command(label="Write Design Section to shapefile                     ",command=lambda: write_shapefileDesign(self,Surfaces))
        self.m6.add_command(label="Write Polygons to shapefile                     ",command=lambda: write_shapefileP(self,Surfaces,self.Polygons))
        self.m6.add_command(label="Write Lines to csv                     ",command=lambda: Save_Lines(self,Surfaces))
        self.m6.add_command(label="Write Grains to csv                     ",command=lambda: self.Set_to_Grain())
        self.m6.add_command(label="Write Stage Capacity of Locked Points                     ",command=lambda: Stage_Capacity(Surfaces))
        self.m6.add_command(label="Reduce Point Density                     ",command=lambda: self.Set_to_Reduce())
        self.popup_menu.add_cascade(label="Save",menu=self.m6)
        
        self.m7=Menu(self.popup_menu,tearoff=0,background='#1c1b1a',fg='white',activebackground='#534c5c', activeforeground='Yellow')
        self.m7.add_command(label="Determine viewshed                     ",command=lambda: self.Set_to_Visible())
        self.m7.add_command(label="Clear viewshed                     ",command=lambda: self.Clear_Visible())
        self.m7.add_command(label="Save viewshed                     ",command=lambda: self.Save_Visibility())
        self.m7.add_command(label="Render Viewpoint Design                     ",command=lambda: self.set_render())
        self.m7.add_command(label="Render Viewpoint Survey                     ",command=lambda: self.set_renderSurv())
        # self.popup_menu.add_command(label="Settle                     ",command=lambda: settlement(Surfaces.Survey,Surfaces.Design))
        self.popup_menu.add_cascade(label="Visibility",menu=self.m7)
        
        self.m8=Menu(self.popup_menu,tearoff=0,background='#1c1b1a',fg='white',activebackground='#534c5c', activeforeground='Yellow')
        self.m8.add_command(label="CAESAR Data Import                     ",command=lambda: self.Set_to_LEM())
        
        self.popup_menu.add_cascade(label="Landform Evolution Result Viewer",menu=self.m8)
        
        self.CB=None
        self.fill=np.array([0.0])
        self.cut=np.array([0.0])
        self.fill0=np.array([0.0])
        self.cut0=np.array([0.0])
        self.A=None
        self.circle=None
        self.dot=None
        self.point=None
        self.drop=None
        self.ReadElev=[]
        self.count=0
        self.LineID=1
        self.polyID=1
        self.notPlotted=True
        self.ActiveLine=None 
        self.ActivePolygon=None 
        self.Linepoints=[]
        self.Lines=[]
        self.shape=[]
        self.Polygons=[]
        self.Measure=[]
        self.xlim=[0,0]
        self.ylim=[0,0]
        self.drawn=False
        self.buttonpressed=False
        self.axesupdate=True
        self.presentmethod='None'
        self.presentmethoddetails='None'
        self.LineVIS=True
        self.PolyVIS=True
        self.DEBOUNCE_DUR=250
        self.subframes=[]
        self._job=None
        self.Visible=None
        self.polyinfo=[]
        self.parameters=[]
        self.dxfdata=[[],[],[],[],[],[],[],[],[],[]]
        self.shape_option_selected=[0,0]
        # self.queue.put(Surfaces.Design)
        # self.queue.put(Surfaces.Survey)
        # self.queue.put(self.cut)
        # self.queue.put(self.fill)
        # self.queue.put(Surfaces.cellsize)
        # ThreadedTask(self.queue).start()
        # self.master.after(100, self.process_queue)
        
        #Dynamic Droplet frame
        self.ReduceFrame = tk.Frame(master=self)
        self.ReduceFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        labelReduce = tk.Label(self.ReduceFrame, text="Elevation Change:")
        labelReduce.grid(row=2,column=6)
        self.ElevChangeR=tk.Entry(self.ReduceFrame,bg="#B0E2FF",relief='flat',width=10)
        self.ElevChangeR.insert(0,0.0)
        self.ElevChangeR.grid(row=2,column=7,sticky='nesw',pady=1)
        buttonReduce = tk.Button(self.ReduceFrame, text="Reduce Points",command=lambda: ReduceSurface(Surfaces,float(self.ElevChangeR.get())))
        buttonReduce.grid(row=0,column=0, rowspan=2,sticky='nesw',pady=1)
        self.ReduceFrame.grid_remove()
        self.subframes.append(self.ReduceFrame)
        
        #Line frame
        self.SelectLineFrame = tk.Frame(master=self)
        self.SelectLineFrame.grid(row=0,column=0,columnspan=27,sticky=tk.NSEW)
        button10 = tk.Button(self.SelectLineFrame, text="Plot Rock Size\n      and  \nVelocity Limits",command=lambda: self.Rock_Vel_Plots(Surfaces))
        button10.grid(row=0,column=0, rowspan=1,sticky='nesw',pady=1)
        
        buttonR = tk.Button(self.SelectLineFrame, text="Make ridges",command=lambda: self.Create_Ridges(Surfaces))
        buttonR.grid(row=1,column=0, rowspan=1,sticky='nesw',pady=1)
        
        self.LineOpt=tk.StringVar()
        self.LineOpt.set("Lock to Edge")
        self.LineOptions=tk.OptionMenu(self.SelectLineFrame,self.LineOpt,"Lock to Edge","Lock Base Only")
        self.LineOptions.grid(row=2,column=0,sticky='nesw',pady=1)
        self.LineOptions.config(relief='solid',borderwidth=1)
        
        # button11 = tk.Button(self.SelectLineFrame, text="Edit Parameters",command=lambda: self.Input_Parameters())
        # button11.grid(row=2,column=0,sticky='nesw',pady=1)
       
        self.divider1 = Separator(self.SelectLineFrame, orient="vertical").grid(column=1, row=0, sticky="ns",rowspan=3, padx=3) 

       
        button1 = tk.Button(self.SelectLineFrame, text="Edit Vertical Alignment",command=lambda: self.ActiveLine.vertical_alignment())
        button1.grid(row=0,column=2,sticky='nesw',pady=1)
        
        button3 = tk.Button(self.SelectLineFrame, text="Apply into surface",command=lambda: self.Create_Canal(Surfaces,self.LineOpt.get()))
        button3.grid(row=1,column=2,sticky='nesw',pady=1)
        
        button8 = tk.Button(self.SelectLineFrame, text="Catchment",command=lambda: self.Drain_Catchment())
        button8.grid(row=2,column=2,sticky='nesw',pady=1)
        
        self.divider2 = Separator(self.SelectLineFrame, orient="vertical").grid(column=3, row=0, sticky="ns",rowspan=3, padx=3) 

        # button4 = tk.Button(self.SelectLineFrame, text="Lock points",command=self.donothing())
        # button4.grid(row=0,column=1)
        
        # button5 = tk.Button(self.SelectLineFrame, text="Unlock points",command=lambda: self.ActiveLine.Unlock(Surfaces,self))
        # button5.grid(row=0,column=4,sticky='nesw',pady=1)
        
        button5 = tk.Button(self.SelectLineFrame, text="Cut/Fill Adjacent",command=lambda: self.Create_CanalCF(Surfaces,self.LineOpt.get()))
        button5.grid(row=0,column=4,sticky='nesw',pady=1)
        
        button6 = tk.Button(self.SelectLineFrame, text="Connect",command=lambda: [self.ActiveLine.Tie_in(self.Lines), self.UpdateConnectedLengths()])
        button6.grid(row=1,column=4,sticky='nesw',pady=1)
        
        button9 = tk.Button(self.SelectLineFrame, text="Delete",command=lambda: self.Delete_Line(Surfaces))
        button9.grid(row=2,column=4,sticky='nesw',pady=1)
        
        self.divider3 = Separator(self.SelectLineFrame, orient="vertical").grid(column=5, row=0, sticky="ns",rowspan=3, padx=3) 

        
        label2 = tk.Label(self.SelectLineFrame, text="Length (m):")
        label2.grid(row=0,column=6,sticky='nesw')
        self.DrainLength=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.DrainLength.insert(0,1.0)
        self.DrainLength.grid(row=0,column=7,sticky='nesw',pady=1)
          
        label3 = tk.Label(self.SelectLineFrame, text="Catchment Area (ha):")
        label3.grid(row=1,column=6)
        self.CatchArea=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.CatchArea.insert(0,0.0)
        self.CatchArea.grid(row=1,column=7,sticky='nesw',pady=1)
        
        label4 = tk.Label(self.SelectLineFrame, text="Drainage Density (m/ha):")
        label4.grid(row=2,column=6)
        self.DrainDens=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.DrainDens.insert(0,0.0)
        self.DrainDens.grid(row=2,column=7,sticky='nesw',pady=1)
        
        self.divider4 = Separator(self.SelectLineFrame, orient="vertical").grid(column=8, row=0, sticky="ns",rowspan=3, padx=3) 

        
        label5 = tk.Label(self.SelectLineFrame, text="Connected Drain ID's:")
        label5.grid(row=0,column=9)
        self.DrainIDS=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.DrainIDS.insert(0,0.0)
        self.DrainIDS.grid(row=0,column=10,sticky='nesw',pady=1)
        
        label6 = tk.Label(self.SelectLineFrame, text="Connected Drain Length (m):")
        label6.grid(row=1,column=9)
        self.AllLengths=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.AllLengths.insert(0,0.0)
        self.AllLengths.grid(row=1,column=10,sticky='nesw',pady=1)
        
        label7 = tk.Label(self.SelectLineFrame, text="Total Drainage Density (m):")
        label7.grid(row=2,column=9)
        self.AllDensity=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.AllDensity.insert(0,0.0)
        self.AllDensity.grid(row=2,column=10,sticky='nesw',pady=1)
        
        self.divider5 = Separator(self.SelectLineFrame, orient="vertical").grid(column=11, row=0, sticky="ns",rowspan=3, padx=3) 




        label8 = tk.Label(self.SelectLineFrame, text="Slope Left (m)")
        label8.grid(row=0,column=12)
        self.SlopeL=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.SlopeL.insert(0,0.0)
        self.SlopeL.grid(row=0,column=13,sticky='nesw',pady=1)
        
        label9 = tk.Label(self.SelectLineFrame, text="Berm Width Left(m)")
        label9.grid(row=0,column=14)
        self.WidthL=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.WidthL.insert(0,0.0)
        self.WidthL.grid(row=0,column=15,sticky='nesw',pady=1)
        
        label10 = tk.Label(self.SelectLineFrame, text="Slope Left canal(m)")
        label10.grid(row=0,column=16)
        self.SlopeLC=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.SlopeLC.insert(0,0.0)
        self.SlopeLC.grid(row=0,column=17,sticky='nesw',pady=1)
        label11 = tk.Label(self.SelectLineFrame, text="Depth Left canal(m)")
        label11.grid(row=1,column=16)
        self.DepthLC=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.DepthLC.insert(0,0.0)
        self.DepthLC.grid(row=1,column=17,sticky='nesw',pady=1)
        
        label12 = tk.Label(self.SelectLineFrame, text="Base Width(m)")
        label12.grid(row=0,column=18)
        self.WidthB=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.WidthB.insert(0,0.0)
        self.WidthB.grid(row=0,column=19,sticky='nesw',pady=1)
        
        label13 = tk.Label(self.SelectLineFrame, text="Slope Right canal(m)")
        label13.grid(row=0,column=20)
        self.SlopeRC=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.SlopeRC.insert(0,0.0)
        self.SlopeRC.grid(row=0,column=21,sticky='nesw',pady=1)
        label14 = tk.Label(self.SelectLineFrame, text="Depth Right canal(m)")
        label14.grid(row=1,column=20)
        self.DepthRC=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.DepthRC.insert(0,0.0)
        self.DepthRC.grid(row=1,column=21,sticky='nesw',pady=1)
        
        label15 = tk.Label(self.SelectLineFrame, text="Berm Width Right(m)")
        label15.grid(row=0,column=22)
        self.WidthBR=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.WidthBR.insert(0,0.0)
        self.WidthBR.grid(row=0,column=23,sticky='nesw',pady=1)
        
        label16 = tk.Label(self.SelectLineFrame, text="Slope Right(m)")
        label16.grid(row=0,column=24)
        self.SlopeR=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat',width=3)
        self.SlopeR.insert(0,0.0)
        self.SlopeR.grid(row=0,column=25,sticky='nesw',pady=1)
        
        # label8 = tk.Label(self.SelectLineFrame, text="Bottom Width (m)")
        # label8.grid(row=0,column=12)
        # self.Width=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat')
        # self.Width.insert(0,0.0)
        # self.Width.grid(row=0,column=13,sticky='nesw',pady=1)
        
        # label9 = tk.Label(self.SelectLineFrame, text="Total Depth (m)")
        # label9.grid(row=1,column=12)
        # self.Depth=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat')
        # self.Depth.insert(0,0.0)
        # self.Depth.grid(row=1,column=13,sticky='nesw',pady=1)
        
        # label10 = tk.Label(self.SelectLineFrame, text="Side Slope (1 in ):")
        # label10.grid(row=2,column=12)
        # self.Side=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat')
        # self.Side.insert(0,0.0)
        # self.Side.grid(row=2,column=13,sticky='nesw',pady=1)
        
        label17 = tk.Label(self.SelectLineFrame, text="Depth Below (m)")
        label17.grid(row=0,column=26)
        self.depthBelow=tk.Entry(self.SelectLineFrame,bg="#B0E2FF",relief='flat')
        self.depthBelow.insert(0,0.0)
        self.depthBelow.grid(row=0,column=27,sticky='nesw')
        
        self.SelectLineFrame.grid_remove()
        self.subframes.append(self.SelectLineFrame)
        
        #LEM frame
        self.LEMFrame = tk.Frame(master=self)
        self.LEMFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        self.sliderLem= tk.Scale(self.LEMFrame,from_=0,to=1,resolution=1,orient='horizontal',length=400,label = "Model Time",command=lambda x,Sf=self,Se=Surfaces: LemUp(x,Sf,Se))
        self.ImportDiff = tk.Button(self.LEMFrame, text="Import Elevation Differences",command=lambda: import_LEM(self,Surfaces))
        self.ImportDiff.grid(row=0,column=1)
        
        self.ImportSib = tk.Button(self.LEMFrame, text="Import SIBERIA results",command=lambda: import_LEM_SIBERIA(self,Surfaces))
        self.ImportSib.grid(row=1,column=1)
        
        self.ImportTiff = tk.Button(self.LEMFrame, text="Import Tiff results",command=lambda: import_LEMTiff(self,Surfaces))
        self.ImportTiff.grid(row=1,column=3)
        
        self.PlotDiff = tk.Button(self.LEMFrame, text="Plot erosion Deposition in Polygon",command=lambda: self.Plot_LEM(Surfaces))
        self.PlotDiff.grid(row=0,column=2)
        self.sliderLem.grid(row=0,column=0)
        self.LEMFrame.grid_remove()
        self.subframes.append(self.LEMFrame)
        
        def DDL(maxD,Sf,Se):
            Sf.drop[-1].maxD=float(maxD)
            print(maxD)
            
        #Dynamic Droplet frame
        self.DDFrame = tk.Frame(master=self)
        self.DDFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        self.sliderDDL= tk.Scale(self.DDFrame,from_=0,to=500,resolution=1,orient='horizontal',length=400,label = "Distance Cut-off",command=lambda x,Sf=self,Se=Surfaces: DDL(x,Sf,Se))
        self.sliderDDL.grid(row=0,column=0)
        self.sliderDDL.set(100)
        self.DDFrame.grid_remove()
        self.subframes.append(self.DDFrame)
        
            
      
        #Modify frame
        self.ModifyFrame = tk.Frame(master=self)
        self.ModifyFrame.grid(row=0,column=0,columnspan=12,rowspan=2,sticky=tk.NSEW)
        self.slidermodup= tk.Scale(self.ModifyFrame,from_=-5,to=5,resolution=0.01,orient='horizontal',length=400,label = "Modify Height")
        self.slidermodup.grid(row=0,column=0,rowspan=2)
        label2 = tk.Label(self.ModifyFrame, text="Exponent:")
        label2.grid(row=0,column=10)

        self.ModExp=tk.Entry(self.ModifyFrame,bg="#B0E2FF",relief='flat')
        self.ModExp.delete(0,tk.END)
        self.ModExp.insert(0,1.0)
        self.ModExp.grid(row=1,column=10)
        self.ModifyFrame.grid_remove()
        self.subframes.append(self.ModifyFrame)
        
        #Topographic Factor frame
        self.TopoFrame = tk.Frame(master=self)
        self.TopoFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        
        label2 = tk.Label(self.TopoFrame, text="Slope Exponent/Erodibility:")
        label2.grid(row=0,column=0)
        self.SlopeExp=tk.Entry(self.TopoFrame,bg="#B0E2FF",relief='flat')
        self.SlopeExp.delete(0,tk.END)
        self.SlopeExp.insert(0,1.5)
        self.SlopeExp.grid(row=0,column=1)
        
        label3 = tk.Label(self.TopoFrame, text="Catchment Exponent/Cover Factor:")
        label3.grid(row=1,column=0)
        self.CatchExp=tk.Entry(self.TopoFrame,bg="#B0E2FF",relief='flat')
        self.CatchExp.delete(0,tk.END)
        self.CatchExp.insert(0,1.0)
        self.CatchExp.grid(row=1,column=1)
        
        label4 = tk.Label(self.TopoFrame, text="Maximum Topographic Factor/Erosion:")
        label4.grid(row=2,column=0)
        self.Topoval=tk.Entry(self.TopoFrame,bg="#B0E2FF",relief='flat')
        self.Topoval.delete(0,tk.END)
        self.Topoval.insert(0,50.0)
        self.Topoval.grid(row=2,column=1)
        self.DrawTopo = tk.Button(self.TopoFrame, text="Draw Topographic Factor",command=lambda: self.draw_TF(Surfaces))
        self.DrawTopo.grid(row=0,column=2)
        
        self.SaveTopo = tk.Button(self.TopoFrame, text="Save Topographic Factor",command=lambda: self.save_TF(Surfaces))
        self.SaveTopo.grid(row=1,column=2)
        
        self.TopoFrame.grid_remove()
        self.subframes.append(self.TopoFrame)
        
        #Grains frame
        self.GrainFrame = tk.Frame(master=self)
        self.GrainFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        
        label2 = tk.Label(self.GrainFrame, text="1:")
        label2.grid(row=0,column=0)
        self.G1=tk.Entry(self.GrainFrame,bg="#B0E2FF",relief='flat')
        self.G1.delete(0,tk.END)
        self.G1.insert(0,0.0)
        self.G1.grid(row=0,column=1)
        
        label3 = tk.Label(self.GrainFrame, text="2:")
        label3.grid(row=1,column=0)
        self.G2=tk.Entry(self.GrainFrame,bg="#B0E2FF",relief='flat')
        self.G2.delete(0,tk.END)
        self.G2.insert(0,0.0)
        self.G2.grid(row=1,column=1)
        
        label4 = tk.Label(self.GrainFrame, text="3:")
        label4.grid(row=2,column=0)
        self.G3=tk.Entry(self.GrainFrame,bg="#B0E2FF",relief='flat')
        self.G3.delete(0,tk.END)
        self.G3.insert(0,0.0)
        self.G3.grid(row=2,column=1)
       
        label5 = tk.Label(self.GrainFrame, text="4:")
        label5.grid(row=0,column=2)
        self.G4=tk.Entry(self.GrainFrame,bg="#B0E2FF",relief='flat')
        self.G4.delete(0,tk.END)
        self.G4.insert(0,0.0)
        self.G4.grid(row=0,column=3)
        
        label6 = tk.Label(self.GrainFrame, text="5:")
        label6.grid(row=1,column=2)
        self.G5=tk.Entry(self.GrainFrame,bg="#B0E2FF",relief='flat')
        self.G5.delete(0,tk.END)
        self.G5.insert(0,0.0)
        self.G5.grid(row=1,column=3)
        
        label7 = tk.Label(self.GrainFrame, text="6:")
        label7.grid(row=2,column=2)
        self.G6=tk.Entry(self.GrainFrame)
        self.G6.delete(0,tk.END)
        self.G6.insert(0,0.0)
        self.G6.grid(row=2,column=3)
     
        label8 = tk.Label(self.GrainFrame, text="7:")
        label8.grid(row=0,column=4)
        self.G7=tk.Entry(self.GrainFrame)
        self.G7.delete(0,tk.END)
        self.G7.insert(0,0.0)
        self.G7.grid(row=0,column=5)
        
        label9 = tk.Label(self.GrainFrame, text="8:")
        label9.grid(row=1,column=4)
        self.G8=tk.Entry(self.GrainFrame)
        self.G8.delete(0,tk.END)
        self.G8.insert(0,0.0)
        self.G8.grid(row=1,column=5)
        
        label10 = tk.Label(self.GrainFrame, text="9:")
        label10.grid(row=2,column=4)
        self.G9=tk.Entry(self.GrainFrame)
        self.G9.delete(0,tk.END)
        self.G9.insert(0,0.0)
        self.G9.grid(row=2,column=5)
       
        self.ExportGrain = tk.Button(self.GrainFrame, text="Write Grains",command=lambda: Export_Grains(Surfaces,float(self.G1.get()),float(self.G2.get()),float(self.G3.get()),float(self.G4.get()),float(self.G5.get()),float(self.G6.get()),float(self.G7.get()),float(self.G8.get()),float(self.G9.get())))
        self.ExportGrain.grid(row=0,column=6)
        self.GrainFrame.grid_remove()
        self.subframes.append(self.GrainFrame)
        
        #Merge frame
        self.MergeFrame = tk.Frame(master=self)
        self.MergeFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        
        labelM2 = tk.Label(self.MergeFrame, text="Alpha Maximum edge length:")
        labelM2.grid(row=0,column=0)
        self.MergeAlpha=tk.Entry(self.MergeFrame)
        self.MergeAlpha.delete(0,tk.END)
        self.MergeAlpha.insert(0,30)
        self.MergeAlpha.grid(row=0,column=1)
        self.ImportP = tk.Button(self.MergeFrame, text="Import Points",command=lambda: Import_Points2(self,Surfaces,float(self.MergeAlpha.get())))
        self.ImportP.grid(row=0,column=2)
        self.ClearMerge = tk.Button(self.MergeFrame, text="Clear Polygon and Points",command=lambda: self.Clear_Merge())
        self.ClearMerge.grid(row=1,column=2)
        
        self.MergeFrame.grid_remove()
        self.subframes.append(self.MergeFrame)
        
        
        
        #CUT FILL FRAME
        self.CutFFrame = tk.Frame(master=self)
        self.CutFFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        
        label2 = tk.Label(self.CutFFrame, text="Max Cut:")
        label2.grid(row=0,column=0)
        self.MaxCut=tk.Entry(self.CutFFrame)
        self.MaxCut.delete(0,tk.END)
        self.MaxCut.insert(0,15)
        self.MaxCut.grid(row=0,column=1)
        
        label3 = tk.Label(self.CutFFrame, text="Max Fill:")
        label3.grid(row=1,column=0)
        self.MaxFill=tk.Entry(self.CutFFrame)
        self.MaxFill.delete(0,tk.END)
        self.MaxFill.insert(0,15)
        self.MaxFill.grid(row=1,column=1)
        
        self.DrawCutFill = tk.Button(self.CutFFrame, text="Draw Cut Fill",command=lambda: self.draw_CutFill(Surfaces))
        self.DrawCutFill.grid(row=0,column=2)
        self.DrawCutFillContours = tk.Button(self.CutFFrame, text="Draw Cut Fill Contours",command=lambda: self.draw_CutFillContours(Surfaces))
        self.DrawCutFillContours.grid(row=1,column=2)
        
        self.RemoveCutFillContours = tk.Button(self.CutFFrame, text="Remove Cut Fill Contours",command=lambda: self.Remove_CutFillContours(Surfaces))
        self.RemoveCutFillContours.grid(row=2,column=2)
        
        self.CutFFrame.grid_remove()
        self.subframes.append(self.CutFFrame)
        
        
        
        #SLope FRAME      
        self.SlopeFrame = tk.Frame(master=self)
        self.SlopeFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        
        label2 = tk.Label(self.SlopeFrame, text="Max Slope:")
        label2.grid(row=3,column=0)
        self.MaxSlope=tk.Entry(self.SlopeFrame)
        self.MaxSlope.delete(0,tk.END)
        self.MaxSlope.insert(0,6)
        self.MaxSlope.grid(row=3,column=1)
        
        label3 = tk.Label(self.SlopeFrame, text="Min Slope:")
        label3.grid(row=2,column=0)
        self.MinSlope=tk.Entry(self.SlopeFrame)
        self.MinSlope.delete(0,tk.END)
        self.MinSlope.insert(0,2.75)
        self.MinSlope.grid(row=2,column=1)
        
        self.DrawSlope = tk.Button(self.SlopeFrame, text="Draw Slope Categorized",command=lambda: self.draw_Slope(Surfaces))
        self.DrawSlope.grid(row=2,column=3,columnspan=2,sticky='nesw')
        self.DrawSlopeContinuous = tk.Button(self.SlopeFrame, text="Draw Slope Continuous",command=lambda: self.draw_Slope2(Surfaces))
        self.DrawSlopeContinuous.grid(row=0,column=3,columnspan=2,sticky='nesw')
        
        label13 = tk.Label(self.SlopeFrame, text="Slope Categories:")
        label13.grid(row=3,column=3,pady=5)
        self.SlopeCat=tk.Entry(self.SlopeFrame)
        self.SlopeCat.delete(0,tk.END)
        self.SlopeCat.insert(0,0)
        self.SlopeCat.insert(1,',')
        self.SlopeCat.insert(2,2.5)
        self.SlopeCat.insert(3,',')
        self.SlopeCat.insert(4,3)
        self.SlopeCat.insert(5,',')
        self.SlopeCat.insert(6,4)
        self.SlopeCat.insert(7,',')
        self.SlopeCat.insert(8,5)
        
        self.SlopeCat.grid(row=3,column=4)
        
        
        self.ShowAllSlopes = tk.IntVar()
        self.ShowAllSlopesButton = tk.Checkbutton(self.SlopeFrame, variable = self.ShowAllSlopes,text = "Show only Design Slopes", onvalue = 1, offvalue=0)
        self.ShowAllSlopesButton.grid(row=0,column=0,columnspan=2)
        self.ShowAllSlopesButton.select()
        
        #Dividers
        self.divider1 = Separator(self.SlopeFrame, orient="vertical").grid(column=2, row=0, sticky="ns",rowspan=4, padx=3) 
        self.divider2 = Separator(self.SlopeFrame, orient="horizontal").grid(column=3, row=1, sticky="ew",columnspan=2, pady=3) 

        

        
        self.SlopeFrame.grid_remove()
        self.subframes.append(self.SlopeFrame)

        
        #Main Menu for Polygon Selection
        self.PolygonFrame = tk.Frame(master=self)
        self.PolygonFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        self.PolygonFrame.grid_columnconfigure(9,weight=1) # the text and entry frames column
        self.CutPw=None
        self.FillPw=None
        self.AreaPolyw=None
        self.DrainPolyw=None

        bwidth=20
        
        labelpcut = tk.Label(self.PolygonFrame, text="Cut:")
        self.CutP=tk.Entry(self.PolygonFrame,width=8)
        self.CutP.insert(0,0.0)
        
        labelpfill = tk.Label(self.PolygonFrame, text="Fill:")
        self.FillP=tk.Entry(self.PolygonFrame,width=8)
        self.FillP.insert(0,0.0)
        
        
        labelparea = tk.Label(self.PolygonFrame, text="Area:")
        self.AreaPoly=tk.Entry(self.PolygonFrame,width=8)
        self.AreaPoly.insert(0,0.0)
        
        labeldrainage = tk.Label(self.PolygonFrame, text="Cut/Fill Area:")
        self.DrainPoly=tk.Entry(self.PolygonFrame,width=8)
        self.DrainPoly.insert(0,0.0) #self.ActivePolygon.density
        
        
        self.buttonPolyLock = tk.Button(self.PolygonFrame, width=bwidth, text="Toggle (Unlocked)",command=lambda: self.ActivePolygon.ToggleLock(Surfaces,self))
        self.buttonPolyDel = tk.Button(self.PolygonFrame, width=bwidth, text="Delete",command=lambda: self.Delete_Poly(Surfaces))
        
        self.OpenWindowButton = tk.Button(self.PolygonFrame, width=bwidth, text="Open Window",command=self.open_poly_window)
        self.OpenWindowLabel = tk.Label(self.PolygonFrame, text="Window Opened", relief="solid", background="#a9a9a9")
        
        self.buttonPolyLock.grid(row=2,column=2,columnspan=2, sticky='nesw',padx=1,pady=1,rowspan=2)
        self.buttonPolyDel.grid(row=2,column=4,columnspan=2, sticky='nesw',padx=1,pady=1,rowspan=2)
        labelpcut.grid(row=0,column=2,sticky='ew',padx=1,pady=1)
        self.CutP.grid(row=1,column=2,sticky='ew',padx=1,pady=1)
        labelpfill.grid(row=0,column=3,sticky='ew',padx=1,pady=1)
        self.FillP.grid(row=1,column=3,sticky='ew',padx=1,pady=1)
        labelparea.grid(row=0,column=4,sticky='ew',padx=1,pady=1)
        self.AreaPoly.grid(row=1,column=4,sticky='ew',padx=1,pady=1)
        labeldrainage.grid(row=0,column=5,sticky='ew',padx=1,pady=1)
        self.DrainPoly.grid(row=1,column=5,sticky='ew',padx=1,pady=1)
    
        self.OpenWindowButton.grid(row=0,column=6,columnspan=2,rowspan=4,sticky='nesw',padx=1,pady=1)
        self.OpenWindowButton.config(height=4)
        
        self.PolygonFrame.grid_remove()
        self.subframes.append(self.PolygonFrame)
        
        
        
        
        #Constant frame
        self.constantFrame = tk.Frame(master=self)
        self.constantFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        label2 = tk.Label(self.constantFrame, text="Elevation:")
        label2.grid(row=0,column=2)
        self.constant=tk.Entry(self.constantFrame)
        self.constant.delete(0,tk.END)
        self.constant.grid(row=0,column=3)
        self.constantVar=tk.StringVar()
        self.constantVar.set("Unconstrained")
        self.ConstantOptions=tk.OptionMenu(self.constantFrame,self.constantVar,"Unconstrained","Above Design","Below Design","Above Survey else Survey","Below Survey else Survey","Set zero to 1","Add Constant to Survey","Set to Lowest","Set to Highest","Set to Survey if Below Elevation")
        self.ConstantOptions.grid(row=1,column=1)
        self.ConstantOptions.config(relief='solid',borderwidth=1)
        label2 = tk.Label(self.constantFrame, text="Method:")
        label2.grid(row=1,column=0)
        self.constantFrame.grid_remove()   
        self.subframes.append(self.constantFrame)
        
        #SlopeIm frame
        # self.SlopeFrame = tk.Frame(master=self)
        # self.SlopeFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        # label2 = tk.Label(self.SlopeFrame, text="Elevation:")
        # label2.grid(row=0,column=2)
        # self.Slope=tk.Entry(self.SlopeFrame)
        # self.Slope.delete(0,tk.END)
        # self.Slope.grid(row=0,column=3)
        # self.SVar=tk.StringVar()
        # self.ConstantOptions=tk.OptionMenu(self.SlopeFrame,self.SVar,"Unconstrained","Above Design","Below Design","Above Survey else Survey","Below Survey else Survey")
        # # self.ModExp.insert(0,self.ModifyExp_var.get())
        # self.SlopeFrame.grid_remove()   
        # self.subframes.append(self.SlopeFrame)
        
        #TFIm frame
        self.TFFrame = tk.Frame(master=self)
        self.TFFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        label2 = tk.Label(self.TFFrame, text="Elevation:")
        label2.grid(row=0,column=2)
        self.TF=tk.Entry(self.TFFrame)
        self.TF.delete(0,tk.END)
        self.TF.grid(row=0,column=3)
        self.TFVar=tk.StringVar()
        self.TFOptions=tk.OptionMenu(self.TFFrame,self.TFVar,"Unconstrained","Above Design","Below Design","Above Survey else Survey","Below Survey else Survey")
        self.TFOptions.config(relief='solid',borderwidth=1)
        # self.ModExp.insert(0,self.ModifyExp_var.get())
        self.TFFrame.grid_remove()   
        self.subframes.append(self.TFFrame)
        
        #TFIm frame
        self.CutFrame = tk.Frame(master=self)
        self.CutFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        label2 = tk.Label(self.CutFrame, text="Elevation:")
        label2.grid(row=0,column=2)
        self.Cutv=tk.Entry(self.CutFrame)
        self.Cutv.delete(0,tk.END)
        self.Cutv.grid(row=0,column=3)
        self.CutVar=tk.StringVar()
        self.CutOptions=tk.OptionMenu(self.TFFrame,self.TFVar,"Unconstrained","Above Design","Below Design","Above Survey else Survey","Below Survey else Survey")
        self.CutOptions.config(relief='solid',borderwidth=1)
        # self.ModExp.insert(0,self.ModifyExp_var.get())
        self.CutFrame.grid_remove()   
        self.subframes.append(self.CutFrame)
        
        #Smooth frame
        self.smoothFrame = tk.Frame(master=self)
        self.smoothFrame.grid(row=0,column=0,columnspan=12,rowspan=4,sticky=tk.NSEW)
        label1 = tk.Label(self.smoothFrame, text="")
        label1.grid(row=0,column=0,columnspan=6)
        
        label4 = tk.Label(self.smoothFrame, text="")
        label4.grid(row=3,column=0,columnspan=6)
        
        
        self.sliderup= tk.Scale(self.smoothFrame,from_=0,to=1,resolution=0.01,orient='horizontal',length=200,label = "Up Multiplier")
        self.sliderup.grid(row=1,column=0,rowspan=2)
        
        self.sliderdwn= tk.Scale(self.smoothFrame,from_=0,to=1,resolution=0.01,orient='horizontal',length=200,label = "Down Multiplier")
        self.sliderdwn.grid(row=1,column=1,rowspan=2)
        
        self.sliderNeigh= tk.Scale(self.smoothFrame,from_=1,to=10,resolution=1.0,orient='horizontal',length=100,label = "Neighbourhood")
        self.sliderNeigh.grid(row=1,column=2,rowspan=2)
        
        self.divider1 = Separator(self.smoothFrame, orient="vertical").grid(column=3, row=1, sticky="ns",rowspan=2, padx=3) 

        
        label2 = tk.Label(self.smoothFrame, text="Exponent:")
        label2.grid(row=1,column=4)
        self.SmoothExp=tk.Entry(self.smoothFrame)
        self.SmoothExp.delete(0,tk.END)
        self.SmoothExp.insert(0,1.0)
        # self.SmoothExp.insert(0,self.SmoothExp_var.get())
        self.SmoothExp.grid(row=1,column=5)
                    
        label3 = tk.Label(self.smoothFrame, text="Smooth iterations:")
        label3.grid(row=2,column=4)
        self.SmoothIter=tk.Entry(self.smoothFrame)
        self.SmoothIter.delete(0,tk.END)
        self.SmoothIter.insert(0,100)
        # self.SmoothIter.insert(0,self.SmoothIter_var.get())
        self.SmoothIter.grid(row=2,column=5)
        
        self.divider2 = Separator(self.smoothFrame, orient="vertical").grid(column=6, row=1, sticky="ns",rowspan=2, padx=3) 
        
        self.SmoothVar=tk.StringVar()
        self.SmoothVar.set("Unconstrained")
        self.SmoothOptions=tk.OptionMenu(self.smoothFrame,self.SmoothVar,"Unconstrained","Above Survey")
        self.SmoothOptions.config(relief='solid',borderwidth=1,width=20,height=2)
        self.SmoothOptions.grid(row=1,column=7,rowspan=2,padx=3,pady=1)
        
        self.smoothFrame.grid_remove()
        self.subframes.append(self.smoothFrame)
        
        # shapeframe
        self.shapeFrame = tk.Frame(master=self)
        self.shapeFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        
        self.constant_slope = tk.Label(self.shapeFrame, text='       Constant Slope:       ')
        self.constant_slope.grid(row=1,column=3,ipadx=20,padx=0.5,pady=0.5,sticky='nesw')
        self.ConstantSlope_off = tk.Label(self.shapeFrame, text="",background='#a9a9a9',relief='sunken',border=0.5)
        # self.ConstantSlope_off.grid(row=2,column=3,ipadx=20,padx=0.5,pady=0.5,sticky='nesw')
        
        self.ConstantSlope=tk.Entry(self.shapeFrame)
        self.ConstantSlope.insert(0,5)
        self.ConstantSlope.grid(row=2,column=3,ipadx=20,padx=0.5,pady=0.5,sticky='nesw')
        
        self.cutoff_elevation = tk.Label(self.shapeFrame, text="       Cutoff Elevation:       ")
        self.cutoff_elevation.grid(row=1,column=4,ipadx=20,padx=0.5,pady=0.5,sticky='nesw')
        self.ShapeCutoff_off= tk.Label(self.shapeFrame, text="",background='#a9a9a9',relief='sunken',border=0.5)
        self.ShapeCutoff_off.grid(row=2,column=4,ipadx=20,pady=0.5,padx=0.5,sticky='nesw')
        
        self.ShapeCutoff=tk.Entry(self.shapeFrame)
        self.ShapeCutoff.insert(0,5)
        
        
        self.exponent_label = tk.Label(self.shapeFrame, text="Exponent:")
        self.exponent_label.grid(row=1,column=1,ipadx=20,sticky='ew')
        self.ShapeExp=tk.Entry(self.shapeFrame)
        self.ShapeExp.insert(0,1.0)
        self.ShapeExp.grid(row=2,column=1,ipadx=20,sticky='ew')
                    
        self.shaping_iterations = tk.Label(self.shapeFrame, text="Shaping iterations:")
        self.shaping_iterations.grid(row=1,column=2,ipadx=20,sticky='ew')
        self.ShapeIter=tk.Entry(self.shapeFrame)
        self.ShapeIter.insert(0,100)
        self.ShapeIter.grid(row=2,column=2,ipadx=20,sticky='ew')
        self.shapeVar=tk.StringVar()
        self.shapeVar.set("Shape cut/fill balanced")
        self.ShapeOptions=tk.OptionMenu(self.shapeFrame,self.shapeVar,"Shape cut/fill balanced","Shape cut","Shape fill","Shape cut/fill balanced to Profile","Shape cut to Profile","Shape fill to Profile","Shape fill above Survey",'Shape cut/fill balanced to Benches','Shape fill to Benches','Shape cut to Benches','Shape fill all in cut', command=self.update_shape_GUI)
        self.ShapeOptions.config(relief='solid',borderwidth=1)
        self.ShapeOptions.grid(row=0,column=1,columnspan=2,ipadx=20,sticky='ew')
        
        self.shapeVar2_options = ["Unconstrained","Above Survey","Below Elevation"]
        self.shapeVar2=tk.StringVar()
        self.shapeVar2.set("Unconstrained")
        self.ShapeOptions=tk.OptionMenu(self.shapeFrame,self.shapeVar2,*self.shapeVar2_options,command=self.update_shape_GUI)
        self.ShapeOptions.config(relief='solid',borderwidth=1)
        self.ShapeOptions.grid(row=0,column=3,columnspan=2,ipadx=20,sticky='ew')
        
        self.shapeFrame.grid_remove()
        self.subframes.append(self.shapeFrame)
        
        #Add Line Frame
        #Subframe 1     
        self.linetypes=("Quadratic Spline","Straight line","Radius and Tangent")
        self.LineVar=tk.StringVar()
        self.LineVar.set("Quadratic Spline")
        self.AddLineFrame= tk.Frame(master=self)
        self.AddLineFrame.grid(row=0,column=0,columnspan=10,rowspan=4,sticky=tk.NSEW)
        self.LineOptions=tk.OptionMenu(self.AddLineFrame,
                                       self.LineVar,
                                       *self.linetypes,
                                       command=self.option_changed)
        self.LineOptions.config(width=20, height=2, relief='solid',borderwidth=1)
        self.LineOptions.grid(row=1,column=0, rowspan=2, sticky='nesw')
        
        #Dividers and Fillers
        # self.divider = Separator(self.AddLineFrame, orient="vertical").grid(column=1, row=1, sticky="ns",rowspan=2,padx=3)
        self.fillerlabel1 = tk.Label(self.AddLineFrame, text="").grid(row=0,column=0,sticky='nesw')
        self.fillerlabel2 = tk.Label(self.AddLineFrame, text="").grid(row=3,column=0,sticky='nesw')
        
        
        self.AddLineFrame.grid_remove()
        self.subframes.append(self.AddLineFrame)
        
        
        #Subframe 1
        self.AddLineFrame1= tk.Frame(master=self)
        self.AddLineFrame1.grid(row=0,column=0,columnspan=10,rowspan=4,sticky=tk.NSEW)
        self.LineOptions1=tk.OptionMenu(self.AddLineFrame1,
                                       self.LineVar,
                                       *self.linetypes,
                                       command=self.option_changed)
        self.LineOptions1.config(width=20, height=2, relief='solid',borderwidth=1)
        self.LineOptions1.grid(row=1,column=0, rowspan=2, sticky='nesw')
        
       
        label9 = tk.Label(self.AddLineFrame1, text="Maximum Radius")
        label9.grid(row=1,column=2)
        self.maxrad=tk.Entry(self.AddLineFrame1)
        self.maxrad.insert(0,50)
        self.maxrad.grid(row=2,column=2)
        
        label10 = tk.Label(self.AddLineFrame1, text="Step Size")
        label10.grid(row=1,column=3)
        self.steprad=tk.Entry(self.AddLineFrame1)
        self.steprad.insert(0,10)
        self.steprad.grid(row=2,column=3)
        
        #Dividers and Fillers
        self.divider1 = Separator(self.AddLineFrame1, orient="vertical").grid(column=1, row=1, sticky="ns",rowspan=2, padx=3) 
        self.fillerlabel1 = tk.Label(self.AddLineFrame1, text="").grid(row=0,column=0,sticky='nesw')
        self.fillerlabel2 = tk.Label(self.AddLineFrame1, text="").grid(row=3,column=0,sticky='nesw')
        
        self.AddLineFrame1.grid_remove()
        self.subframes.append(self.AddLineFrame1)
        
        
        
        #Visible Frame
        self.VisibleFrame= tk.Frame(master=self)
        self.VisibleFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        labelv = tk.Label(self.VisibleFrame, text="Target eye height:")
        labelv.grid(row=0,column=0)
        self.TargetHeight=tk.Entry(self.VisibleFrame)
        self.TargetHeight.insert(0,1.6)
        self.TargetHeight.grid(row=0,column=1)
        
        label2v = tk.Label(self.VisibleFrame, text="Observer eye height:")
        label2v.grid(row=1,column=0)
        self.ObsHeight=tk.Entry(self.VisibleFrame)
        self.ObsHeight.insert(0,0.0)
        self.ObsHeight.grid(row=1,column=1)
        
        label3v = tk.Label(self.VisibleFrame, text="Scale Height:")
        label3v.grid(row=2,column=0)
        self.ScaleHeight=tk.Entry(self.VisibleFrame)
        self.ScaleHeight.insert(0,1000.0)
        self.ScaleHeight.grid(row=2,column=1)
        
        self.VisibleFrame.grid_remove()
        self.subframes.append(self.VisibleFrame)
        # self.var=tk.IntVar()
        # self.var.set(1)
        
        
        # self.QuadraticLine=tk.Radiobutton(self.AddLineFrame,variable =self.var,value=2,text="Quadratic Spline",command=lambda: self.setLine(self.var.get())).grid(row=1,column=1)
        # self.StraightLine=tk.Radiobutton(self.AddLineFrame,variable =self.var,value=1,text="Straight line",command=lambda: self.setLine(self.var.get())).grid(row=0,column=0)
       
        
        self.grid_columnconfigure(3,weight=1) # the text and entry frames column
        self.grid_rowconfigure(10,weight=1) # all frames row_
        
        #PerFrame
        # self.PerFrame = tk.Frame(master=self)
        # self.PerFrame.grid(row=0,column=20,columnspan=4,sticky=tk.NSEW)
        # self.methodlabel = tk.Label(self.PerFrame, text="None",font='Helvetica 10 bold')
        # self.methodlabel.grid(row=0,column=0)
        # labela = tk.Label(self.PerFrame, text="Contour Interval")
        # labela.grid(row=0,column=1)
        # self.Contour_interval=tk.Entry(self.PerFrame,bg="#B0E2FF",relief='flat')
        # self.Contour_interval.insert(0,2.0)
        # self.Contour_interval.grid(row=0,column=2,sticky='nesw',pady=1)
        
        # labelc = tk.Label(self.PerFrame, text="Circle Radius")
        # labelc.grid(row=1,column=1)
        # self.Radius=tk.Entry(self.PerFrame,bg="#B0E2FF",relief='flat')
        # self.Radius.insert(0,20)
        # self.Radius.grid(row=1,column=2,sticky='nesw',pady=1)
        # labela = tk.Label(self.PerFrame, text="Cut")
        # labela.grid(row=2,column=1)
        # self.Filltxt=tk.Entry(self.PerFrame,bg="#B0E2FF",relief='flat')
        # self.Filltxt.grid(row=3,column=2,sticky='nesw',pady=1)
        
        # labelb = tk.Label(self.PerFrame, text="Fill")
        # labelb.grid(row=3,column=1,sticky='nesw',pady=1)
        # self.Cuttxt=tk.Entry(self.PerFrame,bg="#B0E2FF",relief='flat')
        # self.Cuttxt.grid(row=2,column=2)
        # self.Filltxt.delete(0,tk.END)
        # self.Filltxt.insert(0,self.fill[0])
        # self.Cuttxt.delete(0,tk.END)
        # self.Cuttxt.insert(0,self.cut[0])

        self.PerFrame = tk.Toplevel(self)
        # self.PerFrame.grid(row=0,column=20,columnspan=4,sticky=tk.NSEW)
        self.PerFrame.attributes('-topmost','true')
        self.methodlabel = tk.Label(self.PerFrame, text="None",font='Helvetica 10 bold')
        self.methodlabel.grid(row=0,column=0)
        labela = tk.Label(self.PerFrame, text="Contour Interval")
        labela.grid(row=0,column=1)
        self.Contour_interval=tk.Entry(self.PerFrame,bg="#B0E2FF",relief='flat')
        self.Contour_interval.insert(0,2.0)
        self.Contour_interval.grid(row=0,column=2,sticky='nesw',pady=1)
        
        labelc = tk.Label(self.PerFrame, text="Circle Radius")
        labelc.grid(row=1,column=1)
        self.Radius=tk.Entry(self.PerFrame,bg="#B0E2FF",relief='flat')
        self.Radius.insert(0,20)
        self.Radius.grid(row=1,column=2,sticky='nesw',pady=1)
        labela = tk.Label(self.PerFrame, text="Cut")
        labela.grid(row=2,column=1)
        self.Filltxt=tk.Entry(self.PerFrame,bg="#B0E2FF",relief='flat')
        self.Filltxt.grid(row=3,column=2,sticky='nesw',pady=1)
        
        labelb = tk.Label(self.PerFrame, text="Fill")
        labelb.grid(row=3,column=1,sticky='nesw',pady=1)
        self.Cuttxt=tk.Entry(self.PerFrame,bg="#B0E2FF",relief='flat')
        self.Cuttxt.grid(row=2,column=2)
        self.Filltxt.delete(0,tk.END)
        self.Filltxt.insert(0,self.fill[0])
        self.Cuttxt.delete(0,tk.END)
        self.Cuttxt.insert(0,self.cut[0])
           
        self.menubar = Menu(master=self)

        filemenu = Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.donothing)
        filemenu.add_command(label="Open", command=self.donothing)
        filemenu.add_command(label="Save", command=self.donothing)
        filemenu.add_command(label="Save as...", command=self.donothing)
        filemenu.add_command(label="Close", command=self.donothing)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=sys.exit)
        self.menubar.add_cascade(label="File", menu=filemenu)
        
            
            
        def write_dxf():
            print('Line ID list:')
            print(self.dxfdata[0])
            print('-------------')
            
            idlist=self.dxfdata[0]
            EdgeL=self.dxfdata[1]
            Berm1=self.dxfdata[2]
            Berm2=self.dxfdata[3]
            Base1=self.dxfdata[4]
            Center=self.dxfdata[5]
            Base2=self.dxfdata[6]
            Berm3=self.dxfdata[7]
            Berm4=self.dxfdata[8]
            EdgeR=self.dxfdata[9]
            
            write_DXF(idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR,Surfaces)
         
        
        def on_click(event):
            self.f.canvas.get_tk_widget().focus_force()

            # print(('click event',event.xdata,event.ydata))
            if self._job is None:
                self._job = app.after(self.DEBOUNCE_DUR,lambda:_on_single_click(event))
                
            if event.dblclick:
                app.after_cancel(self._job)
                self._job=None
                _on_dblclick(event)
                # print('double')
            # if event.dblclick:
            #     print("double")
        def _on_single_click(event):
            print(('click event actual',event.xdata,event.ydata))
            print('single')

            if event.inaxes is not None and event.button==1:# and not event.dblclick:
                self._job=None
                self.buttonpressed=True
                if self.presentmethod=='ReadElev':
                    self.currentElev.on_click(event)
                    self.ReadElev.append(self.currentElev)
                    self.currentElev=ElevationAnnot(self,Surfaces)
                if self.presentmethod=='DyDrop':
                    DyDroplet= Line2D([0,0], [10,10], animated=False, markerfacecolor='blue')
                    DyDropletMax= Line2D([0,0], [10,10], animated=False, color='red')
                    self.drop.append(DynamicDroplet(self,DyDroplet,DyDropletMax,Surfaces.cellsize))
                if self.presentmethod=='Measure':
                    self.Measure[-1].on_click(event)    
                if self.presentmethod=='Select Line':
                    for p in self.Lines:
                        p.select(event)
                        if p.Active:
                            self.ActiveLine=p
                            self.presentmethod='None'
                            Draw_Update(self,Surfaces)  
                if self.presentmethod=='Select Polygon':
                    for p in self.Polygons:
                        p.select(event,Surfaces,self)
                        if p.Active:
                            self.ActivePolygon=p
                            self.presentmethod='None'
                            Draw_Update(self,Surfaces)  
                if self.presentmethod=='visible':
                    self.show_Visibility(int(event.xdata),int(event.ydata))
                if self.presentmethod=='Render':
                    gen_fig(Surfaces,int(event.xdata),int(event.ydata),self.ReadElev[-1].annot.xy[1],self.ReadElev[-1].annot.xy[0],float(self.ObsHeight.get()),float(self.ScaleHeight.get()))
                if self.presentmethod=='RenderSurv':
                    gen_figSurv(Surfaces,int(event.xdata),int(event.ydata),self.ReadElev[-1].annot.xy[1],self.ReadElev[-1].annot.xy[0],float(self.ObsHeight.get()),float(self.ScaleHeight.get()))                    
                if self.presentmethod=='Shape':
                    a=self.shapeVar.get()
                    b=self.shapeVar2.get()
                    CutFillStrt(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut0,self.fill0,Surfaces.cellsize)
                    if b=='Below Elevation':
                        if a =='Shape cut/fill balanced':
                            Shape_Balanced(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                        
                        if a =='Shape cut':
                            Shape_Cut(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                        
                        if a =='Shape fill':
                            Shape_Fill_Below(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active,float(self.ShapeCutoff.get()))
                         
                    if b=='Unconstrained':
                        if a =='Shape cut/fill balanced':
                            Shape_Balanced(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                        
                        if a =='Shape cut':
                            Shape_Cut(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                        
                        if a =='Shape fill':
                            Shape_Fill(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                            
                        if a =='Shape cut/fill balanced to Profile':
                            Shape_profile(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active,self.ActiveLine.S,0.05,0.05)
                            
                        if a =='Shape fill to Profile':
                            Shape_profile(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active,self.ActiveLine.S,0.005,0.0)
                        
                        if a =='Shape cut to Profile':
                            Shape_profile(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active,self.ActiveLine.S,0.0,0.05)
                        
                        if a =='Shape fill above Survey':
                            Shape_Fill_AboveS(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                        
                        if a =='Shape cut/fill balanced to Benches':
                           Shape_Bench(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active,self.ActiveLine.BElev,self.ActiveLine.BWidth,self.ActiveLine.Bslope,0.05,0.05)
                           
                        if a =='Shape fill to Benches':
                           Shape_Bench(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active,self.ActiveLine.BElev,self.ActiveLine.BWidth,self.ActiveLine.Bslope,0.05,0.0)
                       
                        if a =='Shape cut to Benches':
                           Shape_Bench(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active,self.ActiveLine.BElev,self.ActiveLine.BWidth,self.ActiveLine.Bslope,0.0,0.05)
                        if a =='Shape fill all in cut':
                            Shape_Fill_All(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                              


                    if b=='Above Survey':
                        if a =='Shape cut/fill balanced':
                            Shape_Balanced_Above(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                        
                        if a =='Shape cut':
                            Shape_Cut_Above(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                        
                        if a =='Shape fill':
                            Shape_Fill(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                            
                        if a =='Shape cut/fill balanced to Profile':
                            Shape_profile_Above(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active,self.ActiveLine.S,0.05,0.05)
                            
                        if a =='Shape fill to Profile':
                            Shape_profile(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active,self.ActiveLine.S,0.05,0.0)
                        
                        if a =='Shape cut to Profile':
                            Shape_profile(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active,self.ActiveLine.S,0.0,0.05)
                            
                        if a =='Shape fill above Survey':
                            Shape_Fill_AboveS(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ConstantSlope.get()),float(self.ShapeExp.get()),int(self.ShapeIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)    
                    CutFillEnd(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut0,self.fill0,self.cut,self.fill,Surfaces.cellsize)        
                    
                    #Update any active polygon's cutfill
                    for p in self.Polygons:
                        if p.Active:
                            self.ActivePolygon.getpolycutfill(self,Surfaces)
                            
                    # print((self.fill[0],self.cut[0]))
                if self.presentmethod=='Smooth':
                    a=self.SmoothVar.get()
                    CutFillStrt(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut0,self.fill0,Surfaces.cellsize)
                    if a =='Unconstrained':
                        Smooth(int(event.xdata),int(event.ydata),self.circle.rad,self.sliderdwn.get(),self.sliderup.get(),float(self.sliderNeigh.get()),float(self.SmoothExp.get()),int(self.SmoothIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    if a =='Above Survey':
                        Smooth_above_Survey(int(event.xdata),int(event.ydata),self.circle.rad,self.sliderdwn.get(),self.sliderup.get(),float(self.sliderNeigh.get()),float(self.SmoothExp.get()),int(self.SmoothIter.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    CutFillEnd(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut0,self.fill0,self.cut,self.fill,Surfaces.cellsize)
                   
                    #Update any active polygon's cutfill
                    for p in self.Polygons:
                        if p.Active:
                            self.ActivePolygon.getpolycutfill(self,Surfaces) 
                            
                if self.presentmethod=='Modify':
                    CutFillStrt(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut0,self.fill0,Surfaces.cellsize)
                    Modify(int(event.xdata),int(event.ydata),self.circle.rad,float(self.ModExp.get()),float(self.slidermodup.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    CutFillEnd(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut0,self.fill0,self.cut,self.fill,Surfaces.cellsize)
                    
                    #Update any active polygon's cutfill
                    for p in self.Polygons:
                        if p.Active:
                            self.ActivePolygon.getpolycutfill(self,Surfaces) 
                            
                if self.presentmethod=='Undo':
                    CutFillStrt(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut0,self.fill0,Surfaces.cellsize)
                    Undo(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Design2,Surfaces.Dist,Surfaces.cellsize)
                    CutFillEnd(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut0,self.fill0,self.cut,self.fill,Surfaces.cellsize)
                    
                    #Update any active polygon's cutfill
                    for p in self.Polygons:
                        if p.Active:
                            self.ActivePolygon.getpolycutfill(self,Surfaces) 
                            
                if self.presentmethod=='Set Constant':
                    # print('create constant')
                    a=self.constantVar.get()
                    CutFillStrt(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut0,self.fill0,Surfaces.cellsize)
                    if a=="Unconstrained":
                        Set_ConstantAll(int(event.xdata),int(event.ydata),self.circle.rad,float(self.constant.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    if a=="Above Design":
                        Set_ConstantAbove(int(event.xdata),int(event.ydata),self.circle.rad,float(self.constant.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    if a=="Below Design":    
                        Set_ConstantBelow(int(event.xdata),int(event.ydata),self.circle.rad,float(self.constant.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    if a=="Below Survey else Survey":    
                        Set_ConstantBelowSurvey(int(event.xdata),int(event.ydata),self.circle.rad,float(self.constant.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    if a=="Above Survey else Survey":
                        # print(a)
                        Set_ConstantAboveSurvey(int(event.xdata),int(event.ydata),self.circle.rad,float(self.constant.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    if a=="Set zero to 1":
                        Set_zero_to_one(int(event.xdata),int(event.ydata),self.circle.rad,float(self.constant.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    if a=="Add Constant to Survey":
                        Add_to_Survey(int(event.xdata),int(event.ydata),self.circle.rad,float(self.constant.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    if a=="Set to Lowest":
                        Set_to_Lowest(int(event.xdata),int(event.ydata),self.circle.rad,float(self.constant.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    if a=="Set to Highest":
                        Set_to_Highest(int(event.xdata),int(event.ydata),self.circle.rad,float(self.constant.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    if a=="Set to Survey if Below Elevation":
                        Set_to_SurveyBelow(int(event.xdata),int(event.ydata),self.circle.rad,float(self.constant.get()),Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut,self.fill,Surfaces.cellsize,Surfaces.Active)
                    CutFillEnd(int(event.xdata),int(event.ydata),self.circle.rad,Surfaces.Design,Surfaces.Survey,Surfaces.Dist,self.cut0,self.fill0,self.cut,self.fill,Surfaces.cellsize)
                    
                    #Update any active polygon's cutfill
                    for p in self.Polygons:
                        if p.Active:
                            self.ActivePolygon.getpolycutfill(self,Surfaces) 
                            
# "Quadratic Spline","Straight line"
                if self.presentmethod=='Straight line' or self.presentmethod=='Quadratic Spline' or self.presentmethod=='Radius and Tangent' :
                    self.presentmethod=self.LineVar.get()
                    self.Linepoints.append([event.ydata,event.xdata])
                    if len(self.Linepoints)%2==0:
                        if self.presentmethod=='Straight line':
                            line = Line2D([self.Linepoints[-2][1],self.Linepoints[-1][1]], [self.Linepoints[-2][0],self.Linepoints[-1][0]], animated=False,marker='o', markerfacecolor='r')
                            linesp = Line2D([self.Linepoints[-2][1],self.Linepoints[-1][1]], [self.Linepoints[-2][0],self.Linepoints[-1][0]], animated=False,lw=0.0,color='k')
                            linesrt = Line2D([self.Linepoints[-2][1],self.Linepoints[-1][1]], [self.Linepoints[-2][0],self.Linepoints[-1][0]], animated=False,lw=0.0,color='k')
                            p = LineLinear(self, line,linesp,linesrt,Surfaces,self.dot,self.LineID,'linear',5,1)
                            self.Lines.append(p)
                            self.LineID+=1
                        if self.presentmethod=='Quadratic Spline':
                            line = Line2D([self.Linepoints[-2][1],self.Linepoints[-1][1]], [self.Linepoints[-2][0],self.Linepoints[-1][0]], animated=False,marker='o', markerfacecolor='r')
                            linesp = Line2D([self.Linepoints[-2][1],self.Linepoints[-1][1]], [self.Linepoints[-2][0],self.Linepoints[-1][0]], animated=False,lw=0.8,color='white')
                            linesrt = Line2D([self.Linepoints[-2][1],self.Linepoints[-1][1]], [self.Linepoints[-2][0],self.Linepoints[-1][0]], animated=False,lw=0.0,color='white')
                            p = LineLinear(self, line,linesp,linesrt,Surfaces,self.dot,self.LineID,'quadratic',5,1)
                            self.Lines.append(p)
                            self.LineID+=1
                        if self.presentmethod=='Radius and Tangent':
                            print('Radius and Tangent Mode')
                            line = Line2D([self.Linepoints[-2][1],self.Linepoints[-1][1]], [self.Linepoints[-2][0],self.Linepoints[-1][0]], animated=False,marker='o', markerfacecolor='r')
                            linesp = Line2D([self.Linepoints[-2][1],self.Linepoints[-1][1]], [self.Linepoints[-2][0],self.Linepoints[-1][0]], animated=False,lw=0.0,color='white')
                            linesrt = Line2D([self.Linepoints[-2][1],self.Linepoints[-1][1]], [self.Linepoints[-2][0],self.Linepoints[-1][0]], animated=False,lw=0.8,color='white')
                            p = LineLinear(self, line,linesp,linesrt,Surfaces,self.dot,self.LineID,'radius',5,1)
                            self.Lines.append(p)
                            self.LineID+=1
                        
                        
                        p.initial_distance()
                        p.UpdateSinitial(1)
                        Draw_Update(self,Surfaces)
                        self.presentmethod=='None'
                        
                if self.presentmethod=='Add Polygon':
                    self.Polypoints.append([event.ydata,event.xdata])
                    if len(self.Polypoints)%3==0:
                        print('Adding Polygon')
                        poly = Polygon([[self.Polypoints[-3][1],self.Polypoints[-3][0]],[self.Polypoints[-2][1],self.Polypoints[-2][0]], [self.Polypoints[-1][1],self.Polypoints[-1][0]],[self.Polypoints[-3][1],self.Polypoints[-3][0]]], animated=False,alpha=0.2)
                        p = PolygonInteractor(self, poly,self.polyID)
                        self.Polygons.append(p)
                            
                        Draw_Update(self,Surfaces)        
                        self.Set_to_none()
                        self.polyID+=1
                    self.presentmethod=='None'

                if self.presentmethod!='Add Polygon' and self.presentmethod!='DyDrop' and self.presentmethod!='Measure' and self.presentmethod!='Straight line' and self.presentmethod!='None' and self.presentmethod!='Quadratic Spline' and self.presentmethod!='Select Line'and self.presentmethod!='ReadElev' and self.presentmethod!='Radius and Tangent':            
                    Draw_contours(self,Surfaces)
                    self.Filltxt.delete(0,tk.END)
                    self.Filltxt.insert(0,int(self.fill[0]))
                    self.Cuttxt.delete(0,tk.END)
                    self.Cuttxt.insert(0,int(-1*self.cut[0]))
                if self.ActiveLine is not None:
                    self.ActiveLine.button_press_callback(event)
                if self.ActivePolygon is not None:
                    # print(len(self.polyinfo))
                    if len(self.polyinfo)>0:
                        # print('launching')
                        self.ActivePolygon.updatecutfill(Surfaces,self.Lines)
                        self.polyinfo[-1].updateInfo(self.ActivePolygon)
                    self.ActivePolygon.button_press_callback(event)
            # ThreadedTask(self.queue).start()
            # self.master.after(100, self.process_queue)
        
                
        def _on_dblclick(event):
            if event.inaxes is not None and event.button==1:# and event.dblclick:
                lineselected=False
                polygonselected=False
                
                if self.ActiveLine is not None:
                    self.ActiveLine.SlopeL = self.SlopeL.get()
                    self.ActiveLine.WidthL = self.WidthL.get()
                    self.ActiveLine.SlopeLC = self.SlopeLC.get()
                    self.ActiveLine.DepthLC = self.DepthLC.get()
                    self.ActiveLine.WidthB = self.WidthB.get()
                    self.ActiveLine.SlopeRC = self.SlopeRC.get()
                    self.ActiveLine.DepthRC = self.DepthRC.get()
                    self.ActiveLine.WidthBR = self.WidthBR.get()
                    self.ActiveLine.SlopeR = self.SlopeR.get()
                    
                self.ActiveLine=None
                self.ActivePolygon=None
                for p in self.Lines:
                    p.select(event)
                    if p.Active:
                        lineselected=True
                        self.ActiveLine=p
                        self.presentmethod='None'
                        self.Set_to_SelectLine()
                        self.Linepoints=[]
                
                for p in self.Polygons:
                        p.deselect(event,Surfaces,self)   
                        print(p.Active)
                if not lineselected:
                    # print('polygon')
                    for p in self.Polygons:
                        p.select(event,Surfaces,self)
                        print(p.Active)
                        if p.Active:
                            polygonselected=True
                            self.ActivePolygon=p
                            self.presentmethod='None'
                            self.Set_to_SelectPolygon()
                            self.Polypoints=[]
            
                Draw_Update(self,Surfaces)  

        def on_motion(event):
            if event.inaxes is not None and self.circle is not None:
                self.circle.motion_notify_callback(event)
                if self.presentmethod=='DyDrop':
                    self.drop[-1].motion_notify_callback(event,self.Aspect,self.Slope)
                if self.ActiveLine is not None:
                    self.ActiveLine.motion_notify_callback(event)
                if self.ActivePolygon is not None:
                    self.ActivePolygon.motion_notify_callback(event)
                if self.presentmethod=='ReadElev':
                    self.currentElev.motion_notify_callback(event)
                    # self.ReadElev[-1].motion_notify_callback(event)
                if self.presentmethod=='Measure':
                    self.Measure[-1].motion_notify_callback(event,Surfaces)
                if self.presentmethod!='ReadElev':
                    try:
                        self.currentElev.remover()
                        Draw_Update(self,Surfaces) 
                    except:
                        pass
                    self.currentElev=None

        def button_release(event):
            self.buttonpressed=False
            if event.inaxes is not None:
                self.buttonpressed=False
                if self.ActiveLine is not None:
                    self.ActiveLine.button_release_callback(event)
                if self.ActivePolygon is not None:
                    self.ActivePolygon.button_release_callback(event,Surfaces,self)
                    # print("button released")
                axeschange2()
                
            
       
        
        def key_press(event):
            if event.inaxes is not None:
                if self.ActiveLine is not None:
                    self.ActiveLine.key_press_callback(event)
                    # self.f.canvas.draw_idle()
                    Draw_Update(self,Surfaces)
                if self.ActivePolygon is not None:
                    self.ActivePolygon.key_press_callback(event)
                    Draw_Update(self,Surfaces)
        
        def zoom_fun(event):
            if self.Radius.get() !='':
                if abs(float(self.Radius.get())-self.circle.rad)>2:
                    self.circle.Radius( float(self.Radius.get())-self.circle.rad,Surfaces.cellsize)
            if event.button == 'up':
                self.circle.Radius( -1,Surfaces.cellsize)
            if event.button == 'down':
                self.circle.Radius( 1,Surfaces.cellsize)
            self.Radius.delete(0,tk.END)
            self.Radius.insert(0,self.circle.rad)
        
        # def on_resize(event):
        #     print("resized")
        
        def axeschange2():
            # print('axes2')
            self.axesupdate=False
            if not self.notPlotted:
                if int(self.a.get_xlim()[0]) !=self.xlim[0] or int(self.a.get_xlim()[1]) !=self.xlim[1]:
                    self.xlim=[max(0,int(self.a.get_xlim()[0])),min(Surfaces.Design.shape[1],int(self.a.get_xlim()[1]))]
                    self.a.set_xlim(int(self.a.get_xlim()[0]),int(self.a.get_xlim()[1]))
                    self.ylim=[max(0,int(self.a.get_ylim()[0])),min(Surfaces.Design.shape[0],int(self.a.get_ylim()[1]))]
                    self.a.set_ylim(int(self.a.get_ylim()[0]),int(self.a.get_ylim()[1]))
                    Draw_contours(self,Surfaces)
            # self.axesupdate=True
                        
        def axeschange(event):
            # print('axes')
            if not self.buttonpressed and not self.notPlotted and self.axesupdate:
                if int(self.a.get_xlim()[0]) !=self.xlim[0] or int(self.a.get_xlim()[1]) !=self.xlim[1]:
                    self.xlim=[max(0,int(self.a.get_xlim()[0])),min(Surfaces.Design.shape[1],int(self.a.get_xlim()[1]))]
                    self.a.set_xlim(int(self.a.get_xlim()[0]),int(self.a.get_xlim()[1]))
                    self.ylim=[max(0,int(self.a.get_ylim()[0])),min(Surfaces.Design.shape[0],int(self.a.get_ylim()[1]))]
                    self.a.set_ylim(int(self.a.get_ylim()[0]),int(self.a.get_ylim()[1]))
                    Draw_contours(self,Surfaces)
                
            
        self.f = Figure()
        # self.f.protocol("WM_DELETE_WINDOW",lambda: self.on_closing2())
        self.interval=2
        self.a = self.f.add_subplot(111,facecolor='black')
        self.a.axis('scaled')
        self.levels=0
        self.p = []
        self.a.axis('off')
        self.a.axis('scaled')
        self.cid=self.a.callbacks.connect('ylim_changed',axeschange)
        # self.cid=self.a.callbacks.connect('ylim_changed',self.axeschange)
        # self.a.set_facecolor('black')
        self.canvas = FigureCanvasTkAgg(self.f, self)
        self.f.canvas.get_tk_widget().focus_force()
        self.f.patch.set_facecolor('black')
        self.canvas.callbacks.connect('button_press_event', on_click)
        self.canvas.callbacks.connect('button_release_event', button_release)
        self.canvas.callbacks.connect('motion_notify_event', on_motion)
        self.canvas.callbacks.connect('scroll_event',zoom_fun)
        # self.canvas.callbacks.connect('resize_event',on_resize)
        self.f.canvas.get_tk_widget().bind('<Button-3>',self.popup)
        self.canvas.callbacks.connect('key_press_event', key_press)
        self.canvas.get_tk_widget().grid(row=10, column=0,columnspan=30,ipadx=40,ipady=20,sticky=tk.NSEW)
        toolbarFrame = tk.Frame(master=self)
        toolbarFrame.grid(row=11,column=0,columnspan=8,sticky=tk.NSEW)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbarFrame)
        self.f.subplots_adjust(left=0.1, right=0.9, top=0.99, bottom=0.01)
        self.canvas.draw()

    def option_changed(self, *args):
            self.Set_to_AddLine()
    
    def changeframe(self, *args):
        self.setpoly()
    
    def open_poly_window(self, *args):
        self.PolygonWindowPopUp()
    
    def update_shape_GUI(self, *args):
        a=self.shapeVar.get()
        b=self.shapeVar2.get()
        
        self.ShapeOptions.grid_remove()
        self.ConstantSlope_off.grid_forget()
        self.ConstantSlope.grid_forget()
        self.ShapeCutoff.grid_forget()
        self.ShapeCutoff_off.grid_forget()
        
        if a=="Shape cut/fill balanced to Profile" or a=="Shape cut to Profile" or a=="Shape fill to Profile":
            self.ShapeCutoff_off.grid(row=2,column=4,ipadx=20,pady=0.5,padx=0.5,sticky='nesw')
            self.ConstantSlope_off.grid(row=2,column=3,ipadx=20,padx=0.5,pady=0.5,sticky='nesw')
            
            self.shapeVar2_options=["Unconstrained","Above Survey"]
            self.shapeVar2=tk.StringVar()
            if b=="Above Survey":
                self.shapeVar2.set("Above Survey")
            else:
                self.shapeVar2.set("Unconstrained")
            self.ShapeOptions=tk.OptionMenu(self.shapeFrame,self.shapeVar2,*self.shapeVar2_options,command=self.update_shape_GUI)
            self.ShapeOptions.config(relief='solid',borderwidth=1)
            self.ShapeOptions.grid(row=0,column=3,columnspan=2,ipadx=20,sticky='ew')
            
            
        elif a=='Shape cut/fill balanced to Benches' or a=='Shape fill to Benches' or a=='Shape cut to Benches':
            self.ShapeCutoff_off.grid(row=2,column=4,ipadx=20,pady=0.5,padx=0.5,sticky='nesw')
            self.ConstantSlope_off.grid(row=2,column=3,ipadx=20,padx=0.5,pady=0.5,sticky='nesw')
            
            self.shapeVar2_options=["Unconstrained"]
            self.shapeVar2=tk.StringVar()
            self.shapeVar2.set("Unconstrained")
            self.ShapeOptions=tk.OptionMenu(self.shapeFrame,self.shapeVar2,*self.shapeVar2_options,command=self.update_shape_GUI)
            self.ShapeOptions.config(relief='solid',borderwidth=1)
            self.ShapeOptions.grid(row=0,column=3,columnspan=2,ipadx=20,sticky='ew')
            
        else:   
            self.ConstantSlope.grid(row=2,column=3,ipadx=20,padx=0.5,pady=0.5,sticky='nesw')
            if a=="Shape fill" and b=="Below Elevation":
                self.ShapeCutoff.grid(row=2,column=4,ipadx=20,pady=0.5,padx=0.5,sticky='nesw')
            else:
                self.ShapeCutoff_off.grid(row=2,column=4,ipadx=20,pady=0.5,padx=0.5,sticky='nesw')
                
                
            self.shapeVar2_options=["Unconstrained","Above Survey","Below Elevation"]
            self.shapeVar2=tk.StringVar()
            if b=="Above Survey":
                self.shapeVar2.set("Above Survey")
            elif b=="Below Elevation":
                self.shapeVar2.set("Below Elevation")
            else:
                self.shapeVar2.set("Unconstrained")
            self.ShapeOptions=tk.OptionMenu(self.shapeFrame,self.shapeVar2,*self.shapeVar2_options,command=self.update_shape_GUI)
            self.ShapeOptions.config(relief='solid',borderwidth=1)
            self.ShapeOptions.grid(row=0,column=3,columnspan=2,ipadx=20,sticky='ew')    
                
    
    def recenter(self):
        self.f.subplots_adjust(left=0.1,  top=1.0, bottom=0.01)
        self.canvas.draw_idle()
       
    def Delete_Line(self,Surfaces):
        idlist=self.dxfdata[0]
        EdgeL=self.dxfdata[1]
        Berm1=self.dxfdata[2]
        Berm2=self.dxfdata[3]
        Base1=self.dxfdata[4]
        Center=self.dxfdata[5]
        Base2=self.dxfdata[6]
        Berm3=self.dxfdata[7]
        Berm4=self.dxfdata[8]
        EdgeR=self.dxfdata[9]
        
        (idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR) = self.ActiveLine.DeleteDXF(self,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR)
        
        
        self.ActiveLine.delete_l()
        self.Lines.remove(self.ActiveLine)
        self.ActiveLine=None
        self.presentmethod='None'
        for s in self.subframes:
            s.grid_forget()
        Draw_Update(self,Surfaces)
        
    def Delete_Poly(self,Surfaces):
        self.ActivePolygon.delete_p()
        self.Polygons.remove(self.ActivePolygon)
        self.ActivePolygon=None
        self.presentmethod='None'
        for s in self.subframes:
            s.grid_forget()
        Draw_Update(self,Surfaces)
        
    
    def Create_Ridges(self,Surfaces):
        Surfaces.Design=self.ActiveLine.Createridges(Surfaces)
        Draw_contours(self,Surfaces)
        Draw_Update(self,Surfaces)
        
    def Create_CanalCF(self,Surfaces,lineOptV):
       
        dstep=-0.1
        check=-1
        
        idlist=self.dxfdata[0]
        EdgeL=self.dxfdata[1]
        Berm1=self.dxfdata[2]
        Berm2=self.dxfdata[3]
        Base1=self.dxfdata[4]
        Center=self.dxfdata[5]
        Base2=self.dxfdata[6]
        Berm3=self.dxfdata[7]
        Berm4=self.dxfdata[8]
        EdgeR=self.dxfdata[9]
        
        # for i in range (0,30):
        #     idlist=self.dxfdata[0]
        #     EdgeL=self.dxfdata[1]
        #     Berm1=self.dxfdata[2]
        #     Berm2=self.dxfdata[3]
        #     Base1=self.dxfdata[4]
        #     Center=self.dxfdata[5]
        #     Base2=self.dxfdata[6]
        #     Berm3=self.dxfdata[7]
        #     Berm4=self.dxfdata[8]
        #     EdgeR=self.dxfdata[9]
        #     (idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR,cut,fill) = self.ActiveLine.CreateCanalBalanced(Surfaces,self,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR)
        #     if (cut-fill)*check>0:
        #         dstep=-0.5*dstep
        #         check=-check
        #     depthbelow=float(self.depthBelow.get())
        #     print((depthbelow,dstep,cut,fill))
        #     self.depthBelow.delete(0,tk.END)
        #     self.depthBelow.insert(0,depthbelow+dstep)
        # CreateCanalDendritic
        # (idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR) = self.ActiveLine.CreateCanalDendritic(Surfaces,self,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR)
    
        (idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR) = self.ActiveLine.CreateCanalCUTFILL(Surfaces,self,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR,lineOptV)
        
        Draw_contours(self,Surfaces)
        Draw_Update(self,Surfaces)
        
    def Create_Canal(self,Surfaces,lineOptV):
       
        dstep=-0.1
        check=-1
        
        idlist=self.dxfdata[0]
        EdgeL=self.dxfdata[1]
        Berm1=self.dxfdata[2]
        Berm2=self.dxfdata[3]
        Base1=self.dxfdata[4]
        Center=self.dxfdata[5]
        Base2=self.dxfdata[6]
        Berm3=self.dxfdata[7]
        Berm4=self.dxfdata[8]
        EdgeR=self.dxfdata[9]
        
        # for i in range (0,30):
        #     idlist=self.dxfdata[0]
        #     EdgeL=self.dxfdata[1]
        #     Berm1=self.dxfdata[2]
        #     Berm2=self.dxfdata[3]
        #     Base1=self.dxfdata[4]
        #     Center=self.dxfdata[5]
        #     Base2=self.dxfdata[6]
        #     Berm3=self.dxfdata[7]
        #     Berm4=self.dxfdata[8]
        #     EdgeR=self.dxfdata[9]
        #     (idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR,cut,fill) = self.ActiveLine.CreateCanalBalanced(Surfaces,self,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR)
        #     if (cut-fill)*check>0:
        #         dstep=-0.5*dstep
        #         check=-check
        #     depthbelow=float(self.depthBelow.get())
        #     print((depthbelow,dstep,cut,fill))
        #     self.depthBelow.delete(0,tk.END)
        #     self.depthBelow.insert(0,depthbelow+dstep)
        # CreateCanalDendritic
        # (idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR) = self.ActiveLine.CreateCanalDendritic(Surfaces,self,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR)
    
        (idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR) = self.ActiveLine.CreateCanal(Surfaces,self,idlist,EdgeL,Berm1,Berm2,Base1,Center,Base2,Berm3,Berm4,EdgeR,lineOptV)
        
        Draw_contours(self,Surfaces)
        Draw_Update(self,Surfaces)
    
    
    def Input_Parameters(self):
        #calling the input variables
        if np.size(self.parameters,axis=0)==0:
                pcf=0.3199
                pce=0.8641
                pcc=0
                f200=0.1029
                e200=-0.73
                c200=0
                f300=0.1939
                e300=-0.73
                c300=0
                f400=0.3040
                e400=-0.73
                c400=0
                va=3
                fa=0.1488
                ea=-0.75
                ca=0
                vb=3.5
                fb=0.2188
                eb=-0.75
                cb=0
                vc=3.75
                fc=0.26
                ec=-0.75
                cc=0
                vd=4
                fd=0.3055
                ed=-0.75
                cd=0
                
                self.parameters=[pcf,pce,pcc,f200,e200,c200,f300,e300,c300,f400,e400,c400,va,fa,ea,ca,vb,fb,eb,cb,vc,fc,ec,cc,vd,fd,ed,cd]
        
        #Opening tkinter window
        self.profilewindow1 = tk.Tk()
        self.profilewindow1.title("Input Parameters")
        
        #Creating tkinter frame in window
        self.profilewindow2 = tk.Frame(self.profilewindow1,self)
        self.profilewindow2.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        self.profilewindow2.grid_columnconfigure(3,weight=1) # the text and entry frames column
        self.profilewindow2.grid_rowconfigure(10,weight=1) # all frames row_
        
        
        
        #Save, Reset and Plot Curves buttons
        button1 = tk.Button(self.profilewindow1, text="Save",command=lambda: self.Save_Parameters())
        button1.grid(row=14,column=9)

        button2 = tk.Button(self.profilewindow1, text="Reset",command=lambda: self.Reset_Parameters(self.profilewindow1))
        button2.grid(row=15,column=9)
        
        #Plots rock limit and velocity curves based on input parameters (make sure "Save" button is pressed before plotting)
        button3 = tk.Button(self.profilewindow1, text="Plot Curves",command=lambda: self.ActiveLine.RockVelLinesPlot(self))
        button3.grid(row=16,column=9)
        
        labela1=tk.Label(self.profilewindow2, text="")
        labela1.grid(row=14,column=1)
        
        #Labels and Entry boxes for the input parameters
        #Entry boxes have defualt values, which are assigned in line 48 when the script is first opened,
        #After first opened the entry values are either saved by the save button or reset by the reset button
        #Entry inputs are stored globally not locally
        label1=tk.Label(self.profilewindow2, text="Equation")
        label1.grid(row=1,column=11)
        label2=tk.Label(self.profilewindow2, text="Factor*Catchment Area^Exponent + C")
        label2.grid(row=2,column=11)
        
        label1=tk.Label(self.profilewindow2, text="Peak flow per Catchment Area")
        label1.grid(row=0,column=1)
        label1=tk.Label(self.profilewindow2, text="(100yr)(m3/s)")
        label1.grid(row=0,column=2)
        label2=tk.Label(self.profilewindow2, text="Factor:")
        label2.grid(row=1,column=1)
        self.PCF=tk.Entry(self.profilewindow2)
        self.PCF.insert(0,self.parameters[0])
        self.PCF.grid(row=1,column=2)
        label3=tk.Label(self.profilewindow2, text="Exponent:")
        label3.grid(row=2,column=1)
        self.PCE=tk.Entry(self.profilewindow2)
        self.PCE.insert(0,self.parameters[1])
        self.PCE.grid(row=2,column=2)
        label4=tk.Label(self.profilewindow2, text="Constant:")
        label4.grid(row=3,column=1)
        self.PCC=tk.Entry(self.profilewindow2)
        self.PCC.insert(0,self.parameters[2])
        self.PCC.grid(row=3,column=2)
        
        labela1=tk.Label(self.profilewindow2, text="")
        labela1.grid(row=4,column=1)
        
        label1=tk.Label(self.profilewindow2, text="Rock 200mm")
        label1.grid(row=5,column=1)
        label2=tk.Label(self.profilewindow2, text="Factor:")
        label2.grid(row=6,column=1)
        self.F200=tk.Entry(self.profilewindow2)
        self.F200.insert(0,self.parameters[3])
        self.F200.grid(row=6,column=2)
        label3=tk.Label(self.profilewindow2, text="Exponent:")
        label3.grid(row=7,column=1)
        self.E200=tk.Entry(self.profilewindow2)
        self.E200.insert(0,self.parameters[4])
        self.E200.grid(row=7,column=2)
        label4=tk.Label(self.profilewindow2, text="Constant:")
        label4.grid(row=8,column=1)
        self.C200=tk.Entry(self.profilewindow2)
        self.C200.insert(0,self.parameters[5])
        self.C200.grid(row=8,column=2)
        
        
        label1=tk.Label(self.profilewindow2, text="Rock 300mm")
        label1.grid(row=5,column=4)
        label2=tk.Label(self.profilewindow2, text="Factor:")
        label2.grid(row=6,column=4)
        self.F300=tk.Entry(self.profilewindow2)
        self.F300.insert(0,self.parameters[6])
        self.F300.grid(row=6,column=5)
        label3=tk.Label(self.profilewindow2, text="Exponent:")
        label3.grid(row=7,column=4)
        self.E300=tk.Entry(self.profilewindow2)
        self.E300.insert(0,self.parameters[7])
        self.E300.grid(row=7,column=5)
        label4=tk.Label(self.profilewindow2, text="Constant:")
        label4.grid(row=8,column=4)
        self.C300=tk.Entry(self.profilewindow2)
        self.C300.insert(0,self.parameters[8])
        self.C300.grid(row=8,column=5)
        
        label1=tk.Label(self.profilewindow2, text="Rock 400mm")
        label1.grid(row=5,column=7)
        label2=tk.Label(self.profilewindow2, text="Factor:")
        label2.grid(row=6,column=7)
        self.F400=tk.Entry(self.profilewindow2)
        self.F400.insert(0,self.parameters[9])
        self.F400.grid(row=6,column=8)
        label3=tk.Label(self.profilewindow2, text="Exponent:")
        label3.grid(row=7,column=7)
        self.E400=tk.Entry(self.profilewindow2)
        self.E400.insert(0,self.parameters[10])
        self.E400.grid(row=7,column=8)
        label4=tk.Label(self.profilewindow2, text="Constant:")
        label4.grid(row=8,column=7)
        self.C400=tk.Entry(self.profilewindow2)
        self.C400.insert(0,self.parameters[11])
        self.C400.grid(row=8,column=8)
        
        label1=tk.Label(self.profilewindow2, text="Equation")
        label1.grid(row=6,column=11)
        label2=tk.Label(self.profilewindow2, text="Factor*Slope^Exponent + C")
        label2.grid(row=7,column=11)
        
        labela1=tk.Label(self.profilewindow2, text="")
        labela1.grid(row=9,column=1)
    
        label1=tk.Label(self.profilewindow2, text="Velocity (m/s)")
        label1.grid(row=10,column=1)
        self.V1=tk.Entry(self.profilewindow2)
        self.V1.insert(0,self.parameters[12])
        self.V1.grid(row=10,column=2)
        label2=tk.Label(self.profilewindow2, text="Factor:")
        label2.grid(row=11,column=1)
        self.F1=tk.Entry(self.profilewindow2)
        self.F1.insert(0,self.parameters[13])
        self.F1.grid(row=11,column=2)
        label3=tk.Label(self.profilewindow2, text="Exponent:")
        label3.grid(row=12,column=1)
        self.E1=tk.Entry(self.profilewindow2)
        self.E1.insert(0,self.parameters[14])
        self.E1.grid(row=12,column=2)
        label4=tk.Label(self.profilewindow2, text="Constant:")
        label4.grid(row=13,column=1)
        self.C1=tk.Entry(self.profilewindow2)
        self.C1.insert(0,self.parameters[15])
        self.C1.grid(row=13,column=2)
        
        label1=tk.Label(self.profilewindow2, text="Velocity (m/s)")
        label1.grid(row=10,column=4)
        self.V2=tk.Entry(self.profilewindow2)
        self.V2.insert(0,self.parameters[16])
        self.V2.grid(row=10,column=5)
        label2=tk.Label(self.profilewindow2, text="Factor:")
        label2.grid(row=11,column=4)
        self.F2=tk.Entry(self.profilewindow2)
        self.F2.insert(0,self.parameters[17])
        self.F2.grid(row=11,column=5)
        label3=tk.Label(self.profilewindow2, text="Exponent:")
        label3.grid(row=12,column=4)
        self.E2=tk.Entry(self.profilewindow2)
        self.E2.insert(0,self.parameters[18])
        self.E2.grid(row=12,column=5)
        label4=tk.Label(self.profilewindow2, text="Constant:")
        label4.grid(row=13,column=4)
        self.C2=tk.Entry(self.profilewindow2)
        self.C2.insert(0,self.parameters[19])
        self.C2.grid(row=13,column=5)
        
        label1=tk.Label(self.profilewindow2, text="Velocity (m/s)")
        label1.grid(row=10,column=7)
        self.V3=tk.Entry(self.profilewindow2)
        self.V3.insert(0,self.parameters[20])
        self.V3.grid(row=10,column=8)
        label2=tk.Label(self.profilewindow2, text="Factor:")
        label2.grid(row=11,column=7)
        self.F3=tk.Entry(self.profilewindow2)
        self.F3.insert(0,self.parameters[21])
        self.F3.grid(row=11,column=8)
        label3=tk.Label(self.profilewindow2, text="Exponent:")
        label3.grid(row=12,column=7)
        self.E3=tk.Entry(self.profilewindow2)
        self.E3.insert(0,self.parameters[22])
        self.E3.grid(row=12,column=8)
        label4=tk.Label(self.profilewindow2, text="Constant:")
        label4.grid(row=13,column=7)
        self.C3=tk.Entry(self.profilewindow2)
        self.C3.insert(0,self.parameters[23])
        self.C3.grid(row=13,column=8)
        
        label1=tk.Label(self.profilewindow2, text="Velocity (m/s)")
        label1.grid(row=10,column=10)
        self.V4=tk.Entry(self.profilewindow2)
        self.V4.insert(0,self.parameters[24])
        self.V4.grid(row=10,column=11)
        label2=tk.Label(self.profilewindow2, text="Factor:")
        label2.grid(row=11,column=10)
        self.F4=tk.Entry(self.profilewindow2)
        self.F4.insert(0,self.parameters[25])
        self.F4.grid(row=11,column=11)
        label3=tk.Label(self.profilewindow2, text="Exponent:")
        label3.grid(row=12,column=10)
        self.E4=tk.Entry(self.profilewindow2)
        self.E4.insert(0,self.parameters[26])
        self.E4.grid(row=12,column=11)
        label4=tk.Label(self.profilewindow2, text="Constant:")
        label4.grid(row=13,column=10)
        self.C4=tk.Entry(self.profilewindow2)
        self.C4.insert(0,self.parameters[27])
        self.C4.grid(row=13,column=11)
        
        
        
        
        self.profilewindow1.mainloop()
    
    #Resets equation parameters to the defaults
    def Reset_Parameters(self,profilewindow1):
        #Default values
        pcf=0.3199
        pce=0.8641
        pcc=0
        f200=0.1029
        e200=-0.73
        c200=0
        f300=0.1939
        e300=-0.73
        c300=0
        f400=0.3040
        e400=-0.73
        c400=0
        va=3
        fa=0.1488
        ea=-0.75
        ca=0
        vb=3.5
        fb=0.2188
        eb=-0.75
        cb=0
        vc=3.75
        fc=0.26
        ec=-0.75
        cc=0
        vd=4
        fd=0.3055
        ed=-0.75
        cd=0
        
        self.parameters=[pcf,pce,pcc,f200,e200,c200,f300,e300,c300,f400,e400,c400,va,fa,ea,ca,vb,fb,eb,cb,vc,fc,ec,cc,vd,fd,ed,cd]
        print('Resetting')
        
        #Closes the window with custom values and re-opens window with the restored default values
        profilewindow1.destroy()
        self.Input_Parameters()
        
     
    #Saves parameter inputs to global variables    
    def Save_Parameters(self):
        #(self,F200,E200,C200,F300,E300,C300,F400,E400,C400,V1,F1,E1,C1,V2,F2,E2,C2,V3,F3,E3,C3,V4,F4,E4,C4)
        
        
        #Gets value from each entry box and global values are assigned the value
        self.parameters[0]=self.PCF.get()
        self.parameters[1]=self.PCE.get()
        self.parameters[2]=self.PCC.get()
        self.parameters[3]=self.F200.get()
        self.parameters[4]=self.E200.get()
        self.parameters[5]=self.C200.get()
        self.parameters[6]=self.F300.get()
        self.parameters[7]=self.E300.get()
        self.parameters[8]=self.C300.get()
        self.parameters[9]=self.F400.get()
        self.parameters[10]=self.E400.get()
        self.parameters[11]=self.C400.get()
        self.parameters[12]=self.V1.get()
        self.parameters[13]=self.F1.get()
        self.parameters[14]=self.E1.get()
        self.parameters[15]=self.C1.get()
        self.parameters[16]=self.V2.get()
        self.parameters[17]=self.F2.get()
        self.parameters[18]=self.E2.get()
        self.parameters[19]=self.C2.get()
        self.parameters[20]=self.V3.get()
        self.parameters[21]=self.F3.get()
        self.parameters[22]=self.E3.get()
        self.parameters[23]=self.C3.get()
        self.parameters[24]=self.V4.get()
        self.parameters[25]=self.F4.get()
        self.parameters[26]=self.E4.get()
        self.parameters[27]=self.C4.get()
        
    
    #Function that oversees the plotting of Drain Flow/m and Slope in comparison to rock size and velocity limits      
    def Rock_Vel_Plots(self,Surfaces):
        
        #Checks whether default parameters have been generated or custom ones saved, if neither is true the list will be empty and default values should be set
        if np.size(self.parameters,axis=0)==0:
                pcf=0.3199
                pce=0.8641
                pcc=0
                f200=0.1029
                e200=-0.73
                c200=0
                f300=0.1939
                e300=-0.73
                c300=0
                f400=0.3040
                e400=-0.73
                c400=0
                va=3
                fa=0.1488
                ea=-0.75
                ca=0
                vb=3.5
                fb=0.2188
                eb=-0.75
                cb=0
                vc=3.75
                fc=0.26
                ec=-0.75
                cc=0
                vd=4
                fd=0.3055
                ed=-0.75
                cd=0
                
                self.parameters=[pcf,pce,pcc,f200,e200,c200,f300,e300,c300,f400,e400,c400,va,fa,ea,ca,vb,fb,eb,cb,vc,fc,ec,cc,vd,fd,ed,cd]
        
        
        
        
        
        #function from Landformer_classes that obtains width and slope from the selected line
        #finds the width, slope and point ID every 100 m from the bottom up (the last click the mouse made when the line was created)
        (xy, Width, Slope, points) = self.ActiveLine.RockVelLines(Surfaces,self)
        
        #copy and pasted from the overarching catchment function (Drain_Catchment): finds catchment area of selected line
        #catchment function from Landformer_functions that works under the overaching function 
        
        #runs top down: ie. finds the catchment area for top-most point from function above (this will be less than a 100 m section), then finds catchment for next section point down and adds previous areas to it
        #NOTE: only runs the catchment area based on the design surface, not survey surface or line designs that haven't been aplied to the design surface
        Catchment=np.zeros_like(Surfaces.Design)
    
        col_list=['Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap', 'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy', 'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r', 'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot', 'afmhot_r', 'autumn', 'autumn_r', 'binary', 'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r', 'cividis', 'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix', 'cubehelix_r', 'flag', 'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r', 'gist_ncar', 'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r', 'gnuplot', 'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r', 'hsv', 'hsv_r', 'inferno', 'inferno_r', 'jet', 'jet_r', 'magma', 'magma_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r', 'rainbow', 'rainbow_r', 'seismic', 'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r', 'tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r', 'turbo', 'turbo_r', 'twilight', 'twilight_r', 'twilight_shifted', 'twilight_shifted_r', 'viridis', 'viridis_r', 'winter', 'winter_r']
        
        qlist=np.zeros_like(Slope)
          
        count=-1  
        Catchment=np.zeros_like(Surfaces.Design)
        
        pcf=float(self.parameters[0])
        pce=float(self.parameters[1])
        pcc=float(self.parameters[2])
        
        print('Catchment Area (m2):')
        for k in range (xy.shape[0]-1,-1,-1):
            
            for i in range (-5,6):
                for j in range (-5,6):
                    Catchment[int(xy[k,1])+i,j+int(xy[k,0])]=-1
            
            if k == points[count]:
                
                # print(Catchment[int(self.ActiveLine.interpolated_points[3,1]),int(self.ActiveLine.interpolated_points[3,0])])
                Catchment,W=RunD8(Surfaces.Design,Catchment,Surfaces.cellsize)    
                
                try:
                    Change=abs(np.sum(Catchment))-abs(np.sum(C_old))  
                    
                except:
                    Change=abs(np.sum(Catchment))
                    Total=0
                                
                C_old=Catchment
                Total+=Change
                print(Total)
                
                CA=(1/10000)*(Total)*(Surfaces.cellsize**2)
                CA=float(CA)
                #Eqn. from Drain Width and Rock Sizing, Sheet:Ch-catchment area peak flow.  Gives 100 year peak flow based of catchment area
               
                
                Q = pcf*CA**pce + pcc
                
                #Change to flow/width (m3/2/m) and appends to list that stores this data for each point on the line
                q = Q/Width
                qlist[count]=q
                
                count-=1
                        
        
        #function repsonsible for pop window and plotting - found in Landformer_classe
        self.ActiveLine.RockVelPlots(self,qlist,Slope,points,self.parameters)
            
    
    def UpdateInterval(self):
        if self.Contour_interval.get() != '':
            self.interval=float(self.Contour_interval.get())
        else:
            self.interval=2
        print((Surfaces.minval,Surfaces.maxval))
        self.levels=np.linspace(Surfaces.minval,Surfaces.maxval,int((Surfaces.maxval-Surfaces.minval)/self.interval))
        Draw_contours(self,Surfaces)
               
    def Update_CircleActive(self,v1):
        if v1==0:
           self.circle.Active=False
        else:
           self.circle.Active=True
           self.circle.draw_callback(1)
           
    def Unlock_all(self,Surfaces):
        Surfaces.Active.fill(1)
        for p in self.Polygons:
            p.Lock=False
            
    def Update_AddLine(self):
        if self.AddLine_var.get()==1:
            self.presentmethod='Add Line'
            self.presentmethoddetails='Add Line'
            self.method.delete(0,tk.END)
            self.method.insert(0,self.presentmethoddetails)
            self.Linepoints=[]
        else:
            self.presentmethod='None'
            self.presentmethoddetails='None'
            self.method.delete(0,tk.END)
            self.method.insert(0,self.presentmethoddetails)
            self.Linepoints=[]
            self.modify.set(0)
            self.NoEdit=True
            
    def donothing(self):
        pass
    
    def popup(self, event):
#      print(event)
      try:
        self.popup_menu.tk_popup(event.x_root, event.y_root)
      finally:
        self.popup_menu.grab_release()
        
    def Copy(self):
      self.event_generate('<<Copy>>')

    def Paste(self):
      self.event_generate('<<Paste>>')

    def Cut(self):
      self.event_generate('<<Cut>>')
      
    def Set_to_Undo(self):
      for s in self.subframes:
          s.grid_forget()
      # self.shapeFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
      self.presentmethod='Undo'
      self.methodlabel.config(text='Undo to Previous Design')  
    
    def Set_to_shape(self):
      for s in self.subframes:
          s.grid_forget()
      self.shapeFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
      self.presentmethod='Shape'
      self.methodlabel.config(text='Shape Surface')
      
    def Set_to_modify(self):
      for s in self.subframes:
          s.grid_forget()
      self.ModifyFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
      self.presentmethod='Modify'
      self.methodlabel.config(text='Modify Surface')
      
    def CutFill(self):
        Fill_Cut(Surfaces.Design,Surfaces.Survey,self.cut,self.fill,Surfaces.cellsize)
        self.Filltxt.delete(0,tk.END)
        self.Filltxt.insert(0,int(self.fill[0]))
        self.Cuttxt.delete(0,tk.END)
        self.Cuttxt.insert(0,int(-1*self.cut[0]))  
        print((self.fill[0],self.cut[0]))
      
      
    def Set_to_smooth(self):
      for s in self.subframes:
          s.grid_forget()
      self.smoothFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
      self.presentmethod='Smooth'
      self.methodlabel.config(text='Smooth')
      
    def on_closing(self):
        for p in self.polyinfo:
            p.destroy()
        # self.polyinfo[-1].destroy()
        self.polyinfo=[]
        
    def on_closing2(self):
        print("this window is closing")
         
    def ToggleInfo(self):
        self.polyinfo.append(PolygonInfo('Polygon Info','Catchment'))
        
        self.polyinfo[-1].updateInfo(self.ActivePolygon)
        self.polyinfo[-1].protocol("WM_DELETE_WINDOW",lambda: self.on_closing())
    
    def Plot_LEM(self,Surfaces):
        if self.ActivePolygon is not None:
           self.ActivePolygon.UpdateElevDiff(Surfaces)
               
    def Set_to_Visible(self):
        self.presentmethod='visible'
        for s in self.subframes:
          s.grid_forget()
        self.VisibleFrame.grid(row=0,column=0,columnspan=9,sticky=tk.NSEW)
        self.methodlabel.config(text='Visibility')
        
    def show_Visibility(self,x,y):
        if self.Visible is None:
            self.Visible=np.zeros_like(Surfaces.Design)
        for p in self.ReadElev:
            pos=p.annot.xy
            Visibility(pos[1],pos[0],x,y,Surfaces.Design,self.Visible,Surfaces.cellsize,float(self.TargetHeight.get()),float(self.ObsHeight.get()))
        DrawVisible(self.Visible,self,Surfaces)
        
    def Clear_Visible(self):
        self.Visible=np.zeros_like(Surfaces.Design)
        self.RemoveImages()
        
    def Save_Visibility(self):
        Save_Visible(Surfaces,self.Visible,self.ReadElev)
                
    def Clear_Elev(self):
      self.presentmethod='None'
      for p in self.ReadElev:
            p.remover()
      self.ReadElev=[]
      Draw_Update(self,Surfaces)
      self.methodlabel.config(text='None')
      # self.f.canvas.draw_idle()
      
    def Clear_Measure(self):
      self.presentmethod='None'
      for p in self.Measure:
            p.remover()
      self.Measure=[]
      Draw_Update(self,Surfaces)
      self.methodlabel.config(text='None')
      # self.f.canvas.draw_idle()
    
    def Set_to_none(self):
          if self.presentmethod=='Measure':
              self.Measure[-1].remove_last()
          self.presentmethod='None'
          for s in self.subframes:
              s.grid_forget()
          self.methodlabel.config(text='None')
          # Draw_contours(self,Surfaces)
          Draw_Update(self,Surfaces)
          # print(self.presentmethod)
    
    def Set_to_AddLine(self):
      # self.Linepoints=[]
      for s in self.subframes:
          s.grid_forget()
      if self.LineVar.get()=="Radius and Tangent":
          self.AddLineFrame1.grid(row=0,column=0,columnspan=27,sticky=tk.NSEW)
      else:
          self.AddLineFrame.grid(row=0,column=0,columnspan=27,sticky=tk.NSEW)
      self.presentmethod=self.LineVar.get()
      # print(self.presentmethod)
      self.methodlabel.config(text='Add Line')
      # self.setLine(self.LineVar.get())

    def Set_Design2(self,Surfaces):
            Surfaces.Design2=np.copy(Surfaces.Design)  
    
    def ToggleLines(self):
      self.LineVIS=not self.LineVIS
      for p in self.Lines:
          p.set_visible(self.LineVIS)
          # print("update")
      Draw_Update(self,Surfaces)
      
    def TogglePolygons(self):
      self.PolyVIS=not self.PolyVIS
      for p in self.Polygons:
          p.set_visible(self.PolyVIS)
          # print("update")
      Draw_Update(self,Surfaces)
      
    def Set_to_AddPolygon(self):
      self.Polypoints=[]
      for s in self.subframes:
          s.grid_forget()
      # self.AddLineFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
      self.presentmethod='Add Polygon'
      self.methodlabel.config(text='Add Polygon')
      
    def Set_to_LEM(self):
          for s in self.subframes:
              s.grid_forget()
          self.LEMFrame.grid(row=0,column=0,columnspan=9,sticky=tk.NSEW)
          self.presentmethod='None'
          self.methodlabel.config(text='None') 
          
    def Set_to_SelectLine(self):
      for s in self.subframes:
          s.grid_forget()
      self.SelectLineFrame.grid(row=0,column=0,columnspan=30,sticky=tk.NSEW)
      # self.presentmethod='Select Line'
      
    def Set_to_SelectPolygon(self):
      for s in self.subframes:
          s.grid_forget()
      self.PolygonFrame.grid(row=0,column=0,columnspan=30,sticky=tk.NSEW)
      self.ActivePolygon.updateCF(Surfaces,self)
      
    def Del_PolygonWindowPopUp(self):
        self.OpenWindowLabel.grid_remove()
        self.OpenWindowButton.grid(row=0,column=6,columnspan=2,rowspan=4,sticky='nesw',padx=1,pady=1)
        self.polygonwindow.destroy()
      
    def PolygonWindowPopUp(self):
        self.OpenWindowButton.grid_remove()
        self.OpenWindowLabel.grid(row=0,column=6,columnspan=2,rowspan=4,sticky='nesw',padx=1,pady=1)
        
        self.polygonwindow = tk.Toplevel(self)
        self.polygonwindow.protocol('WM_DELETE_WINDOW', self.Del_PolygonWindowPopUp) #Protocol to delete frame if window closed on top right
        self.polygonwindow.grid_columnconfigure(12,weight=1) # the text and entry frames column
        # self.polygonwindow.grid_rowconfigure(5,weight=1) # all frames row_
        
        bwidth=20
        bheight=2
        
        ### Top left menu, cut, fill etc. 
        self.action_options=("Edit","Movement")
        self.action_var=tk.StringVar()
        self.action_var.set("Edit")
        
        self.PolyMenu=tk.OptionMenu(self.polygonwindow,
                                    self.action_var,
                                    *self.action_options,
                                    command=self.changeframe)
        self.PolyMenu.config(relief='solid',borderwidth=1)
        
        labelpcut = tk.Label(self.polygonwindow, text="Cut:")
        self.CutPw=tk.Entry(self.polygonwindow,width=8)
        # self.CutPw.insert(0,0.0)
        
        labelpfill = tk.Label(self.polygonwindow, text="Fill:")
        self.FillPw=tk.Entry(self.polygonwindow,width=8)
        # self.FillPw.insert(0,0.0)

        labelparea = tk.Label(self.polygonwindow, text="Area:")
        self.AreaPolyw=tk.Entry(self.polygonwindow,width=8)
        # self.AreaPolyw.insert(0,0.0)
        
        labeldrainage = tk.Label(self.polygonwindow, text="Cut/Fill Area:")
        self.DrainPolyw=tk.Entry(self.polygonwindow,width=8)
        # self.DrainPolyw.insert(0,0.0) #self.ActivePolygon.density
        
        labelpcut = tk.Label(self.polygonwindow, text="Cut:")
        self.CutPw=tk.Entry(self.polygonwindow,width=8)
        # self.CutPw.insert(0,0.0)
        
        labelpfill = tk.Label(self.polygonwindow, text="Fill:")
        self.FillPw=tk.Entry(self.polygonwindow,width=8)
        # self.FillPw.insert(0,0.0)
        
        labelparea = tk.Label(self.polygonwindow, text="Area:")
        self.AreaPolyw=tk.Entry(self.polygonwindow,width=8)
        # self.AreaPolyw.insert(0,0.0)
        
        labeldrainage = tk.Label(self.polygonwindow, text="Cut/Fill Area:")
        self.DrainPolyw=tk.Entry(self.polygonwindow,width=8)
        # self.DrainPolyw.insert(0,0.0) #self.ActivePolygon.density
            
        self.buttonPolyLockw = tk.Button(self.polygonwindow, width=bwidth, text="Toggle (Unlocked)",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.ToggleLock(Surfaces,self)])
        self.buttonPolyDelw = tk.Button(self.polygonwindow, width=bwidth, text="Delete",command=lambda: self.Delete_Poly(Surfaces))
        
        self.ActivePolygon.checkpolylock(self) #Updates the state of the newly generated self.buttonPolyLockw button
        self.ActivePolygon.getpolycutfill(self,Surfaces)
        
        ### Divider lines and blank labels
        self.hdivider1 = Separator(self.polygonwindow, orient="horizontal")
        self.hdivider2 = Separator(self.polygonwindow, orient="horizontal")
        self.hdivider3 = Separator(self.polygonwindow, orient="horizontal")
        self.hdivider4 = Separator(self.polygonwindow, orient="horizontal")
        self.vdivider1 = Separator(self.polygonwindow, orient="vertical")
        self.vdivider2 = Separator(self.polygonwindow, orient="vertical")
        self.vdivider3 = Separator(self.polygonwindow, orient="vertical")
        self.vdivider4 = Separator(self.polygonwindow, orient="vertical")
        self.vdivider5 = Separator(self.polygonwindow, orient="vertical")
        self.vdivider6 = Separator(self.polygonwindow, orient="vertical")
        self.vdivider7 = Separator(self.polygonwindow, orient="vertical")
        self.vdivider8 = Separator(self.polygonwindow, orient="vertical")

        self.deadlabel0 = tk.Label(self.polygonwindow, text="               ")
        self.deadlabel1 = tk.Label(self.polygonwindow, text="               ")
        self.deadlabel2 = tk.Label(self.polygonwindow, text="               ")
        
        ### Edit Actions
        self.dividerlabel1 = tk.Label(self.polygonwindow, text="Use with measure elevation")
        self.dividerlabel2 = tk.Label(self.polygonwindow, text="Use with long profile design")


        ### Apply button, some other editting tools
        self.buttonClear = tk.Button(self.polygonwindow, width=bwidth, text="Clear Contours",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.Remove_contours(self,Surfaces)])
        
        self.buttonPolySlope = tk.Button(self.polygonwindow, width=bwidth, text="Calculate Average Slope",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),AverageSlope(self.ActivePolygon,Surfaces,self)])
        self.PolySlopeLabel = tk.Label(self.polygonwindow, text="Average Slope:")
        self.PolySlopeReq=tk.Entry(self.polygonwindow)
        self.PolySlopeReq.delete(0,tk.END)
        self.PolySlopeReq.insert(0,0.0)
        
        self.buttonPolyMesh = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Triangulate Border",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.polygonpoints(self,Surfaces),self.ActivePolygon.updatePolygonPoints(self,Surfaces)])

        self.buttonPolyApply = tk.Button(self.polygonwindow, width=bwidth, text="Apply Polygon Points",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.Apply_Poly(Surfaces,self),self.ActivePolygon.updatePolygonPoints(self,Surfaces),Draw_contours(self,Surfaces)])
        
        self.buttonAll1 = tk.Button(self.polygonwindow, width=bwidth, text="Apply Vertical Offset",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.VerticalOffset(Surfaces,self),self.ActivePolygon.updatePolygonPoints(self,Surfaces)])
        self.labelOff = tk.Label(self.polygonwindow, text="Vertical Offset (m):")
        self.VOff=tk.Entry(self.polygonwindow)
        self.VOff.insert(0,0.0)
        
        self.buttonSurv = tk.Button(self.polygonwindow, width=bwidth, height=bheight, text="Set to Survey",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.SetSurv(Surfaces,self),self.ActivePolygon.updatePolygonPoints(self,Surfaces)])
        self.buttonSett = tk.Button(self.polygonwindow, width=bwidth, height=bheight, text="Invert Settlement",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.Settlement(Surfaces,self),self.ActivePolygon.updatePolygonPoints(self,Surfaces)])

        
        ### Drawing tools, typically use a slope input and rely on 'read elevation' markers
        self.buttonDrawPolySlope = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Draw Slope to Point",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.Slope_to(Surfaces,self,self.ReadElev,float(self.Poly_SlopeReq.get()))])
        
        self.buttonDistanceSpigot = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Distance to points",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.Distance_to(Surfaces,self,self.ReadElev,float(self.TailingsS.get()),float(self.TailingsL.get()))])
        self.Poly_slope_to_apply = tk.Label(self.polygonwindow, text="Slope to apply:")
        self.Poly_SlopeReq=tk.Entry(self.polygonwindow)
        self.Poly_SlopeReq.delete(0,tk.END)
        self.Poly_SlopeReq.insert(0,1.0)

        self.buttonPolyFree = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Draw Free Drain",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.Free_Drain(Surfaces,self,self.ReadElev,float(self.Free_SlopeReq.get()))])

        self.Free_slope_to_apply = tk.Label(self.polygonwindow, text="Slope to apply:")
        self.Free_SlopeReq=tk.Entry(self.polygonwindow)
        self.Free_SlopeReq.delete(0,tk.END)
        self.Free_SlopeReq.insert(0,1.0)
        
        self.buttonPolyDome = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Draw Dome",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.Dome_to(Surfaces,self,self.ReadElev,float(self.Dome_SlopeReq.get()))])

        self.Dome_slope_to_apply = tk.Label(self.polygonwindow, text="Slope to apply:")
        self.Dome_SlopeReq=tk.Entry(self.polygonwindow)
        self.Dome_SlopeReq.delete(0,tk.END)
        self.Dome_SlopeReq.insert(0,1.0)
        
        self.buttonBench = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Draw Benches",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.Benches(Surfaces,self,float(self.BenchH.get()),float(self.BenchBottom.get()),float(self.BenchTop.get()))])

        self.bench_height = tk.Label(self.polygonwindow, text="Bench Height:")
        self.BenchH=tk.Entry(self.polygonwindow)
        self.BenchH.delete(0,tk.END)
        self.BenchH.insert(0,10.0)
        
        self.Tailings_Slope=tk.Label(self.polygonwindow, text="Tailings Beach Slope:")
        self.TailingsS=tk.Entry(self.polygonwindow)
        self.TailingsS.delete(0,tk.END)
        self.TailingsS.insert(0,100.0)
        self.Tailings_Lift=tk.Label(self.polygonwindow, text="Height Up at Spigot:")
        self.TailingsL=tk.Entry(self.polygonwindow)
        self.TailingsL.delete(0,tk.END)
        self.TailingsL.insert(0,0.1)
        self.Constant_elev=tk.Label(self.polygonwindow, text="Set to Constant Elevation:")
        self.ConstantE=tk.Entry(self.polygonwindow)
        self.ConstantE.delete(0,tk.END)
        self.ConstantE.insert(0,1.0)
        
        
        self.bench_bottom = tk.Label(self.polygonwindow, text="Bottom Elevation:")
        self.BenchBottom=tk.Entry(self.polygonwindow)
        self.BenchBottom.delete(0,tk.END)
        self.BenchBottom.insert(0,10.0)
        
        self.bench_top = tk.Label(self.polygonwindow, text="Maximum Elevation:")
        self.BenchTop=tk.Entry(self.polygonwindow)
        self.BenchTop.delete(0,tk.END)
        self.BenchTop.insert(0,10.0)
        
        ### Drawing tools, typically use a slope input and rely on 'read elevation' markers
        self.buttonPolyShapeP = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Shape locked to Profile",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),RunShapePoly(Surfaces,self,self.Lines[-1].S)])
        self.buttonPolyShapePSurv = tk.Button(self.polygonwindow, width=bwidth, height=bheight,text="Shape locked to Profile Above Survey",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),RunShapePolySurvey(Surfaces,self,self.Lines[-1].S)])  
        self.buttonPolyShapeB = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Shape locked to Benches",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),RunShapePolyBench(Surfaces,self,self.Lines[-1].BElev,self.Lines[-1].BWidth,self.Lines[-1].Bslope)])
        self.buttonPolyShapeBSurvey = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Shape locked to Benches above Survey",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),RunShapePolyBenchSurvey(Surfaces,self,self.Lines[-1].BElev,self.Lines[-1].BWidth,self.Lines[-1].Bslope)])
        
        self.buttonPolyConstant = tk.Button(self.polygonwindow, width=bwidth, height=bheight,text="Set to Constant",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.RunPolyConstant(Surfaces,self,float(self.ConstantE.get()))])
        
        #Movement Actions
        self.buttonPolyMoveCalc = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Calculate Movement",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.material_opt_polygon(Surfaces,self,float(self.Block.get()))])
        
        self.block_size = tk.Label(self.polygonwindow, text="Block Size (m):")
        
        self.Block=tk.Entry(self.polygonwindow,width=4)
        self.Block.delete(0,tk.END)
        self.Block.insert(0,20)
        
        self.buttonFraction = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Plot fraction expensive",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.Fraction(Surfaces,self,float(self.maxD.get()))])
        
        self.most_expensive_movements = tk.Label(self.polygonwindow, text="Move expensive movements (%):")
        
        self.maxD=tk.Entry(self.polygonwindow,width=4)
        self.maxD.delete(0,tk.END)
        self.maxD.insert(0,10.0)

        self.arrowtif =  tk.Button(self.polygonwindow, width=bwidth, height=bheight,text="Generate Arrows Shapefile",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.OutputArrowShapefile(Surfaces,self)])
        self.buttonAll = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Plot All Arrows",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.AllArrows(Surfaces,self)])
        self.buttonUphill = tk.Button(self.polygonwindow, width=bwidth, height=bheight,text="Highlight uphill",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.Uphill(Surfaces,self)])
        self.buttonToggleInfo = tk.Button(self.polygonwindow, width=bwidth, height=bheight,text="75% volumes",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.LimitVolumes(Surfaces,self)])
        

        self.buttonDistance = tk.Button(self.polygonwindow, width=bwidth,height=bheight, text="Highlight Distance Exceeded",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.DistanceExceeded(Surfaces,self,self.CutoffD.get())])
        self.distance_cutoff = tk.Label(self.polygonwindow, text="Distance Cutoff(s):")
        self.CutoffD=tk.Entry(self.polygonwindow,width=10)
        self.CutoffD.delete(0,tk.END)
        self.CutoffD.insert(0,'10.0,25.0')

        self.buttonPlotSubsetArrows = tk.Button(self.polygonwindow, width=bwidth, height=bheight,text="Plot Subset of Arrows",command=lambda: [self.ActivePolygon.updatePolygonPoints(self,Surfaces),self.ActivePolygon.ArrowConstraints(Surfaces,self,self.MinD.get(),self.MaxD.get(),self.MinV.get(),self.MaxV.get())])
        self.distance_min = tk.Label(self.polygonwindow, text="Distance Min:")
        self.MinD=tk.Entry(self.polygonwindow,width=5)
        self.MinD.delete(0,tk.END)
        self.MinD.insert(0,10.0)
        
        self.distance_max = tk.Label(self.polygonwindow, text="Distance Max:")
        self.MaxD=tk.Entry(self.polygonwindow,width=5)
        self.MaxD.delete(0,tk.END)
        self.MaxD.insert(0,1000000.0)
        
        self.volume_min = tk.Label(self.polygonwindow, text="Volume Min:")
        self.MinV=tk.Entry(self.polygonwindow,width=5)
        self.MinV.delete(0,tk.END)
        self.MinV.insert(0,10.0)
        
        self.volume_max = tk.Label(self.polygonwindow, text="Volume Max:")
        self.MaxV=tk.Entry(self.polygonwindow,width=5)
        self.MaxV.delete(0,tk.END)
        self.MaxV.insert(0,1000000.0)
        
        ### Top left menu, cut, fill etc. 
        self.PolyMenu.grid(row=1,column=0,columnspan=2,rowspan=2,sticky='nesw')
        self.buttonPolyLockw.grid(row=1,column=2,columnspan=2, sticky='ew',padx=1,pady=1)
        self.buttonPolyDelw.grid(row=2,column=2,columnspan=2, sticky='ew',padx=1,pady=1)
        labelpcut.grid(row=1,column=4,sticky='ew',padx=1,pady=1)
        self.CutPw.grid(row=2,column=4,sticky='ew',padx=1,pady=1)
        labelpfill.grid(row=1,column=5,sticky='ew',padx=1,pady=1)
        self.FillPw.grid(row=2,column=5,sticky='ew',padx=1,pady=1)
        labelparea.grid(row=1,column=6,sticky='ew',padx=1,pady=1)
        self.AreaPolyw.grid(row=2,column=6,sticky='ew',padx=1,pady=1)
        labeldrainage.grid(row=1,column=7,sticky='ew',padx=1,pady=1)
        self.DrainPolyw.grid(row=2,column=7,sticky='ew',padx=1,pady=1)
            
        ### Dividers
        # self.deadlabel0.grid(row=5,column=0,columnspan=6,rowspan=1, sticky='nesw',padx=1,pady=1)
        self.hdivider1.grid(column=0, row=5, sticky="new",columnspan=10,pady=10) 
        
        ### Apply button, some other editting tools
        #self.calccutfillbutton.grid(row=6,column=0,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1) 
        self.buttonPolyApply.grid(row=6,column=0,columnspan=2,rowspan=4, sticky='nesw',padx=1,pady=1)
        
        self.buttonClear.grid(row=8,column=2,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)  
        self.buttonSurv.grid(row=6,column=2,columnspan=2, rowspan=2, sticky='nesw',padx=1,pady=1)
        self.buttonSett.grid(row=6,column=4,columnspan=2, rowspan=2, sticky='nesw',padx=1,pady=1)
        
        self.buttonAll1.grid(row=6,column=6,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
        self.labelOff.grid(row=8,column=6, columnspan=2, sticky='ew',padx=1,pady=1)
        self.VOff.grid(row=9,column=6,columnspan=2, sticky='ew',padx=1,pady=1)
        
        self.buttonPolySlope.grid(row=6,column=8,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
        self.PolySlopeLabel.grid(row=8,column=8,columnspan=2,rowspan=1, sticky='nesw',padx=1,pady=1)
        self.PolySlopeReq.grid(row=9,column=8,columnspan=2,rowspan=1, sticky='nesw',padx=1,pady=1)
        
        ### Dividers
        self.deadlabel1.grid(column=0,row=10,sticky="nesw",columnspan=8)
        self.vdivider3.grid(column=2,row=11, sticky="nes",rowspan=2,pady=20)
        self.vdivider4.grid(column=9,row=11, sticky="nsw",rowspan=2,pady=20)
        self.hdivider2.grid(column=3, row=11, sticky="new",columnspan=6,pady=20) 
        self.dividerlabel1.grid(column=3, row=11, sticky="new",columnspan=2)
        
        
        ### Drawing tools, typically use a slope input and rely on 'read elevation' markers
        self.buttonPolyDome.grid(row=12,column=0,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1) #Does not use read elevation marker
        self.Dome_slope_to_apply.grid(row=14,column=0,columnspan=2, sticky='ew',padx=1,pady=1)
        self.Dome_SlopeReq.grid(row=15,column=0,columnspan=2, sticky='ew',padx=1,pady=1)

        self.buttonDrawPolySlope.grid(row=12,column=2,columnspan=2, rowspan=2, sticky='nesw',padx=1,pady=1)
        self.Poly_slope_to_apply.grid(row=14,column=2,columnspan=2, sticky='ew',padx=1,pady=1)
        self.Poly_SlopeReq.grid(row=15,column=2,columnspan=2, sticky='ew',padx=1,pady=1)

        self.buttonPolyFree.grid(row=12,column=4,columnspan=2, rowspan=2, sticky='nesw',padx=1,pady=1)
        self.Free_slope_to_apply.grid(row=14,column=4,columnspan=2, sticky='ew',padx=1,pady=1)
        self.Free_SlopeReq.grid(row=15,column=4,columnspan=2, sticky='ew',padx=1,pady=1)
        
        self.buttonBench.grid(row=12,column=6,columnspan=4, rowspan=2, sticky='nesw',padx=1,pady=1)
        self.bench_height.grid(row=14,column=6,padx=1,pady=1,columnspan=2, sticky='nesw')
        self.BenchH.grid(row=15,column=6,padx=1,pady=1,columnspan=2, sticky='nesw')
        self.bench_bottom.grid(row=14,column=8,padx=1,pady=1,columnspan=2, sticky='nesw')
        self.BenchBottom.grid(row=15,column=8,padx=1,pady=1,columnspan=2, sticky='nesw')
        
        self.buttonDistanceSpigot.grid(row=12,column=11,columnspan=1, rowspan=2, sticky='nesw',padx=1,pady=1)
        
        self.bench_top.grid(row=14,column=10,padx=1,pady=1,columnspan=2, sticky='nesw')
        self.BenchTop.grid(row=15,column=10,padx=1,pady=1,columnspan=2, sticky='nesw')
        
        
        ### Dividers
        self.deadlabel2.grid(column=0,row=16,sticky="nesw",columnspan=8)
        self.vdivider5.grid(column=2,row=17, sticky="nes",rowspan=2,pady=20)
        self.vdivider6.grid(column=9,row=17, sticky="nsw",rowspan=2,pady=20)
        self.hdivider3.grid(column=3, row=17, sticky="new",columnspan=6,pady=20) 
        self.dividerlabel2.grid(column=3, row=17, sticky="new",columnspan=2)
      
        
        ### Drawing tools typically requiring long profiles drawn 
        self.buttonPolyMesh.grid(row=18,column=0,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1) #Does not use a long profile
        self.buttonPolyShapeP.grid(row=18,column=2,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
        self.buttonPolyShapePSurv.grid(row=18,column=6,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
        self.buttonPolyConstant.grid(row=18,column=10,columnspan=4,rowspan=2, sticky='nesw',padx=1,pady=1)
        self.buttonPolyShapeB.grid(row=18,column=4,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
        self.buttonPolyShapeBSurvey.grid(row=18,column=8,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
        
        self.Tailings_Slope.grid(row=20,column=0,padx=1,pady=1,columnspan=2, sticky='nesw')
        self.TailingsS.grid(row=21,column=0,padx=1,pady=1,columnspan=2, sticky='nesw')
        self.Tailings_Lift.grid(row=20,column=2,padx=1,pady=1,columnspan=2, sticky='nesw')
        self.TailingsL.grid(row=21,column=2,padx=1,pady=1,columnspan=2, sticky='nesw')
        self.Constant_elev.grid(row=20,column=4,padx=1,pady=1,columnspan=2, sticky='nesw')
        self.ConstantE.grid(row=21,column=4,padx=1,pady=1,columnspan=2, sticky='nesw')
        
        
    
    
    def setpoly(self):
      for s in self.subframes:
          s.grid_forget()
      option1=self.action_var.get()    
      
      ### Edit widgets                              
      self.deadlabel1.grid_forget()
      self.vdivider3.grid_forget()
      self.vdivider4.grid_forget()
      self.hdivider2.grid_forget()
      self.dividerlabel1.grid_forget()      
                              
      self.deadlabel2.grid_forget()
      self.vdivider5.grid_forget()
      self.vdivider6.grid_forget()
      self.hdivider3.grid_forget()
      self.dividerlabel2.grid_forget()
      
      self.buttonClear.grid_forget()
      self.buttonPolySlope.grid_forget()
      self.buttonPolyApply.grid_forget()
      self.buttonPolyMesh.grid_forget()
      
      self.PolySlopeLabel.grid_forget()
      self.PolySlopeReq.grid_forget()
      self.buttonPolyShapePSurv.grid_forget()
      
      self.buttonPolyDome.grid_forget()
      self.Dome_slope_to_apply.grid_forget()
      self.Dome_SlopeReq.grid_forget()
      
      self.buttonPolyFree.grid_forget()
      self.Free_slope_to_apply.grid_forget()
      self.Free_SlopeReq.grid_forget()
      
      self.buttonDrawPolySlope.grid_forget()
      self.buttonDistanceSpigot.grid_forget()
      self.Poly_slope_to_apply.grid_forget()
      self.Poly_SlopeReq.grid_forget()
      
      self.buttonBench.grid_forget() 
      self.bench_height.grid_forget()
      self.BenchH.grid_forget()
      self.bench_bottom.grid_forget()
      self.BenchBottom.grid_forget()
      self.buttonPolyShapeP.grid_forget()
      self.buttonPolyShapeB.grid_forget()
      self.buttonPolyShapeBSurvey.grid_forget()
      self.buttonPolyConstant.grid_forget()
      
      self.Tailings_Slope.grid_forget()
      self.TailingsS.grid_forget()
      self.Tailings_Lift.grid_forget()
      self.TailingsL.grid_forget()
      
      self.Constant_elev.grid_forget()
      self.ConstantE.grid_forget()
      
      ### Movement Widgets
      self.buttonPolyMoveCalc.grid_forget()
      self.block_size.grid_forget()
      self.Block.grid_forget()
      self.buttonFraction.grid_forget()
      self.most_expensive_movements.grid_forget()
      self.maxD.grid_forget()
      self.buttonAll.grid_forget()
      
      self.buttonAll.grid_forget()
      self.buttonAll1.grid_forget()
      self.labelOff.grid_forget()
      self.VOff.grid_forget()
      self.buttonSurv.grid_forget()
      
      self.buttonDistance.grid_forget()
      self.distance_cutoff.grid_forget()
      self.CutoffD.grid_forget()
      
      self.buttonPlotSubsetArrows.grid_forget()
      self.distance_min.grid_forget()
      self.MinD.grid_forget()
      self.distance_max.grid_forget()
      self.MaxD.grid_forget()
      self.volume_min.grid_forget()
      self.MinV.grid_forget()
      self.volume_max.grid_forget()
      self.MaxV.grid_forget()
      self.arrowtif.grid_forget()
      self.buttonUphill.grid_forget()
      self.buttonToggleInfo.grid_forget()
      # self.buttonTogglePolygonInfo.grid_forget()
    
      

      
      if option1=="Edit":
          ### Apply button, some other editting tools
          #self.calccutfillbutton.grid(row=6,column=0,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1) 
          self.buttonPolyApply.grid(row=6,column=0,columnspan=2,rowspan=4, sticky='nesw',padx=1,pady=1)
          
          self.buttonClear.grid(row=8,column=2,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)  
          self.buttonSurv.grid(row=6,column=2,columnspan=2, rowspan=2, sticky='nesw',padx=1,pady=1)
          
          self.buttonAll1.grid(row=6,column=6,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
          self.labelOff.grid(row=8,column=6, columnspan=2, sticky='ew',padx=1,pady=1)
          self.VOff.grid(row=9,column=6,columnspan=2, sticky='ew',padx=1,pady=1)
          
          self.buttonPolySlope.grid(row=6,column=8,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
          self.PolySlopeLabel.grid(row=8,column=8,columnspan=2,rowspan=1, sticky='nesw',padx=1,pady=1)
          self.PolySlopeReq.grid(row=9,column=8,columnspan=2,rowspan=1, sticky='nesw',padx=1,pady=1)
          
          ### Dividers
          self.deadlabel1.grid(column=0,row=10,sticky="nesw",columnspan=8)
          self.vdivider3.grid(column=2,row=11, sticky="nes",rowspan=2,pady=20)
          self.vdivider4.grid(column=9,row=11, sticky="nsw",rowspan=2,pady=20)
          self.hdivider2.grid(column=3, row=11, sticky="new",columnspan=6,pady=20) 
          self.dividerlabel1.grid(column=3, row=11, sticky="new",columnspan=2)
          
          
          ### Drawing tools, typically use a slope input and rely on 'read elevation' markers
          self.buttonPolyDome.grid(row=12,column=0,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1) #Does not use read elevation marker
          self.Dome_slope_to_apply.grid(row=14,column=0,columnspan=2, sticky='ew',padx=1,pady=1)
          self.Dome_SlopeReq.grid(row=15,column=0,columnspan=2, sticky='ew',padx=1,pady=1)

          self.buttonDrawPolySlope.grid(row=12,column=2,columnspan=2, rowspan=2, sticky='nesw',padx=1,pady=1)
          self.Poly_slope_to_apply.grid(row=14,column=2,columnspan=2, sticky='ew',padx=1,pady=1)
          self.Poly_SlopeReq.grid(row=15,column=2,columnspan=2, sticky='ew',padx=1,pady=1)

          self.buttonPolyFree.grid(row=12,column=4,columnspan=2, rowspan=2, sticky='nesw',padx=1,pady=1)
          self.Free_slope_to_apply.grid(row=14,column=4,columnspan=2, sticky='ew',padx=1,pady=1)
          self.Free_SlopeReq.grid(row=15,column=4,columnspan=2, sticky='ew',padx=1,pady=1)
          
          self.buttonBench.grid(row=12,column=6,columnspan=4, rowspan=2, sticky='nesw',padx=1,pady=1)
          self.bench_height.grid(row=14,column=6,padx=1,pady=1,columnspan=2, sticky='nesw')
          self.BenchH.grid(row=15,column=6,padx=1,pady=1,columnspan=2, sticky='nesw')
          self.bench_bottom.grid(row=14,column=8,padx=1,pady=1,columnspan=2, sticky='nesw')
          self.BenchBottom.grid(row=15,column=8,padx=1,pady=1,columnspan=2, sticky='nesw')
          
          self.bench_top.grid(row=14,column=10,padx=1,pady=1,columnspan=2, sticky='nesw')
          self.BenchTop.grid(row=15,column=10,padx=1,pady=1,columnspan=2, sticky='nesw')
          
          self.buttonDistanceSpigot.grid(row=12,column=11,columnspan=1, rowspan=2, sticky='nesw',padx=1,pady=1)
         
          ### Dividers
          self.deadlabel2.grid(column=0,row=16,sticky="nesw",columnspan=8)
          self.vdivider5.grid(column=2,row=17, sticky="nes",rowspan=2,pady=20)
          self.vdivider6.grid(column=9,row=17, sticky="nsw",rowspan=2,pady=20)
          self.hdivider3.grid(column=3, row=17, sticky="new",columnspan=6,pady=20) 
          self.dividerlabel2.grid(column=3, row=17, sticky="new",columnspan=2)
        
          
          ### Drawing tools typically requiring long profiles drawn 
          self.buttonPolyMesh.grid(row=18,column=0,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1) #Does not use a long profile
          self.buttonPolyShapeP.grid(row=18,column=2,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
          self.buttonPolyShapePSurv.grid(row=18,column=6,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
          self.buttonPolyConstant.grid(row=18,column=6,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
          self.buttonPolyShapeB.grid(row=18,column=4,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
          self.buttonPolyShapeBSurvey.grid(row=18,column=8,columnspan=2,rowspan=2, sticky='nesw',padx=1,pady=1)
          
          self.Tailings_Slope.grid(row=20,column=0,padx=1,pady=1,columnspan=2, sticky='nesw')
          self.TailingsS.grid(row=21,column=0,padx=1,pady=1,columnspan=2, sticky='nesw')
          self.Tailings_Lift.grid(row=20,column=2,padx=1,pady=1,columnspan=2, sticky='nesw')
          self.TailingsL.grid(row=21,column=2,padx=1,pady=1,columnspan=2, sticky='nesw')
          
          self.Constant_elev.grid(row=20,column=4,padx=1,pady=1,columnspan=2, sticky='nesw')
          self.ConstantE.grid(row=21,column=4,padx=1,pady=1,columnspan=2, sticky='nesw')

          
          
      
      else:
          # self.PolygonFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)          
          self.buttonPolyMoveCalc.grid(row=6,column=0,columnspan=2,rowspan=2,sticky='nesw' ,padx=1, pady=1)
          self.block_size.grid(row=8,column=0,columnspan=2,sticky='ew' ,padx=1, pady=1)
          self.Block.grid(row=9,column=0,columnspan=2,sticky='ew' ,padx=1, pady=1)
          
          self.buttonAll.grid(row=6,column=2,columnspan=2,rowspan=4,ipadx=20,sticky='nesw' ,padx=1, pady=1)


          self.buttonPlotSubsetArrows.grid(row=6,column=4,columnspan=4,rowspan=2,sticky='nesw' ,padx=1, pady=1)
          self.distance_min.grid(row=8,column=4,columnspan=1,rowspan=1,sticky='ew' ,padx=1, pady=1)
          self.MinD.grid(row=9,column=4,columnspan=1,rowspan=1,sticky='ew' ,padx=1, pady=1)
          self.distance_max.grid(row=8,column=5,columnspan=1,rowspan=1,sticky='ew' ,padx=1, pady=1)
          self.MaxD.grid(row=9,column=5,columnspan=1,rowspan=1,sticky='ew' ,padx=1, pady=1)
          self.volume_min.grid(row=8,column=6,columnspan=1,rowspan=1,sticky='ew' ,padx=1, pady=1)
          self.MinV.grid(row=9,column=6,columnspan=1,rowspan=1,sticky='ew' ,padx=1, pady=1)
          self.volume_max.grid(row=8,column=7,columnspan=1,rowspan=1,sticky='ew' ,padx=1, pady=1)
          self.MaxV.grid(row=9,column=7,columnspan=1,rowspan=1,sticky='ew' ,padx=1, pady=1)
          
          self.deadlabel1.grid(column=0,row=10,sticky="nesw",columnspan=8,pady=10)

          
          self.buttonUphill.grid(row=12,column=0,columnspan=2,rowspan=4,sticky='nesw' ,padx=1, pady=1)
          
          self.buttonToggleInfo.grid(row=12,column=2,columnspan=2,rowspan=4,sticky='nesw' ,padx=1, pady=1)
          
          self.buttonFraction.grid(row=12,column=4,columnspan=2,rowspan=2,sticky='nesw' ,padx=1, pady=1)
          self.most_expensive_movements.grid(row=14,column=4,columnspan=2,sticky='ew' ,padx=1, pady=1)
          self.maxD.grid(row=15,column=4,columnspan=2,sticky='ew' ,padx=1, pady=1)
          
          self.buttonDistance.grid(row=12,column=6,columnspan=2, rowspan=2,ipadx=20,sticky='nesw' ,padx=1, pady=1)
          self.arrowtif.grid(row=12,column=8,columnspan=2, rowspan=2,ipadx=20,sticky='nesw' ,padx=1, pady=1)
          self.distance_cutoff.grid(row=14,column=6,columnspan=2,sticky='ew' ,padx=1, pady=1)
          self.CutoffD.grid(row=15,column=6,columnspan=2,sticky='ew' ,padx=1, pady=1)
          
          
          
          
      self.ActivePolygon.updateCF(Surfaces,self)
      # self.presentmethod='Select Polygon'
      
      
    def Set_to_constant(self):
      for s in self.subframes:
          s.grid_forget()
      self.constantFrame.grid(row=0,column=0,columnspan=30,sticky=tk.NSEW)
      self.presentmethod='Set Constant'
      self.methodlabel.config(text='Set to Constant')
    
    def Gen_3D(self):
      for s in self.subframes:
          s.grid_forget()
      self.presentmethod='None'
      # print(self.presentmethod)
      ThreeD(self,Surfaces)
    
    
      
        
    def Set_to_DyDrop(self):
      self.Aspect, self.Slope=RunAspect(Surfaces.Design,Surfaces.cellsize)
      # plt.imshow(self.Aspect[:,:,0])
      
      DyDroplet= Line2D([0,0], [10,10], animated=False, markerfacecolor='blue')
      DyDropletMax= Line2D([0,0], [10,10], animated=False, color='red')
      self.drop.append(DynamicDroplet(self,DyDroplet,DyDropletMax,Surfaces.cellsize))
      for s in self.subframes:
          s.grid_forget()
      self.presentmethod='DyDrop'
      self.DDFrame.grid(row=0,column=0,columnspan=30,sticky=tk.NSEW)
      self.methodlabel.config(text='Dynamic Droplet')
      # background = self.canvas.copy_from_bbox(self.fig.bbox)
      # self.canvas.restore_region(background)
      # self.ax.draw_artist(self.line)
      # self.f.canvas.draw_idle()
      # self.circle.Active=False
      
    def Clear_DyDrop(self):
      for p in self.drop:
          p.remover()
      self.drop=[]
      Draw_Update(self,Surfaces)
      self.presentmethod='None'
    
    def draw_Slope(self,Surfaces):
        # for s in self.subframes:
        #   s.grid_forget()
        # self.SlopeFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
        # self.presentmethod='None'
        RunSlope(Surfaces,self,self.ShowAllSlopes.get())
        Draw_Update(self,Surfaces)
        
    def draw_Slope2(self,Surfaces):
         # for s in self.subframes:
         #   s.grid_forget()
         # self.SlopeFrame.grid(row=0,column=0,columnspan=10,sticky=tk.NSEW)
         # self.presentmethod='None'
         RunSlope3(Surfaces,self,self.ShowAllSlopes.get())
         Draw_Update(self,Surfaces)
    
    def draw_TFFrame(self,Surfaces):
        for s in self.subframes:
          s.grid_forget()
        self.TopoFrame.grid(row=0,column=0,columnspan=30,sticky=tk.NSEW)
        self.presentmethod='None'
        self.methodlabel.config(text='None')
    
    def draw_MergeFrame(self):
        for s in self.subframes:
          s.grid_forget()
        self.MergeFrame.grid(row=0,column=0,columnspan=30,sticky=tk.NSEW)
        self.presentmethod='None'
        self.methodlabel.config(text='None')
        
    def draw_CutFFrame(self,Surfaces):
        for s in self.subframes:
          s.grid_forget()
        self.CutFFrame.grid(row=0,column=0,columnspan=30,sticky=tk.NSEW)
        self.presentmethod='None'
        self.methodlabel.config(text='None')
        
    def draw_SlopeFrame(self,Surfaces):
        for s in self.subframes:
          s.grid_forget()
        self.SlopeFrame.grid(row=0,column=0,columnspan=30,sticky=tk.NSEW)
        self.presentmethod='None'
        self.methodlabel.config(text='None')
        
    def Clear_Merge(self):
        self.Mergepoly.remove()
        self.Mergepoly=None
        self.MergeScat.remove()
        self.MergeScat=None
        Draw_Update(self,Surfaces)    
        
    def draw_TF(self,Surfaces):
        RunTF(Surfaces,self,float(self.SlopeExp.get()),float(self.CatchExp.get()),float(self.Topoval.get()))
        Draw_Update(self,Surfaces)
        
    def save_TF(self,Surfaces):
        SaveTF(Surfaces,self,float(self.SlopeExp.get()),float(self.CatchExp.get()),float(self.Topoval.get()))
                
    def draw_CutFill(self,Surfaces):
        CutFill(Surfaces,self,float(self.MaxCut.get()),float(self.MaxFill.get()))
        Draw_Update(self,Surfaces)
        
    def draw_CutFillContours(self,Surfaces):
        CutFillContours(Surfaces,self,float(self.MaxCut.get()),float(self.MaxFill.get()))
        Draw_Update(self,Surfaces)
        
    def Remove_CutFillContours(self,Surfaces):
        CutFillContoursRemove(Surfaces,self,float(self.MaxCut.get()),float(self.MaxFill.get()))
        Draw_Update(self,Surfaces)
        
    def Set_to_Elev(self):
      # self.circle.Active=False
      for s in self.subframes:
          s.grid_forget()
      # self.Aspect=RunAspect(Surfaces.Design)
      self.presentmethod='ReadElev'
      self.methodlabel.config(text='Read Elevation')
      self.currentElev=ElevationAnnot(self,Surfaces)
    
    def Set_to_Reduce(self):
      # self.circle.Active=False
      for s in self.subframes:
          s.grid_forget()
      self.ReduceFrame.grid(row=0,column=0,columnspan=30,sticky=tk.NSEW)
      # self.Aspect=RunAspect(Surfaces.Design)
      self.presentmethod='None'
      self.methodlabel.config(text='None')
      
    def Set_to_Grain(self):
      # self.circle.Active=False
      for s in self.subframes:
          s.grid_forget()
      self.GrainFrame.grid(row=0,column=0,columnspan=30,sticky=tk.NSEW)
      # self.Aspect=RunAspect(Surfaces.Design)
      self.presentmethod='None'
      self.methodlabel.config(text='None')
      
    def Set_to_Measure(self):
      # self.circle.Active=False
      for s in self.subframes:
          s.grid_forget()
      # self.Aspect=RunAspect(Surfaces.Design)
      self.presentmethod='Measure'
      self.methodlabel.config(text='Measure')
      self.Measure.append(MeasureAnnot(self))
      
    def ToggleCircle(self):
        self.circle.Active = not self.circle.Active
        Draw_Update(self,Surfaces) 
        
    def delete_selected(self):
#      self.select_range(0, tk.END)
      self.focus()
      self.event_generate("<Delete>")

    def delete_only(self):
      self.event_generate("<BackSpace>")

    def select_all(self):
      self.select_range(0, tk.END)
      self.focus()
      
    def UpdateConnectedLengths(self):
        self.AllLengths.delete(0,tk.END)
        totalLength=int(self.DrainLength.get())
        for i in self.ActiveLine.connectedLines:
            # print(i)
            # print(self.Lines[i].distance[-1])
            totalLength+=self.Lines[i-1].distance2[-1]
            self.AllLengths.insert(0,int(totalLength))
            self.ActiveLine.AllLengths=int(totalLength)
            
        

    def Drain_Catchment(self):
        Catchment=np.zeros_like(Surfaces.Design)
        # print([int(self.ActiveLine.interpolated_points[3,0]),int(self.ActiveLine.interpolated_points[3,1])])
        for k in range (0,self.ActiveLine.interpolated_points.shape[0]):
            for i in range (-5,6):
                for j in range (-5,6):
                    Catchment[int(self.ActiveLine.interpolated_points[k,1])+i,j+int(self.ActiveLine.interpolated_points[k,0])]=-1
        # print(Catchment[int(self.ActiveLine.interpolated_points[3,1]),int(self.ActiveLine.interpolated_points[3,0])])
        Catchment,W=RunD8(Surfaces.Design,Catchment,Surfaces.cellsize)
        # Surfaces.Design=W
        self.a.imshow(Catchment)
        self.f.canvas.draw_idle()
        CA=float(-(1/10000)*np.sum(Catchment)*(Surfaces.cellsize**2))
        self.ActiveLine.CA=CA
        self.CatchArea.delete(0,tk.END)
        self.CatchArea.insert(0,round(float(CA),4))
        self.ActiveLine.DrainDense=int(int(self.DrainLength.get())/float(CA))
        self.DrainDens.delete(0,tk.END)
        self.DrainDens.insert(0,round(self.ActiveLine.DrainDense,2))
        
        self.UpdateConnectedLengths()
        
        
        self.AllDensity.delete(0,tk.END)
        self.AllDensity.insert(0,round(self.ActiveLine.AllLengths/CA,2))
        self.ActiveLine.AllDensity=round(self.ActiveLine.AllLengths/CA,2)
        
    def RemoveArrows(self):
        objectlist=list(self.a.get_children())
        for i in range(len(self.a.get_children())-1,0,-1):
            objectname=str(objectlist[i])
            if objectname=='FancyArrow()':
                self.a.get_children()[i].remove()
                
            
        Draw_Update(self,Surfaces)
        
    def RemoveShape(self):
        for l in self.shape:
            l[0].remove()
        Draw_Update(self,Surfaces)
        self.shape=[]
        
    def Set_text_to_black(self):
        for l in range (0,3):
            for im in self.a.images:
                try:
                   
                    im.colorbar.ax.title.set_color('black')
                    for t in im.colorbar.ax.get_yticklabels():
                        t.set_color('black')
                    t=im.colorbar.ax.get_ylabel()
                    im.colorbar.ax.set_ylabel(t,color='black')
                    
                except:
                    pass
            Draw_Update(self,Surfaces)
            
    def RemoveImages(self):
        for l in range (0,3):
            for im in self.a.images:
                self.a.images.remove(im)
                try:
                    im.colorbar.remove()
                except:
                    pass
        Draw_Update(self,Surfaces)
        
    def set_render(self):
        self.presentmethod='Render'
        for s in self.subframes:
          s.grid_forget()
        self.VisibleFrame.grid(row=0,column=0,columnspan=9,sticky=tk.NSEW)
        self.methodlabel.config(text='Render')
        
    def set_renderSurv(self):
        self.presentmethod='RenderSurv'
        for s in self.subframes:
          s.grid_forget()
        self.VisibleFrame.grid(row=0,column=0,columnspan=9,sticky=tk.NSEW)
        self.methodlabel.config(text='Render Survey')
        
def on_closing2():
    print("this window is closing")
    
app = Landformer()
app.protocol('WM_DELETE_WINDOW', lambda: on_closing2())

app.mainloop()
