C=gcc
CFLAGS_BASE=-std=gnu99 -Wall -Wshadow -Wvla -pedantic -lpthread
CFLAGS_DEBUG=-g $(CFLAGS_BASE)
CFLAGS_OPT=-O3 $(CFLAGS_BASE)
#-g -std=c11 -Wall -Wshadow -Wvla -Werror -pedantic -Wno-unused-function
CFLAGS_GCOV=-fprofile-arcs -ftest-coverage $(CFLAGS_DEBUG)
SHELL=/bin/bash

BASE_NAME=server
SRC_C = can.c broadcast_can.c queue.c
SRC_H = can.h broadcast_can.h queue.h
MAIN_C=$(BASE_NAME).c 
TEST_C=test_$(BASE_NAME).c
SUBMIT_FILES=$(MAIN_C) $(SRC_C) $(SRC_H) Makefile
EXECUTABLE=$(BASE_NAME)
EXECUTABLE_TEST=test_$(BASE_NAME)
EXECUTABLE_DBG=$(EXECUTABLE)_dbg
EXECUTABLE_GCOV=$(EXECUTABLE)_gcov
B=4_5
IN_DIR=pa5_examples/examples
OUT_DIR=output
ARGS=vcan0
ARGS_TEST=1

$(EXECUTABLE): $(MAIN_C) $(SRC_C) $(SRC_H)
	$(CC) -o $(EXECUTABLE) $(MAIN_C) $(SRC_C) $(CFLAGS_OPT) 

debug_exec: $(MAIN_C) $(SRC_C) $(SRC_H)
	$(CC) -o $(EXECUTABLE_DBG) $(MAIN_C) $(SRC_C) $(CFLAGS_DEBUG) -DDEBUG

test_exec: $(SRC_C) $(SRC_H) $(TEST_C)
	$(CC) -o $(EXECUTABLE_TEST) $(TEST_C) $(SRC_C) $(CFLAGS_DEBUG) -DDEBUG

run: $(EXECUTABLE)
	./$(EXECUTABLE) $(ARGS)
	valgrind --leak-check=full ./$(EXECUTABLE) $(ARGS)

run_test: test_exec
	./$(EXECUTABLE_TEST) $(ARGS_TEST)
	valgrind --leak-check=full ./$(EXECUTABLE_TEST) $(ARGS_TEST)

run_debug: debug_exec
	./$(EXECUTABLE_DBG) $(ARGS)
	valgrind --leak-check=full ./$(EXECUTABLE_DBG) $(ARGS)

gdb: debug_exec
	gdb --args ./$(EXECUTABLE_DBG) $(ARGS)

gdb_test: test_exec
	gdb --args ./$(EXECUTABLE_TEST) $(ARGS_TEST)

test: $(EXECUTABLE)
	python3 test.py

coverage: $(MAIN_C) $(SRC_C) $(SRC_H)
	$(CC) -o $(EXECUTABLE_GCOV) $(MAIN_C) $(SRC_C) $(CFLAGS_GCOV) -DDEBUG
	./$(EXECUTABLE_GCOV) $(ARGS)
	gcov -f $(SRC_C)

zip:
	zip $(BASE_NAME) $(SUBMIT_FILES)

clean:
	rm -f $(EXECUTABLE) $(EXECUTABLE_DBG) $(EXECUTABLE_GCOV) $(EXECUTABLE_TEST) *.c.gcov *.gcda *.gcno

clean_out:
	rm -f $(OUT_DIR)/*

.PHONY: run, run_test, run_debug, gdb, gdb_test, test, coverage, clean, clean_out
