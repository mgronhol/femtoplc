/*
   Copyright 2013 Markus Gronholm <markus@alshain.fi> / Alshain Oy

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/



#include "femtoplc.h"

#define FLAG_HIGH_BANK 	(8)
#define BANK_MASK		(7)
#define ADDRESS_MASK	(15)
#define OPCODE_MASK		(0xE0)
#define FLAG_MEMORY		(16)

#define BRANCH_BEGIN	(0)
#define BRANCH_END		(1)

static const uint8_t plc_masks[8] = {1, 2, 4, 8, 16, 32, 64, 128};

static uint8_t plc_read( plc_context_t *ctx, uint8_t port, uint8_t address ){
	uint8_t bank = (uint8_t)((address & FLAG_HIGH_BANK) != 0);
	return (uint8_t)((ctx->ports[port][bank] & plc_masks[ address & BANK_MASK ]) != 0);
	}

static void plc_write( plc_context_t *ctx, uint8_t port, uint8_t address, uint8_t value ){
	uint8_t bank = (uint8_t)((address & FLAG_HIGH_BANK) != 0);
	
	if( value == 0 ){
		ctx->ports[port][bank] &= ~plc_masks[ address & BANK_MASK ];
		}
	else{
		ctx->ports[port][bank] |= plc_masks[ address & BANK_MASK ];
		}
	}

static uint8_t plc_branch_read( plc_context_t *ctx, uint8_t port, uint8_t address ){
	uint8_t bank = (uint8_t)((address & FLAG_HIGH_BANK) != 0);
	return (uint8_t)((ctx->branches[port][bank] & plc_masks[ address & BANK_MASK ]) != 0);
	}

static void plc_branch_write( plc_context_t *ctx, uint8_t port, uint8_t address, uint8_t value ){
	uint8_t bank = (uint8_t)((address & FLAG_HIGH_BANK) != 0);
	
	if( value == 0 ){
		ctx->branches[port][bank] &= ~plc_masks[ address & BANK_MASK ];
		}
	else{
		ctx->branches[port][bank] |= plc_masks[ address & BANK_MASK ];
		}
	}



uint16_t plc_execute( 	plc_context_t *ctx, 
						uint8_t *rung, 
						uint16_t offset, 
						uint16_t length, 
						plc_callback_t callback,
						uint8_t /*@out@*/ *result ){
	
	
	uint16_t pos;
	uint8_t done = 0;
	for( pos = offset ; (pos <= length) && (done == 0) ; ++pos ){
		uint8_t cmd = rung[pos];
		
		uint8_t opcode = cmd & OPCODE_MASK;

#ifdef _PLC_DEBUG
		printf( "-> cmd: %02x, opcode: %3i, stack: %02x\n", (unsigned int)(cmd), (unsigned int)(opcode), (unsigned int)(ctx->stack) );
#endif

		switch( opcode ){
			case OP_END:
				done = 1;
				pos += 1;
			break;
			
			case OP_LD:
				{
					uint8_t value = 0;
					if( (cmd & FLAG_MEMORY ) == 0 ){
						value = plc_read( ctx, PORT_INPUT, cmd & ADDRESS_MASK );
						}
					else {
						value = plc_read( ctx, PORT_MEMORY, cmd & ADDRESS_MASK );
						}
					ctx->stack <<= 1;
					ctx->stack |= value;
					}
			break;
			
			case OP_ST:
				{
					uint8_t value = ctx->stack & 0x01;
					ctx->stack >>= 1;
					if( (cmd & FLAG_MEMORY ) == 0 ){
						plc_write( ctx, PORT_OUTPUT, cmd & ADDRESS_MASK, value );
						}
					else {
						plc_write( ctx, PORT_MEMORY, cmd & ADDRESS_MASK, value );
						}
					}
			break;
			
			case OP_NOT:
				{
					ctx->stack ^= 0x01;
					}
			break;
			
			case OP_AND:
				{
					uint8_t value0, value1;
					value0 = ctx->stack & 0x01;
					ctx->stack >>= 1;
					value1 = ctx->stack & 0x01;
					ctx->stack &= ~1;		
					ctx->stack |= value0 & value1;
					
					}
			break;

			case OP_CALL:
				{
					uint8_t value0, value1;
					value0 = ctx->stack & 0x01;
					ctx->stack >>= 1;
					
					value1 = (*callback)( ctx, cmd & ( FLAG_MEMORY | ADDRESS_MASK ), value0 );
					ctx->stack <<= 1;
					ctx->stack |= value1 & 0x01;
					}
			break;
			
			
			
			case OP_BRX:
				{
					uint8_t current_value = ctx->stack & 0x01;
					uint8_t address = cmd & ADDRESS_MASK;
					
					uint8_t previous_value = plc_branch_read( ctx, BRANCH_BEGIN, address );
					
					uint8_t new_value = current_value | previous_value;
					
					plc_branch_write( ctx, BRANCH_BEGIN, address, new_value );
					
					ctx->stack <<= 1;
					ctx->stack |= new_value;
					
					}
			break;
			
			case OP_BRN:
				{
					
					uint8_t current_value = ctx->stack & 0x01;
					uint8_t address = cmd & ADDRESS_MASK;
					
					uint8_t previous_value = plc_branch_read( ctx, BRANCH_END, address );
					
					uint8_t new_value = current_value | previous_value;
					
					plc_branch_write( ctx, BRANCH_END, address, new_value );
					
					ctx->stack <<= 1;
					ctx->stack |= new_value;
					
					}
			break;
			
			default:
				*result = RUNG_ERROR;
				return pos;
			}
		
		}
	*result = RUNG_OK;
	return pos;
	}

void plc_init( /*@out@*/ plc_context_t *ctx ){
	
	ctx->ports[PORT_INPUT][0] = 0;
	ctx->ports[PORT_INPUT][1] = 0;
	
	ctx->ports[PORT_OUTPUT][0] = 0;
	ctx->ports[PORT_OUTPUT][1] = 0;

	ctx->ports[PORT_MEMORY][0] = 0;
	ctx->ports[PORT_MEMORY][1] = 0;
	
	ctx->stack = 0;
	
	ctx->branches[BRANCH_BEGIN][0] = 0;
	ctx->branches[BRANCH_BEGIN][1] = 0;
	
	ctx->branches[BRANCH_END][0] = 0;
	ctx->branches[BRANCH_END][1] = 0;
	
	}

void plc_reset( /*@out@*/ plc_context_t *ctx ){
	
	ctx->stack = 0;
	
	ctx->branches[BRANCH_BEGIN][0] = 0;
	ctx->branches[BRANCH_BEGIN][1] = 0;
	
	ctx->branches[BRANCH_END][0] = 0;
	ctx->branches[BRANCH_END][1] = 0;
	
	}
