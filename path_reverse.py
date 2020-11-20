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

import inkex

class PathReverse(inkex.EffectExtension):

    def add_arguments(self, pars):
        pass

    def effect(self):
        if (len(self.options.ids) == 0 ):
            raise inkex.AbortExtension("Please select a path to reverse")

        # Take a first path segment
        for pathID in self.options.ids:
            path = self.svg.getElementById(pathID).original_path
            inkex.utils.debug(path)

            reversedPath = path.reverse()
            inkex.utils.debug(reversedPath)

            self.svg.getElementById(pathID).set("d",reversedPath)

if __name__ == '__main__':
    PathReverse().run()
