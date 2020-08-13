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
import types 
from lxml import etree

def __myStr__(mySelf):
    return mySelf.letter + " " + " ".join(mySelf.args)

def __myRepr__(mySelf):
    return 'repr'    
    # return self.name + "(" + ", ".join(*self.args)
        # return "{{}}({})".format(self._argt(", ")).format(self.name, *self.args)

class LaserSVG(inkex.EffectExtension):

    selected_nodes = {}
    LASER_NAMESPACE = "http://www.heller-web.net/lasersvg/"
    LASER_PREFIX = "laser"
    LASER = "{%s}" % LASER_NAMESPACE

    def add_arguments(self, pars):
        pars.add_argument("--material_thickness", default=3, help="The material thickness")
        pars.add_argument("--process_run", default=1, help="The step number of the two-step process")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        etree.register_namespace("laser", self.LASER_NAMESPACE)
        inkex.utils.NSS["laser"] = self.LASER_NAMESPACE

        inkex.utils.debug(self.options)

        # If nothing is selected, we can't do anything
        if not self.svg.selected:
            raise inkex.AbortExtension("Please select an object.")

        for pathID in self.options.ids:
            path = self.svg.getElementById(pathID)
            if self.options.tab == "tag_all":
                self.tagSegments(path, float(self.options.material_thickness))
            elif self.options.tab == "tag_selection":    
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


    class horzTemplate(inkex.paths.horz):
        def __str__(self):
            return self.letter + " " + " ".join(self.args)
    class vertTemplate(inkex.paths.vert):
        def __str__(self):
            return self.letter + " " + " ".join(self.args)

    def tagSegments(self, path, length):

        template = inkex.paths.Path()

        # inkex.utils.debug(path.original_path.to_superpath())
        inkex.utils.debug(path.original_path.to_relative())

        for command in path.original_path.to_relative():
            # if the length matches, we replace the args with the according tags
            if command.letter == 'l':
                x = command.args[0]
                y = command.args[1]
                if (x*x + y*y) == length*length:
                    template.append(inkex.path.line("\{{1}*thickness\}".format(x/length),"{\{1}*thickness\}".format(y/length)))
                else:
                    template.append(command)
            elif command.letter in ['v', 'h']:
                x = command.args[0]

                if  x * x == length * length:
                    ratio = (x / length)
                    pattern = ""
                    if ratio == 1:
                        pattern = "{thickness}"
                    elif ratio == -1:
                        pattern = "{-thickness}"
                    else:
                        pattern = "{{{0}*thickness}}".format( (x / length))
                    if command.letter == 'h':
                        newCommand = PathCommand.horz(pattern)
                    elif command.letter == 'v':
                        newCommand = self.vertTemplate(pattern)
                    # inkex.utils.debug(newCommand.__str__)
                        # newCommand.__str__ =  types.MethodType(__myStr__, super(inkex.paths.PathCommand, newCommand))
                        # newCommand.__str__ = self.__myStr__
                        # newCommand.__repr__ = types.MethodType(__myRepr__, newCommand)
                   #inkex.utils.debug(newCommand.__str__.__name__)
                    # inkex.utils.debug(newCommand.__str__())
                    template.append(newCommand)
                else: #if the length does not match
                    template.append(command)
            else: # if the command is not handled
                template.append(command)



        inkex.utils.debug(template)
        path.set(inkex.addNS("template", self.LASER_PREFIX),template)

    def parse_selected_nodes(self, nodes):
        result = {}
        for elem in nodes:
            # inkex.utils.debug(elem)
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

if __name__ == '__main__':
    LaserSVG().run()
