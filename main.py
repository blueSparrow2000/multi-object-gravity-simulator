"""
Created on Tue Mar 18 20:24:35 2025

@author: kingc

features
- (key up, down, right, left): camara movement 
- (mouse click on a matter): lock center on a matter, click again to dislock
- press 'v' to toggle VERBOSE
- press 't' to toggle Trail
- Mouse click&drag also moves camera

TBU
- option menu (more like a complete app)
- matter maker system (UI for easy addition of matter)


P.S.
생각보다 내가 개선한 방식으로는 안정적인 궤도를 만들기가 더 어렵다 -> dt를 매우 작게해야 내 AC방식이 돌아감
현실이 그런건가 아니면 내 방식이 잘못된건가? 
현실에선 타원이나 원궤도가 만들어지기 쉬울것 같은데 이 코드에선 다 태양에 부딫히거나 멀리 날라가버리거나 둘 중 하나만 나온다

"""
import pygame

from fileIO import *
from gui import *
pygame.init()

class Simulator():
    def __init__(self, w=700, h=700):
        self.mr = MatterReader()
        self.matter_list = []
        self.matter_including_artificial_list = [] # human made matters - which has very little mass itself, so it does not affect matter_list, but be affected by them

        self.w = w
        self.h = h
        self.FPS = 100#100#60
        self.BUSYFPS = 10
        self.SPEEDUP = 10
        self.VERBOSE = [True]
        self.SHOWTRAIL = [True]

        self.time = 0 # time in delta_t (10 delta_t = 1 time)
        self.screen_timer = Text(70, 16, "Timestep: %d"%(int(self.time)), size = 30)

        # mouse scroll / zoom parameter
        self.scale_unit = 0.1
        self.scale = 1

        # mouse click drag variable
        self.base_drag = None
        
        # init display
        self.display = pygame.display.set_mode((self.w, self.h)) #pygame.display.set_mode((self.w, self.h), pygame.SRCALPHA)
        pygame.display.set_caption('Gravity')
        self.clock = pygame.time.Clock()
        self.display.fill((0,0,0)) 
        
        # trace option
        self.transparent_screen = pygame.Surface((self.w, self.h))
        self.transparent_screen.fill((50, 50, 50))
        self.transparent_screen.set_alpha(200) # 0: transparent / 255: opaque
        
        # lock matter
        self.lock = False
        self.locked_matter = None # no matter has ID 0
        self.lock_vector = [0,0]
        self.center = [self.w//2, self.h//2]
        self.text_paint_request = []

        # smooth transition
        self.smooth_interval_num = 16*self.SPEEDUP
        self.smooth_interval = self.smooth_interval_num

        # simulation method
        self.simulation_method = 'LF'#'RK4'  # 'AC': Acceleration Decomposition (my suggestion) / 'E': Euler method / 'LF': Leapfrog method / 'RF4': Runge-Kutta 4th order

        # simulation system initial setting
        self.system_name = 'matters'


        self.main_screen_buttons = [Button(self, 'simulation_screen', self.w//2, self.h//2+100, 'Simulate'),
                                    Button(self, 'quit_simulation', self.w - 25, 15, 'QUIT', button_length=50,color = (60,60,60), hover_color = (100,100,100))]
        self.pause_screen_buttons = [ToggleButton(self, 'toggle_trail', self.w//2, self.h//2 + 200, 'TRAIL',toggle_variable = self.SHOWTRAIL),
                                     ToggleButton(self, 'toggle_verbose', self.w//2, self.h//2 + 150, 'UI',toggle_variable = self.VERBOSE),
                                     Button(self, 'go_to_main', self.w//2, self.h//2 + 250, 'Main menu'),
                                     Button(self, 'unpause', self.w - 30, 20, 'Back', button_length=60)]
        # put all pause screen rects here! this includes interactable things like buttons! -> extract rects!
        self.pause_screen_rects = []
        for pause_button in self.pause_screen_buttons:
            self.pause_screen_rects.append(pause_button.rect)

        self.simulation_screen_buttons = [Button(self, 'pause', self.w - 30, 20, 'Pause', button_length=60,color = (30,30,30), hover_color = (80,80,80))]
        self.option_screen_buttons = []
        self.help_screen_buttons = []
        self.mapmaker_screen_buttons = []

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

    def toggle_trail(self):
        self.SHOWTRAIL[0] = not self.SHOWTRAIL[0]

    def toggle_verbose(self):
        self.VERBOSE[0] = not self.VERBOSE[0]

    def quit_simulation(self):
        pygame.quit()
        return 0

    def reset(self):
        self.mr.reset()

        self.remove_matter() # artificial list 도 함께 없앰

        self.time = 0  # time in delta_t (10 delta_t = 1 time)
        self.scale = 1

        self.lock = False
        self.locked_matter = None # no matter has ID 0
        self.lock_vector = [0,0]

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
        if self.simulation_method == 'AC':
            for matter in self.matter_including_artificial_list:
                matter.calc_p()
                matter.calc_acceleration(self.matter_list)
                matter.calc_v_AC()
        elif self.simulation_method == 'E':
            for matter in self.matter_including_artificial_list:
                matter.calc_acceleration(self.matter_list)
                matter.calc_v_Euler()
                matter.calc_p()
        elif self.simulation_method == 'LF':
            # first pass - update all positions before recalculating new acceleration
            for matter in self.matter_including_artificial_list:
                matter.calc_v_LeapFrog()
                matter.calc_p()  # 기본적으로 update된 v로 구함
            # second pass
            for matter in self.matter_including_artificial_list:
                matter.calc_acceleration(self.matter_list)  # update 된 p_next로 구함
                matter.calc_v_LeapFrog_second_pass()  # do again
        elif self.simulation_method == 'RK4':
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

    def simulation_screen(self): # 2
        self.initialize()  # '2 body'
        self.button_function(self.simulation_screen_buttons, 'initialize')

        while True:
            for i in range(self.SPEEDUP-1): # fast forward (not using pygame features) => 10 times speedup? (if pygame is bottleneck)
                self.calculate_without_frame()
            flag = self.play_step()
            if flag == 0:  # quit pygame
                return 0
            elif flag == -1: # pause screen
                pause_result = self.pause_screen()
                if pause_result == 0: # quit pygame
                    return 0
                elif pause_result  == 1: # if it returns go to main (=1)
                    return 1
            elif flag == 1:  # goto main
                return 1
            else: # keep running simulation
                pass

    def play_step(self): # get action from the agent
        self.update_timer()
        self.calculate_physics()

        # remove after checking collision
        self.remove_matter()
                
        # collect user input
        events = pygame.event.get()
        keys = pygame.key.get_pressed()  # 꾹 누르고 있으면 계속 실행되는 것들 # SHOULD BE CALLED AFTER pygame.event.get()!
        # handle events
        for event in events:
            if event.type == pygame.QUIT:  # 윈도우를 닫으면 종료
                pygame.quit()
                return 0 # force quit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:  # esc 키를 누르면 pause
                    return -1 # pause
                elif event.key == pygame.K_t:  # toggle trail
                    self.toggle_trail()
                elif event.key == pygame.K_v:  # toggle verbose
                    self.toggle_verbose()

            if event.type == pygame.MOUSEMOTION:
                mousepos = pygame.mouse.get_pos()
                self.button_function(self.simulation_screen_buttons, 'hover_check', mousepos)
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

                if event.button == 4: # scroll up
                    pass
                if event.button == 5: # scroll down
                    pass

                if self.base_drag: # 드래그를 하던 중 클릭이 타겟위에서 끝났다 하더라도 드래그를 끝내는걸 우선시함, 드래그를 끝냄
                    self.base_drag = None # 드래그 종료
                else:
                    # 버튼을 누른것 또는 타깃을 클릭하기 위해 클릭한것
                    if self.button_function(self.simulation_screen_buttons, 'on_click', mousepos) == -1: # pause인지 체크
                        return -1
                    else:
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
                        text_temp.write(self.display)
                        lock_text_drawn = True
                    text_temp.frames -= 1
                    if text_temp.frames==0:
                        self.text_paint_request.remove(text_temp)
                        
            # show locked target info
            if self.lock:
                self.locked_matter.info_text.write(self.display)

        # draw buttons (should be drawn regardless of verbose)
        self.button_function(self.simulation_screen_buttons, 'draw_button', self.display)

        pygame.display.flip()

    def initialize(self):
        self.reset()
        self.mr.read_matter(self.system_name)  # 3 body stable orbit / matters
        self.matter_list = self.mr.get_matter_list() # assign matter
        self.matter_including_artificial_list = self.matter_list + self.mr.get_artificial_list() # assign artificial matters too
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
                    return 0  # force quit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:  # esc 키를 누르면 메인 화면으로
                        return 0  # goto main
                if event.type == pygame.MOUSEMOTION:
                    mousepos = pygame.mouse.get_pos()
                    self.button_function(min_display_buttons, 'hover_check', mousepos)
                if event.type == pygame.MOUSEBUTTONUP:  # 마우스를 뗼떼 실행됨
                    mousepos = pygame.mouse.get_pos()
                    return self.button_function(min_display_buttons, 'on_click', mousepos) # 이게 에러를 냄. 바로 pygame quit시 none을 리턴

            # galaxy.update_p() # calc p_next
            # galaxy.cam_follow_physics(1) # move cam pos
            # galaxy.draw(self.display)
            # galaxy.update_physics() # p <- p_next
            self.button_function(min_display_buttons, 'draw_button', self.display)

            pygame.display.flip()
            self.clock.tick(self.FPS)

    '''
    Choose map
    use while until user selects one of the option
    if player clicked simulation button, run below and return 1 (TBU)
    self.system_name # 이걸 여기서 바꿔주기
    '''
    def main_screen(self): # 1 -> pause screen과 유사 토글로 맵 종류 바꾸기
        while 1:
            self.display.fill((0, 0, 0))
            # collect user input
            events = pygame.event.get()
            keys = pygame.key.get_pressed()  # 꾹 누르고 있으면 계속 실행되는 것들 # SHOULD BE CALLED AFTER pygame.event.get()!
            # handle events
            for event in events:
                if event.type == pygame.QUIT:  # 윈도우를 닫으면 종료
                    pygame.quit()
                    return 0  # force quit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:  # esc 키를 누르면 메인 화면으로
                        return 0  # goto main
                if event.type == pygame.MOUSEMOTION:
                    mousepos = pygame.mouse.get_pos()
                    self.button_function(self.main_screen_buttons, 'hover_check', mousepos)
                if event.type == pygame.MOUSEBUTTONUP:  # 마우스를 뗼떼 실행됨
                    mousepos = pygame.mouse.get_pos()
                    return self.button_function(self.main_screen_buttons, 'on_click', mousepos) # 이게 에러를 냄. 바로 pygame quit시 none을 리턴

            self.button_function(self.main_screen_buttons, 'draw_button', self.display)

            pygame.display.flip()
            self.clock.tick(self.FPS)



    def go_to_main(self):
        return 1

    def pause(self):
        return -1 # pause

    def unpause(self):
        return 2 # simulation screen

    def pause_screen(self): #4 show commands and how to use this simulator
        # draw transparent screen - stop increasing time, only clock tick for interaction, but still can click buttons, update display for buttons
        # increase FPS -> 토글로 할지 슬라이더로 조작할지 버튼으로 올릴지 나중에 선택 / toggle v,t -> button text 바뀜 / toggle simulation method / trail length
        self.display.blit(self.transparent_screen, (0, 0))
        pygame.display.flip()

        self.button_function(self.pause_screen_buttons, 'initialize')

        while 1:
            # collect user input
            events = pygame.event.get()
            keys = pygame.key.get_pressed()  # 꾹 누르고 있으면 계속 실행되는 것들 # SHOULD BE CALLED AFTER pygame.event.get()!
            # handle events
            for event in events:
                if event.type == pygame.QUIT:  # 윈도우를 닫으면 종료
                    pygame.quit()
                    return 0  # force quit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        return 2 # 그대로 시뮬레이션 계속 함 (사실 이 리턴값은 안쓰임)
                if event.type == pygame.MOUSEMOTION:
                    mousepos = pygame.mouse.get_pos()
                    self.button_function(self.pause_screen_buttons, 'hover_check', mousepos)
                if event.type == pygame.MOUSEBUTTONUP:  # 마우스를 뗼떼 실행됨
                    mousepos = pygame.mouse.get_pos()
                    click_result = self.button_function(self.pause_screen_buttons, 'on_click', mousepos)
                    if click_result == 1:  # go to main
                        return 1 # simulation loop 탈출을 위해 필요했음
                    elif click_result ==2: # keep simulating
                        return 2

            self.button_function(self.pause_screen_buttons, 'draw_button', self.display)

            pygame.display.update(self.pause_screen_rects)
            # pygame.event.pump() # in case update does not work properly
            self.clock.tick(self.BUSYFPS)


    # adjust hyper parameters like trajectory length, use rough calculation of v or my calculation of v, FPS etc.
    def option_screen(self): # 3
        # use while until user clicks to get out of the current screen
        pass

    def help_screen(self): #4 show commands and how to use this simulator
        pass

    def map_maker_screen(self): #4 show commands and how to use this simulator
        pass


if __name__=="__main__":
    # soundPlayer.music_Q("Chill")
    sim = Simulator(w = WIDTH, h = HEIGHT)

    runFlag = 1
    while runFlag:
        runFlag = sim.main_screen()  # 0 force quit / 1 means main menu / 2 means run simulation / means go to options / 4 means help screen / 5 map maker screen
        print("DEBUG FLAG: %s"%runFlag)
        if runFlag==0:
            break # leave loop
        elif runFlag==2:
            runFlag = sim.simulation_screen()
        elif runFlag==3:
            runFlag = sim.option_screen() # 이건 이 안에 while loop가 들어가 있는 꼴임
        elif runFlag==4:
            runFlag = sim.help_screen()
        elif runFlag==5:
            runFlag = sim.map_maker_screen()


    



















