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


import sys, struct


class LadderCompiler( object ):
	OP_END  = 0
	OP_LD	= 32
	OP_ST	= 64
	OP_NOT	= 96
	OP_AND	= 128
	OP_CALL	= 160
	OP_BRN	= 192
	OP_BRX	= 224

	ADDR_INPUT  = 0
	ADDR_OUTPUT = 1
	ADDR_MEMORY = 2

	@staticmethod
	def create_address( _type, pos, bit ):
		
		if _type == LadderCompiler.ADDR_INPUT:
			return int(pos) << 3 | int(bit)
		
		elif _type == LadderCompiler.ADDR_OUTPUT:
			return int(pos) << 3 | int(bit)
		
		else:
			return 16 | int(pos) << 3 | int(bit)
	
	

	@staticmethod
	def parse_address( addr ):
		addr = addr.strip()
		
		(pos, bit) = addr[1:].split('.')
		
		if addr[0] == "I":
			return LadderCompiler.create_address( LadderCompiler.ADDR_INPUT, pos, bit )
		
		elif addr[0] == "O":
			return LadderCompiler.create_address( LadderCompiler.ADDR_OUTPUT, pos, bit )
		
		return LadderCompiler.create_address( LadderCompiler.ADDR_MEMORY, pos, bit)
	

	@staticmethod
	def parse_line( line ):
		out = ""
		parts = line.split()
		
		if parts[0] == "LD":
			addr = LadderCompiler.parse_address( parts[1] )
			out += struct.pack( ">B", LadderCompiler.OP_LD | addr )
		
		elif parts[0] == "LDN":
			addr = LadderCompiler.parse_address( parts[1] )
			out += struct.pack( ">B", LadderCompiler.OP_LD | addr )
			out += struct.pack( ">B", LadderCompiler.OP_NOT )
			
		elif parts[0] == "ST":
			addr = LadderCompiler.parse_address( parts[1] )
			out += struct.pack( ">B", LadderCompiler.OP_ST | addr )
		
		elif parts[0] == "STN":
			addr = LadderCompiler.parse_address( parts[1] )
			out += struct.pack( ">B", LadderCompiler.OP_NOT )
			out += struct.pack( ">B", LadderCompiler.OP_STN | addr )
		
		elif parts[0] == "A":
			out += struct.pack( ">B", LadderCompiler.OP_AND )
		
		elif parts[0] == "AN":
			out += struct.pack( ">B", LadderCompiler.OP_AND )
			out += struct.pack( ">B", LadderCompiler.OP_NOT )
				
		elif parts[0] == "BRN":
			addr = int( parts[1] )
			out += struct.pack( ">B", LadderCompiler.OP_BRN | addr )
			
		elif parts[0] == "BRX":
			addr = int( parts[1] )
			out += struct.pack( ">B", LadderCompiler.OP_BRX | addr )
		
		elif parts[0] == "CALL":
			addr = int( parts[1] )
			out += struct.pack( ">B", LadderCompiler.OP_CALL | addr )
		
		elif parts[0] == "END":
			out += struct.pack( ">B", LadderCompiler.OP_END )
		else:
			print >>sys.stderr, "ERROR: Unknown opcode %s." % parts[0]
			
		return out

	@staticmethod
	def compile( txt ):
		lines = txt.strip().splitlines()
		out = ""
		bucket = []
		Nrungs = 0
		for line in lines:
			line = line.strip()
			if len( line ) > 0:
				if line.startswith( "rung" ):
					Nrungs += 1
					if len( bucket ) > 0:
						content = ""
						bucket.append( "END" )
						
						for b in bucket:
							content += LadderCompiler.parse_line( b )
						out += content
						bucket = []
				else:
					bucket.append( line )
						
						

		if len( bucket ) > 0:
			content = ""
			bucket.append( "END" )
			for b in bucket:
				content += LadderCompiler.parse_line( b )
			
			out += content
					

		header = struct.pack( ">H", len(out))
		
		return header + out


if __name__ == "__main__":
	txt = ""
	with open( sys.argv[1] ) as handle:
		txt = handle.read()
	
	sys.stdout.write( LadderCompiler.compile( txt ) )

