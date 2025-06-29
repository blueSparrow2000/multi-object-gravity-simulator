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
    DEBUG = False

    # some constants
    lock_tolerance = 5 # clicking nearby points can also target that matter
    traj_size = 30  # maximum # of traj saved
    traj_save_freq = 1 / delta_t  # every 10 frames(dt=0.2) - dt 에 따라 바뀔 수 있다. 충분히 조밀하게 계산하면 더 크게 늘려도 됨 (coarse하게)
    traj_rad = 1  # self.radius//4 if self.radius//4 >= 1 else 1

    def __init__(self, name, mass, p, v, radius, type='rocky',save_trajectory = False, p_cam = None):
        super().__init__(name, p, v, p_cam)
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
        if Matter.DEBUG:
            self.info_text = "[{:^10}]Mass: {:>6}Radius: {:>4}Speed: {:.3f}".format(self.name, str(int(self.mass)), str(int(self.radius)),0)
        else:
            self.info_text = "[{:^10}]Mass: {:>6}Radius: {:>4}".format(self.name, str(int(self.mass)),
                                                                                    str(int(self.radius)))

        # locked
        self.locked = False

        # trajectories
        self.save_trajectory_defined = save_trajectory
        self.save_trajectory = save_trajectory
        self.trajectory = []
        self.traj_colors = [(self.color_capping(self.color[0] - i * 5), self.color_capping(self.color[1] - i * 5),
                             self.color_capping(self.color[2] - i * 5)) for i in range(self.traj_size)]
        self.traj_count = 0

        # auxilliary variable for leapfrog calculation
        self.a_saved = [0,0]

    def initialize(self, matter_list):
        self.calc_acceleration(matter_list)

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
            pygame.draw.circle(screen, self.traj_colors[i],self.trajectory[i], Matter.traj_rad)

    def __str__(self):
        return "{}, mass: {}, position: ({}, {}), velocity: ({}, {})".format(self.name,self.mass,self.p[0],self.p[1],self.v[0],self.v[1])
    
    def update_info_text(self,speed = 0):
        if Matter.DEBUG:
            self.info_text = "[{:^10}]Mass: {:>6}Radius: {:>4}Speed: {:.3f}".format(self.name, str(int(self.mass)), str(int(self.radius)),speed)
        else:
            self.info_text = "[{:^10}]Mass: {:>6}Radius: {:>4}".format(self.name, str(int(self.mass)),
                                                                                    str(int(self.radius)))
    def get_info_text(self):
        return self.info_text

    def textFollow(self):
        self.text.change_pos(self.p_cam[0], self.p_cam[1] - self.radius_cam - 10)

    def draw(self, screen, show_trajectory = False):
        #draw camera view
        if show_trajectory:
            self.draw_traj(screen)
        pygame.draw.circle(screen, self.color, self.p_cam, self.radius_cam)
        # # draw real - 문제없음 카메라 문제
        # pygame.draw.circle(screen, self.color, self.p, self.radius)

    def draw_velocity_arrow(self,screen):
        # also draw direction pointer
        if self.locked:
            speed = (self.v[0] ** 2 + self.v[1] ** 2)**(1/2) ## speed calculation makes performance slower
            if Matter.DEBUG:
                self.update_info_text(speed)  # follow 할때만 속도를 변화
            if speed > 0.1: # only show when large enough
                if speed > 10: # too large
                    pygame.draw.line(screen, (100, 0, 0), self.p_cam,
                                     [self.p_cam[0] + self.v[0]/speed*200,
                                      self.p_cam[1] + self.v[1]/speed*200], 2)
                else:
                    pygame.draw.line(screen, (100, 0, 0), self.p_cam,
                                     [self.p_cam[0] + self.v[0] * 20,
                                      self.p_cam[1] + self.v[1] * 20], 2)

    def check_clicked_on_display(self, mousepos):
        return (mousepos[0] - self.p_cam[0]) ** 2 + (mousepos[1] - self.p_cam[1]) ** 2 <= (
                self.radius_cam + Matter.lock_tolerance) ** 2

    def calculate_lock_vector(self,center):
        return center[0] - self.p_cam[0] , center[1] - self.p_cam[1]

    # sum all acceleration allied to itself (net acceleration) by 'matter_list' only -> excluding artificials and drawables
    # calculate acceleration and save it to a (also returns a)
    def calc_acceleration(self, matter_list, midpoint = False): # use_next_p = False
        a_net = [0,0]
        for matter in matter_list:
            if self.matterID == matter.matterID: # prevent self calculation
                continue

            # dx = matter.p[0] - self.p[0]
            # dy = matter.p[1] - self.p[1]
            dx = matter.p_next[0] - self.p_next[0]
            dy = matter.p_next[1] - self.p_next[1]
            if midpoint:
                dx = (matter.p_next[0] - self.p_next[0] + matter.p[0] - self.p[0])/2
                dy = (matter.p_next[1] - self.p_next[1] + matter.p[1] - self.p[1])/2
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
                print("{}'s Mass after collision: {}".format(larger_one.name,larger_one.mass))

            a_div_r = G*matter.mass/(r_temp**3)
            a_net[0] += a_div_r*dx
            a_net[1] += a_div_r*dy

        self.a_saved = a_net
        return a_net

    # project & subtract
    def decompose_acceleration(self, a, v_size_squared):        
        a_dot_v = a[0]*self.v[0] + a[1]*self.v[1]
        a_norm = [0,0]
        if v_size_squared!=0: # v can change direction only if it is not zero
            coef = a_dot_v/v_size_squared
            a_norm = [self.v[0]*coef , self.v[1]*coef]
        else: # if zero size
            #print("WARNING! zero velocity reached when decomposing acceleration")
            a_norm = [0,0]
            a_para = a
            return a_norm, a_para

        a_para = [a[0] - a_norm[0], a[1] - a_norm[1]]
        return a_norm,a_para
    
    # vector rotation - dont have to be in matter class (rotated theta radians counter clockwise)
    def rotate_vector(self, vector, theta): 
        vx,vy = vector
        rotated_vector = [vx*math.cos(theta) - vy*math.sin(theta) , vx*math.sin(theta) + vy*math.cos(theta)]
        return rotated_vector

    # calculate next position p - using v, v_next, and average of them separately (we will compare)
    def calc_p(self, midpoint = False):
        # using newerly calculated velocity only
        self.p_next[0] = self.p[0] + self.v_next[0]*delta_t
        self.p_next[1] = self.p[1] + self.v_next[1]*delta_t
        if midpoint:
            # using weighted vel - 큰 차이 없더라
            lamb = 0.5
            self.p_next[0] = self.p[0] + (lamb * self.v[0] + (1 - lamb) * self.v_next[0]) * delta_t
            self.p_next[1] = self.p[1] + (lamb * self.v[1] + (1 - lamb) * self.v_next[1]) * delta_t
        
    # calculate normal component of v
    def calc_v_norm(self,a_norm, v_size):
        if v_size == 0: # if zero velocity, no need to calculate changed v
            return [0,0]
        
        # save theta - restore after calculating
        if self.v[0] == 0: # div by 0
            if self.v[1] > 0:
                theta = math.pi/2
            else:
                theta = -math.pi/2
        else:
             # prevent div by 0 / minimal precision of vx is 0.01
            theta = math.atan(self.v[1]/self.v[0])
            if self.v[0] < 0:
                theta += math.pi

        # we only need scala of a_norm
        a_norm_size = (a_norm[0]**2 + a_norm[1]**2)**(1/2)
        
        # depending on the direction of a_norm w.r.t v, we have to plug in either  a_norm_size or -a_norm_size
        if self.v[0]*a_norm[1] - self.v[1]*a_norm[0] > 0:
            # reverse direction of a!
            a_norm_size = -a_norm_size

        # calculate v due to normal component of a
        v_applied_a_norm = [v_size - (a_norm_size*delta_t)**2/(2*v_size) , a_norm_size*delta_t*( abs(1 - (a_norm_size*delta_t)**2/(4*v_size**2) ) )**(1/2)  ]
        # rotate back to original coordinate
        v_rotated_back = self.rotate_vector(v_applied_a_norm, theta)
        return v_rotated_back
    
    # calculate parallel component of v
    def calc_v_para(self,a_para):
        return [a_para[0]*delta_t , a_para[1]*delta_t ]

    def calc_v_AD(self):
        v_size_squared = (self.v[0] ** 2 + self.v[1] ** 2)
        v_size = (v_size_squared) ** (1 / 2)

        a_norm, a_para = self.decompose_acceleration(self.a_saved, v_size_squared)
        v_norm = self.calc_v_norm(a_norm, v_size)
        v_para = self.calc_v_para(a_para)
        self.v_next[0] = v_norm[0] + v_para[0]
        self.v_next[1] = v_norm[1] + v_para[1]

    def calc_v_Euler(self):
        self.v_next[0] = self.v[0] + self.a_saved[0]*delta_t
        self.v_next[1] = self.v[1] + self.a_saved[1]*delta_t

    def calc_v_LeapFrog(self):
        self.v_next[0] = self.v[0] + self.a_saved[0]*delta_t/2
        self.v_next[1] = self.v[1] + self.a_saved[1]*delta_t/2

    def calc_v_LeapFrog_second_pass(self):
        self.v_next[0] = self.v_next[0] + self.a_saved[0] * delta_t / 2
        self.v_next[1] = self.v_next[1] + self.a_saved[1] * delta_t / 2

    # Runge Kutta helper functions
    def calc_v_RK4(self, acc):
        self.v_next[0] = self.v[0] + acc[0]*delta_t/2
        self.v_next[1] = self.v[1] + acc[1]*delta_t/2
        return [self.v_next[0], self.v_next[1]]

    # enforce next p,v : used in Runge Kutta method
    def set_v_next_RK4(self, k1,k2,k3,k4):
        self.v_next[0] = self.v[0] + (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])*delta_t/6
        self.v_next[1] = self.v[1] + (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])*delta_t/6

    def set_p_next_RK4(self, v1,v2,v3):
        self.p_next[0] = self.p[0] + (self.v[0] + 2*v1[0] + 2*v2[0] + v3[0])*delta_t/6
        self.p_next[1] = self.p[1] + (self.v[1] + 2*v1[1] + 2*v2[1] + v3[1])*delta_t/6

        ###################### camera update #############################
    def move_cam(self,dx,dy,preserve = False): # directly move cam
        self.p_cam[0] += dx # make cam pos integer
        self.p_cam[1] += dy
        if preserve:
            self.move_traj(dx, dy)

    def get_movement(self):
        return self.p_next[0] - self.p[0], self.p_next[1] - self.p[1]

    def cam_follow_physics(self, scale): # cam update just before update_physics
        dx = (self.p_next[0] - self.p[0])*scale
        dy = (self.p_next[1] - self.p[1])*scale
        self.move_cam(dx,dy)
        self.try_save_traj()

    def change_radius_scale(self,scale):
        self.radius_cam = self.radius * scale

    def allign_cam(self):
        self.p_cam = [self.p[0], self.p[1]]
        self.textFollow()













