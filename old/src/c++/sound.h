#ifndef AUDIO_PLAYER_H
#define AUDIO_PLAYER_H

#include <string>
#include <thread>
#include <atomic>

class AudioPlayer {
public:
    // 构造函数
    AudioPlayer();
    // 析构函数
    ~AudioPlayer();

    // 播放音频文件
    bool play(const std::string& filePath);
    
    // 停止播放
    void stop();
    
    // 检查是否正在播放
    bool isPlaying() const;
    
    // 等待播放完成
    void waitForFinish();

private:
    // 实际播放函数
    void playAudio(const std::string& filePath);
    
    // 播放线程
    std::thread playerThread;
    
    // 播放状态标志
    std::atomic<bool> isPlayingFlag;
    
    // 停止标志
    std::atomic<bool> stopFlag;
};

#endif // AUDIO_PLAYER_H
