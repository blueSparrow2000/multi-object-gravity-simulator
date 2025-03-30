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
    def __init__(self, master, function_to_call, x,y, name, text_size=20,text_color = 'black', button_length=120, button_height=30, color = (150,150,150), hover_color = (80,80,80), move_ratio = [1,0]):
        self.master = master # 버튼이 부를 함수가 정의되어있는 주인 클래스 (여기 안에서만 이 버튼이 정의되며 존재함)
        self.function_to_call = function_to_call # given by string
        self.x = x
        self.y = y
        self.move_ratio = move_ratio
        self.name = name
        self.text_size = text_size
        self.text_color = text_color
        self.button_length = button_length
        self.button_height = button_height
        self.hover_color = hover_color
        self.original_color = color
        self.color = color
        self.hover = False

        self.text = Text(self.x, self.y, self.name,size = self.text_size,color=self.text_color)
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
    def __init__(self, master, function_to_call, x, y, name, text_size=20,text_color = 'black', button_length=120, button_height=30,
                 color=(150, 150, 150), hover_color=(80, 80, 80),move_ratio = [1,0], toggle_text_dict = None, toggle_variable = None, max_toggle_count = 2):
        super().__init__(master, function_to_call, x, y, name, text_size,text_color, button_length, button_height,color, hover_color,move_ratio)
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



class Selector():
    def __init__(self, x, y, name, choices, text_sizes=[15,17,23,17,15],
                 colors=[(90, 90, 90),(130, 130, 130),(150, 150, 150),(130, 130, 130),(90, 90, 90)], move_ratio = [0.5,0.5]):
        self.x = x # center coordinate
        self.y = y # center coordinate
        self.move_ratio = move_ratio
        self.name = name
        self.text_sizes = text_sizes
        self.colors = colors

        self.select_pointer = 2 # having second entity pointing as default
        self.choices = choices
        self.choice = self.choices[self.select_pointer]

        self.choice_texts = []
        self.initialize_text()
        self.rect = None # includes text rect(should be made manually) and button rect -> if you are going to used selector in update screen

        self.name_text = Text(self.x, self.y - 120, self.name,size = 23,color=self.colors[2])

        self.buttons = [Button(self, 'up', self.x, self.y - 75, 'Λ',move_ratio = self.move_ratio,text_size=20,text_color=(100,100,100), button_length=30, button_height=30,
                 color=(0, 0, 0), hover_color=(10, 10, 10)),
                        Button(self, 'down', self.x, self.y + 75 , 'V',move_ratio = self.move_ratio,text_size=20,text_color=(100,100,100), button_length=30, button_height=30,
                 color=(0, 0, 0), hover_color=(10, 10, 10))]

    def scroll_up(self, mousepos):
        if self.check_inside_selector(mousepos):
            return self.up()

    def scroll_down(self, mousepos):
        if self.check_inside_selector(mousepos):
            return self.down()

    def check_inside_selector(self, mousepos):
        if abs(mousepos[0] - self.x) < 70 and abs(
                mousepos[1] - self.y) < 75:
            return True
        else:
            return False

    # 이거 main에서 클릭할때 불러줘야함 - 스크롤시엔 각 경우마다 up/down을 직접 불러야함
    def buttons_on_click(self, mousepos):
        ret = False
        for button in self.buttons:
            temp = button.on_click(mousepos)
            if temp: # if some output exists
                ret = temp
        return ret

    def up(self):
        return self.update_pointer(-1)

    def down(self):
        return self.update_pointer(1)

    def initialize_text(self):
        self.choice_texts = []
        for i in range(len(self.text_sizes)): # assert len(self.text_sizes) == len(self.colors) == len(self.choices)
            choice_text = Text(self.x, self.y + (i-2)*(29 - abs(i-2)*3), self.choices[i],size = self.text_sizes[i],color=self.colors[i])
            self.choice_texts.append(choice_text)

    def get_current_choice(self):
        # print("Selected system: {}".format(self.choice))
        return self.choice

    def check_bound(self):
        if self.select_pointer < 0: # unchanged
            self.select_pointer = 0
        elif self.select_pointer > len(self.choices) - 1:
            self.select_pointer = len(self.choices) - 1
        else:
            return True # changed
        return False # unchanged

    # pointer NOT periodic
    # if pointer value is changed, return True, else False
    def update_pointer(self, amt):
        self.select_pointer += amt
        changed_flag = self.check_bound()
        if changed_flag:
            self.choice = self.choices[self.select_pointer] # change choice
            self.update_texts() # update text contents too
        return changed_flag

    # if pointer changed, update text contents
    def update_texts(self):
        for i in range(len(self.text_sizes)):  # assert len(self.text_sizes) == len(self.colors) == len(self.choices)
            content = ""
            index_to_grab = self.select_pointer + (i-2)
            if  0 <= index_to_grab <= len(self.choices) - 1: # proper content exist
                content = self.choices[index_to_grab]
            self.choice_texts[i].change_content(content)

    # move ratio 0.5 is when assumed to be in the middle of the screen
    def move_to(self, dx,dy):
        # change my coord
        self.x += dx*self.move_ratio[0]
        self.y += dy*self.move_ratio[1]
        # change text pos
        for i in range(len(self.text_sizes)): # assert len(self.text_sizes) == len(self.colors) == len(self.choices)
            selection_text = self.choice_texts[i]
            selection_text.change_pos(self.x, self.y + (i-2)*(29 - abs(i-2)*3))
        self.name_text.change_pos(self.x,self.y- 120)
        # change button pos
        for button in self.buttons:
            button.move_to(dx,dy)
        # change rect pos

    def draw(self, screen):
        # Write name
        self.name_text.write(screen)
        # write selection text
        for selection_text in self.choice_texts:
            selection_text.write(screen)

        # draw buttons
        for button in self.buttons:
            getattr(button, 'draw_button')(screen)


'''
Read all content in specified image_folder and draws content of the same name 
'''
class Preview():
    def __init__(self, x, y, name, image_folder, image_size = [200,200] , initiial_img_name = "",move_ratio = [0.5,0.5]):
        self.x = x  # center coordinate
        self.y = y  # center coordinate
        self.image_size = image_size # fixed
        self.move_ratio = move_ratio
        self.name = name
        self.image_folder = image_folder
        self.image_names = list()
        self.image_dict = dict()
        self.current_content = None # current image to draw

        self.initialize(initiial_img_name)

    # initially download images
    def initialize(self,initiial_img_name):
        self.image_names = self.read_all_image_names()

        for img_name in self.image_names:
            img = Image(self.x,self.y, "%s"%img_name ,folder = self.image_folder,size = self.image_size)
            # 이미지 회전해서 넣기 (아케아처럼)
            self.image_dict[img_name] = img

        self.change_content(initiial_img_name)

    def read_all_image_names(self):
        image_names = list(os.listdir(self.image_folder[1:]))
        # remove '.png' part
        image_names = [system_name[:-4] for system_name in image_names]
        # print(image_names)
        return image_names

    # draw if current content is not None
    def draw(self,screen):
        if self.current_content:
            self.current_content.draw(screen)

    def move_to(self,dx,dy):
        # change my coord
        dx_motion = dx * self.move_ratio[0]
        dy_motion = dy * self.move_ratio[1]
        self.x += dx_motion
        self.y += dy_motion
        for img_name in self.image_names:
            img_to_move = self.image_dict[img_name]
            if img_to_move:
                img_to_move.move_image(dx_motion,dy_motion)

    # if it is in jacket name list, use it. Otherwise, leave as None
    def change_content(self,content_name):
        if content_name in self.image_names:
            self.current_content = self.image_dict[content_name]
        else:
            self.current_content = None
            # print("no img named '{}' in the folder '{}'".format(content_name,self.image_folder) )






