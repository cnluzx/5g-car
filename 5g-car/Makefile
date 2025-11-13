CXX = g++
CXXFLAGS = `pkg-config --cflags opencv4` -Wall -std=c++17 -Iinclude
LDFLAGS = `pkg-config --libs opencv4` -lpigpio -lpthread -lopenal

TARGET = g5g_refactored
SRCS = $(wildcard src/*.cpp)
OBJS = $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean