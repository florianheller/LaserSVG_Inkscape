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


# Removes all 0-length segments from a path

import inkex
from math import sqrt

class LaserSVG_cleaner(inkex.EffectExtension):

    threshold = 0.00001

    def add_arguments(self, pars):
        pars.add_argument("--threshold", default=0.0001, help="The threshold under which segments are removed")


    def effect(self):
        if not self.svg.selected:
            raise inkex.AbortExtension("Please select an object.")
       
        self.threshold = float(self.options.threshold)

        for pathID in self.options.ids:
            path = self.svg.getElementById(pathID)
            cleanedPath = inkex.paths.Path()

            for segment in path.original_path.to_relative():
                if self.getCommandLength(segment) > self.threshold:
                    cleanedPath.append(segment)
            
            inkex.utils.debug(cleanedPath)
            path.set("d",cleanedPath)



    # Get the length of a relative command segment
    # such that we don't have to handle all the different parameter locations
    def getCommandLength(self, command) -> float:
        dx,dy = self.getCommandDelta(command)
        return sqrt(dx**2 + dy**2)
        
    def getCommandDelta(self, command):
        if command.letter == 'l' or command.letter == 'm':
            return (command.args[0], command.args[1])
        elif command.letter == 'h':
            return (command.args[0], 0)
        elif command.letter == 'v':
            return (0, command.args[0])
        elif command.letter == 'c':
            return (command.args[4], command.args[5])
        elif command.letter in ['s', 'q']:
            return (command.args[2], command.args[3])
        elif command.letter == 'a':
            return (command.args[5], command.args[6])
        else:
            return (0, 0)


if __name__ == '__main__':
    LaserSVG_cleaner().run()
