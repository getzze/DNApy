#!/usr/bin/env python


#This file is part of DNApy. DNApy is a DNA editor written purely in python. 
#The program is intended to be an intuitive, fully featured, 
#extendable, editor for molecular and synthetic biology.  
#Enjoy!
#
#Copyright (C) 2014  Martin Engqvist | 
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#LICENSE:
#This file is part of DNApy.
#
#DNApy is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License, or
#(at your option) any later version.
# 
#DNApy is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Library General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software Foundation,
#Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#Get source code at: https://github.com/0b0bby0/DNApy
#

#TODO
#fix long plasmid names
#add 'dna ruler'

import wx
import wx.lib.graphics
from wx.lib.pubsub import pub


import genbank
import copy
import math

import os, sys
import string
from base_class import DNApyBaseDrawingClass
import featureedit_GUI

files={}   #list with all configuration files
files['default_dir'] = os.path.abspath(os.path.dirname(sys.argv[0]))+"/"
files['default_dir']=string.replace(files['default_dir'], "\\", "/")
files['default_dir']=string.replace(files['default_dir'], "library.zip", "")
settings=files['default_dir']+"settings"   ##path to the file of the global settings
execfile(settings) #gets all the pre-assigned settings

class PlasmidView(DNApyBaseDrawingClass):
	def __init__(self, parent, id):
		DNApyBaseDrawingClass.__init__(self, parent, wx.ID_ANY)

		genbank.dna_selection = (1,1)

		self.centre_x = 0
		self.centre_y = 0
		self.highlighted_feature = False
		
	

		self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
		self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
		self.Bind(wx.EVT_MOTION, self.OnMotion)
		self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDouble)


		#determing which listening group from which to recieve messages about UI updates
		self.listening_group = 'from_feature_list' #needs to be assigned or will raise an error		
		pub.Publisher.subscribe(self.listen_to_updateUI, self.listening_group)

		self.listening_group2 = 'from_feature_edit'		
		pub.Publisher.subscribe(self.listen_to_updateUI, self.listening_group2)		

		self.listening_group3 = 'from_dna_edit'		
		pub.Publisher.subscribe(self.listen_to_updateUI, self.listening_group3)	

		self.listening_group4 = 'from_main'
		pub.Publisher.subscribe(self.listen_to_updateUI, self.listening_group4)

		self.listening_group5 = 'private_group_for_those_that_affect_DNA_selection_from_DNA_editor'
		pub.Publisher.subscribe(self.listen_to_updateUI, self.listening_group5)


############ Setting required methods ####################

	def update_globalUI(self):
		'''Method should be modified as to update other panels in response to changes in own panel.
		Preferred use is through sending a message using the pub module.
		Example use is: pub.Publisher.sendMessage('feature_list_updateUI', '').
		The first string is the "listening group" and deterimines which listeners get the message. 
		The second string is the message and is unimportant for this implementation.
		The listening group assigned here (to identify recipients) must be different from the listening group assigned in __init__ (to subscribe to messages).'''
		pub.Publisher.sendMessage('from_plasmid_view', '')

	
	def update_ownUI(self):
		"""
		This would get called if the drawing needed to change, for whatever reason.

		The idea here is that the drawing is based on some data generated
		elsewhere in the system. If that data changes, the drawing needs to
		be updated.

		This code re-draws the buffer, then calls Update, which forces a paint event.
		"""
		dc = wx.MemoryDC()
		dc.SelectObject(self._Buffer)
		self.Draw(dc)
		dc.SelectObject(wx.NullBitmap) # need to get rid of the MemoryDC before Update() is called.
		self.Refresh()
		self.Update()


	def set_dna_selection(self, selection):
		'''Recieves requests for DNA selection and then sends it.'''
		assert type(selection) == tuple, 'Error, dna selection must be a tuple'
		selection = (int(selection[0]), int(selection[1]))
		genbank.dna_selection = selection


############### Done setting required methods #######################

	def find_overlap(self, drawn_locations, new_range):
		'''Takes two ranges and determines whether the new range has overlaps with the old one.
		If there are overlaps the overlap locations are returned.'''
		assert type(drawn_locations) == list			
		assert type(new_range) == tuple

		if drawn_locations == []:
			drawn_locations.append([new_range])
			return drawn_locations, 0
		else:
			i = 0
			while i < len(drawn_locations):
				overlap_found = False
				for n in range(0,len(drawn_locations[i])):
					if drawn_locations[i][n][0]<=new_range[0]<=drawn_locations[i][n][1] or drawn_locations[i][n][0]<=new_range[1]<=drawn_locations[i][n][1]: #if they overlap
						overlap_found = True
					elif new_range[0]<=drawn_locations[i][n][0]<=new_range[1] or new_range[0]<=drawn_locations[i][n][1]<=new_range[1]: #if they overlap
						overlap_found = True
				if overlap_found == False:
					drawn_locations[i].append(new_range)
					return drawn_locations, i
					break	
				elif i+1==len(drawn_locations):
					drawn_locations.append([new_range])
					return drawn_locations, i+1
					break
				i += 1

		

	def Draw(self, dc):
		self.centre_x = self.size[0]/2 #centre of window in x
		self.centre_y = self.size[1]/2 #centro of window in y
		self.min_centre = min(self.centre_x, self.centre_y)
			
		self.Radius = min(self.size[0], self.size[1])/3 - self.min_centre/8 #the last one is the label line length

#		dc.SetDeviceOrigin(size_x/2, size_y/2)

		dc.SetBackground(wx.Brush("White"))
		dc.Clear() # make sure you clear the bitmap!
		gcdc = wx.GCDC(dc)

		#make a hidden dc to which features can be drawn in uinique colors and later used for hittests
		self.hidden_dc = wx.MemoryDC()
		self.hidden_dc.SelectObject(wx.EmptyBitmap(self.ClientSize[0], self.ClientSize[1]))
		self.hidden_dc.SetBackground(wx.Brush("White"))
		self.hidden_dc.Clear() # make sure you clear the bitmap!

		#draw DNA circles
		gcdc.SetPen(wx.Pen(colour='#444444', width=3))
		gcdc.SetBrush(wx.Brush("White"))
		gcdc.DrawCircle(x=self.centre_x, y=self.centre_y, radius=self.Radius) #outer DNA circle

		#draw plasmid name
		self.Draw_plasmid_name(gcdc)

		#draw features
		self.Draw_features(gcdc)

		#draw enzymes
		self.Draw_enzymes(gcdc)

		#draw selection
		self.Draw_selection(gcdc)

		#draw search hits
		self.Draw_search_hits(gcdc)
	
			
#		self.hidden_dc.SelectObject(wx.NullBitmap) # need to get rid of the MemoryDC before Update() is called.


	def Draw_plasmid_name(self, gcdc):
		'''Draw the plasmid name and basepairs in the middle'''
		name = genbank.gb.fileName.split('.')[0]
		basepairs = str(len(genbank.gb.GetDNA())) + ' bp'

		font = wx.Font(pointSize=self.min_centre/16, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_BOLD, weight=wx.FONTWEIGHT_BOLD)
		gcdc.SetFont(font)
		gcdc.SetTextForeground(('#666666'))
		name_length = gcdc.GetTextExtent(name) #length of text in pixels
		gcdc.DrawText(name, self.centre_x-name_length[0]/2, self.centre_y-name_length[1])

		font = wx.Font(pointSize=self.min_centre/20, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_NORMAL, weight=wx.FONTWEIGHT_NORMAL)
		gcdc.SetFont(font)
		gcdc.SetTextForeground(('#666666'))
		basepairs_length = gcdc.GetTextExtent(basepairs)
		gcdc.DrawText(basepairs, self.centre_x-basepairs_length[0]/2, self.centre_y+basepairs_length[1]/2)



	def Draw_selection(self, gcdc):
		'''Draws the current selection'''
		gcdc.SetBrush(wx.Brush(colour=wx.Colour(0,75,255,128))) #blue
		gcdc.SetPen(wx.Pen(colour='#444444', width=1))

		start, finish = copy.copy(genbank.dna_selection)
		start_angle = self.pos_to_angle(start-1)
		if finish == -1: #if no selection
			finish_angle = start_angle
		else:
			finish_angle = self.pos_to_angle(finish)

#		print('plasmid start finsh', start, finish)
#		print('plasmid angles', start_angle, finish_angle)

		if start == finish+1 or finish_angle-start_angle<0.3:
			xc=self.centre_x
			yc=self.centre_y
			x1 = xc + self.Radius * math.cos((finish_angle-90)*(math.pi/180))
			y1 = yc + self.Radius * math.sin((finish_angle-90)*(math.pi/180))
			gcdc.DrawLine(xc, yc, x1, y1)
		
		else:	
			xc=self.centre_x
			yc=self.centre_y
			x1 = xc + self.Radius * math.cos((finish_angle-90)*(math.pi/180)) #the latter needs to be first as the arc draws backwards
			y1 = yc + self.Radius * math.sin((finish_angle-90)*(math.pi/180))
			x2 = xc + self.Radius * math.cos((start_angle-90)*(math.pi/180))
			y2 = yc + self.Radius * math.sin((start_angle-90)*(math.pi/180))
			gcdc.DrawArc(x1, y1, x2, y2, xc, yc);


	def Draw_enzymes(self, gcdc):
		pass

	def Draw_features(self, gcdc):
		'''Function dedicated to drawing feature arrows. The highlighted variable is used to pass an integer in case one wishes to highlight features.'''
		#for features
		self.min_centre = min(self.centre_x, self.centre_y) #length of shortest part of window
		feature_thickness = self.min_centre/24 #thickness of feature arrows and is used for a bunch of derived measurements
		outside_space = feature_thickness/4 #space between the outermost feature and the DNA circle
		arrowhead_length = 5 #length of arrowhead
		step = 0.25 #degree interval at which polygon point should be drawn
		spacer = feature_thickness/4 #for in-between features

		#for labels
		label_type = 'circular'
		font_size = int(self.Radius/18)
		font = wx.Font(pointSize=font_size, family=wx.FONTFAMILY_SWISS, style=wx.FONTWEIGHT_BOLD, weight=wx.FONTWEIGHT_BOLD)
		gcdc.SetFont(font)
		label_line_length = self.min_centre/8
		max_label_length = self.Radius/2 #max length of label in pixels
		xc=self.centre_x #centre of circle
		yc=self.centre_y #centre of circle

		#calculate possible positions for labels. 
		label_positions = {}	

		#grouping labels
		if label_type == 'group':
			for i in range(0, 360, 2):
				if 0 <= i <=15:
					x = self.centre_x
					y = 5 + (i-0)*font_size/2
				elif 15 < i <= 40:
					x = self.centre_x + max_label_length
					y = self.Radius/3 + (i-15)*font_size/2
				elif 40 < i <= 90:
					x = self.centre_x + self.Radius + label_line_length
					y = self.Radius/2 + (i-40)*font_size/2

				elif 90 < i <= 140:
					x = self.centre_x + self.Radius + label_line_length
					y = self.centre_y + (i-90)*font_size/2
				elif 140 < i <= 165:
					x = self.centre_x + max_label_length
					y = self.centre_y + self.Radius + (i-140)*font_size/2
				elif 165 < i <=180:
					x = self.centre_x
					y = self.centre_y + self.Radius + label_line_length + (i-165)*font_size/2

				elif 180 < i <= 195:
					x = self.centre_x
					y = self.centre_y + self.Radius + label_line_length + (i-180)*font_size/2
				elif 195 < i <= 220:
					x = self.centre_x - max_label_length
					y = self.centre_y + self.Radius + (i-195)*font_size/2
				elif 220 < i <=270:
					x = self.centre_x - self.Radius - label_line_length
					y = self.centre_y + (i-220)*font_size/2

				elif 270 < i <=320:
					x = self.centre_x - self.Radius - label_line_length
					y = self.centre_y - (i-270)*font_size/2
				elif 320 < i <= 345:
					x = self.centre_x - max_label_length
					y = self.Radius/3 + (i-320)*font_size/2
				elif 345 < i <= 360:
					x = self.centre_x
					y = 5 + (i-345)*font_size/2

				else:
					raise ValueError
				label_positions[str(i)] = (x, y, False) #add coordinates of points and indicate that it is not used

		#radiating labels
		elif label_type == 'radiating':
			for i in range(0, 360, 2):
				x, y = self.AngleToPoints(xc, yc, self.Radius+label_line_length, i)
				label_positions[str(i)] = (x, y, False) #add coordinates of points and indicate that it is not used

		#circular labels
		elif label_type == 'circular':
			for i in range(0, 92, 4):
				j = 88-i #I need to go backwards since I use the y-coordinate at the centre of the circle as a starting point
				if j == 88:
					x, y = self.AngleToPoints(xc, yc, self.Radius+label_line_length, j)
				else:
					x, y = self.AngleToPoints(xc, yc, self.Radius+label_line_length, j)
					if y > label_positions[str(j+4)][1] - gcdc.GetTextExtent('Text')[1]:
						y = label_positions[str(j+4)][1] - gcdc.GetTextExtent('Text')[1]
				label_positions[str(j)] = (x, y, False) #add coordinates of points and indicate that it is not used
			for i in range(92, 180, 4):
				if i == 92:
					x, y = self.AngleToPoints(xc, yc, self.Radius+label_line_length, i)
				else:
					x, y = self.AngleToPoints(xc, yc, self.Radius+label_line_length, i)
					if y < label_positions[str(i-4)][1] + gcdc.GetTextExtent('Text')[1]:
						y = label_positions[str(i-4)][1] + gcdc.GetTextExtent('Text')[1]
				label_positions[str(i)] = (x, y, False) #add coordinates of points and indicate that it is not used

			for i in range(0, 92, 4): # for the actual range 180 to 270
				j = 268-i #I need to go backwards since I use the y-coordinate at the centre of the circle as a starting point
				if j == 268:
					x, y = self.AngleToPoints(xc, yc, self.Radius+label_line_length, j)
				else:
					x, y = self.AngleToPoints(xc, yc, self.Radius+label_line_length, j)
					if y < label_positions[str(j+4)][1] + gcdc.GetTextExtent('Text')[1]:
						y = label_positions[str(j+4)][1] + gcdc.GetTextExtent('Text')[1]
				label_positions[str(j)] = (x, y, False) #add coordinates of points and indicate that it is not used

			for i in range(268, 360, 4):
				if i == 268:
					x, y = self.AngleToPoints(xc, yc, self.Radius+label_line_length, i)
				else:
					x, y = self.AngleToPoints(xc, yc, self.Radius+label_line_length, i)
					if y > label_positions[str(i-4)][1] - gcdc.GetTextExtent('Text')[1]:
						y = label_positions[str(i-4)][1] - gcdc.GetTextExtent('Text')[1]
				label_positions[str(i)] = (x, y, False) #add coordinates of points and indicate that it is not used	

		else:
			raise ValueError


		drawn_fw_locations = [] #for keeping track of how many times a certain region has been painted on
		drawn_rv_locations = [] #for keeping track of how many times a certain region has been painted on


		#features
		featurelist = genbank.gb.get_all_feature_positions()
		self.feature_catalog = {} #for matching features with the unique colors
		self.feature_catalog['(255, 255, 255, 255)'] = False #the background is white, have to add that key

		unique_color = (0, 0, 0)
		for i in range(0,len(featurelist)): 
			unique_color = self.GetNextRGB(unique_color) #get color for drawing unique colors on the hidden dc

			self.feature_catalog[str(unique_color+(255,))] = i	

			featuretype, complement, start, finish, name, index = featurelist[i]
		
			featuretype = featuretype.replace('-', 'a') #for -10 and -35 region
			featuretype = featuretype.replace("5'", "a5") #for 5' features
			featuretype = featuretype.replace("3'", "a3") #for 5' features


			start_angle = self.pos_to_angle(start)
			finish_angle = self.pos_to_angle(finish)
			xc=self.centre_x #centre of circle
			yc=self.centre_y #centre of circle

			#set color surrounding feature. Normally black, red if feature is highlighted. Also change text color.
			if i is self.highlighted_feature: #if the current feature corresponds to that which should be highlighted
				gcdc.SetPen(wx.Pen(colour='#FF0000', width=2))
				gcdc.SetTextForeground('#FF0000')
			else:
				gcdc.SetPen(wx.Pen(colour='#444444', width=1))
				gcdc.SetTextForeground('#000000')

			#draw feature
			if complement == False:
				#find level to draw on
				drawn_fw_locations, level = self.find_overlap(drawn_fw_locations, (start, finish))
				if level>3 or finish-start<=3: #Only allow for tree levels. Also, for very short features, draw them at bottom level
					level = 0
				
				#set colors
				color = eval(featuretype)['fw'] #get the color of feature (as string)
				assert type(color) == str
				gcdc.SetBrush(wx.Brush(color))

				if arrowhead_length > int(finish_angle-start_angle): #if feature is too short to make arrow, make box
					radius = self.Radius+outside_space+feature_thickness+((feature_thickness+spacer)*level)
					pointlist = self.make_arc(xc, yc, start_angle, finish_angle, radius, feature_thickness, step, arrowhead_length, arrow=False)

				else: #if not too short, make arrow
					radius = self.Radius+outside_space+feature_thickness+((feature_thickness+spacer)*level)
					pointlist = self.make_arc(xc, yc, start_angle, finish_angle, radius, feature_thickness, step, arrowhead_length, arrow='fw')

			elif complement == True:
				#find level to draw on
				drawn_rv_locations, level = self.find_overlap(drawn_rv_locations, (start, finish))
				if level>3 or finish-start<=3: #Only allow for tree levels. Also, for very short features, draw them at bottom level
					level = 0
				
				#set colors
				color = eval(featuretype)['rv'] #get the color of feature (as string)
				assert type(color) == str
				gcdc.SetBrush(wx.Brush(color))

				if arrowhead_length > int(finish_angle-start_angle): #if feature is too short to make arrow, make box
					radius = self.Radius-outside_space-((feature_thickness+spacer)*level)
					pointlist = self.make_arc(xc, yc, start_angle, finish_angle, radius, feature_thickness, step, arrowhead_length, arrow=False)
	
				else: #if not too short, make arrow
					radius = self.Radius-outside_space-((feature_thickness+spacer)*level)
					pointlist = self.make_arc(xc, yc, start_angle, finish_angle, radius, feature_thickness, step, arrowhead_length, arrow='rv')


			#first draw the hidden features which are used for hittests on click
			self.hidden_dc.SetPen(wx.Pen(colour=unique_color, width=0))
			self.hidden_dc.SetBrush(wx.Brush(colour=unique_color))
			self.hidden_dc.DrawPolygon(pointlist)

			#now draw the real features
			gcdc.DrawPolygon(pointlist)



			###############
			# Draw label #
			###############

			#draw label for feature
			#text parameters
			feature_name = name
			name_length = gcdc.GetTextExtent(feature_name) #length of text in pixels
			feature_radius = self.Radius-outside_space-((feature_thickness+spacer)*level) #the feature radius depends on where on the plasmid it is drawn

			while name_length[0] > max_label_length: #shorten text if it is too long 
				feature_name = feature_name[:-3]+'..'
				name_length = gcdc.GetTextExtent(feature_name) #length of text in pixels
	
			#draw the lines to the label and the label itself, if the feature is highlighted
			radius = self.Radius-outside_space-((feature_thickness+spacer)*level)
			angle = start_angle+(finish_angle-start_angle)/2
			x1, y1 = self.AngleToPoints(xc, yc, radius, angle)	

			#now get the second coordinate
			if label_type == 'group' or label_type == 'radiating': #'group' and 'radiating' have labels every 2 degrees, circular every 4
				angle_step = 2
			elif label_type == 'circular':
				angle_step = 4				
			else:
				raise ValueError
				

			angle = start_angle+(finish_angle-start_angle)/2 #naivly assume that the coordinate at label angle is ok and try that
			angle = int(angle/angle_step)*angle_step #I have to round to a numbers divisible by 3 (this gives 120 possible labels)

			
			x2, y2, used = label_positions[str(angle)]

			counter = 0
			while used == True: #if it turns out that it is used already, then  try next
				counter += angle_step
				if counter > 360:
					raise ValueError, 'There are more labels than there are available positions to draw them'
					break
				angle += angle_step
				if angle == 360:
					angle = angle_step
				x2, y2, used = label_positions[str(angle)]
			label_positions[str(angle)] = (x2, y2, True) #update so that the position is now used


			if label_type == 'group' or label_type == 'circular':
				gcdc.DrawLine(x1,y1,x2,y2) #draw line to feature
				if angle <= 180:
					gcdc.DrawLine(x2,y2,x2+name_length[0]+3,y2)
					gcdc.DrawText(feature_name,x2+3,y2-gcdc.GetTextExtent(feature_name)[1])

					#draw hidden box at text positon, used for hittests
					self.hidden_dc.SetPen(wx.Pen(colour=unique_color, width=0))
					self.hidden_dc.SetBrush(wx.Brush(colour=unique_color))
					self.hidden_dc.DrawRectangle(x2, y2, gcdc.GetTextExtent(feature_name)[0], -gcdc.GetTextExtent(feature_name)[1])

				elif angle > 180:
					gcdc.DrawLine(x2,y2,x2-name_length[0],y2)
					gcdc.DrawText(feature_name,x2-name_length[0],y2-gcdc.GetTextExtent(feature_name)[1])

					#draw hidden box at text positon, used for hittests
					self.hidden_dc.SetPen(wx.Pen(colour=unique_color, width=0))
					self.hidden_dc.SetBrush(wx.Brush(colour=unique_color))
					self.hidden_dc.DrawRectangle(x2, y2, -gcdc.GetTextExtent(feature_name)[0], -gcdc.GetTextExtent(feature_name)[1])

			elif label_type == 'radiating':
				if i is self.highlighted_feature: #only draw line if feature is highlighted
					gcdc.DrawLine(x1,y1,x2,y2)
				if angle <= 180:
					text_extent = gcdc.GetTextExtent(feature_name)
					text_radius = self.Radius + label_line_length

					#need to adjust for text height. Imagine right angled triangle. Adjecent is radius. Opposite is half of the text height. Calculate tan angle.
					tanangle = (0.5*text_extent[1])/text_radius #calculate the Tan(angle)
					radians = math.atan(tanangle) #negate the Tin part and get radians
					degrees = radians*(180/math.pi)	#convert radians to degrees
					text_position_angle = angle-degrees			

					tx, ty = self.AngleToPoints(xc, yc, text_radius, text_position_angle)
					gcdc.DrawRotatedText(feature_name, tx, ty, -angle+90)

					#draw hidden box at text positon, used for hittests
					self.hidden_dc.SetPen(wx.Pen(colour=unique_color, width=0))
					self.hidden_dc.SetBrush(wx.Brush(colour=unique_color))
					x1, y1 = self.AngleToPoints(xc, yc, text_radius, angle+degrees)
					x2, y2 = self.AngleToPoints(xc, yc, text_radius + text_extent[0], angle+degrees)
					x3, y3 = self.AngleToPoints(xc, yc, text_radius + text_extent[0], angle-degrees)
					x4, y4 = self.AngleToPoints(xc, yc, text_radius, angle-degrees)
					self.hidden_dc.DrawPolygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])					

				elif angle > 180:
					text_extent = gcdc.GetTextExtent(feature_name)
					text_radius = self.Radius + label_line_length + text_extent[0]

					#need to adjust for text height. Imagine right angled triangle. Adjecent is radius. Opposite is half of the text height. Calculate tan angle.
					tanangle = (0.5*text_extent[1])/text_radius #calculate the Tan(angle)
					radians = math.atan(tanangle) #negate the Tin part and get radians
					degrees = radians*(180/math.pi)	#convert radians to degrees
					text_position_angle = angle+degrees			

					tx, ty = self.AngleToPoints(xc, yc, text_radius, text_position_angle)
					gcdc.DrawRotatedText(feature_name, tx, ty, -angle-90)

					#draw hidden box at text positon, used for hittests
					self.hidden_dc.SetPen(wx.Pen(colour=unique_color, width=0))
					self.hidden_dc.SetBrush(wx.Brush(colour=unique_color))
					x1, y1 = self.AngleToPoints(xc, yc, text_radius, angle+degrees)
					x2, y2 = self.AngleToPoints(xc, yc, text_radius - text_extent[0], angle+degrees)
					x3, y3 = self.AngleToPoints(xc, yc, text_radius - text_extent[0], angle-degrees)
					x4, y4 = self.AngleToPoints(xc, yc, text_radius, angle-degrees)
					self.hidden_dc.DrawPolygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])
					
				else:
					raise ValueError

	def Draw_search_hits(self, gcdc):
		'''Indicate where search hits were found'''
		gcdc.SetPen(wx.Pen(colour=(204,255,0,255), width=3))
		gcdc.SetBrush(wx.Brush(colour=(204,255,0,255)))

		xc=self.centre_x #centre of circle
		yc=self.centre_y #centre of circle
		step = 0.25 #how tightly the points should be
		
		if len(genbank.search_hits) > 0:
			for hit in genbank.search_hits:
				pointlist = []
				start, finish = hit
				start_angle = self.pos_to_angle(start-1)
				finish_angle = self.pos_to_angle(finish)

				#near side of box
				i = 0
				while i <= int(finish_angle-start_angle):
					radius = self.Radius-5
					angle = finish_angle-i
					x, y = self.AngleToPoints(xc, yc, radius, angle)
					pointlist.append((x,y))
					i += step

				#far side of box
				i = int(finish_angle-start_angle)
				while i >= 0:
					radius = self.Radius+5
					angle = finish_angle-i
					x, y = self.AngleToPoints(xc, yc, radius, angle)
					pointlist.append((x,y))
					i -= step				
				gcdc.DrawPolygon(pointlist)

############### Setting methods for interconverting angles to dna positions ##############

	def angle_to_pos(self, angle):
		'''Convert an angle of a circle to a DNA position'''
		len_dna = float(len(genbank.gb.GetDNA()))
		dna_pos = int(self.AngleToFraction(angle)*len_dna)
		return dna_pos

	def pos_to_angle(self, pos):
		'''Calculate angles from DNA positions'''
		assert type(pos) == int, 'Error, position needs to be an integer'
		len_dna = float(len(genbank.gb.GetDNA()))
		if len_dna == 0:
			angle = 0
		else:
			angle = self.FractionToAngle(pos/float(len_dna))
		return angle		

########## Done with angle to dna methods ####################



######### Mouse methods #####################


	def HitTest(self):
		'''Tests whether the mouse is over any feature or label'''
		dc = wx.ClientDC(self) #get the client dc
		x, y = self.ScreenToClient(wx.GetMousePosition()) #get coordinate of mouse event
		pixel_color = self.hidden_dc.GetPixel(x,y) #use that coordinate to find pixel on the hidden d
		return self.feature_catalog[str(pixel_color)] #return the index
			

	def OnLeftDown(self, event):
		'''When left mouse button is pressed down, store angle at which this happened.'''
		self.centre_x = self.size[0]/2 #centre of window in x
		self.centre_y = self.size[1]/2 #centro of window in y
		x, y = self.ScreenToClient(wx.GetMousePosition())	
		angle = self.PointsToAngle(self.centre_x, self.centre_y, x, y)
		self.left_down_angle = angle #save the angle at which left button was clicked for later use


	def OnLeftUp(self, event):
		'''When left mouse button is lifted up, determine the DNA selection from angles generated at down an up events.'''
		self.centre_x = self.size[0]/2 #centre of window in x
		self.centre_y = self.size[1]/2 #centro of window in y
		x, y = self.ScreenToClient(wx.GetMousePosition())	

		up_angle = self.PointsToAngle(self.centre_x, self.centre_y, x, y)
		down_angle = self.left_down_angle

		if abs(down_angle-up_angle) <= 0.2: # want to do 'down == up' but I need some tolerance
			self.highlighted_feature = self.HitTest()
			if self.highlighted_feature is False: #if there is no feature, then there is not selection, just an insertion of the charet. Draw a line
				start = self.angle_to_pos(down_angle) 
				finish = -1 
			else:
				featuretype, complement, start, finish, name, index = genbank.gb.get_all_feature_positions()[self.highlighted_feature] #get info for the feature that was 'hit'
				start += 1 #need to adjust for some reason
		elif down_angle < up_angle:
			start = self.angle_to_pos(down_angle)
			finish = self.angle_to_pos(up_angle)
		elif down_angle > up_angle:
			start = self.angle_to_pos(up_angle)
			finish = self.angle_to_pos(down_angle)

		self.set_dna_selection((start, finish))
		self.update_ownUI()
		pub.Publisher.sendMessage('private_group_for_those_that_affect_DNA_selection_from_plasmid_view', '') #tell others that DNA selection changed


	def OnMotion(self, event):
		'''When mouse is moved with the left button down determine the DNA selection from angle generated at mouse down and mouse move event.'''
		if event.Dragging() and event.LeftIsDown():
			x, y = self.ScreenToClient(wx.GetMousePosition())	

			up_angle = self.PointsToAngle(self.centre_x, self.centre_y, x, y)
			down_angle = self.left_down_angle

			if down_angle <= up_angle:
				start = self.angle_to_pos(down_angle)
				finish = self.angle_to_pos(up_angle)
			elif down_angle > up_angle:
				start = self.angle_to_pos(up_angle)
				finish = self.angle_to_pos(down_angle)			

			self.set_dna_selection((start, finish))
			self.update_ownUI()
			pub.Publisher.sendMessage('private_group_for_those_that_affect_DNA_selection_from_plasmid_view', '') #tell others that DNA selection changed
		else:
			new_index = self.HitTest()
			if new_index is self.highlighted_feature: #if the index did not change
				pass
			else:
				self.highlighted_feature = new_index
				self.update_ownUI()


	def OnLeftDouble(self, event):
		'''When left button is duble clicked, launch the feature edit dialog.'''
		new_index = self.HitTest() #this does not get the "true" feature index. Some featues are split and this is an index that accounts for that.
		if new_index is not False: #False is returned for the background
			featurelist = genbank.gb.get_all_feature_positions()
			featuretype, complement, start, finish, name, index = featurelist[new_index]
			genbank.feature_selection = copy.copy(index)

			dlg = featureedit_GUI.FeatureEditDialog(None, 'Edit Feature') # creation of a dialog with a title
			dlg.ShowModal()
			dlg.Center()


	def OnRightUp(self, event):
		print('plasmid right')


############ Done with mouse methods ####################


##### main loop
class MyApp(wx.App):
	def OnInit(self):
		frame = wx.Frame(None, -1, title="Plasmid View", size=(700,600), style = wx.NO_FULL_REPAINT_ON_RESIZE)
		panel =	PlasmidView(frame, -1)
		frame.Centre()
		frame.Show(True)
		self.SetTopWindow(frame)
		return True


if __name__ == '__main__': #if script is run by itself and not loaded	

	files={}   #list with all configuration files
	files['default_dir'] = os.path.abspath(os.path.dirname(sys.argv[0]))+"/"
	files['default_dir']=string.replace(files['default_dir'], "\\", "/")
	files['default_dir']=string.replace(files['default_dir'], "library.zip", "")
	settings=files['default_dir']+"settings"   ##path to the file of the global settings
	execfile(settings) #gets all the pre-assigned settings

	genbank.dna_selection = (1, 1)	 #variable for storing current DNA selection
	genbank.feature_selection = False #variable for storing current feature selection

	import sys
	assert len(sys.argv) == 2, 'Error, this script requires a path to a genbank file as an argument.'
	print('Opening %s' % str(sys.argv[1]))

	genbank.gb = genbank.gbobject(str(sys.argv[1])) #make a genbank object and read file


	app = MyApp(0)
	app.MainLoop()