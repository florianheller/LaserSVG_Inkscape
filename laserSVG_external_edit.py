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

import gi
gi.require_version('Gtk', '3.0') 
from gi.repository import Gtk

class EditorWindow(Gtk.Window):
    def __init__(self, extension):
        Gtk.Window.__init__(self, title="Button Demo")
        self.set_border_width(10)

        hbox = Gtk.Box(spacing=6)
        self.add(hbox)

        button = Gtk.Button.new_with_label("Click Me")
        button.connect("clicked", self.on_click_me_clicked)
        hbox.pack_start(button, True, True, 0)

        button = Gtk.Button.new_with_mnemonic("_Open")
        button.connect("clicked", self.on_open_clicked)
        hbox.pack_start(button, True, True, 0)

        button = Gtk.Button.new_with_mnemonic("_Close")
        button.connect("clicked", self.on_close_clicked)
        hbox.pack_start(button, True, True, 0)

    def on_click_me_clicked(self, button):
        print('"Click me" button was clicked')

    def on_open_clicked(self, button):
        print('"Open" button was clicked')

    def on_close_clicked(self, button):
        print("Closing application")
        Gtk.main_quit()


class LaserSVG_Editor(inkex.EffectExtension):

    selected_nodes = {}
    LASER_NAMESPACE = "http://www.heller-web.net/lasersvg/"
    LASER_PREFIX = "laser"
    LASER = "{%s}" % LASER_NAMESPACE

    def add_arguments(self, pars):
        pars.add_argument("--material_thickness", default=3, help="The material thickness")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        inkex.utils.debug("Extension Run")
        # Doesn't seem to exist anymore
        # stdout = inkex.command.call('echo','test')
        # inkex.utils.debug(stdout)

        # Create a new Gtk window with the content of the file we're handling. 
        # TODO: Gtk.main creates a new runloop, blocking interaction with inkscape until our new window is closed. 
        # win = Gtk.Window()
        # image = Gtk.Image()
        # image.set_from_file(self.options.input_file)
        # win.add(image)



if __name__ == '__main__':
    lEditor =  LaserSVG_Editor()
    win = EditorWindow(lEditor)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    lEditor.run()
