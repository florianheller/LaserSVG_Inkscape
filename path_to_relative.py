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

import inkex

class PathToRelative(inkex.EffectExtension):

    def add_arguments(self, pars):
        pass

    def effect(self):
        if not self.svg.selected:
            raise inkex.AbortExtension("Please select an object.")
       
        for pathID in self.options.ids:
            path = self.svg.getElementById(pathID)

            #assume default namespace for d-attribute
            path.set("d",path.original_path.to_relative())

if __name__ == '__main__':
    PathToRelative().run()
