# -*- coding: utf-8 -*-
"""
matter format:
name, mass, position, velocity, radius, type
line starting with '#' is considered as comment and ignored

converted to:
string, int, list, list, int, string

"""

import os, sys
from matter import *


class MatterReader():
    def __init__(self):
        self.matter_list = []
        
    def read_matter(self, filename='matters'):
        # do file i/o 
        APP_FOLDER = os.path.dirname(os.path.realpath(sys.argv[0]))
        full_path = os.path.join(APP_FOLDER, '{}.txt'.format(filename))
        
        # instantiate each text into matter (check format!)
        with open(full_path, "r") as f:
            lines = [line.strip() for line in f.readlines()] # each lines 
            lines = [line for line in lines if line[0]!='#'] # comment 처리
            tokens = [line.split(',') for line in lines]
        
        for token in tokens:
            matter = Matter( token[0], float(token[1]), [float(token[2]),float(token[3])], [float(token[4]),float(token[5])], float(token[6]), type = token[7], save_trajectory = True)
            self.matter_list.append(matter)

    def get_matter_list(self):
        return self.matter_list
    
    def print_matter_list(self):
        for matter in self.matter_list:
            print(matter)

    def reset(self):
        self.matter_list = []








