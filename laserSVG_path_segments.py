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

class LaserSVG(inkex.EffectExtension):

    selected_nodes = {}

    """Replace the selection's nodes with numbered dots according to the options"""
    def add_arguments(self, pars):
        pars.add_argument("--material_thickness", default=3, help="The material thickness")
        pars.add_argument("--process_run", default=1, help="The step number of the two-step process")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        # inkex.utils.debug(self.options.selected_nodes)

        # If nothing is selected, we can't do anything
        if not self.svg.selected:
            raise inkex.AbortExtension("Please select an object.")

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
