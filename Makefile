CC=gcc
FLAGS=-Wall -pedantic -ansi -D_PLC_DEBUG

all: femtoplc
	$(CC) $(FLAGS) -Os test.c -o test femtoplc.o

femtoplc:
	$(CC) $(FLAGS) -c femtoplc.c -o femtoplc.o
	

clean:
	rm *.o
	rm test
