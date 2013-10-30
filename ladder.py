#!/usr/bin/env python
#
#   Copyright 2013 Markus Gronholm <markus@alshain.fi> / Alshain Oy
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import wx
import wx.stc

import sys

import pprint

import math


def read_file( fn ):
	txt = ""
	with open( fn, 'rb' ) as handle:
		txt = handle.read()
	return txt

def read_ladder( txt ):
	lines = txt.strip().splitlines()
	rungs = {}
	current = None
	for line in lines:
		line = line.strip()
		if len( line ) < 1:
			continue
		
		if line.startswith( "rung" ):
			current = line[:-1]
			rungs[current] = []
			continue
		
		if " " in line:
			(a, b) = line.split(" ")
			rungs[current].append( (a,b) )
		else:
			rungs[current].append( (line, ) )
	return rungs
		
def stack_branches_old( rung ):
	print rung
	main = []
	branches = {}
	key = None
	current = []
	for entry in rung:
		oper = entry[0]
		if oper not in ["BRN", "BRX"]:
			if not key:
				main.append( entry )
			else:
				current.append( entry )
		else:
			param = entry[1]
			if oper == "BRN":
				if param != key:
					current.append( entry )
				else:
					current.append( entry )
					branches[key].append( current )
					current = []
					key = None
			else:
				if param not in branches:
					branches[param] = []
					main.append( ("BRANCH", param) )
					current.append( entry )
					key = param
				else:
					key = param
					current.append( entry )
	
	print branches, current
	print ""
	#pprint.pprint( main )
	for i in range( len( main ) ):
		entry = main[i]
		if entry[0] == "BRANCH":
			lines = branches[entry[1]]
			out = []
			for line in lines:
				#out.append( stack_branches( line ) )
				print "line", line
				tmp = [line[0]]
				tmp.extend( stack_branches( line[1:-1] ) )
				tmp.append( line[-1] )
				out.append( tmp )
				
			main[i] = out
		
	return main

def stack_branches( rung ):
	branches = {}
	main = []
	current = []
	key = None
	
	for entry in rung:
			oper = entry[0]
			if oper == "BRX":
				if not key:
					key = entry[1]
					current.append( entry )
					if len( main ) > 0:
						if main[-1] != ("BRANCH", key ):
							main.append( ("BRANCH", key ) )
					else:
						main.append( ("BRANCH", key ) )
					if key not in branches:
						branches[key] = []
				else:
					current.append( entry )
			elif oper == "BRN":
				if entry[1] == key:
					current.append( entry )
					branches[key].append( current )
					current = []
					key = None
				else:
					current.append( entry )
			else:
				if key:
					current.append( entry )
				else:
					main.append( entry )
	
	out = []
	for entry in main:
		if entry[0] == "BRANCH":
			branch = branches[entry[1]]
			lines = []
			for line in branch:
				brx = line[0]
				brn = line[-1]
				middle = line[1:-1]
				tmp = [brx]
				tmp.extend( stack_branches( middle ) )
				tmp.append( brn )
				lines.append( tmp )
			out.append( lines )
		else:
			out.append( entry )
	return out





		
class MainWindow( wx.Frame ):
	def __init__( self, parent, title, ladder, txt, filename ):
		super( MainWindow, self ).__init__( parent, title = title, size = (800, 600) )
		self.ladder = ladder
		self.txt = txt
		self.filename = filename
		
		self.font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, 'Courier 10 Pitch')
		self.Bind( wx.EVT_PAINT, self.onPaint )
		
		menubar = wx.MenuBar()
		fileMenu = wx.Menu()
		quitItem = fileMenu.Append( wx.ID_EXIT, "&Quit", "Quit Application" )
		menubar.Append( fileMenu, "&File" )
		
		self.SetMenuBar( menubar )
		self.Bind( wx.EVT_MENU, self.onQuit, quitItem )
		
		
		self.Show()		
	
	def onQuit( self, event ):
		self.Close()
	
	def draw_arc( self, dc, angle0, angle1, r, cx, cy, N = 8 ):
		theta0 = angle0 * math.pi/180.0
		theta1 = angle1 * math.pi/180.0
		
		
		dphi = (theta1-theta0)/(N-1)
		for i in range( N-1 ):
			phi0 = theta0 + dphi*i
			phi1 = theta0 + dphi*(i+1)
			
			x0 = int( r*math.cos( phi0 ) + cx )
			y0 = int( r*math.sin( phi0 ) + cy )
			
			x1 = int( r*math.cos( phi1 ) + cx )
			y1 = int( r*math.sin( phi1 ) + cy )
			
			dc.DrawLine( x0, y0, x1, y1 )
	
	def draw_LD( self, dc, name, x, y ):
		dc.DrawLine( x, y, x+15, y )
		dc.DrawLine( x+15, y-10, x+15, y+10 )
		dc.DrawLine( x+25, y-10, x+25, y+10 )
		dc.DrawLine( x+25, y, x+40, y )
		dc.DrawText( name, x+10, y - 25 )
	
	def draw_LDN( self, dc, name, x, y ):
		dc.DrawLine( x, y, x+15, y )
		dc.DrawLine( x+15, y-10, x+15, y+10 )
		dc.DrawLine( x+25, y-10, x+25, y+10 )
		dc.DrawLine( x+25, y, x+40, y )
		dc.DrawText( name, x+10, y - 25 )
		dc.DrawLine( x+15, y+10, x+25, y-10 )
		
	def draw_A( self, dc, x, y ):
		dc.DrawLine( x, y, x+40, y )
	
	def draw_BRX( self, dc, first, id, x, y ):
		if first:
			dc.DrawLine( x, y, x+40, y )
			#dc.DrawLine( x, y, x, y+40 )
			dc.DrawText( str(id), x+3, y )
		else:
			dc.DrawLine( x, y, x+40, y )
	
	def draw_BRN( self, dc, first, x, y ):
		if first:
			dc.DrawLine( x, y, x+40, y )
			#dc.DrawLine( x, y, x, y+40 )
		else:
			#dc.DrawLine( x, y, x+40, y )
			pass
	
	def draw_ST( self, dc, name, x, y ):
		dc.DrawLine( x, y, x+12, y )
		dc.DrawLine( x+28, y, x+40, y )
		dc.DrawText( name, x+10, y - 25 )
		
		#dc.DrawArc( x+10, y-10, x+10, y+10, x+20, y )
		self.draw_arc( dc, 180+20, 180-20, 30, x+42, y )
		self.draw_arc( dc, 180+20+180, 180-20+180, 30, x-2, y )
	
	def draw_STN( self, dc, name, x, y ):
		dc.DrawLine( x, y, x+12, y )
		dc.DrawLine( x+28, y, x+40, y )
		dc.DrawText( name, x+10, y - 25 )
		
		#dc.DrawArc( x+10, y-10, x+10, y+10, x+20, y )
		self.draw_arc( dc, 180+20, 180-20, 30, x+42, y )
		self.draw_arc( dc, 180+20+180, 180-20+180, 30, x-2, y )
		
		dc.DrawLine( x+14, y+10, x+26, y-10 )
	
	def draw_rung( self, dc, rung, old_x, old_y, first = True ):
		x = old_x
		y = old_y
		max_y = y
		
		end_x = old_x
		end_y = old_y
		
		for entry in rung:
			if type( entry ) == tuple:
				if entry[0] == "LD":
					self.draw_LD( dc, entry[1], x, y )
				elif entry[0] == "LDN":
					self.draw_LDN( dc, entry[1], x, y )
				elif entry[0] == "A":
					self.draw_A( dc, x, y )
				elif entry[0] == "BRX":
					self.draw_BRX( dc, first, entry[1], x, y )
				elif entry[0] == "BRN":
					self.draw_BRN( dc, first, x, y )
				elif entry[0] == "ST":
					self.draw_ST( dc, entry[1], x, y )
				elif entry[0] == "STN":
					self.draw_STN( dc, entry[1], x, y )
				else:
					dc.DrawText( entry[0], x, y )
				
				x += 40
				end_y = y
			else:
				mx = []
				my = []
				mye = []
				ly = y
				lfirst = True
				for e in entry:
					kx, ky, ex, ey = self.draw_rung( dc, e, x, ly, lfirst )
					mx.append( kx )
					my.append( ky )
					mye.append( ey )
					ly = ky + 40
					lfirst = False
					#print ly
				end_y = ly - 40
				maxx = max(mx)
				maxy = max(mye)
				for i in range( len( mx ) ):
					if my[i] < maxy:
						dc.DrawLine( x, y, x, maxy )
						dc.DrawLine( maxx-40, y, maxx-40, maxy )
						if mx[i] < maxx:
							dc.DrawLine( mx[i]-40, mye[i], maxx, mye[i] )
					
					else:
						if mx[i] < maxx:
							dc.DrawLine( mx[i]-40, mye[i], maxx-40, mye[i] )
					
				
				x = max( mx ) #+ 40
				if max(my) > max_y:
					max_y = max(my)
		
		end_x = x
		
		return x, max_y, end_x, end_y
	
	def onPaint( self, event ):
		dc = wx.PaintDC( self )
		dc.SetFont( self.font )
		
		x = 40
		y = 40
		dc.SetPen( wx.Pen('#000000') )
		
		rungs = self.ladder.keys()
		rungs.sort()
		for key in rungs:
			
			dc.DrawLine( 30, y, 40, y )
			
			nx, ny, ex, ey = self.draw_rung( dc, stack_branches( self.ladder[key] ), x, y )		
			y = ny+80
		
		dc.DrawLine( 30, 10, 30, y )
		

class EditorWindow( wx.Frame ):
	def __init__( self, parent, title, main ):
		super( EditorWindow, self ).__init__( parent, title = title, size = (300, 600) )
		self.main = main
		#self.font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, 'Monospace')
		self.font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, 'Monospace')
		self.font2 = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, 'Monospace')
		
		self.init_ui()
		self.init_menus()
		
		dw, dh = wx.DisplaySize()
		w, h = self.GetSize()
		self.SetPosition( (dw-w-20, h) )
		
		self.Show()	
	
	def init_menus( self ):
		menubar = wx.MenuBar()
		
		fileMenu = wx.Menu()
		editMenu = wx.Menu()
		insertMenu = wx.Menu()
		
		testtItem = wx.MenuItem( fileMenu, wx.NewId(), "&Refresh\tCtrl+R" )
		
		fileMenu.AppendItem( testtItem )
		
		saveItem = wx.MenuItem( fileMenu, wx.NewId(), "&Save\tCtrl+S" )
		
		fileMenu.AppendItem( saveItem )
		
		
		quitItem = fileMenu.Append( wx.ID_EXIT, "&Quit", "Quit Application" )
		menubar.Append( fileMenu, "&File" )
		
		undoItem = wx.MenuItem( editMenu, wx.ID_UNDO, "&Undo\tCtrl+Z" )
		editMenu.AppendItem( undoItem )
		redoItem = wx.MenuItem( editMenu, wx.ID_REDO, "&Redo\tCtrl+Y" )
		editMenu.AppendItem( redoItem )
		menubar.Append( editMenu, "&Edit" )
		
		
		branchItem = wx.MenuItem( insertMenu, wx.ID_ANY, "&Branch\tCtrl+B" )
		
		insertMenu.AppendItem( branchItem )
		
		menubar.Append( insertMenu, "&Insert" )
		
		self.SetMenuBar( menubar )
		
		self.Bind( wx.EVT_MENU, self.onQuit, quitItem )
		self.Bind( wx.EVT_MENU, self.onDemo, testtItem)
		self.Bind( wx.EVT_MENU, self.onUndo, undoItem)
		self.Bind( wx.EVT_MENU, self.onRedo, redoItem)
		
		self.Bind( wx.EVT_MENU, self.onSave, saveItem)
		
		
		self.Bind( wx.EVT_MENU, self.onInsertBranch, branchItem)
		
	def onQuit( self, event ):
		self.Close()
	
	def onDemo( self, event ):
		value = self.text.GetTextUTF8()
		
		self.main.txt = value
		self.main.ladder = read_ladder( self.main.txt )
		self.main.Refresh()
	
	def onUndo( self, event ):
		self.text.Undo()

	def onRedo( self, event ):
		self.text.Redo()

	def onInsertBranch( self, event ):
		pos = self.text.GetCurrentPos()
		lpos = self.text.GetCurrentLine()
		txt = self.text.GetTextUTF8()
		lines = txt.splitlines()
		
		
		if lpos < 1 or pos < 1:
			return None
		
		indent = False
		if txt[pos-1] != "\n":
			indent = True
		line = lines[lpos-1]
		line = line.strip()
		
		if line.startswith("BRN"):
			parts = line.split()
			
			dtab = len(lines[lpos-1]) - len( line )
			if not indent:
				out = "\t"*dtab + "BRX %s\n"%parts[1] + "\t"*(dtab+1) + "\n" + "\t"*dtab + "BRN %s\n"%parts[1]
			else:
				out = "BRX %s\n"%parts[1] + "\t"*(dtab+1) + "\n" + "\t"*dtab + "BRN %s\n"%parts[1]
			
			self.text.InsertText( pos, out )
			self.text.LineDown()
			self.text.LineEnd()
			
		else:
			rstart = lpos
			cnt = 1
			while not lines[rstart].strip().startswith( "rung" ):
				if lines[rstart].strip().startswith( "BRX" ):
					cnt += 1
				elif lines[rstart].strip().startswith( "BRN" ):
					cnt -= 1
				
				rstart -= 1
			
			rstop = lpos
			while rstop < len(lines) and not lines[rstop].strip().startswith( "rung" ):
				rstop += 1
			
			rng = lines[rstart:rstop]
			branch_id = -1
			for x in rng:
				x = x.strip()
				if x.startswith( "BRN" ):
					parts = x.split()
					if int(parts[1]) > branch_id:
						branch_id = int(parts[1])
			branch_id += 1
			if indent:
				out = "BRX %i\n"%branch_id + "\t"*(cnt+1) + "\n" + "\t"*cnt + "BRN %i\n"%branch_id
			else:
				out = "\t"*cnt + "BRX %i\n"%branch_id + "\t"*(cnt+1) + "\n" + "\t"*cnt + "BRN %i\n"%branch_id
			
			self.text.InsertText( pos, out )
			self.text.LineDown()
			self.text.LineEnd()
			
	
	def onSave( self, event ):
		with open( self.main.filename, 'w' ) as handle:
			handle.write( self.text.GetTextUTF8() )		
		
		
	
	def init_ui( self ):
		
		
		panel = wx.Panel( self, -1 )
		vbox = wx.BoxSizer( wx.VERTICAL )
		hbox = wx.BoxSizer( wx.HORIZONTAL )
		
		#self.text = wx.TextCtrl( panel, style = wx.TE_MULTILINE, pos = (10, 10), size = (280, 540) )
		self.text = wx.stc.StyledTextCtrl( panel, style = wx.TE_MULTILINE, pos = (10, 10), size = (280, 540) )
		
		
		faces = {"font": self.font2.GetFaceName(), "size": self.font2.GetPointSize() }
		fonts = "face:%(font)s,size:%(size)d" % faces
		
		self.text.StyleSetFont( 0, font = self.font )
		self.text.AppendText( self.main.txt )
		self.text.EmptyUndoBuffer()
		
		self.text.SetLexer( wx.stc.STC_LEX_ASM )
		self.text.SetKeyWords( 0, "ld ldn a brx brn st stn")
		self.text.StyleSetSpec( wx.stc.STC_P_WORD, "fore:#000000,normal,"+fonts )
		self.text.StyleSetSpec( wx.stc.STC_ASM_COMMENT, "fore:#330000,normal,"+fonts )
		self.text.StyleSetSpec( wx.stc.STC_ASM_NUMBER, "fore:#000000,normal,"+fonts )
		self.text.StyleSetSpec( wx.stc.STC_ASM_OPERATOR, "fore:#0000FF,bold,"+fonts )
		self.text.StyleSetSpec( wx.stc.STC_ASM_CPUINSTRUCTION, "fore:#0000FF,bold,"+fonts )
		self.text.StyleSetSpec( wx.stc.STC_ASM_IDENTIFIER, "fore:#227722,normal,"+fonts )
		
		self.text.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
		self.text.SetMarginMask(1, 0)
		self.text.SetMarginWidth(1, 25)
		self.text.SetMarginLeft( 10 )
		
		self.text.StyleSetSpec( wx.stc.STC_STYLE_LINENUMBER, "fore:#333333,normal,"+fonts )
		
		

#ladder = read_ladder( sys.argv[1] )
#
#rung = ladder["rung 0"]
#
#
#pprint.pprint( stack_branches( rung ) )

txt = read_file( sys.argv[1] )

ladder = read_ladder( txt )

#pprint.pprint( stack_branches( ladder["rung 2"] ) )

#tmp = stack_branches( ladder["rung 2"] )

#sys.exit(1)

app = wx.App()

main = MainWindow( None, title = "Ladder", ladder = ladder, txt = txt, filename = sys.argv[1])
EditorWindow( main, title = "List", main = main )

app.MainLoop()
