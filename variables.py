"""
WLOG, G = 1.0 gravitational constant

HELP
(key up, down, right, left): camara movement                P

"""
HELP_TEXT = "(key up, down, right, left): camara movement                (mouse click on a matter): lock center on a matter, click   again to unlock (resizing window also unlocks)              (mouse wheel): zoom in and zoom out                         (mouse click&drag): camara movement                         press 'v' to toggle VERBOSE and UI                          press 't' to toggle Trail                                   press 'ESC' or 'Space' to pause in simulation screen (pause)"
delta_t = 0.02 #0.5
G = 2.0



# def f(*arg):
#     if arg: #len(arg)>0
#         print(arg[0])
#     elif len(arg)==0:
#         print('no input')
#
# f()
# f(1)
# f((1))
# f(1,2)