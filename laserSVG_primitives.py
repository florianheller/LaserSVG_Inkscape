 #!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) 2020 Florian Heller, florian.heller@uhasselt.be
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

# see https://launchpadlibrarian.net/235367843/debug_sel_nodes.py for more details
import math

import inkex
from lxml import etree

class LaserSVGPrimitives(inkex.EffectExtension):

    selected_nodes = {}
    LASER_NAMESPACE = "http://www.heller-web.net/lasersvg/"
    LASER_PREFIX = "laser"
    LASER = "{%s}" % LASER_NAMESPACE

    """Replace the selection's nodes with numbered dots according to the options"""
    def add_arguments(self, pars):
        pars.add_argument("--rect_adjustment", default="none", help="The dimension in which a rect should be adjusted when material thickness changes.")
        pars.add_argument("--rect_origin", default="none", help="The dimension in which a rect should be adjusted when material thickness changes.")
        pars.add_argument("--material_thickness", default=3, help="The material thickness")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        
        # Register the namespace prefix both with etree and inkscape
        etree.register_namespace("laser", self.LASER_NAMESPACE)
        inkex.utils.NSS["laser"] = self.LASER_NAMESPACE

        for elementID in self.options.ids:
            element = self.svg.getElementById(elementID)
            if element.tag == "{http://www.w3.org/2000/svg}rect":
                self.rectangleSettings(element, self.options)
        

        
        # # If nothing is selected, we can't do anything
        # if not self.svg.selected:
        #     raise inkex.AbortExtension("Please select an object.")

        # self.selected_nodes = self.parse_selected_nodes(self.options.selected_nodes)
        
        # # inkex.utils.debug(self.selected_nodes)

        # # report about selected nodes
        # for pathID, selected in self.selected_nodes.items():
        #     path = self.svg.getElementById(pathID)
        #     # p2 = path.original_path.to_superpath()
        #     # inkex.utils.debug('{0}'.format(p2))
        #     for element in selected: 
        #         inkex.utils.debug( '{0} - selected nodes of subpath {1}: {2}'.format(pathID, element, selected[element]))
        #         # show the coordinates
        #         for nodes in selected[element]:
        #             coordinates = path.original_path.to_superpath()[element][nodes][1]
        #             inkex.utils.debug('{0} - selected node {1}: {2}'.format(pathID, nodes, coordinates))
        #         # Check if path segment length matches specified thickness
        #         # check if a path template is already defined, if not, create one
        #         # place the {thickness} label at the repective place in the path template

    def rectangleSettings(self, element, options):
        element.set(inkex.addNS("thickness-adjust", self.LASER_PREFIX),options.rect_adjustment)

if __name__ == '__main__':
    LaserSVGPrimitives().run()
