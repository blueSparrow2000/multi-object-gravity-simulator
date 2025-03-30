'''
Artificial is a controllable matter
'''
from fontTools.misc.bezierTools import epsilon

from matter import *

class Artificial(Matter):
    ANGULAR_VELOCITY_LIMIT = 0.01
    def __init__(self, name, mass, p, v, radius, type='metal',save_trajectory = False, rotation_acc = 0.001, linear_acc = 0.1):
        super().__init__(name, mass, p, v, radius, type=type,save_trajectory = save_trajectory)
        self.color = (184,134,11) # 'darkgoldenrod'
        self.object_type = 'artificial'
        self.traj_colors = [(self.color_capping(self.color[0] - i * 5), self.color_capping(self.color[1] - i * 5),
                             self.color_capping(self.color[2] - i * 5)) for i in range(self.traj_size)]

        self.text = Text(self.p_cam[0], self.p_cam[1] - 30, self.name, color=self.color)

        self.rotation_acc = rotation_acc
        self.linear_acc = linear_acc

        # shape = rectangle (ploygon)
        self.rect_angle = math.atan2(1, 4) # redefine initial angle since it is used as a point initial angle from x-axis
        # initialize points
        self.points = self.angels_to_points(self.p_cam ,self.radius_cam, [self.rect_angle, -self.rect_angle + math.pi, self.rect_angle + math.pi, -self.rect_angle])

        # rocket의 뒷부분
        self.back_color = (80, 80, 80)
        self.back_height = self.radius_cam*math.sin(self.rect_angle)
        self.back_width = self.radius_cam/5
        self.back_radius = ( self.back_width**2 + self.back_height**2 )**(1/2)
        self.back_dist = self.radius_cam*math.cos(self.rect_angle) + self.back_width

        self.back_rect_angle = math.atan2(self.back_height, self.back_width)
        self.back_pos = [self.p_cam[0] - self.back_dist, self.p_cam[1]]
        self.back_points = self.angels_to_points(self.back_pos,self.back_radius, [self.back_rect_angle, -self.back_rect_angle + math.pi, self.back_rect_angle + math.pi, -self.back_rect_angle])

        self.direction_rad = 100

    def change_radius_scale(self,scale):
        super().change_radius_scale(scale)
        self.back_height = self.radius_cam*math.sin(self.rect_angle)
        self.back_width = self.radius_cam/5
        self.back_radius = ( self.back_width**2 + self.back_height**2 )**(1/2)
        self.back_dist = self.radius_cam*math.cos(self.rect_angle) + self.back_width

    def angels_to_points(self, center, rad, angles):
        points = []
        for angle in angles:
            y_offset = -1 * rad * math.sin(angle + self.angle)
            x_offset = rad * math.cos(angle + self.angle)
            points.append((center[0] + x_offset, center[1] + y_offset))
        return points

    def draw(self, screen, show_trajectory = False):
        #draw camera view
        if show_trajectory:
            self.draw_traj(screen)

        pygame.draw.polygon(screen, self.color, self.points)
        pygame.draw.polygon(screen, self.back_color, self.back_points)

    def draw_direction_arrow(self,screen):
        # also draw direction pointer
        if self.locked:
            if Matter.DEBUG:
                speed = (self.v[0] ** 2 + self.v[1] ** 2) ** (1 / 2)  ## speed calculation makes performance slower
                self.update_info_text(speed)  # follow 할때만 속도를 변화
            pygame.draw.line(screen, (100, 0, 0), self.p_cam,
                             [self.p_cam[0] + self.direction_rad * math.cos(-self.angle),
                              self.p_cam[1] + self.direction_rad * math.sin(-self.angle)], 2)

    def calc_next_angle(self):
        self.angle_next = self.angle + self.angular_v
        # decay speed of rotation (or not)
        # self.angular_v /= 2
        # if abs(self.angular_v) < 0.001: # threshold
        #     self.angular_v = 0

    # change points with respect to angular velocity
    def calc_rot(self):
        # Calculate the coordinates of each point.
        self.points = self.angels_to_points(self.p_cam ,self.radius_cam, [self.rect_angle, -self.rect_angle + math.pi, self.rect_angle + math.pi, -self.rect_angle])
        self.back_pos = [self.p_cam[0] - self.back_dist*math.cos(-self.angle), self.p_cam[1]- self.back_dist*math.sin(-self.angle)]
        self.back_points = self.angels_to_points(self.back_pos,self.back_radius, [self.back_rect_angle, -self.back_rect_angle + math.pi, self.back_rect_angle + math.pi, -self.back_rect_angle])

    def update_physics(self):
        super().update_physics()
        # additional param for rotation - direclty update it instead of updating in the simulator (since it is only used in artficials)
        self.angle = self.angle_next

    # get the input from the keyboard if locked
    def handle_key_input(self, event_key):
        if self.locked:
            if event_key==pygame.K_a:
                self.rotate(1)
            elif event_key==pygame.K_d:
                self.rotate(-1)

    def handle_key_press(self, w_press, s_press):
        if self.locked:
            if w_press:
                self.thrust(1)
            if s_press:
                self.thrust(-1)

    def handle_click_input(self, mousepos):
        if self.locked:
            self.laser(mousepos)

        # 1: counter clock / -1: clock wise
    def rotate(self, direction=1):
        if abs(self.angular_v + direction * self.rotation_acc)>=Artificial.ANGULAR_VELOCITY_LIMIT: # rotation limit
            return
        soundPlayer.play_sound_effect('rotate gas')
        self.angular_v += direction * self.rotation_acc

    # 1: forward / -1: backward
    def thrust(self, direction=1):
        soundPlayer.play_sound_effect('thrust', True)
        # 해당 방향으로 속도 +
        # v_next에다 더해서 다음 루프때 속도를 올리는 개념으로 ㄱㄱ (v에다 하면 덮어씌워진다)
        # forward가 angle 방향임
        x_thrust = direction*math.cos(-self.angle)*self.linear_acc
        y_thrust = direction*math.sin(-self.angle)*self.linear_acc
        self.v_next = [self.v_next[0] + x_thrust, self.v_next[1]+ y_thrust]

    def laser(self, target):
        pass

    def test_particle(self):
        pass

    def move_cam(self,dx,dy,preserve = False): # directly move cam
        super().move_cam(dx,dy,preserve)
        self.back_pos[0] += dx # make cam pos integer
        self.back_pos[1] += dy


class Station(Artificial):
    def __init__(self, name, mass, p, v, radius, type='metal',save_trajectory = False, rotation_acc = 0.0005, linear_acc = 0.05):
        super().__init__(name, mass, p, v, radius, type=type,save_trajectory = save_trajectory, rotation_acc = rotation_acc, linear_acc = linear_acc)
        self.color = (100,200,220)
        self.traj_colors = [(self.color_capping(self.color[0] - i * 5), self.color_capping(self.color[1] - i * 5),
                             self.color_capping(self.color[2] - i * 5)) for i in range(self.traj_size)]

        self.text = Text(self.p_cam[0], self.p_cam[1] - 30, self.name, color=self.color)

    # draw more complicated shape
    def draw(self, screen, show_trajectory = False):
        #draw camera view
        if show_trajectory:
            self.draw_traj(screen)

        pygame.draw.polygon(screen, self.color, self.points)
        # pygame.draw.polygon(screen, self.back_color, self.back_points)

    # overwrite laser function of a rocket
    def handle_click_input(self, mousepos):
        if self.locked:
            self.spawn_rocket(mousepos)

    def spawn_rocket(self, mousepos):
        pass


