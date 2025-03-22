# -*- coding: utf-8 -*-
"""
matter format:
name, mass, position, velocity, radius, type
line starting with '#' is considered as comment and ignored

converted to:
string, int, list, list, int, string

"""

import os, sys
from artificial import *

class MatterReader():
    APP_FOLDER = os.path.dirname(os.path.realpath(sys.argv[0])) + '/systems/'
    def __init__(self):
        self.matter_list = []
        self.artificial_list = []
        self.system_names = self.read_all_system_names()

    def read_matter(self, filename='matters'):
        # do file i/o 
        full_path = os.path.join(MatterReader.APP_FOLDER, '{}.txt'.format(filename))
        
        # instantiate each text into matter (check format!)
        with open(full_path, "r") as f:
            lines = [line.strip() for line in f.readlines()] # each lines 
            lines = [line for line in lines if line[0]!='#'] # comment 처리
            tokens = [line.split(',') for line in lines]
        
        for token in tokens:
            if token[8]=='m':
                matter = Matter( token[0], float(token[1]), [float(token[2]),float(token[3])], [float(token[4]),float(token[5])], float(token[6]), type = token[7], save_trajectory = True)
                self.matter_list.append(matter)
            elif token[8]=='a': # get artificial list - 구분자로 구분되어있음
                artificial = Artificial( token[0], float(token[1]), [float(token[2]),float(token[3])], [float(token[4]),float(token[5])], float(token[6]), type = token[7], save_trajectory = True)
                self.artificial_list.append(artificial)

    def read_all_system_names(self):
        all_system_names = list(os.listdir("systems/"))
        # remove '.txt' part
        all_system_names = [system_name[:-4] for system_name in all_system_names]
        # print(all_system_names)
        return all_system_names

    def get_system_names(self):
        return self.system_names

    def get_artificial_list(self):
        return self.artificial_list

    def get_matter_list(self):
        return self.matter_list
    
    def print_matter_list(self):
        for matter in self.matter_list:
            print(matter)

    def reset(self):
        self.matter_list = []
        self.artificial_list = []








