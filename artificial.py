'''
Artificial is a controllable matter
'''

from matter import *

class Artificial(Matter):
    def __init__(self, name, mass, p, v, radius, type='rocky',save_trajectory = False):
        super().__init__(name, mass, p, v, radius, type='rocky',save_trajectory = save_trajectory )
        self.color = (184,134,11) # 'darkgoldenrod'
        self.object_type = 'artificial'
        self.traj_colors = [(self.color_capping(self.color[0] - i * 5), self.color_capping(self.color[1] - i * 5),
                             self.color_capping(self.color[2] - i * 5)) for i in range(self.traj_size)]

        self.text = Text(self.p_cam[0], self.p_cam[1] - 30, self.name, color=self.color)

    def rotate(self, clockwise = False):
        pass

    def thrust(self):
        pass

    def laser(self, direction):
        pass

    def test_particle(self):
        pass
