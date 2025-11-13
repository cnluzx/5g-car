# ==================== 编译器和工具 ====================
CXX = g++
CXXFLAGS = `pkg-config --cflags opencv4` -Wall -Wextra -std=c++17 -Iinclude
LDFLAGS = `pkg-config --libs opencv4` -lpigpio -lpthread

# 目标可执行文件
TARGET = g5g_refactored

# 源文件和目标文件
SRCS = $(wildcard src/*.cpp)
OBJS = $(SRCS:.cpp=.o)

# ==================== 编译规则 ====================

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)
	@echo "编译完成: $(TARGET)"

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# ==================== 清理规则 ====================

clean:
	rm -f $(OBJS) $(TARGET)
	@echo "已清理编译文件"

clean-all: clean
	rm -rf image/
	@echo "已清理所有生成文件"

# ==================== 其他规则 ====================

# 创建必需的目录
setup:
	@mkdir -p image/check image/mid image/yellow
	@echo "已创建输出目录"

# 运行程序
run: all setup
	./$(TARGET)

# 调试构建（包含调试符号）
debug: CXXFLAGS += -g -O0
debug: clean $(TARGET)
	@echo "调试版本编译完成"

# 优化构建
release: CXXFLAGS += -O2
release: clean $(TARGET)
	@echo "发布版本编译完成"

.PHONY: all clean clean-all setup run debug release