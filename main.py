"""
Created on Tue Mar 18 20:24:35 2025

@author: kingc

features
- (key up, down, right, left): camara movement 
- (mouse click on a matter): lock center on a matter, click again to dislock
- press 'v' to toggle VERBOSE
- press 't' to toggle Trail

TBU
- option menu (more like a complete app)
- matter maker system (UI for easy addition of matter)


P.S.
생각보다 내가 개선한 방식으로는 안정적인 궤도를 만들기가 더 어렵다
현실이 그런건가 아니면 내 방식이 잘못된건가? 
현실에선 타원이나 원궤도가 만들어지기 쉬울것 같은데 이 코드에선 다 태양에 부딫히거나 멀리 날라가버리거나 둘 중 하나만 나온다

"""

from fileIO import *
pygame.init()


class Simulator():
    def __init__(self, w=700, h=700):
        self.mr = MatterReader()
        self.matter_list = []
        self.matter_including_artificial_list = [] # human made matters - which has very little mass itself, so it does not affect matter_list, but be affected by them

        self.w = w
        self.h = h
        self.FPS = 100#60
        self.VERBOSE = True
        self.SHOWTRAIL = True

        self.time = 0 # time in delta_t (10 delta_t = 1 time)
        self.screen_timer = Text(60, 30, "Timestep: %d"%(int(self.time)), size = 30)

        # mouse scroll / zoom parameter
        self.scale_unit = 0.1
        self.scale = 1
        
        # init display
        self.display = pygame.display.set_mode((self.w, self.h)) #pygame.display.set_mode((self.w, self.h), pygame.SRCALPHA)
        pygame.display.set_caption('Gravity')
        self.clock = pygame.time.Clock()
        self.display.fill((0,0,0)) 
        
        # trace option
        # self.transparent_screen = pygame.Surface((self.w, self.h))
        # self.transparent_screen.fill((0, 0, 0))
        
        # trace_coef = int(10*delta_t) # default of 10 or 20 is fine
        # if trace_coef<4:
        #     trace_coef = 4
        # self.transparent_screen.set_alpha(trace_coef) # 0: transparent / 255: opaque
        
        # lock matter
        self.lock = False
        self.locked_matter = None # no matter has ID 0
        self.lock_vector = [0,0]
        self.center = [self.w//2, self.h//2]
        self.text_paint_request = []

        # smooth transition
        self.smooth_interval_num = 16
        self.smooth_interval = self.smooth_interval_num

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
            # if self.VERBOSE:
            #     print("Zoom in scale: {}".format(self.scale))

    def zoom_out(self,mousepos):
        if self.scale > 0.05:
            self.scale *= (1 - self.scale_unit)
            self.change_display_scale(mousepos, 1)
            # if self.VERBOSE:
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
        if self.VERBOSE:
            lockText = Text(self.center[0], self.center[1] - 80, "Target locked: {}".format(target_matter.name), size=40,color= "maroon",frames = 3*self.FPS//2)
            self.text_paint_request.append(lockText)
            print('{} locked!'.format(target_matter.name))
        
    def unlock_matter(self):
        # self.allign_display()
        # reset lock if successful
        locked_name = self.locked_matter.name
        self.locked_matter.unlock()
        self.lock = False
        self.locked_matter = None
        self.lock_vector = [0,0]
        if self.VERBOSE:
            print('{} unlocked!'.format(locked_name))

    def reset_smooth_transition(self):
        self.smooth_interval = self.smooth_interval_num
        
    def follow_locked_matter(self):
        self.lock_vector = self.locked_matter.calculate_lock_vector(self.center)
        dx,dy = self.lock_vector

        transitioning = self.smooth_interval >= 1
        if transitioning: # theres some left for smooth transition
            # print(self.lock_vector)
            dx /= self.smooth_interval
            dy /= self.smooth_interval
            if dx**2 + dy**2 <= 50: # close enough tolerance is given 50
                self.smooth_interval -= 1
            
        for matter in self.matter_including_artificial_list: # lock vector following은 이미 cam 공간에서 하므로 따로 scale을 곱해줄 필요가 없다!
            matter.move_cam(dx,dy, preserve = transitioning) # preserve while locking in progress

    def update_timer(self):
        self.time += delta_t*0.1

    def play_step(self): # get action from the agent
        self.update_timer()

        # run simulation step - 이 함수 이후엔 update physics하기 전까지 p_next와 p 값이 다르다
        for matter in self.matter_including_artificial_list:
            matter.calc_physics(self.matter_list)
        
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
                if event.key == pygame.K_ESCAPE:  # esc 키를 누르면 메인 화면으로
                    return 1 # goto main
                elif event.key == pygame.K_t:  # toggle trail
                    self.SHOWTRAIL = not self.SHOWTRAIL
                elif event.key == pygame.K_v:  # toggle verbose
                    self.VERBOSE = not self.VERBOSE
            # if event.type == pygame.MOUSEMOTION:
            #     mousepos = pygame.mouse.get_pos()
            
            # if mouse click is near a matter, then lock / unlock
            if event.type == pygame.MOUSEBUTTONUP:    
                mousepos = pygame.mouse.get_pos()

                if event.button == 4: # scroll up
                    pass
                if event.button == 5: # scroll down
                    pass

                target_matter = self.get_near_matter(mousepos)
                if target_matter is not None: # there exists a target matter
                    if self.lock: # already locked
                        if target_matter.matterID == self.locked_matter.matterID: # if already locked matter is selected again, unlock
                            self.unlock_matter() 
                        else: # clicked on a new matter => unlock and lock
                            self.unlock_matter() 
                            self.lock_matter(target_matter) 
                    else:
                        self.lock_matter(target_matter)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mousepos = pygame.mouse.get_pos()
                if event.button == 4:  # scroll up
                    self.zoom_in(mousepos)
                    break
                if event.button == 5:  # scroll down
                    self.zoom_out(mousepos)
                    break

            # if event.type == pygame.MOUSEBUTTONDOWN:
            #     mousepos = pygame.mouse.get_pos()

        if self.lock:
            self.follow_locked_matter()
        else: # adjust camera only if not locked
            if keys[pygame.K_UP]:
                self.adjust_camera(0,1)
            if keys[pygame.K_DOWN]:
                self.adjust_camera(0,-1)
            if keys[pygame.K_RIGHT]:
                self.adjust_camera(-1,0)
            if keys[pygame.K_LEFT]:
                self.adjust_camera(1,0)

        # update ui and clock
        self._update_ui()
        self.clock.tick(self.FPS)

    def _update_ui(self):
        # if self.trace:
        #     self.display.blit(self.transparent_screen, (0, 0))
        # else:
        #     self.display.fill((0,0,0))
        self.display.fill((0, 0, 0))
        
        # update location and paint matters
        for matter in self.matter_including_artificial_list:
            matter.cam_follow_physics(self.scale)
            matter.draw(self.display,self.SHOWTRAIL)
            matter.update_physics()

        # display text on screen
        if self.VERBOSE: 
            # show matter names 
            for matter in self.matter_including_artificial_list:
                matter.textFollow()
                matter.paintName(self.display)
            
            # show timer
            self.screen_timer.change_content("Timestep: %d"%(int(self.time)))
            self.screen_timer.write(self.display)
            
            # show temporary texts (camera lock etc.)
            for text_temp in self.text_paint_request:
                if text_temp.frames>0:
                    text_temp.write(self.display)
                    text_temp.frames -= 1
                    if text_temp.frames==0:
                        self.text_paint_request.remove(text_temp)
                        
            # show locked target info
            if self.lock:
                self.locked_matter.info_text.write(self.display)

        pygame.display.flip()

    def main_screen(self): # 1
        # Choose map

        self.reset()
        # use while until user selects one of the option
        # if player clicked simulation button, run below and return 1 (TBU)
        self.mr.read_matter('matters')  # 3 body stable orbit / matters
        self.matter_list = self.mr.get_matter_list() # assign matter

        self.matter_including_artificial_list = self.matter_list + self.mr.get_artificial_list()
        return 2

    def simulation_screen(self): # 2
        while True:
            flag = sim.play_step()
            if flag == 0:  # quit pygame
                return 0
            elif flag == 1:  # goto main
                return 1
            else: # keep running simulation
                pass

    # adjust hyper parameters like trajectory length, use rough calculation of v or my calculation of v, FPS etc.
    def option_screen(self): # 3
        # use while until user clicks to get out of the current screen
        pass

    def help_screen(self): #4 show commands and how to use this simulator
        pass




if __name__=="__main__":
    # soundPlayer.music_Q("Chill")
    sim = Simulator(w = WIDTH, h = HEIGHT)

    runFlag = 1
    while runFlag:
        runFlag = sim.main_screen()  # 0 force quit / 1 means main menu / 2 means run simulation / means go to options / 4 means help screen
        if runFlag==2:
            runFlag = sim.simulation_screen()
        elif runFlag==3:
            runFlag = sim.option_screen() # 이건 이 안에 while loop가 들어가 있는 꼴임
        elif runFlag==4:
            runFlag = sim.help_screen()
        else:
            runFlag=0 # leave loop

    



















