from variables import delta_t, G
from util import *

class Drawable():
    def __init__(self, name, p, v, image_name = None):
        # print(self.matterID)
        self.object_type = 'drawable'
        self.name = name
        self.p = [p[0], p[1]]  # position
        self.p_next = [p[0], p[1]]
        self.v = [v[0], v[1]]  # velocity
        self.v_next = [v[0], v[1]]
        # camera variables
        self.p_cam = [p[0], p[1]]
        self.angle = 0
        self.angle_next = 0
        self.angular_v = 0
        
        self.color = (180, 180, 180)

        # collision attributes
        self.removed = False  # remove when collision (if mass smaller than the other collider)

        # information text
        self.text = Text(self.p_cam[0], self.p_cam[1] - 30, self.name)
        self.info_text = "[{:^10}]".format(self.name)

        self.image = None
        self.image_loaded = False
        if image_name:
            self.image = Image(self.p_cam, image_name) # pos 를 레퍼런스로 하여 동기화되도록 함!
            self.image_loaded = True

    def __str__(self):
        return "{}, position: ({}, {}), velocity: ({}, {})".format(self.name, self.p[0], self.p[1],
                                                                             self.v[0], self.v[1])
    def update_info_text(self):
        self.info_text = "[{:^10}]".format(self.name)

    def textFollow(self):
        self.text.change_pos(self.p_cam[0], self.p_cam[1] - 30)

    def paintName(self, screen):
        self.text.write(screen)

    def draw(self, screen):
        if self.image_loaded:
            self.image.draw(screen)

    def check_clicked_on_display(self, mousepos):
        return False # currently not clickable - must be made custom

    # calculate next position p - using v, v_next, and average of them separately (we will compare)
    def update_p(self):
        # using newerly calculated velocity only
        self.p_next[0] = self.p[0] + self.v_next[0] * delta_t
        self.p_next[1] = self.p[1] + self.v_next[1] * delta_t
        '''
        # using weighted vel - 큰 차이 없더라
        lamb = 1
        self.p_next[0] = self.p[0] + (lamb*self.v[0] + (1-lamb)*self.v_next[0])*delta_t
        self.p_next[1] = self.p[1] + (lamb*self.v[1] + (1-lamb)*self.v_next[1])*delta_t
        '''

    def update_v(self,a):
        self.v_next[0] = self.v[0] + a[0] * delta_t
        self.v_next[1] = self.v[1] + a[1] * delta_t

    def calc_physics(self, a):
        self.update_v(a)
        self.update_p()

    # update my v to v_next etc.
    def update_physics(self):
        self.v = [self.v_next[0], self.v_next[1]]
        self.p = [self.p_next[0], self.p_next[1]]

    ###################### camera update #############################
    def move_cam(self, dx, dy, preserve=False):  # directly move cam
        self.p_cam[0] += dx
        self.p_cam[1] += dy

    def cam_follow_physics(self, scale):  # cam update just before update_physics
        dx = (self.p_next[0] - self.p[0]) * scale
        dy = (self.p_next[1] - self.p[1]) * scale
        self.move_cam(dx, dy)

    # scale이 변화하여 실제 거리를 카메라 상의 거리로 변환해야 함
    def change_cam_scale(self, scale_change_unit, centerX, centerY):  # called immediately when changing scale
        dx = (centerX - self.p_cam[0]) * scale_change_unit
        dy = (centerY - self.p_cam[1]) * scale_change_unit
        self.move_cam(dx, dy, preserve=True)

    def change_scale(self, scale):
        pass






