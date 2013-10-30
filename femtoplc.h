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

#ifndef _FEMTOPLC_H_
#define _FEMTOPLC_H_

#include <stdio.h>
#include <stdint.h>

#define OP_END	(0)
#define OP_LD	(32)
#define OP_ST	(64)
#define OP_NOT	(96)
#define OP_AND	(128)
#define OP_CALL	(160)
#define OP_BRN	(192)
#define OP_BRX	(224)


#define PORT_INPUT		(0)
#define PORT_OUTPUT		(1)
#define PORT_MEMORY		(2)

#define RUNG_OK			(0)
#define RUNG_ERROR		(1)

#define PLC_IO			(0)
#define PLC_MEM			(1)

#define RUNG_PUSH(rung, index, value)	( (rung)[(index)++] = (value))
#define OP( opcode, port, address ) (((uint8_t)(opcode)) | (((uint8_t)(port)) << 4) | ((uint8_t)(address)))



typedef struct plc_context {
	uint8_t ports[3][2];
	
	uint8_t stack;
	
	uint8_t branches[2][2];
		
	} plc_context_t;

typedef uint8_t (*plc_callback_t)(plc_context_t *, uint8_t, uint8_t );

void plc_init( /*@out@*/ plc_context_t *ctx );
void plc_reset( /*@out@*/ plc_context_t *ctx );

uint16_t plc_execute( 	plc_context_t *ctx, uint8_t *rung, 
						uint16_t offset, 
						uint16_t length,
						plc_callback_t callback,
						uint8_t /*@out@*/ *result );





#endif
