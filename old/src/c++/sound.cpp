#include "sound.h"
#include <cstdlib>
#include <iostream>


///// 需要安装 omxplayer
AudioPlayer::AudioPlayer() : isPlayingFlag(false), stopFlag(false) {
}

AudioPlayer::~AudioPlayer() {
    stop();
}

bool AudioPlayer::play(const std::string& filePath) {
    if (isPlaying()) {
        std::cerr << "Already playing audio!" << std::endl;
        return false;
    }

    // 重置停止标志
    stopFlag = false;
    
    // 启动播放线程
    playerThread = std::thread(&AudioPlayer::playAudio, this, filePath);
    
    return true;
}

void AudioPlayer::stop() {
    if (isPlaying()) {
        stopFlag = true;
        if (playerThread.joinable()) {
            playerThread.join();
        }
    }
}

bool AudioPlayer::isPlaying() const {
    return isPlayingFlag;
}

void AudioPlayer::waitForFinish() {
    if (playerThread.joinable()) {
        playerThread.join();
    }
}

void AudioPlayer::playAudio(const std::string& filePath) {
    isPlayingFlag = true;
    
    // 构建omxplayer命令
    std::string command = "omxplayer \"" + filePath + "\"";
    
    // 执行播放命令
    int result = system(command.c_str());
    
    isPlayingFlag = false;
    
    if (result != 0 && !stopFlag) {
        std::cerr << "Error playing audio: " << filePath << std::endl;
    }
}
