"""
Matter calculation
- calculate physics


#### simulation choice ####
in between these code blocks, you can test two different methods of aproximating the physics
#### simulation choice ####

type
rocky, gas, metal, icy

"""
from drawable import *

class Matter(Drawable):
    matterID = 0 # starts from 1, 2, 3, ...

    # some constants
    lock_tolerance = 5 # clicking nearby points can also target that matter
    traj_size = 20  # maximum # of traj saved
    traj_save_freq = 1 / delta_t  # every 10 frames(dt=0.2) - dt 에 따라 바뀔 수 있다. 충분히 조밀하게 계산하면 더 크게 늘려도 됨 (coarse하게)

    advanced_calculation = False

    def __init__(self, name, mass, p, v, radius, type='rocky',save_trajectory = False):
        super().__init__(name, p, v)
        # unique ID given to each matter
        Matter.matterID += 1
        self.matterID = Matter.matterID
        self.object_type = 'matter'

        self.mass = mass
        self.radius_cam = radius
        self.radius = radius
        self.type = type
        if self.name == 'sun':
            self.color = (200, 161, 20)


        # information text - 재정의함
        self.text = Text(self.p_cam[0], self.p_cam[1] - 30, self.name, color=self.color)
        self.info_text = MultiText(WIDTH-65, HEIGHT - 65, "[{:^10}]Mass: {:>6}Radius: {:>4}".format(self.name,str(int(self.mass)),str(int(self.radius))), size = 20, content_per_line=12)

        # locked
        self.locked = False

        # trajectories
        self.save_trajectory_defined = save_trajectory
        self.save_trajectory = save_trajectory
        self.trajectory = []
        self.traj_colors = [(self.color_capping(self.color[0] - i * 5), self.color_capping(self.color[1] - i * 5),
                             self.color_capping(self.color[2] - i * 5)) for i in range(self.traj_size)]

        self.traj_count = 0
        self.traj_rad = self.radius//4 if self.radius//4 >= 1 else 1

    def color_capping(self, given_color):
        if given_color < 0:
            given_color = 0
        elif given_color > 255:
            given_color = 255
        return given_color

    def lock(self):
        self.locked = True
        # dont show trajectory
        self.save_trajectory = False
        self.reset_traj()

    def unlock(self):
        self.locked = False
        self.save_trajectory = self.save_trajectory_defined

    def queue_traj(self):
        if len(self.trajectory) == Matter.traj_size: # dequeue if full
            self.dequeue_traj()
        self.trajectory.insert(0,[self.p_cam[0],self.p_cam[1]]) # save 된 시점의 p_cam부터 계속 추적됨

    def reset_traj(self): # called when zoom
        self.trajectory = []
        self.traj_count = 0

    def move_traj(self,dx,dy): # directly move cam
        for traj in self.trajectory:
            traj[0] += dx
            traj[1] += dy

    def dequeue_traj(self):
        self.trajectory.pop()

    def try_save_traj(self):
        if not self.save_trajectory:
            return
        self.traj_count += 1
        if self.traj_count == self.traj_save_freq:
            self.traj_count = 0
            self.queue_traj()

    def draw_traj(self,screen):
        for i in range(len(self.trajectory)):
            pygame.draw.circle(screen, self.traj_colors[i],self.trajectory[i], self.traj_rad)

    def __str__(self):
        return "{}, mass: {}, position: ({}, {}), velocity: ({}, {})".format(self.name,self.mass,self.p[0],self.p[1],self.v[0],self.v[1])
    
    def update_info_text(self):
        self.info_text = MultiText(WIDTH-65, HEIGHT - 65, "[{:^10}]Mass: {:>6}Radius: {:>4}".format(self.name,str(int(self.mass)),str(int(self.radius))), size = 20, content_per_line=12)

    def textFollow(self):
        self.text.change_pos(self.p_cam[0], self.p_cam[1] - self.radius_cam - 10)

    def draw(self, screen, show_trajectory = False):
        #draw camera view
        if show_trajectory:
            self.draw_traj(screen)
        pygame.draw.circle(screen, self.color, self.p_cam, self.radius_cam)
        # # draw real - 문제없음 카메라 문제
        # pygame.draw.circle(screen, self.color, self.p, self.radius)

    def check_clicked_on_display(self, mousepos):
        return (mousepos[0] - self.p_cam[0]) ** 2 + (mousepos[1] - self.p_cam[1]) ** 2 <= (
                self.radius_cam + Matter.lock_tolerance) ** 2

    def calculate_lock_vector(self,center):
        return center[0] - self.p_cam[0] , center[1] - self.p_cam[1]

    # sum all acceleration allied to itself (net acceleration)
    def calc_acceleration(self, matter_list):
        a_net = [0,0]
        for matter in matter_list:
            if self.matterID == matter.matterID: # prevent self calculation
                continue
            dx = matter.p[0] - self.p[0]
            dy = matter.p[1] - self.p[1]
            r_temp = (dx**2 + dy**2)**(1/2)

            # handle collision
            if (not matter.removed and not self.removed) and r_temp <= (matter.radius + self.radius)*3/4:
                soundPlayer.collision_sound_effect(self.type, matter.type)
                larger_one = self if self.mass > matter.mass else matter
                smaller_one = matter if self.mass > matter.mass else self
                # conservation of mass
                larger_one.mass += smaller_one.mass
                # conservation of linear momentum (assuming completely nonelastic collision)
                larger_one.v[0] = (larger_one.mass*larger_one.v[0] + smaller_one.mass*smaller_one.v[0])/larger_one.mass
                larger_one.v[1] = (larger_one.mass*larger_one.v[1] + smaller_one.mass*smaller_one.v[1])/larger_one.mass

                # flag to remove a matter
                smaller_one.removed = True

                # update info
                larger_one.update_info_text()

                print("collision between {} and {}".format(larger_one.name,smaller_one.name))
                print("{}'s Mass after: {}".format(larger_one.name,larger_one.mass))

            a_div_r = G*matter.mass/(r_temp**3)
            a_net[0] += a_div_r*dx
            a_net[1] += a_div_r*dy
        return a_net

    # project & subtract
    def decompose_acceleration(self, a, v_size_squared):        
        a_dot_v = a[0]*self.v[0] + a[1]*self.v[1]
        a_norm = [0,0]
        if v_size_squared!=0: # v can change direction only if it is not zero
            coef = a_dot_v/v_size_squared
            a_norm = [self.v[0]*coef , self.v[1]*coef]
            
        a_para = [a[0] - a_norm[0], a[1] - a_norm[1]]
        return a_norm,a_para
    
    # vector rotation - dont have to be in matter class (rotated theta radians counter clockwise)
    def rotate_vector(self, vector, theta): 
        vx,vy = vector[0],vector[1]
        rotated_vector = [vx*math.cos(theta) - vy*math.sin(theta) , vx*math.sin(theta) + vy*math.cos(theta)]
        return rotated_vector
    
    
    # calculate next position p - using v, v_next, and average of them separately (we will compare)
    def calc_p(self):
        # using newerly calculated velocity only
        self.p_next[0] = self.p[0] + self.v_next[0]*delta_t
        self.p_next[1] = self.p[1] + self.v_next[1]*delta_t
        '''
        # using weighted vel - 큰 차이 없더라
        lamb = 1
        self.p_next[0] = self.p[0] + (lamb*self.v[0] + (1-lamb)*self.v_next[0])*delta_t
        self.p_next[1] = self.p[1] + (lamb*self.v[1] + (1-lamb)*self.v_next[1])*delta_t
        '''
        
    # calculate normal component of v
    def calc_v_norm(self,a_norm, v_size):
        if v_size == 0: # if zero velocity, no need to calculate changed v
            return [0,0]
        
        # save theta - restore after calculating
        atan_vx = 0.001 if self.v[0] == 0 else self.v[0] # prevent div by 0 / minimal precision of vx is 0.01
        theta = math.atan(self.v[1]/atan_vx)
        if self.v[0]<0:
            theta += math.pi
        # we only need scala of a_norm
        a_norm_size = (a_norm[0]**2 + a_norm[1]**2)**(1/2)
        
        # depending on the direction of a_norm w.r.t v, we have to plug in either  a_norm_size or -a_norm_size
        if self.v[0]*a_norm[1] - self.v[1]*a_norm[0] >0:
            # reverse direction of a!
            a_norm_size = -a_norm_size
            
        
        # calculate v due to normal component of a
        v_applied_a_norm = [v_size - (a_norm_size*delta_t)**2/(2*v_size)   , a_norm_size*delta_t*( abs(1 - (a_norm_size*delta_t)**2/(4*v_size**2) ) )**(1/2)  ]
        # rotate back to original coordinate
        v_rotated_back = self.rotate_vector(v_applied_a_norm, theta)
        return v_rotated_back
    
    # calculate parallel component of v
    def calc_v_para(self,a_para, v_size):
        return [a_para[0]*delta_t , a_para[1]*delta_t ]

    def calc_v_rough(self,a):
        self.v_next[0] = self.v[0] + a[0]*delta_t
        self.v_next[1] = self.v[1] + a[1]*delta_t

    def calc_v(self,a):        
        v_size_squared = (self.v[0]**2+self.v[1]**2)
        v_size = (v_size_squared)**(1/2)
        
        a_norm, a_para = self.decompose_acceleration(a,v_size_squared)
        v_norm = self.calc_v_norm(a_norm, v_size)
        v_para = self.calc_v_para(a_para, v_size)
        self.v_next[0] = v_norm[0] + v_para[0]
        self.v_next[1] = v_norm[1] + v_para[1]

    def calc_physics(self,matter_list):
        a = self.calc_acceleration(matter_list)

        #### simulation choice ####
        if Matter.advanced_calculation:
            self.calc_v(a)
        else:
            self.calc_v_rough(a)
        #### simulation choice ####
        
        self.calc_p()
        
    # update my v to v_next etc.
    def update_physics(self):
        self.v = [self.v_next[0],self.v_next[1]]
        self.p = [self.p_next[0],self.p_next[1]]

    ###################### camera update #############################
    def move_cam(self,dx,dy,preserve = False): # directly move cam
        self.p_cam[0] += dx
        self.p_cam[1] += dy
        if preserve:
            self.move_traj(dx, dy)

    def cam_follow_physics(self, scale): # cam update just before update_physics
        dx = (self.p_next[0] - self.p[0])*scale
        dy = (self.p_next[1] - self.p[1])*scale
        self.move_cam(dx,dy)
        self.try_save_traj()

    # scale이 변화하여 실제 거리를 카메라 상의 거리로 변환해야 함
    def change_cam_scale(self, scale_change_unit, centerX, centerY): # called immediately when changing scale
        dx = (centerX - self.p_cam[0])*scale_change_unit
        dy = (centerY - self.p_cam[1])*scale_change_unit
        self.move_cam(dx,dy,preserve = True)

        # self.reset_traj()

    def change_radius_scale(self,scale):
        self.radius_cam = self.radius * scale

    def allign_cam(self):
        self.p_cam = [self.p[0], self.p[1]]
        self.textFollow()













