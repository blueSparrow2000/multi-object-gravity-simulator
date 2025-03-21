'''
Artificial is a controllable matter
'''

from matter import *

class Artificial(Matter):
    def __init__(self, name, mass, p, v, radius, type='rocky',save_trajectory = False):
        super().__init__(name, mass, p, v, radius, type='rocky',save_trajectory = save_trajectory )
        self.color = (184,134,11) # 'darkgoldenrod'
        self.object_type = 'artificial'


    def rotate(self, clockwise = False):
        pass

    def thrust(self):
        pass

    def laser(self, direction):
        pass

    def test_particle(self):
        pass
