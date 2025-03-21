"""

"""
import pygame
import os, sys
import math
from variables import WIDTH,HEIGHT

'''
basic text box
'''
class Text():
    def __init__(self, x, y, content, size=20, color='darkturquoise',frames=100): #color aqua
        self.x = int(x)
        self.y = int(y)
        self.frames = frames
        self.size = size
        self.color = color
        self.paintable = True
        if not (self.size <= self.y <= HEIGHT-self.size):
            self.paintable = False
            print('text y out of range!')
            #raise Exception('text y out of range!')
        if not (self.size <= self.x <= WIDTH-self.size):
            self.paintable = False
            print('text x out of range!')
            #raise Exception('text y out of range!')
        
        self.content = content
        self.font = pygame.font.SysFont('arial', size)
        self.text = self.font.render(self.content, True, self.color)
        # text.set_alpha(127)
        self.textRect = self.text.get_rect()
        self.textRect.center = (self.x, self.y)
        
    def change_pos(self,x,y):
        self.x = int(x)
        self.y = int(y)
        self.textRect.center = (self.x, self.y)
        
    def change_content(self, content):
        self.content = content
        self.text = self.font.render(self.content, True, self.color)
        self.textRect = self.text.get_rect()
        # self.textRect.center = (self.x, self.y)
    
    def write(self,screen): 
        if self.paintable:
            screen.blit(self.text, self.textRect)


'''
write center-alligned multiple line text 
'''
class MultiText():
    def __init__(self, x, y, content, size=20, color='darkturquoise', frames=100, content_per_line=10): #color aqua
        self.x = int(x)
        self.y = int(y)
        self.frames = frames
        if not (0 <= self.y <= HEIGHT):
            raise Exception('text y out of range!')
        self.size = size
        self.color = color
        
        # string alligning process
        self.content_blocks = []
        
        total_length = len(content)
        current_start = 0
        cnt = 0
        while current_start + content_per_line < total_length:
            text_content = Text(self.x, self.y+cnt*self.size, content[current_start:current_start+content_per_line], self.size ,self.color,self.frames)
            self.content_blocks.append(text_content)
            current_start += content_per_line
            cnt += 1
        last_content = Text(self.x, self.y+cnt*self.size, content[current_start:total_length],self.size ,self.color,self.frames)
        self.content_blocks.append(last_content)
        
    def write(self,screen):
        for text_box in self.content_blocks:
            text_box.write(screen)

'''
music player
'''
class MusicBox():
    def __init__(self):
        pygame.mixer.init()
        mixer_channel_num = 8  # default 로 8임
        self.current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.MUSIC_FOLDER = self.current_dir+'/musics/'
        self.SOUND_EFFECT = self.current_dir+'/sound_effects/'
        
        self.sound_effect_list = ['confirm','fissure','glass_break','lazer','metal','railgun_reload','shruff','smash','sudden','swing_by','thmb']
        self.sound_effects = dict()
        for sound in self.sound_effect_list:
            self.sound_effects[sound] = pygame.mixer.Sound(self.SOUND_EFFECT+sound+'.mp3')

    
    def music_Q(self,music_file,repeat = False): #현재 재생되고 있는 음악을 확인하고 음악을 틀거나 말거나 결정해야 할때 check_playing_sound = True 로 줘야 함
        try:
            full_path = os.path.join(self.MUSIC_FOLDER, '%s.mp3'%music_file)
            pygame.mixer.music.load(full_path)
        except:
            full_path = os.path.join(self.MUSIC_FOLDER, '%s.wav'%music_file)
            pygame.mixer.music.load(full_path)
    
        pygame.mixer.music.set_volume(1) # 0.5
        if repeat:
            pygame.mixer.music.play(-1)
        else:
            pygame.mixer.music.play()

    def collision_sound_effect(self, type1, type2): # for fun! you cant hear sound in space tho
        # print("collision between {} and {} type".format(type1, type2))
        if type1=='gas' or type2=='gas': # if they contain at least one gas type
            self.play_sound_effect('shruff')
        else: # no gas planets
            if type1=='icy' or type2=='icy': # at least one ice type
                self.play_sound_effect('glass_break')
            else:  # rocky, metal
                if type1 == 'metal' or type2 == 'metal':
                    self.play_sound_effect('metal')
                else:
                    self.play_sound_effect('fissure')

    def play_sound_effect(self,name):
        self.sound_effects[name].play()
    
    
soundPlayer = MusicBox()
