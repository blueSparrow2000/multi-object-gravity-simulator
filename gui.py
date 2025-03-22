'''
Buttons and GUI design here

move_ratio = [ratio_x, ratio_y]
현재 맵에서 어느 위치에 지정되었느냐에 따라 화면 크기가 변할때 얼마나 움직여야 하는지가 다르다
오른쪽 모서리에 고정된 버튼은 y 움직임 없어야 하므로 [1,0]
가운데 위치한 버튼은 (self.y//2 같이 /2 operation이 붙을시 y 길이 증가함에 따라 반만 증가) [0.5,0.5]
어중간하게 중간이면 이런식 [0.5,1]
'''
from matplotlib.pyplot import xscale

from util import *

class Button():
    def __init__(self, master, function_to_call, x,y, name, text_size=20, button_length=120, button_height=30, color = (150,150,150), hover_color = (80,80,80), move_ratio = [1,0]):
        self.master = master # 버튼이 부를 함수가 정의되어있는 주인 클래스 (여기 안에서만 이 버튼이 정의되며 존재함)
        self.function_to_call = function_to_call # given by string
        self.x = x
        self.y = y
        self.move_ratio = move_ratio
        self.name = name
        self.text_size = text_size
        self.button_length = button_length
        self.button_height = button_height
        self.hover_color = hover_color
        self.original_color = color
        self.color = color
        self.hover = False

        self.text = Text(self.x, self.y, self.name,size = self.text_size,color='black')
        self.rect = pygame.Rect((self.x -button_length//2 ,self.y-button_height//2),(button_length,button_height))

    def check_inside_button(self,mousepos):
        if abs(mousepos[0] - self.x) < self.button_length//2 and abs(
                mousepos[1] - self.y) < self.button_height//2:
            return True
        else:
            return False

    def on_click(self,mousepos):
        if self.check_inside_button(mousepos):
            return getattr(self.master, self.function_to_call)() # 리턴값이 있다면 여기서 리턴해준다

    def hover_check(self,mousepos): # mousemotion일때 불러줘야함
        inside = self.check_inside_button(mousepos)
        if (not self.hover) and inside: # 호버 아니었는데 버튼 위에 올라옴 => 호버시작
            self.color = self.hover_color
            self.hover = True
        elif self.hover and not inside: # 호버링이었는데 벗어남 => 호버 끝
            self.color = self.original_color
            self.hover = False

    def draw_button(self,screen):
        pygame.draw.rect(screen, self.color,
                         [self.x - self.button_length // 2, self.y - self.button_height // 2, self.button_length,self.button_height])
        self.text.write(screen)

    def initialize(self):
        pass

    def get_all_rect(self):
        return [self.rect]

    def move_to(self, dx,dy):
        # change my coord
        self.x += dx*self.move_ratio[0]
        self.y += dy*self.move_ratio[1]
        # change text pos
        self.text.change_pos(self.x,self.y)
        # change rect pos
        self.rect.x = self.x - self.button_length // 2
        self.rect.y = self.y - self.button_height // 2

class ToggleButton(Button):
    def __init__(self, master, function_to_call, x, y, name, text_size=20, button_length=120, button_height=30,
                 color=(150, 150, 150), hover_color=(80, 80, 80),move_ratio = [1,0], toggle_text_dict = None, toggle_variable = None, max_toggle_count = 2):
        super().__init__(master, function_to_call, x, y, name, text_size, button_length, button_height,color, hover_color,move_ratio)
        self.toggle_text_dict = toggle_text_dict
        self.toggle_count = 0
        self.max_toggle_count = max_toggle_count
        self.toggle_variable = toggle_variable # for synchronization
        self.toggle_tracker = toggle_variable[0]

        # self.text = Text(self.x, self.y, "{}: {}".format(self.toggle_text_dict[self.toggle_count],self.toggle_variable[0]), size=self.text_size, color='black')
        self.text = Text(self.x, self.y, "{}: {}".format(self.name,self.toggle_variable[0]), size=self.text_size, color='black')

        self.text_explanation_rect = None

        if self.toggle_text_dict:
            self.explain_text_offset = [0 , self.text_size*2]
            self.text_explanation = Text(self.x+self.explain_text_offset[0], self.y + self.explain_text_offset[1], self.get_explanation(), size=15, color='gray')
            self.text_explanation_rect = pygame.Rect((self.x -button_length//2 + self.explain_text_offset[0],self.y-button_height//2 + self.explain_text_offset[1]),(button_length,button_height))


    def get_all_rect(self):
        if not self.toggle_text_dict:
            return super().get_all_rect()
        return [self.rect, self.text_explanation_rect]

    def get_explanation(self):
        return self.toggle_text_dict[self.toggle_tracker]

    def update_explanation(self):
        if self.toggle_text_dict:
            self.text_explanation.change_content(self.get_explanation())

    def on_click(self,mousepos):
        if self.check_inside_button(mousepos): # 반드시 토글변수가 바뀜
            do_toggle = getattr(self.master, self.function_to_call)()
            # self.update_toggle_count()
            # print(self.name,self.toggle_variable[0])
            self.synch()
            return do_toggle# 리턴값이 있다면 여기서 리턴해준다

    def synch(self):
        if self.toggle_variable[0] != self.toggle_tracker:
            self.update_toggle_tracker(self.toggle_variable[0])
            self.text.change_content("{}: {}".format(self.name,self.toggle_variable[0]))
            self.update_explanation()

    def initialize(self):
        self.synch()

    def update_toggle_tracker(self, togglevar):
        self.toggle_tracker = togglevar

    # not used
    def update_toggle_count(self):
        self.toggle_count += 1
        if self.toggle_count == self.max_toggle_count: # reset
            self.toggle_count = 0

    def draw_button(self,screen):
        super().draw_button(screen)
        # draw explanation if needed
        if self.hover and self.toggle_text_dict:
            pygame.draw.rect(screen, 'black',
                             [self.x - self.button_length // 2 + self.explain_text_offset[0], self.y - self.button_height // 2 + self.explain_text_offset[1], self.button_length,
                              self.button_height])
            self.text_explanation.write(screen)

    def move_to(self, dx,dy):
        super().move_to(dx,dy)
        # change explanation rect pos
        if self.toggle_text_dict:
            # change explanation text pos
            self.text_explanation.change_pos(self.x+self.explain_text_offset[0], self.y+self.explain_text_offset[1])
            self.text_explanation_rect.x = self.x - self.button_length // 2 + self.explain_text_offset[0]
            self.text_explanation_rect.y = self.y - self.button_height // 2 + self.explain_text_offset[1]