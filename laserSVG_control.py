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


import math

import inkex
from lxml import etree

class LaserSVG(inkex.EffectExtension):

    selected_nodes = {}
    LASER_NAMESPACE = "http://www.heller-web.net/lasersvg/"
    LASER_PREFIX = "laser"
    LASER = "{%s}" % LASER_NAMESPACE

    def add_arguments(self, pars):
        pars.add_argument("--kerf_width", default=0, help="The kerf width")
        pars.add_argument("--interactive", default=true, help="whether or not to add the stylesheet and the JS references to the file")
        pars.add_argument("--material_thickness", default=3, help="The material thickness")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        # self.document and self.svg seem both to be the same etree
        # The trailing slash is important, otherwise inkscape doesn't load the file correctly

        # Register the namespace prefix both with etree and inkscape
        etree.register_namespace("laser", self.LASER_NAMESPACE)
        inkex.utils.NSS["laser"] = self.LASER_NAMESPACE


        # Set/Update the global thickness in the SVG root node
        self.document.getroot().set(inkex.addNS("material-thickness", self.LASER_PREFIX), self.options.material_thickness)
        
        # adjust the thickness on all elements 
        self.adjust_element_thickness(self.options.material_thickness)

        # inkex.utils.debug(self.document.getroot().nsmap)



        #inkex.utils.debug(etree.tostring(self.document.getroot(),pretty_print=True))

        # #rect.set(XHTML + "thickness-adjust","width")
        # inkex.utils.debug(etree.tostring(rect))

    def adjust_element_thickness(self, newThickness):
        for node in self.document.getroot().iterfind(".//*[@%sthickness-adjust]" % self.LASER):
            adjust_setting = node.get("%s:thickness-adjust" % self.LASER_PREFIX)
            if adjust_setting == "width":
                node.attrib["width"] = newThickness
            elif adjust_setting == "height":
                node.attrib["height"] = newThickness
            elif adjust_setting == "both":
                node.attrib["height"] = newThickness
                node.attrib["width"] = newThickness
            # inkex.utils.debug(node.get("laser:thickness-adjust"))    
            # inkex.utils.debug(node.attrib)    
            # nodes = self.document.getroot().findall(".//*[@%s:thickness-adjust]" % self.LASER_PREFIX)
 


if __name__ == '__main__':
    LaserSVG().run()
