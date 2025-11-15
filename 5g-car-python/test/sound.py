import pygame
import os 

class Broadcast:
    def __init__(self):

        ####初始化pygame 
        ####其中有全局变量控制 if_sound是否播放 
        ####类成员变量 audio_initialized控制是否初始化成功 
        #### 如果initialized成功，则可以播放音频 
        ####整体调用流程:

        ###sound = Broadcast() 
        ###sound._play_sound(sound,speak )  即可播放音频 

        try:
            pygame.init()
            pygame.mixer.init()
            self.audio_initialized = True
            print("[Broadcast] pygame.mixer 初始化成功")

        except Exception as e:
            ###如果初始化失败
            print(f"[Broadcast] pygame.mixer 初始化失败: {e}")
            self.audio_initialized = False

    def _play_sound(self, place, name):


        if not self.audio_initialized:
            print("[Broadcast] 音频未初始化，跳过播放")
            return False 
        sound_path = f"files/{place}/{name}.mp3"

        print(f"[Broadcast] 尝试播放: {sound_path}")
        if not os.path.exists(sound_path):
            print(f"[Broadcast] 错误: 文件不存在 - {sound_path}")
            return False 
        try:
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
            print(f"[Broadcast] 开始播放 {name}")
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(20)
            print(f"[Broadcast] 播放完成 {name}")  ###直至播放完毕
            if_sound = True 
            return True 

        except Exception as e:
            print(f"[Broadcast] 播放声音失败: {e}")
            return False 

if __name__ == "__main__": 
    sound = Broadcast()
    ret= sound._play_sound("sound","speak") 
    print(ret)  
