CC=gcc
CFLAGS = -std=gnu99
LFLAGS = -lpthread
TARGET = server

all: $(TARGET)

$(TARGET): $(TARGET).c
	$(CC) -o $(TARGET) $(TARGET).c $(CFLAGS) $(LFLAGS)

clean:
	$(RM) *.o *~ $(TARGET)
