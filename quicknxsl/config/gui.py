#-*- coding: utf-8 -*-
'''
GUI configuration settings
'''

config_file='gui'

# UI geometry
interface='default'
geometry=None
state=None
splitters=([240, 505, 239], [298, 438], [240, 169, 360])

# plot options
color_selection=0
show_colorbars=False
normalizeXTof=False
# plot borders
figure_params=[
               {'top': 0.95, 'right': 0.95, 'bottom': 0.1, 'left': 0.15}, # xy_overview
               {'top': 0.95, 'right': 0.95, 'bottom': 0.1, 'left': 0.15}, # xtof_overview
               {'top': 0.95, 'right': 0.95, 'bottom': 0.1, 'left': 0.15}, # refl
               {'top': 0.95, 'right': 0.95, 'bottom': 0.1, 'left': 0.15}, # x_project
               {'top': 0.95, 'right': 0.95, 'bottom': 0.1, 'left': 0.15}  # y_project
               ]
