# Сборка C++ библиотек (Linux/macOS/MinGW). Для Windows без make используйте build.bat
CXX ?= g++
CXXFLAGS ?= -O2 -std=c++11 -Wall -Wextra -shared -fPIC

ifeq ($(OS),Windows_NT)
  EXT = dll
else ifeq ($(shell uname),Darwin)
  EXT = dylib
else
  EXT = so
endif

all: queue_dyn.$(EXT) queue_stl.$(EXT)

queue_dyn.$(EXT): queue_dyn.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

queue_stl.$(EXT): queue_stl.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

clean:
	rm -f queue_dyn.so queue_stl.so queue_dyn.dll queue_stl.dll queue_dyn.dylib queue_stl.dylib
