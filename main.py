"""
Created on Tue Mar 18 20:24:35 2025

@author: kingc

features
(key up, down, right, left): camara movement
(mouse click on a matter): lock center on a matter, click
again to unlock (resizing window also unlocks)
(mouse wheel): zoom in and zoom out
(mouse click&drag): camara movement
press 'v' to toggle VERBOSE and UI
press 't' to toggle Trail
press 'ESC' or 'Space' to pause in simulation screen (pause)

TBU
- matter maker system (UI for easy addition of matter)


P.S.
생각보다 내가 개선한 방식으로는 안정적인 궤도를 만들기가 더 어렵다 -> dt를 매우 작게해야 내 AD방식이 돌아감
현실이 그런건가 아니면 내 방식이 잘못된건가? 
현실에선 타원이나 원궤도가 만들어지기 쉬울것 같은데 이 코드에선 다 태양에 부딫히거나 멀리 날라가버리거나 둘 중 하나만 나온다
"""
import pygame

from fileIO import *
from gui import *
from variables import HELP_TEXT
pygame.init()

class Simulator():
    DEBUG = False
    def __init__(self, w=700, h=700):
        Matter.DEBUG = Simulator.DEBUG
        self.w = w
        self.h = h
        self.FPS = 100#100#60
        self.BUSYFPS = 30
        # self.speedup_dict = {1:'x0.1',5:'x0.5',10:'x1',20:'x2', 40:'x4', 80:'x8'}
        self.speedup_dict = {'x0.1': 1, 'x0.5': 5, 'x1': 10, 'x2': 20, 'x4': 40, 'x8': 80}
        self.speedup_list = list(self.speedup_dict.keys())
        self.speedup_idx = 2
        self.SPEEDUP_str = [self.speedup_list[self.speedup_idx]]# 이걸 변화시킬거임
        self.SPEEDUP = [self.speedup_dict[self.SPEEDUP_str[0]]]

        self.VERBOSE = [True]
        self.SHOWTRAIL = [True]
        self.time = 0 # time in delta_t (10 delta_t = 1 time)
        self.screen_timer = Text(self.w//2, 16, "Timestep: %d"%(int(self.time)), size = 30)

        # init display
        self.display = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE|pygame.SRCALPHA) #pygame.display.set_mode((self.w, self.h), pygame.SRCALPHA)
        pygame.display.set_caption('Gravity')
        self.clock = pygame.time.Clock()
        self.display.fill((0,0,0))

        # matter reader
        self.mr = MatterReader()
        self.matter_list = []
        self.artificial_list = []
        self.matter_including_artificial_list = [] # human made matters - which has very little mass itself, so it does not affect matter_list, but be affected by them

        # selector
        self.system_names = self.mr.get_system_names()
        self.selector = Selector(3*self.w//4, 3*self.h//8 + 50, 'Select System', self.system_names)  # make a selector

        # preview
        self.preview = Preview(self.w//4, 3*self.h//8 - 50,'Jacket Preview', "/jackets/",initiial_img_name=self.selector.get_current_choice())

        # mouse scroll / zoom parameter
        self.scale_unit = 0.1
        self.scale = 1

        # mouse click drag variable
        self.base_drag = None
        
        # trace option
        self.transparent_screen = pygame.Surface((self.w, self.h))
        self.transparent_screen.fill((40, 40, 40))
        self.transparent_screen.set_alpha(100) # 0: transparent / 255: opaque
        
        # lock matter
        self.lock = False
        self.locked_matter = None # no matter has ID 0
        self.lock_vector = [0,0]
        self.center = [self.w//2, self.h//2]
        self.text_paint_request = []
        self.info_text = None

        # smooth transition
        self.smooth_interval_num = 16*self.SPEEDUP[0]
        self.smooth_interval = self.smooth_interval_num

        # simulation method
        self.simulation_method_dict = {'E':'Euler method', 'LF': 'Leapfrog method','AD': 'Acceleration Decomposition','RK4':'Runge-Kutta 4th order'}
        self.simulation_method_list = list(self.simulation_method_dict.keys())
        self.simulation_method_idx = 3
        self.simulation_method = [self.simulation_method_list[self.simulation_method_idx]]  # 'RK4'  # 'AD': Acceleration Decomposition (my suggestion) / 'E': Euler method / 'LF': Leapfrog method / 'RF4': Runge-Kutta 4th order

        # simulation system initial setting
        self.system_name = 'matters'

        # buttons
        self.main_title_text = Text(self.w // 2, min(self.h // 8, 100), "Gravity Simulator", size=30, color=(180, 180, 180))
        self.main_version_text = Text(self.w // 2, min(self.h // 8, 100) + 30, "V 1.0", size=15, color=(150, 150, 150))

        self.main_screen_buttons = [Button(self, 'simulation_screen', self.w//2, self.h - 150, 'Simulate',move_ratio=[0.5,1]),
                                    Button(self, 'help_screen', self.w // 2, self.h - 100, 'Help', move_ratio=[0.5, 1]),

                                    Button(self, 'quit_simulation', self.w - 25, 15, 'QUIT', button_length=50,color = (60,60,60), hover_color = (100,100,100))]
        self.main_screen_toggle_buttons = [ToggleButton(self, 'toggle_simulation_method', self.w // 2, self.h - 225,
                                                 'Simulation method', toggle_variable=self.simulation_method,
                                                 toggle_text_dict=self.simulation_method_dict, button_length=160,
                                                 text_size=16, move_ratio=[0.5, 1])]

        self.pause_screen_toggle_buttons = [ToggleButton(self, 'toggle_trail', self.w//2, self.h//2 + 200, 'TRAIL',toggle_variable = self.SHOWTRAIL,move_ratio=[0.5,1]),
                                            ToggleButton(self, 'toggle_verbose', self.w//2, self.h//2 + 150, 'UI',toggle_variable = self.VERBOSE,move_ratio=[0.5,1]),
                                            ToggleButton(self, 'toggle_simulation_method', self.w//2, self.h//2 + 50, 'Simulation method',toggle_variable = self.simulation_method, toggle_text_dict = self.simulation_method_dict,button_length=160, text_size=16,move_ratio=[0.5,1]),
                                            ToggleButton(self, 'toggle_speedup', self.w//2, self.h//2, 'SPEED UP',toggle_variable = self.SPEEDUP_str, toggle_text_dict = None,button_length=160, text_size=16,move_ratio=[0.5,1])]
        self.pause_screen_buttons = [Button(self, 'go_to_main', self.w//2, self.h//2 + 250, 'Main menu',move_ratio=[0.5,1]),
                                     Button(self, 'unpause', self.w - 30, 15, 'Back', button_length=60)]


        # put all pause screen rects here! this includes interactable things like buttons! -> extract rects!
        self.pause_screen_rects = [] # this is used to efficiently draw on pause screen
        for pause_screen_button in self.pause_screen_buttons+self.pause_screen_toggle_buttons:
            for item in pause_screen_button.get_all_rect():
                self.pause_screen_rects.insert(0, item)

        self.simulation_screen_buttons = [Button(self, 'pause', self.w - 30, 15, 'Pause', button_length=60,color = (30,30,30), hover_color = (80,80,80))]
        self.option_screen_buttons = []

        # help text
        self.help_title_text = Text(self.w//2, min(self.h//8,100), "MANUAL", size=30,color= (180,180,180))
        self.help_text = MultiText(self.w//2, self.h//5, HELP_TEXT, size=22, content_per_line=60, color = (150,150,150), text_gap = 20)
        self.help_screen_buttons = [Button(self, 'back_to_main', self.w//2, self.h - 100, 'Back',move_ratio=[0.5,1])]
        self.help_screen_rects = []
        for help_screen_button in self.help_screen_buttons:
            for item in help_screen_button.get_all_rect():
                self.help_screen_rects.insert(0, item)

        self.artificial_ui_buttons = [
            Button(self, 'orbit', 4* self.w // 5 , self.h // 2 - 25, 'ORBIT', move_ratio=[0.8, 0.5]),
            Button(self, 'descend', 4* self.w // 5 , self.h // 2 + 25, 'DESCEND', move_ratio=[0.8, 0.5])]

        self.matter_ui_buttons = [Button(self, 'spawn_rocket', 4* self.w // 5 , self.h // 2 , 'SPAWN', move_ratio=[0.8, 0.5])]

        self.mapmaker_screen_buttons = []

        self.all_buttons = self.main_screen_buttons + self.main_screen_toggle_buttons + self.pause_screen_toggle_buttons + self.pause_screen_buttons + self.simulation_screen_buttons + self.option_screen_buttons + self.help_screen_buttons + self.mapmaker_screen_buttons + self.artificial_ui_buttons + self.matter_ui_buttons

    def simulation_screen(self): # 2
        self.initialize()  # '2 body'
        self.button_function(self.simulation_screen_buttons, 'initialize')

        flag = True
        while flag:
            for i in range(self.SPEEDUP[0]-1): # fast forward (not using pygame features) => 10 times speedup? (if pygame is bottleneck)
                self.calculate_without_frame()
            flag = self.play_step()
            if flag == 'pause':  # quit pygame
                pygame.mixer.pause()
                flag = self.pause_screen() # flag가 false면 main으로!
                pygame.mixer.unpause()
        return True

    def toggle_speedup(self):
        self.speedup_idx += 1
        if self.speedup_idx == len(self.speedup_list):
            self.speedup_idx = 0
        self.SPEEDUP_str[0] = self.speedup_list[self.speedup_idx]
        self.SPEEDUP[0] = self.speedup_dict[self.SPEEDUP_str[0]]

        self.smooth_interval_num = 16 * self.SPEEDUP[0]

    def button_function(self, button_list, function_name, *args):
        flag = None # false가 아닌 값이 하나라도 있다면 그 값을 리턴(무작위라 보면 됨. 버튼 순서에 따라 달라져서. 마지막 버튼의 리턴이 우선 - 근데 버튼은 안겹쳐 한번에 하나만 선택가능임)
        if len(args)==0: # no input
            for button in button_list:
                ret = getattr(button,function_name)()
                if ret:
                    flag = ret
        elif len(args)==1: # one input -> given as tuples
            for button in button_list:
                ret = getattr(button,function_name)(args[0])
                if ret:
                    flag = ret
        else: # multi inputs
            for button in button_list:
                ret = getattr(button,function_name)(args)
                if ret:
                    flag = ret
        return flag

    def toggle_simulation_method(self):
        self.simulation_method_idx += 1
        if self.simulation_method_idx == len(self.simulation_method_list):
            self.simulation_method_idx = 0
        self.simulation_method[0] = self.simulation_method_list[self.simulation_method_idx]  # 'RK4'  # 'AD': Acceleration Decomposition (my suggestion) / 'E': Euler method / 'LF': Leapfrog method / 'RF4': Runge-Kutta 4th order

    def toggle_trail(self):
        self.SHOWTRAIL[0] = not self.SHOWTRAIL[0]

    def toggle_verbose(self):
        self.VERBOSE[0] = not self.VERBOSE[0]

    def quit_simulation(self):
        pygame.quit()
        return False

    def reset(self):
        self.mr.reset()

        self.remove_matter() # artificial list 도 함께 없앰

        self.time = 0  # time in delta_t (10 delta_t = 1 time)
        self.scale = 1

        self.lock = False
        self.locked_matter = None # no matter has ID 0
        self.lock_vector = [0,0]
        self.info_text = None

        self.text_paint_request = []

        self.smooth_interval = self.smooth_interval_num

    def remove_matter(self):
        for matter in self.matter_including_artificial_list:
            if matter.removed:
                # change locked target -> unlock
                if self.locked_matter is not None and self.locked_matter.matterID == matter.matterID:
                    self.unlock_matter()
                self.matter_including_artificial_list.remove(matter)
                if matter.object_type == 'matter': # 추가적으로 matter에서도 제거해주기
                    self.matter_list.remove(matter)
                del matter # 이건 필요 없을지도 . 파이썬 가비지 컬렉션이 처리

    def zoom_in(self,mousepos):
        if self.scale < 20:
            self.scale *= (1 + self.scale_unit)
            self.change_display_scale(mousepos, -1)
            # if self.VERBOSE[0]:
            #     print("Zoom in scale: {}".format(self.scale))

    def zoom_out(self,mousepos):
        if self.scale > 0.05:
            self.scale *= (1 - self.scale_unit)
            self.change_display_scale(mousepos, 1)
            # if self.VERBOSE[0]:
            #     print("Zoom out scale: {}".format(self.scale))

    # 매번 zoom in / out할때마다 불림
    def change_display_scale(self, mousepos, sign):
        centerX, centerY = self.center
        if self.lock: # if locked on
            pass
        elif mousepos: # not locked, mouse pos given
            centerX, centerY = mousepos

        for matter in self.matter_including_artificial_list:
            matter.change_cam_scale(sign*self.scale_unit, centerX, centerY)
            matter.change_radius_scale(self.scale)

    def adjust_camera(self,dx,dy):
        for matter in self.matter_including_artificial_list:
            matter.move_cam(dx,dy,preserve = True)
            
    def get_near_matter(self,mousepos):
        for matter in self.matter_including_artificial_list:
            if matter.check_clicked_on_display(mousepos):
                return matter
        return None

    def lock_matter(self, target_matter):
        soundPlayer.play_sound_effect('swing_by') 
        # assign lock if successful
        self.lock = True
        self.locked_matter = target_matter
        self.locked_matter.lock()
        self.reset_smooth_transition() # only update for the first timelock occured
        # info text 받아오기
        self.info_text = MultiText(self.w - 65, self.h - 65, self.locked_matter.get_info_text(), size=20, content_per_line=12)

        if self.VERBOSE[0]:
            lockText = Text(self.center[0], self.center[1] - 80, "Target locked: {}".format(target_matter.name), size=40,color= "darkred",frames = 3*self.FPS//2)
            self.text_paint_request.insert(0,lockText)
            print('{} locked!'.format(target_matter.name))
        
    def unlock_matter(self):
        # self.allign_display()
        # reset lock if successful
        locked_name = self.locked_matter.name
        self.locked_matter.unlock()
        self.lock = False
        self.locked_matter = None
        self.lock_vector = [0,0]
        # info text 초기화
        self.info_text = None

        if self.VERBOSE[0]:
            print('{} unlocked!'.format(locked_name))

    def reset_smooth_transition(self):
        self.smooth_interval = self.smooth_interval_num
        
    def follow_locked_matter(self):
        transitioning = self.smooth_interval >= 1
        dx, dy = 0,0
        if transitioning: # theres some left for smooth transition
            self.lock_vector = self.locked_matter.calculate_lock_vector(self.center)
            dx = self.lock_vector[0] / self.smooth_interval
            dy = self.lock_vector[1] /  self.smooth_interval
            if dx**2 + dy**2 <= 50: # close enough tolerance is given 50
                self.smooth_interval -= 1
        else: # not transitioning but lock
            # cancel movement completely
            lockx, locky = self.locked_matter.get_movement()
            dx, dy = -lockx*self.scale ,-locky*self.scale

        for matter in self.matter_including_artificial_list: # lock vector following은 이미 cam 공간에서 하므로 따로 scale을 곱해줄 필요가 없다!
            matter.move_cam(dx,dy, preserve = transitioning) # preserve while locking in progress

    def update_timer(self):
        self.time += delta_t*0.1

    # run simulation step - 이 함수 이후엔 update physics하기 전까지 p_next와 p 값이 다르다
    def calculate_physics(self):
        if self.simulation_method[0] == 'AD':
            for matter in self.matter_including_artificial_list:
                matter.calc_p()
                matter.calc_acceleration(self.matter_list)
                matter.calc_v_AD()
        elif self.simulation_method[0] == 'E':
            for matter in self.matter_including_artificial_list:
                matter.calc_acceleration(self.matter_list)
                matter.calc_v_Euler()
                matter.calc_p()
        elif self.simulation_method[0] == 'LF':
            # first pass - update all positions before recalculating new acceleration
            for matter in self.matter_including_artificial_list:
                matter.calc_v_LeapFrog()
                matter.calc_p()  # 기본적으로 update된 v로 구함
            # second pass
            for matter in self.matter_including_artificial_list:
                matter.calc_acceleration(self.matter_list)  # update 된 p_next로 구함
                matter.calc_v_LeapFrog_second_pass()  # do again
        elif self.simulation_method[0] == 'RK4':
            k_mat = [[], [], [], []]
            v_mat = [[], [], []]
            # first, second, third pass
            for RK4_pass in range(3):
                for matter_i in range(len(self.matter_including_artificial_list)):
                    matter = self.matter_including_artificial_list[matter_i]
                    acc = matter.calc_acceleration(self.matter_list)  # k 계산
                    matter.calc_p()  # 기본적으로 update된 v로 구함
                    k_mat[RK4_pass].append(acc)
                    v_temp = matter.calc_v_RK4(acc)  # v
                    v_mat[RK4_pass].append(v_temp)
            # final pass
            for matter_i in range(len(self.matter_including_artificial_list)):
                matter = self.matter_including_artificial_list[matter_i]
                acc = matter.calc_acceleration(self.matter_list)
                k_mat[3].append(acc)
                matter.set_v_next_RK4(k_mat[0][matter_i], k_mat[1][matter_i], k_mat[2][matter_i], k_mat[3][matter_i])
                matter.set_p_next_RK4(v_mat[0][matter_i], v_mat[1][matter_i], v_mat[2][matter_i])

        # angular velocity - only changed for artificials
        for artificial in self.artificial_list:
            artificial.calc_next_angle()
            artificial.calc_rot()



    def resize_window_updates(self):
        old_w, old_h = self.w, self.h
        self.w, self.h = self.display.get_width(), self.display.get_height()
        dx, dy = self.w - old_w, (self.h - old_h)

        # center 변경
        self.center = [self.w // 2, self.h // 2]

        # lock 걸린채로 resize할시 lock 풀기
        if self.lock:
            self.unlock_matter()

        # timer 의 위치 변경
        self.screen_timer.change_pos(self.w//2, 16)

        # infotext가 있다면 위치 바꾸기
        if self.info_text:
            if Simulator.DEBUG:
                self.info_text.change_pos(self.w - 65, self.h - 95)
            else:
                self.info_text.change_pos(self.w - 65, self.h - 65)

        # pause screen transparent rect resize
        # pygame.transform.scale(self.transparent_screen, (self.w,self.h)) # 걍 새로 만들었다
        self.transparent_screen = pygame.Surface((self.w, self.h))
        self.transparent_screen.fill((40, 40, 40))
        self.transparent_screen.set_alpha(100) # 0: transparent / 255: opaque

        # 모든 버튼의 위치 변경
        for buttons in self.all_buttons:
            buttons.move_to(dx, dy)

        # main, help text 위치 변경
        self.main_title_text.change_pos(self.w // 2, min(self.h // 8, 100))
        self.main_version_text.change_pos(self.w // 2, min(self.h // 8, 100) + 30)
        self.help_title_text.change_pos(self.w // 2, min(self.h // 8, 100))
        self.help_text.change_pos(self.w // 2, self.h // 5)

        # move selector
        self.selector.move_to(dx, dy)

        # move preview
        self.preview.move_to(dx, dy)

    def play_step(self): # get action from the agent
        self.update_timer()
        self.calculate_physics()

        # remove after checking collision
        self.remove_matter()
                
        # collect user input
        events = pygame.event.get()
        keys = pygame.key.get_pressed()  # 꾹 누르고 있으면 계속 실행되는 것들 # SHOULD BE CALLED AFTER pygame.event.get()!
        # handle key press for artificials
        for controlable in self.artificial_list:
            controlable.handle_key_press(keys[pygame.K_w],keys[pygame.K_s])
        # handle events
        for event in events:
            if event.type == pygame.QUIT:  # main
                # pygame.quit()
                return False # to main
            if event.type == pygame.WINDOWRESIZED:
                self.resize_window_updates()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:  # esc 키를 누르면 pause
                    return 'pause' # pause
                elif event.key == pygame.K_t:  # toggle trail
                    self.toggle_trail()
                elif event.key == pygame.K_v or event.key == pygame.K_u:  # toggle verbose
                    self.toggle_verbose()

                # handle input for artificials
                for controlable in self.artificial_list:
                    controlable.handle_key_input(event.key)


            if event.type == pygame.MOUSEMOTION:
                mousepos = pygame.mouse.get_pos()
                self.button_function(self.simulation_screen_buttons, 'hover_check', mousepos)
                if self.lock:
                    if self.locked_matter.object_type == 'artificial':  # lock 된 상태에서 UI 버튼을 누른 상황일떄 먼저 체크
                        self.button_function(self.artificial_ui_buttons, 'hover_check', mousepos)
                    elif self.locked_matter.object_type == 'matter':  # lock 된 상태에서 UI 버튼을 누른 상황일떄 먼저 체크
                        self.button_function(self.matter_ui_buttons, 'hover_check', mousepos)

                if self.base_drag: # 드래그가 켜져 있을때 마우스 이동시 카메라 변화시키기
                     # 현재 위치 (base는 이전 위치)
                    if mousepos:
                        dx = mousepos[0] - self.base_drag[0]
                        dy = mousepos[1] - self.base_drag[1]
                        self.adjust_camera(dx, dy)
                        self.base_drag = mousepos # 이동해두기
                    else: # 마우스가 화면 밖으로 나간 경우 (드래그하다 나갈수도 있음) 드래그 종료하기
                        self.base_drag = None # 드래그 종료

            # if mouse click is near a matter, then lock / unlock
            if event.type == pygame.MOUSEBUTTONUP:     # 마우스를 뗼떼 실행됨
                mousepos = pygame.mouse.get_pos()
                if event.button == 4 or event.button == 5: # scroll up or scroll down
                    pass
                if self.base_drag: # 드래그를 하던 중 클릭이 타겟위에서 끝났다 하더라도 드래그를 끝내는걸 우선시함, 드래그를 끝냄
                    self.base_drag = None # 드래그 종료
                else:
                    # 버튼을 누른것 또는 타깃을 클릭하기 위해 클릭한것
                    click_result = self.button_function(self.simulation_screen_buttons, 'on_click', mousepos)
                    if click_result: # pause인지 체크
                        return click_result
                    else:
                        if self.lock:
                            if self.locked_matter.object_type == 'artificial':  # lock 된 상태에서 UI 버튼을 누른 상황일떄 먼저 체크
                                self.button_function(self.artificial_ui_buttons, 'on_click', mousepos)
                            elif self.locked_matter.object_type == 'matter':  # lock 된 상태에서 UI 버튼을 누른 상황일떄 먼저 체크
                                self.button_function(self.matter_ui_buttons, 'on_click', mousepos)

                        target_matter = self.get_near_matter(mousepos)
                        if target_matter: # there exists a target matter
                            if self.lock: # already locked
                                if target_matter.matterID == self.locked_matter.matterID: # if already locked matter is selected again, unlock
                                    self.unlock_matter()
                                else: # clicked on a new matter => unlock and lock
                                    self.unlock_matter()
                                    self.lock_matter(target_matter)
                            else:
                                self.lock_matter(target_matter)
                        else:
                            # handle input for artificials
                            for controlable in self.artificial_list:
                                controlable.handle_click_input(mousepos)

            if event.type == pygame.MOUSEBUTTONDOWN: # 클릭 직후, 마우스 떼기 전
                mousepos = pygame.mouse.get_pos()
                if event.button == 4:  # scroll up
                    self.zoom_in(mousepos)
                    break
                elif event.button == 5:  # scroll down
                    self.zoom_out(mousepos)
                    break
                else:
                    target_matter = self.get_near_matter(mousepos)
                    # 버튼 클릭부터 체크
                    if self.button_function(self.simulation_screen_buttons, 'check_inside_button', mousepos):
                        pass
                    elif target_matter: # 타깃을 먼저 클릭한 경우 드래그 하지 않기
                        pass
                    else: # 타깃매터가 있는 위치가 아니었음 => 드래그 활성화
                        if not self.lock: # lock 이 아닐때만 드래그 이동 가능
                            self.base_drag = mousepos # 현재 마우스 위치가 드래그 기준점임

        if self.lock:
            self.follow_locked_matter() #################### !!! should be after calculating p_next (will subtract difference) !!!

        else: # adjust camera only if not locked
            if keys[pygame.K_UP]:
                self.adjust_camera(0,1)
            if keys[pygame.K_DOWN]:
                self.adjust_camera(0,-1)
            if keys[pygame.K_RIGHT]:
                self.adjust_camera(-1,0)
            if keys[pygame.K_LEFT]:
                self.adjust_camera(1,0)

        self.update_cam_position()

        # update ui and clock
        self._update_ui()
        self.update_real_position()
        self.clock.tick(self.FPS)

        return True # keep simulation loop

    # for fast forward
    def calculate_without_frame(self):
        self.update_timer()
        self.calculate_physics()
        self.remove_matter()
        if self.lock:
            self.follow_locked_matter()
        self.update_cam_position()
        self.update_real_position()

    def update_cam_position(self):
        for matter in self.matter_including_artificial_list:
            matter.cam_follow_physics(self.scale)

    def update_real_position(self):
        for matter in self.matter_including_artificial_list:
            matter.update_physics()

    def _update_ui(self):
        self.display.fill((0, 0, 0))
        
        # paint matters
        for matter in self.matter_including_artificial_list:
            matter.draw(self.display, self.SHOWTRAIL[0])

        # display text on screen
        if self.VERBOSE[0]:
            # show matter names 
            for matter in self.matter_including_artificial_list:
                matter.textFollow()
                matter.paintName(self.display)
            
            # show timer
            self.screen_timer.change_content("Timestep: %d"%(int(self.time)))
            self.screen_timer.write(self.display)
            
            # show temporary texts (camera lock etc.)
            lock_text_drawn = False
            for text_temp in self.text_paint_request:
                if text_temp.frames>0:
                    if not lock_text_drawn: # only draw one lock text at a time
                        if self.VERBOSE[0]: # double check verbose condition (for artificial's text request)
                            text_temp.write(self.display)
                        lock_text_drawn = True
                    text_temp.frames -= 1
                    if text_temp.frames==0:
                        self.text_paint_request.remove(text_temp)
                        
            # show locked target info
            if self.lock:
                if self.locked_matter.object_type == 'artificial':
                    self.button_function(self.artificial_ui_buttons, 'draw_button', self.display)
                    self.locked_matter.draw_fuel(self.display)
                elif self.locked_matter.object_type == 'matter':
                    '''
                    If current planet is 'occupied', you can generate artificials!
                    rocket: generates rocket that orbits current planet in the high orbit
                    station: generates station that orbits current planet in the low orbit
                    '''
                    self.button_function(self.matter_ui_buttons, 'draw_button', self.display)


                if Simulator.DEBUG:
                    self.info_text = MultiText(self.w - 65, self.h - 95, self.locked_matter.get_info_text(), size=20,
                                               content_per_line=12) # if you want constant update of info text
                self.info_text.write(self.display)
                # show direction for locked artificials
                for artificial in self.artificial_list:
                    artificial.draw_direction_arrow(self.display)


                for matter in self.matter_list:
                    matter.draw_velocity_arrow(self.display)


        # draw buttons (should be drawn regardless of verbose)
        self.button_function(self.simulation_screen_buttons, 'draw_button', self.display)

        pygame.display.flip()

    def initialize(self):
        self.reset()
        self.system_name = self.selector.get_current_choice()
        self.mr.read_matter(self.system_name)  # 3 body stable orbit / matters
        self.matter_list = self.mr.get_matter_list() # assign matter
        self.artificial_list = self.mr.get_artificial_list()
        for artificial in self.artificial_list:
            artificial.text_request = self.text_paint_request
        self.matter_including_artificial_list = self.matter_list + self.artificial_list  # assign artificial matters too
        for matter in self.matter_including_artificial_list:
            matter.initialize(self.matter_list)

    ### this is for testing images ###
    def minimum_display(self):
        # back = Image(0,0,'back_white')
        # back.draw(self.display)
        # galaxy = Drawable('galaxy',[100,100],[10,10], 'sparkles')
        min_display_buttons = [Button(self, 'simulation_screen', self.w//2, self.h//2, 'Simulate')]
        while 1:
            self.display.fill((0, 0, 0))
            # collect user input
            events = pygame.event.get()
            keys = pygame.key.get_pressed()  # 꾹 누르고 있으면 계속 실행되는 것들 # SHOULD BE CALLED AFTER pygame.event.get()!
            # handle events
            for event in events:
                if event.type == pygame.QUIT:  # 윈도우를 닫으면 종료
                    pygame.quit()
                    return False  # force quit
                if event.type == pygame.WINDOWRESIZED:
                    self.resize_window_updates()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:  # esc 키를 누르면 메인 화면으로
                        return False  # goto main
                if event.type == pygame.MOUSEMOTION:
                    mousepos = pygame.mouse.get_pos()
                    self.button_function(min_display_buttons, 'hover_check', mousepos)
                if event.type == pygame.MOUSEBUTTONUP:  # 마우스를 뗼떼 실행됨
                    mousepos = pygame.mouse.get_pos()
                    if self.button_function(min_display_buttons, 'check_inside_button', mousepos):
                        return self.button_function(min_display_buttons, 'on_click', mousepos) # 이게 에러를 냄. 바로 pygame quit시 none을 리턴

            # galaxy.update_p() # calc p_next
            # galaxy.cam_follow_physics(1) # move cam pos
            # galaxy.draw(self.display)
            # galaxy.update_physics() # p <- p_next
            self.button_function(min_display_buttons, 'draw_button', self.display)

            pygame.display.flip()
            self.clock.tick(self.FPS)

    # change the jacket image according to selection
    def selection_changed(self):
        current_choice_name = self.selector.get_current_choice()
        self.preview.change_content(current_choice_name)

    '''
    Choose map
    use while until user selects one of the option
    if player clicked simulation button, run below and return 1 (TBU)
    self.system_name # 이걸 여기서 바꿔주기
    '''
    def main_screen(self): # 1 -> pause screen과 유사 토글로 맵 종류 바꾸기
        self.button_function(self.main_screen_toggle_buttons, 'initialize')

        while 1:
            self.display.fill((0, 0, 0))
            # collect user input
            events = pygame.event.get()
            keys = pygame.key.get_pressed()  # 꾹 누르고 있으면 계속 실행되는 것들 # SHOULD BE CALLED AFTER pygame.event.get()!
            # handle events
            for event in events:
                if event.type == pygame.QUIT:  # 종료
                    pygame.quit()
                    return False  # force quit
                if event.type == pygame.WINDOWRESIZED:
                    self.resize_window_updates()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:  # 종료
                        pygame.quit()
                        return False  # quit
                if event.type == pygame.MOUSEMOTION:
                    mousepos = pygame.mouse.get_pos()
                    self.button_function(self.main_screen_buttons + self.main_screen_toggle_buttons, 'hover_check', mousepos)
                if event.type == pygame.MOUSEBUTTONUP:  # 마우스를 뗼떼 실행됨
                    mousepos = pygame.mouse.get_pos()
                    self.button_function(self.main_screen_toggle_buttons, 'on_click', mousepos)
                    # 버튼 클릭인 경우에만 리턴 -> 중복호출이 있음
                    if self.button_function(self.main_screen_buttons, 'check_inside_button', mousepos):
                        pygame.mixer.music.stop()
                        return self.button_function(self.main_screen_buttons, 'on_click',
                                                    mousepos)  # 이게 에러를 냄. 바로 pygame quit시 none을 리턴
                    if self.selector.buttons_on_click(mousepos):
                        self.selection_changed()
                if event.type == pygame.MOUSEBUTTONDOWN:  # 클릭 직후, 마우스 떼기 전
                    mousepos = pygame.mouse.get_pos()
                    if event.button == 4:  # scroll up
                        if self.selector.scroll_up(mousepos):
                            self.selection_changed()
                    elif event.button == 5:  # scroll down
                        if self.selector.scroll_down(mousepos):
                            self.selection_changed()

            self.button_function(self.main_screen_buttons + self.main_screen_toggle_buttons, 'draw_button', self.display)
            self.main_title_text.write(self.display)
            self.main_version_text.write(self.display)

            self.selector.draw(self.display)
            self.preview.draw(self.display)

            pygame.display.flip()
            self.clock.tick(self.FPS)

    def go_to_main(self):
        return False # escape current loop

    def back_to_main(self):
        return True # main loop의 flag를 True로 만들어줌

    # pause only used in simulation screen
    def pause(self):
        return 'pause'

    # only used in pause screen
    def unpause(self):
        return True # simulation screen

    def pause_screen(self): #4 show commands and how to use this simulator
        # draw transparent screen - stop increasing time, only clock tick for interaction, but still can click buttons, update display for buttons
        # increase FPS -> 토글로 할지 슬라이더로 조작할지 버튼으로 올릴지 나중에 선택 / toggle v,t -> button text 바뀜 / toggle simulation method / trail length
        self.display.blit(self.transparent_screen, (0, 0))
        pygame.display.flip()

        self.button_function(self.pause_screen_toggle_buttons, 'initialize')

        while 1:
            # collect user input
            events = pygame.event.get()
            keys = pygame.key.get_pressed()  # 꾹 누르고 있으면 계속 실행되는 것들 # SHOULD BE CALLED AFTER pygame.event.get()!
            # handle events
            for event in events:
                if event.type == pygame.QUIT:  # 윈도우를 닫으면 main으로
                    # pygame.quit()
                    return False  # main
                if event.type == pygame.WINDOWRESIZED:
                    self.resize_window_updates()
                    self.display.blit(self.transparent_screen, (0, 0))
                    pygame.display.flip() # if resize is done, redraw everything
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        return True # keep simulation
                if event.type == pygame.MOUSEMOTION:
                    mousepos = pygame.mouse.get_pos()
                    self.button_function(self.pause_screen_buttons + self.pause_screen_toggle_buttons, 'hover_check', mousepos)
                if event.type == pygame.MOUSEBUTTONUP:  # 마우스를 뗼떼 실행됨
                    mousepos = pygame.mouse.get_pos()
                    self.button_function(self.pause_screen_toggle_buttons, 'on_click', mousepos) # toggle은 리턴값을 안씀
                    if self.button_function(self.pause_screen_buttons, 'check_inside_button', mousepos):
                        return self.button_function(self.pause_screen_buttons, 'on_click', mousepos) # False: main / True: Keep simulation

            self.button_function(self.pause_screen_buttons + self.pause_screen_toggle_buttons, 'draw_button', self.display)

            pygame.display.update(self.pause_screen_rects)
            # pygame.event.pump() # in case update does not work properly
            self.clock.tick(self.BUSYFPS)

    def draw_help_text(self):
        self.display.fill((0, 0, 0))
        self.help_text.write(self.display)
        self.help_title_text.write(self.display)
        pygame.display.flip()

    def help_screen(self): #4 show commands and how to use this simulator
        self.draw_help_text()

        while 1:
            # collect user input
            events = pygame.event.get()
            keys = pygame.key.get_pressed()  # 꾹 누르고 있으면 계속 실행되는 것들 # SHOULD BE CALLED AFTER pygame.event.get()!
            # handle events
            for event in events:
                if event.type == pygame.QUIT:  # 윈도우를 닫으면 main으로
                    # pygame.quit()
                    return True  # main loop
                if event.type == pygame.WINDOWRESIZED:
                    self.resize_window_updates()
                    self.draw_help_text()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        return True  # main loop
                if event.type == pygame.MOUSEMOTION:
                    mousepos = pygame.mouse.get_pos()
                    self.button_function(self.help_screen_buttons, 'hover_check',mousepos)
                if event.type == pygame.MOUSEBUTTONUP:  # 마우스를 뗼떼 실행됨
                    mousepos = pygame.mouse.get_pos()
                    if self.button_function(self.help_screen_buttons, 'check_inside_button', mousepos):
                        return self.button_function(self.help_screen_buttons, 'on_click', mousepos) # False: main / True: Keep simulation

            self.button_function(self.help_screen_buttons, 'draw_button', self.display)

            pygame.display.update(self.help_screen_rects)
            # pygame.event.pump() # in case update does not work properly
            self.clock.tick(self.BUSYFPS)

    def map_maker_screen(self): #4 show commands and how to use this simulator
        pass

    # sound effect, bgm etc.
    def option_screen(self): # 3
        # use while until user clicks to get out of the current screen
        pass

    '''
    1. find nearest planet 
    2. from current position, calculate the velocity vector to orbit the planet: should know distance from planet and mass, and current position (direction of v should be tangent to pos vector)
    3. adjust the velocity vector 
    '''
    def orbit(self):
        nearness_threshold = 100**2 # planet should be at least 100 meters far to orbit
        orbiter = self.locked_matter
        nearest_planet = None # find nearest planet
        min_dist = nearness_threshold
        for matter in self.matter_list:
            dist_squared = ((orbiter.p[0] - matter.p[0])**2 + (orbiter.p[1] - matter.p[1])**2)
            if min_dist > dist_squared: # change pivot
                nearest_planet = matter
                min_dist = dist_squared

        if nearest_planet and nearest_planet.mass >= 10: # if found and big enough
            lockText = Text(self.center[0], self.center[1] - 80, "Orbiting {}".format(nearest_planet.name),
                            size=30, color="darkred", frames=self.FPS)
            self.text_paint_request.insert(0, lockText)
            print("Nearest planet found: ", nearest_planet.name)

            dist_root = min_dist ** (1 / 2)
            # calculate speed needed
            orbital_speed = (G * nearest_planet.mass / dist_root ) ** (1/2)
            # calculate directional vector & multiply direction and speed = velocity
            factor = orbital_speed/dist_root
            dP = [factor* (orbiter.p[0] - nearest_planet.p[0]), factor*(orbiter.p[1] - nearest_planet.p[1])]
            # rotate to get orthogonal vectors
            rv1 = orbiter.rotate_vector(dP, math.pi / 2)
            rv2 = orbiter.rotate_vector(dP, -math.pi/2)
            v1 = [rv1[0] + nearest_planet.v_next[0], rv1[1] + nearest_planet.v_next[1]]
            v2 = [rv2[0] + nearest_planet.v_next[0], rv2[1] + nearest_planet.v_next[1]]

            # assign that velocity to the artificial: choose between two options that changes the velocity the least
            v1_diff = (orbiter.v[0] - v1[0])**2 + (orbiter.v[1] - v1[1])**2 # add relative speed with star also
            v2_diff = (orbiter.v[0] - v2[0])**2 + (orbiter.v[1] - v2[1])**2
            if v1_diff < v2_diff:
                orbiter.set_vel(v1)
            else:
                orbiter.set_vel(v1)
        else:
            lockText = Text(self.center[0], self.center[1] - 80, "Too far!",
                            size=30, color="darkred", frames=self.FPS)
            self.text_paint_request.insert(0, lockText)


    def spawn_rocket(self):
        if self.locked_matter:
            dist = 20
            orbital_speed = (G * self.locked_matter.mass / dist) ** (1 / 2)
            rocket = Artificial('Rocket', 0,  [self.locked_matter.p_next[0], self.locked_matter.p_next[1] + dist],
                                    [self.locked_matter.v_next[0] + orbital_speed, self.locked_matter.v_next[1]], 0.5,
                                    save_trajectory=True, p_cam = [self.locked_matter.p_cam[0],self.locked_matter.p_cam[1] + dist* self.scale] )
            rocket.text_request = self.text_paint_request
            rocket.initialize(self.matter_list)
            self.artificial_list.append(rocket)

            self.matter_including_artificial_list.append(rocket)


    def descend(self):
        print("This feature is not ready!")


if __name__=="__main__":
    # soundPlayer.music_Q("Chill")
    sim = Simulator(w = 700, h = 700)

    run = True
    while run:
        soundPlayer.music_Q('Chill', True)
        run = sim.main_screen()  # 0 force quit / 1 means main menu / 2 means run simulation / means go to options / 4 means help screen / 5 map maker screen



    



















