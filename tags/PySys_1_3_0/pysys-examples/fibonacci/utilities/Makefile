# Makefile for socket unit tests
#
# Note: compatible with gmake only
#
# @author  Moray Grieve
# @version $Id: Makefile,v 1.1.1.1 2006-06-15 21:18:31 moraygrieve Exp $


# The list of executables to create
EXE_LIST=fibonacci.exe 

# Variables common to both Linux and Solaris
OS=$(shell uname)
SRC=$(shell pwd)/src
BIN=$(shell pwd)/bin
INCLUDE=$(shell pwd)/include
PROGS=$(addprefix $(BIN)/, $(EXE_LIST))

# OS specific flags
ifeq ($(OS), SunOS)
	CC=/opt/SUNWspro/bin/cc
endif

ifeq ($(OS), Linux)
	CC=/usr/bin/gcc
endif

# set the ldflags and Cflags
LDFLAGS :=
DEFINITIONS := 
SYS_LIBS :=
INCLUDES := -I$(INCLUDE)
CFLAGS=$(DEFINITIONS) $(SYS_LIBS) $(INCLUDES)

# define implicit rules
$(BIN)/%.exe: $(SRC)/%.c
	$(CC) $(CFLAGS) $? $(LDFLAGS) -o $@ 

# targets
all: $(BIN) $(PROGS)

$(BIN):
	mkdir $@

clean:
	rm -rf $(BIN)


