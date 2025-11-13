#ifndef DEBUG_H
#define DEBUG_H

#include <iostream>
#include <sstream>
#include <chrono>
#include <iomanip>
#include "config.h"

// 日志级别枚举
enum LogLevel { DEBUG, INFO, WARNING, ERROR };

/**
 * @class Logger
 * @brief 简单的日志输出工具，支持不同级别的日志记录
 */
class Logger {
public:
    /**
     * @brief 输出日志信息
     * @param level 日志级别
     * @param msg 日志消息
     */
    static void log(LogLevel level, const std::string& msg) {
        if (!ENABLE_DEBUG_LOG && level == DEBUG) {
            return;  // 关闭调试日志时跳过 DEBUG 级别
        }
        
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()) % 1000;
        
        std::stringstream ss;
        ss << std::put_time(std::localtime(&time), "%H:%M:%S")
           << "." << std::setfill('0') << std::setw(3) << ms.count();
        
        std::cout << "[" << ss.str() << "] "
                  << "[" << levelStr(level) << "] "
                  << msg << std::endl;
    }

    /**
     * @brief 输出调试信息（仅在 ENABLE_DEBUG_LOG 为 true 时输出）
     */
    static void debug(const std::string& msg) {
        log(DEBUG, msg);
    }

    /**
     * @brief 输出信息
     */
    static void info(const std::string& msg) {
        log(INFO, msg);
    }

    /**
     * @brief 输出警告信息
     */
    static void warning(const std::string& msg) {
        log(WARNING, msg);
    }

    /**
     * @brief 输出错误信息
     */
    static void error(const std::string& msg) {
        log(ERROR, msg);
    }

private:
    /**
     * @brief 获取日志级别的字符串表示
     */
    static std::string levelStr(LogLevel level) {
        switch(level) {
            case DEBUG:   return "DBUG";
            case INFO:    return "INFO";
            case WARNING: return "WARN";
            case ERROR:   return "ERR ";
            default:      return "UNKN";
        }
    }
};

// 便捷宏定义
#define LOG_DEBUG(msg) Logger::debug(msg)
#define LOG_INFO(msg) Logger::info(msg)
#define LOG_WARN(msg) Logger::warning(msg)
#define LOG_ERROR(msg) Logger::error(msg)

#endif // DEBUG_H