'''
Buttons and GUI design here

'''
from util import *

class Button():
    def __init__(self, master, function_to_call, x,y, name, text_size=20, button_length=120, button_height=30, color = (200,200,200), hover_color = (100,100,100)):
        self.master = master # 버튼이 부를 함수가 정의되어있는 주인 클래스 (여기 안에서만 이 버튼이 정의되며 존재함)
        self.function_to_call = function_to_call # given by string
        self.x = x
        self.y = y
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

class ToggleButton(Button):
    def __init__(self, master, function_to_call, x, y, name, text_size=20, button_length=120, button_height=30,
                 color=(200, 200, 200), hover_color=(100, 100, 100), toggle_text = ['before','after'], toggle_variable = None, max_toggle_count = 2):
        super().__init__(master, function_to_call, x, y, name, text_size, button_length, button_height,color, hover_color)
        self.toggle_text = toggle_text
        self.toggle_count = 0
        self.max_toggle_count = max_toggle_count
        self.toggle_variable = toggle_variable # for synchronization
        self.toggle_tracker = toggle_variable[0]

        # self.text = Text(self.x, self.y, "{}: {}".format(self.toggle_text[self.toggle_count],self.toggle_variable[0]), size=self.text_size, color='black')
        self.text = Text(self.x, self.y, "{}: {}".format(self.name,self.toggle_variable[0]), size=self.text_size, color='black')

    def update_toggle_count(self):
        self.toggle_count += 1
        if self.toggle_count == self.max_toggle_count: # reset
            self.toggle_count = 0

    def update_toggle_tracker(self, togglevar):
        self.toggle_tracker = togglevar

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

    def initialize(self):
        self.synch()