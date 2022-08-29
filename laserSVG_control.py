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
import re

class LaserSVG(inkex.EffectExtension):

    selected_nodes = {}
    LASER_NAMESPACE = "http://www.heller-web.net/lasersvg/"
    LASER_PREFIX = "laser"
    LASER = "{%s}" % LASER_NAMESPACE
    laserSVGScriptURL = "https://florianheller.github.io/lasersvg/lasersvg.js"

    oldThickness = 0
    def add_arguments(self, pars):
        pars.add_argument("--kerf_width", default=0, help="The kerf width")
        pars.add_argument("--action", default="cut", help="The default laser operation")
        pars.add_argument("--scale", default="100", help="The scaling factor ")

        pars.add_argument("--interactive", default=True, help="whether or not to add the stylesheet and the JS references to the file")
        pars.add_argument("--material_thickness", default=3, help="The material thickness")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        # self.document and self.svg seem both to be the same etree
        # The trailing slash is important, otherwise inkscape doesn't load the file correctly

        # Register the namespace prefix both with etree and inkscape
        etree.register_namespace("laser", self.LASER_NAMESPACE)
        inkex.utils.NSS["laser"] = self.LASER_NAMESPACE

        #Save the old thickness 
        oldValue = self.document.getroot().get(inkex.addNS("material-thickness", self.LASER_PREFIX))
        if oldValue is not None:
            self.oldThickness  = float(oldValue)

        # Set/Update the global thickness in the SVG root node
        self.document.getroot().set(inkex.addNS("material-thickness", self.LASER_PREFIX), self.options.material_thickness)

        # Set/Update the global kerf value in the SVG root node
        self.document.getroot().set(inkex.addNS("kerf", self.LASER_PREFIX), self.options.kerf_width)

        #Set/Update the gobal laser action in the SVG root node
        self.document.getroot().set(inkex.addNS("action", self.LASER_PREFIX), self.options.action)
        
        # adjust the thickness on all elements 
        self.adjust_element_thickness(self.options.material_thickness)

        # inkex.utils.debug(self.document.getroot().nsmap)

        if self.options.interactive == 'true':
            # Check if there is a reference to the JS and CSS already, otherwise add it
            # While workin on the file, Inkscape requires the SVG namespace in front of SVG element, even though the prefix will be removed while saving. 
            if not self.document.getroot().findall(".//{http://www.w3.org/2000/svg}script[@xlink:href='http://www2.heller-web.net/lasersvg/lasersvg.js']"):
                scriptElement = etree.SubElement(self.document.getroot(), "script")
                # inkex.utils.debug(scriptElement.localName)
                scriptElement.set("type", "text/javascript")
                scriptElement.set("xlink:href",  self.laserSVGScriptURL)

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

            # Adjust position of origin is specified
            newThicknessF = float(newThickness)
            originX, originY, centerX, centerY = 0, 0, 0, 0
            origin = node.get(inkex.addNS("origin", self.LASER_PREFIX))

            if origin is not None:
                if node.get(inkex.addNS("x", self.LASER_PREFIX)) is None:
                    centerX = float(node.get("x")) + (self.oldThickness/2)
                    node.set(inkex.addNS("centerX", self.LASER_PREFIX), centerX)
                    node.set(inkex.addNS("x", self.LASER_PREFIX), node.get("x"))
 
                centerX = float(node.get(inkex.addNS("centerX", self.LASER_PREFIX)))
                originX = float(node.get(inkex.addNS("x", self.LASER_PREFIX)))

                if node.get(inkex.addNS("y", self.LASER_PREFIX)) is None:
                    centerY = float(node.get("y")) + (self.oldThickness/2)
                    node.set(inkex.addNS("centerY", self.LASER_PREFIX), centerY)
                    node.set(inkex.addNS("y", self.LASER_PREFIX), node.get("y"))
                
                centerY = float(node.get(inkex.addNS("centerY", self.LASER_PREFIX)))
                originY = float(node.get(inkex.addNS("y", self.LASER_PREFIX)))

                if origin == "bottom":
                    if adjust_setting == "height" or adjust_setting == "both":
                        node.set("y", originY + self.oldThickness - newThicknessF)
                elif origin == "right":
                    if adjust_setting == "width" or adjust_setting == "both":
                        node.set("x", originX + self.oldThickness - newThicknessF)
                elif origin == "bottom-right":
                    if adjust_setting == "height" or adjust_setting == "both":
                        node.set("y", originY + self.oldThickness - newThicknessF)
                    if adjust_setting == "width" or adjust_setting == "both":
                        node.set("x", originX + self.oldThickness - newThicknessF)
                elif origin == "center":
                    if adjust_setting == "height" or adjust_setting == "both":
                        node.set("y", centerY - (newThicknessF/2))
                    if adjust_setting == "width" or adjust_setting == "both":
                        node.set("x", centerX - (newThicknessF/2))
            # inkex.utils.debug(node.get("laser:thickness-adjust"))    
            # inkex.utils.debug(node.attrib)    
            # nodes = self.document.getroot().findall(".//*[@%s:thickness-adjust]" % self.LASER_PREFIX)
        # And now the paths     
        self.adjust_path_thickness(newThickness)


    def adjust_path_thickness(self, newThickness):
        for node in self.document.getroot().iterfind(".//*[@{}template]".format(self.LASER)):
            template = node.get(inkex.addNS("template", self.LASER_PREFIX))
            pattern = re.compile(r'[{](.*?)[}]')
            evaluate = lambda x: str(eval(x.group(1),{},{"thickness":float(self.options.material_thickness)}))
            result = re.sub(pattern, evaluate, template)
            node.set("d",result)




if __name__ == '__main__':
    LaserSVG().run()
