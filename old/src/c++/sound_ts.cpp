// main.cpp
#include "sound.h"  // 包含头文件
#include <iostream>
#include <chrono>
#include <thread>

int main() {
    // 1. 创建 AudioPlayer 对象（栈上创建，自动析构）
    AudioPlayer audioPlayer;

    // 2. 调用 play() 播放音频（传入音频文件路径，需是绝对路径或相对路径）
    std::string audioPath = "5g-car\\files\\sound\\speak.mp3";  // 示例：树莓派上的音频文件
    bool playSuccess = audioPlayer.play(audioPath);

    if (playSuccess) {
        std::cout << "开始播放音频：" << audioPath << std::endl;
        
        // 可选：等待5秒后停止播放（或按需调用 stop()）

        std::this_thread::sleep_for(std::chrono::seconds(5));

        audioPlayer.stop();  // 停止播放

        std::cout << "已停止播放" << std::endl;
    } else {
        std::cerr << "播放失败：可能正在播放其他音频" << std::endl;
    }

    // 可选：等待播放线程结束（避免程序退出时线程未回收）
    audioPlayer.waitForFinish();

    return 0;
}