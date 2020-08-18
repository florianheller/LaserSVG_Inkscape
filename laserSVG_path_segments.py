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
from math import sqrt

class LaserSVG(inkex.EffectExtension):

    selected_nodes = {}
    LASER_NAMESPACE = "http://www.heller-web.net/lasersvg/"
    LASER_PREFIX = "laser"
    LASER = "{%s}" % LASER_NAMESPACE

    def add_arguments(self, pars):
        pars.add_argument("--material_thickness", default=3, help="The material thickness")
        pars.add_argument("--selection_process_run", default=1, help="The step number of the two-step process")
        pars.add_argument("--slit_process_run", default=1, help="The step number of the two-step process")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        etree.register_namespace("laser", self.LASER_NAMESPACE)
        inkex.utils.NSS["laser"] = self.LASER_NAMESPACE

        inkex.utils.debug(self.options)

        # If nothing is selected, we can't do anything
        if not self.svg.selected:
            raise inkex.AbortExtension("Please select an object.")

        if not "{}material-thickness".format(self.LASER) in self.document.getroot().keys():
            raise inkex.AbortExtension("Please set the material thickness in the LaserSVG parameter control panel first.")            

        material_thickness = float(self.document.getroot().get("{}material-thickness".format(self.LASER)))

        for pathID in self.options.ids:
            path = self.svg.getElementById(pathID)
            if self.options.tab == "tag_all":
                self.tagSegments(path, float(material_thickness))
            elif self.options.tab == "tag_selected":    
                self.selected_nodes = self.parse_selected_nodes(self.options.selected_nodes)
                
                # inkex.utils.debug(self.selected_nodes)

                # report about selected nodes
                for pathID, selected in self.selected_nodes.items():
                    path = self.svg.getElementById(pathID)
                    # p2 = path.original_path.to_superpath()
                    # inkex.utils.debug('{0}'.format(p2))
                    for element in selected: 
                        inkex.utils.debug( '{0} - selected nodes of subpath {1}: {2}'.format(pathID, element, selected[element]))
                        # show the coordinates
                        for nodes in selected[element]:
                            coordinates = path.original_path.to_superpath()[element][nodes][1]
                            inkex.utils.debug('{0} - selected node {1}: {2}'.format(pathID, nodes, coordinates))
                        # Check if path segment length matches specified thickness
                        # check if a path template is already defined, if not, create one
                        # place the {thickness} label at the repective place in the path template
            elif self.options.tab == "tag_selection":    
                if self.options.selection_process_run == '1':
                    self.addSelectionLayer(path, float(material_thickness))
                elif self.options.selection_process_run == '2':
                    highlightLayer = self.svg.getElementById("highlightLayer")
                    if highlightLayer is not None:
                        self.mapSelectionToPaths(highlightLayer)
                    else:
                        raise inkex.AbortExtension("Please highlight the segments first using the selection layer")


    class template(object):
        def __str__(self):
            return self.letter + " " + ", ".join(self.args)
    class horzTemplate(template,inkex.paths.horz):
        pass
    class vertTemplate(template, inkex.paths.vert):
        pass
    class lineTemplate(template, inkex.paths.line):
        pass

    def tagSegments(self, path, length):

        template = inkex.paths.Path()

        # inkex.utils.debug(path.original_path.to_superpath())
        inkex.utils.debug(path.original_path.to_relative())

        for command in path.original_path.to_relative():
            # if the length matches, we replace the args with the according tags
           template.append(self.tagCommand(command, length))

        inkex.utils.debug(template)
        path.set(inkex.addNS("template", self.LASER_PREFIX),template)

    def parse_selected_nodes(self, nodes):
        result = {}
        for elem in nodes:
            elemData = elem.rsplit(':', 2)
            pathID = elemData[0]
            sub_path = int(elemData[1])
            sel_node = int(elemData[2])
            if pathID not in result:
                result[pathID] = {sub_path: [sel_node]}
            else:
                if sub_path not in result[pathID]:
                    result[pathID][sub_path] = [sel_node]
                else:
                    result[pathID][sub_path].extend([sel_node])
        return result

    def addSelectionLayer(self, path, length):
        # In Inkscape, layers are SVG-Groups with a special label. 
        if not self.document.getroot().findall(".//{http://www.w3.org/2000/svg}g[@id='highlightLayer']"):
            layer = etree.SubElement(self.document.getroot(), "g")
            layer.set("id", "highlightLayer")
            layer.set("inkscape:label",  "Highlight layer")
        else:
            layer = self.svg.getElementById("highlightLayer")

        # Check for every path segment that is of size length
        for index,command in enumerate(path.original_path.to_relative()): #Easier in relative mode
            commandLength = self.getCommandLength(command)
            if commandLength is not None:
                if abs(commandLength-length) < 0.01:
                # Now get the coordinates to draw a line from the absolute mode path
                # TODO: handle Move and Close and H and V (do they exist in absolute mode? Doesn't make much sense)
                    line = etree.SubElement(layer, "line")
                    line.set("x1", path.original_path.to_absolute()[index].args[0] )
                    line.set("y1", path.original_path.to_absolute()[index].args[1])
                    line.set("x2", path.original_path.to_absolute()[index-1].args[0])
                    line.set("y2", path.original_path.to_absolute()[index-1].args[1])
                    line.set("stroke", "limegreen")
                    # Use a similar notation to map the segments as for selected nodes
                    # id:entity:segment_number
                    # TODO: handle paths with multiple entities, aka, multiple M commands
                    # example [n for n in xrange(len(text)) if text.find('ll', n) == n]
                    line.set("id", "{}:{}:{}".format(path.get("id"),0, index))

    # Replaces the path segments corresponding to the markers in selectionLayer with {thickness} labels
    def mapSelectionToPaths(self, selectionLayer):
        # Iterate over all children in selectionLayer and create a dictionary of IDs and segments numbers
        # While we could just call the replace method for every line, I think storing it an then running over the individual paths only once should be faster
        result = {}
        for line in selectionLayer:
            elemData = line.get("id").rsplit(':', 2)
            pathID = elemData[0]
            sub_path = int(elemData[1])
            segment = int(elemData[2])
            if pathID in result:
                result[pathID].append(segment)
            else:
                result[pathID] = [segment]
            selectionLayer.remove(line)

        #if empty, remove the selection layer
        if len(selectionLayer) == 0:
            selectionLayer.getparent().remove(selectionLayer)


        # Now that we have everything collected, let's tag these segments
        for element,segments in result.items():
            self.tagSegmentsInPath(self.svg.getElementById(element), segments)



    def tagSegmentsInPath(self, path, segments):
        template = path.copy().original_path.to_relative()

        for index,command in enumerate(path.original_path.to_relative()):
            if index in segments:
                template[index] = self.tagCommand(command, float(self.document.getroot().get("{}material-thickness".format(self.LASER))))

        path.set(inkex.addNS("template", self.LASER_PREFIX),template)



        # sp = path.original_path.to_superpath()
        # inkex.utils.debug(sp[0][2])
        # for segment in path.original_path:
        #     inkex.utils.debug(segment)

    # returns a command with tagged parameters
    def tagCommand(self, command, thickness):
        if command.letter == 'l':
            x = command.args[0]
            y = command.args[1]

            # In non-orthogonal cases, there can be a minimal difference due to floating points
            difference = (x*x + y*y) - (thickness*thickness)

            if abs(difference) < 0.01:
                return self.lineTemplate("{{{}*thickness}}".format(x/thickness),"{{{}*thickness}}".format(y/thickness))
            else:
                return command
        elif command.letter in ['v', 'h']:
            x = command.args[0]

            if  x * x == thickness * thickness:
                ratio = (x / thickness)
                pattern = ""
                if ratio == 1:
                    pattern = "{thickness}"
                elif ratio == -1:
                    pattern = "{-thickness}"
                else:
                    pattern = "{{{0}*thickness}}".format( (x / thickness))
                if command.letter == 'h':
                    newCommand = self.horzTemplate(pattern)
                elif command.letter == 'v':
                    newCommand = self.vertTemplate(pattern)

                return newCommand
            else: #if the length does not match
                return command
        else: # if the command is not handled
            return command

    # Get the length of a relative command segment
    # such that we don't have to handle all the different parameter locations
    def getCommandLength(self, command):
        if command.letter in ['l', 'm']:
            return sqrt(command.args[0]**2 + command.args[1]**2)
        elif command.letter in ['h', 'v']:
            return command.args[0]
        # TODO: rest of the commands 



if __name__ == '__main__':
    LaserSVG().run()
