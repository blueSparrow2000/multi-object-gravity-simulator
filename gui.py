'''
Buttons and GUI design here

'''
from util import *

class Button():
    def __init__(self, master, function_to_call, x,y, name, text_size=20, button_length=100, button_width=30, color = (200,200,200), hover_color = (150,150,150)):
        self.master = master # 버튼이 부를 함수가 정의되어있는 주인 클래스 (여기 안에서만 이 버튼이 정의되며 존재함)
        self.function_to_call = function_to_call # given by string
        self.x = x
        self.y = y
        self.name = name
        self.text_size = text_size
        self.button_length = button_length
        self.button_width = button_width
        self.hover_color = hover_color
        self.original_color = color
        self.color = color
        self.hover = False

        self.text = Text(self.x, self.y, self.name,size = self.text_size,color='black')

    def check_inside_button(self,mousepos):
        if abs(mousepos[0] - self.x) < self.button_length//2 and abs(
                mousepos[1] - self.y) < self.button_width//2:
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
                         [self.x - self.button_length // 2, self.y - self.button_width // 2, self.button_length,self.button_width])
        self.text.write(screen)
