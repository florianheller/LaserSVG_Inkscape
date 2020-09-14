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
import re
from lxml import etree
from math import sqrt, atan2, pi, sin, cos, trunc

class LaserSVG(inkex.EffectExtension):

    selected_nodes = {}
    LASER_NAMESPACE = "http://www.heller-web.net/lasersvg/"
    LASER_PREFIX = "laser"
    LASER = "{%s}" % LASER_NAMESPACE

    def add_arguments(self, pars):
        pars.add_argument("--material_thickness", default=3, help="The material thickness")
        pars.add_argument("--selection_process_run", default=1, help="The step number of the two-step process")
        pars.add_argument("--slit_process_run", default=1, help="The step number of the two-step process")
        pars.add_argument("--kerf_direction", default=0, help="The direction in which the kerf-adjustments should be made.")
        pars.add_argument("--action", default="none", help="The default laser operation")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        etree.register_namespace("laser", self.LASER_NAMESPACE)
        inkex.utils.NSS["laser"] = self.LASER_NAMESPACE

        # inkex.utils.debug(self.options)

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
                    self.addSelectionLayer(path, float(material_thickness), "highlightLayer", "Thickness segments", "limegreen")
                elif self.options.selection_process_run == '2':
                    highlightLayer = self.svg.getElementById("highlightLayer")
                    if highlightLayer is not None:
                        self.mapSelectionToPaths(highlightLayer, "segments")
                    else:
                        raise inkex.AbortExtension("Please highlight the segments first using the selection layer")
            elif self.options.tab == "tag_slots":    
                if self.options.slit_process_run == '1':
                    self.addSelectionLayer(path, float(material_thickness), "slitLayer", "Thickness slits", "fuchsia")
                elif self.options.slit_process_run == '2':
                    slitLayer = self.svg.getElementById("slitLayer")
                    if slitLayer is not None:
                        self.mapSelectionToPaths(slitLayer, "slits")
                    else:
                        raise inkex.AbortExtension("Please highlight the slits first using the selection layer")


    class template(object):
        def __str__(self):
            return self.letter + " " + ", ".join(self.args)
    class horzTemplate(template,inkex.paths.horz):
        pass
    class vertTemplate(template, inkex.paths.vert):
        pass
    class lineTemplate(template, inkex.paths.line):
        pass
    class moveTemplate(template, inkex.paths.move):
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

    def addSelectionLayer(self, path, length, layername, readable_layername, layercolor):
        # In Inkscape, layers are SVG-Groups with a special label. 
        if not self.document.getroot().findall(".//g[@id='{}']".format(layername)):
            layer = etree.SubElement(self.document.getroot(), "g")
            layer.set("id", layername)
            layer.set("inkscape:label",  readable_layername)
        else:
            layer = self.svg.getElementById(layername)
        # Check for every path segment that is of size length
        for index,command in enumerate(path.original_path.to_relative()): #Easier in relative mode
            commandLength = self.getCommandLength(command)
            if commandLength is not None:
                if abs(commandLength-length) < 1:
                # Now get the coordinates to draw a line from the absolute mode path

                    line = etree.SubElement(layer, "line")
                    line.set("x1", self.getCommandEndpoint(path.original_path.to_absolute()[index], path.original_path.to_absolute()[index-1])[0])
                    line.set("y1", self.getCommandEndpoint(path.original_path.to_absolute()[index], path.original_path.to_absolute()[index-1])[1])
                    line.set("x2", self.getCommandEndpoint(path.original_path.to_absolute()[index-1], path.original_path.to_absolute()[index-2])[0])
                    line.set("y2", self.getCommandEndpoint(path.original_path.to_absolute()[index-1], path.original_path.to_absolute()[index-2])[1])
                    line.set("stroke", layercolor)
                    # Use a similar notation to map the segments as for selected nodes
                    # id:entity:segment_number
                    # TODO: handle paths with multiple entities, aka, multiple M commands
                    # example [n for n in xrange(len(text)) if text.find('ll', n) == n]
                    line.set("id", "{}:{}:{}".format(path.get("id"),0, index))

    # Replaces the path segments corresponding to the markers in selectionLayer with {thickness} labels
    def mapSelectionToPaths(self, selectionLayer, mode):
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
            if mode == "segments":
                self.tagSegmentsInPath(self.svg.getElementById(element), segments)
            elif mode == "slits":
                self.tagSlitsInPath(self.svg.getElementById(element), segments)

    # The tagging of a slit is a bit more complicatedas we need to adapt the two segments to the left and right respectively.
    # First, we tag the slit base as being of material thickness
    # Second, we calculate a line between the start point of the left slit wall and the end-point of the right slit wall. 
    # This gives us a line that closes the slit, which we will use as an approximation of the slope of the cutout. 

    # This only works after https://gitlab.com/inkscape/extensions/-/commit/44f09e5a01b3ee9dda6d75499f97561a2ef9351f this fix

    def tagSlitsInPath(self, path, segments):
        template = path.copy().original_path.to_relative()
        thickness = float(self.document.getroot().get("{}material-thickness".format(self.LASER)))

        csp_abs = path.original_path.to_absolute().to_superpath()
        # inkex.utils.debug(csp_abs[0])
        # csp = path.original_path
        # inkex.utils.debug(csp)
        # for segment in csp.proxy_iterator():
        #     for point in csp.control_points:
        #         inkex.utils.debug("{} {}".format(segment, point))
        # Store away the original control points in absolute values
        cps = []
        for cp in path.original_path.proxy_iterator():
            cps.append(cp.previous_end_point)

        for index,command in enumerate(path.original_path.to_relative()):
            if index in segments:
                # if index > 1:
                    # i = command.control_points(csp[index], csp[index-1], csp[index-2])
                    # inkex.utils.debug(cps[index])
                if index >=2:
                    ll = inkex.transforms.DirectedLineSegment(cps[index-2],cps[index-1])
                if index >=1:
                    l = inkex.transforms.DirectedLineSegment(cps[index-1],cps[index])
                center = inkex.transforms.DirectedLineSegment(cps[index], cps[index+1])
                if index < len(cps)-2:
                    r = inkex.transforms.DirectedLineSegment(cps[index+1], cps[index+2])
                if index < len(cps)-3:
                    rr = inkex.transforms.DirectedLineSegment(cps[index+2],cps[index+3])                

                gap = inkex.transforms.DirectedLineSegment(cps[index-1],cps[index+2])

                self.drawDebugLine("layer1", gap.x0, gap.y0, gap.x1, gap.y1, "green")

                #inkex.utils.debug("{} {} {}".format(ll.angle, ll.intersect(rr), rr.angle))

                # Set the length of the slit base
                template[index] = self.tagCommand(command, thickness)

                # The segment to the left and right of the base need to be adjusted. 
                # For that, we take the centerpoint of the slit base, and calculate how much change in x and y
                # this generates if we draw a vector of half the thickness from there with the same angle as the current base
                base_dx, base_dy = self.getCommandDelta(command)
                base_origin_x, base_origin_y = csp_abs[0][index-1][0][0], csp_abs[0][index-1][0][1]
                # centerpoint = ((base_dx/2),(base_dy/2))
                base_center= (base_origin_x+(base_dx/2), base_origin_y+(base_dy/2))

                # self.drawDebugLine("layer1" , centerpoint[0], centerpoint[1], centerpoint[0]+((5/2)*cos(c.angle)), centerpoint[1]+((5/2)*sin(c.angle)), "red")




                # TODO: this test should be mod 180° or mod π 
                #if not truncate(gap.angle,8) == truncate(center.angle,8):
                # If the segment leading to or from the slit is parallel to the slit base, we do not need to adjust the length of the slit walls
                inkex.utils.debug(f"{ll.angle} {template[index-2].letter} {center.angle} {rr.angle}")

                if abs(ll.angle - center.angle) > 0.0001 and template[index-2].letter != 'm':
                    inkex.utils.debug("LL Not parallel")
                    calc_l = self.shortenSlitLeg(thickness, gap, template[index], template[index-1], l)
                    inkex.utils.debug(f"Calc l {calc_l}")
                    template[index-1] = self.tagCommandWithCalculation(template[index-1],calc_l)

                if abs(rr.angle - center.angle) > 0.0001 and template[index+2].letter != 'z':
                    inkex.utils.debug(f"RR Not parallel {rr.angle} {center.angle} {abs(truncate(rr.angle - center.angle, 5))}")
                    calc_r = self.shortenSlitLeg(thickness, gap, template[index], template[index+1], r)
                    inkex.utils.debug(f"Calc r {calc_r}")
                    template[index+1] = self.tagCommandWithCalculation(template[index+1],calc_r)

          

                if index >=2:
                    template[index-2] = self.tagCommandWithCalculation(template[index-2], self.tagSlitSegment(template[index-2],gap, center))
                if index < len(cps)-2:
                    template[index+2] = self.tagCommandWithCalculation(template[index+2], self.tagSlitSegment(template[index+2],gap, center))
                # self.drawDebugLine("layer1", gap_center[0], gap_center[1], gap_center[0]+((5/2)*cos(gap.angle)),gap_center[1]+((5/2)*sin(c.angle)), "limegreen")
                

                # The new endpoint for the ll segment is thus gap_center.x-{thickness*cos(gap.angle),gap_center.y-{thickness*sin(gap.angle)}}
                path.set(inkex.addNS("template", self.LASER_PREFIX),template)

                # template[index-1] = self.tagCommandWithCalculation(command, )
                # inkex.utils.debug(template[index].end_point)

                # x = command.previous_end_point
                # inkex.utils.debug("{}".format(x))
                #segments-2 and +2 need to be shortened by 0.5*thickness to keep the slit centered
                #segments-1 and +1 need to be adjusted such that they match

    def shortenSlitLeg(self, thickness, gap, base, leg, leg_line):
        # We assume that the base and it's adjacent walls are orthogonal to each-other (90°)
        # This allows us to use the sinus-calulations in a triangle, as the sum of all inner angles in a triangle is 180, 
        # and one is fixed to 90, the last angle (opposite of alpha) is then 90-alpha

        # First we need to transform gap.angle into an inner angle if it is not already the case
        alpha = pi+gap.angle if gap.angle < -pi/2 else pi - gap.angle if gap.angle > pi/2 else gap.angle
        beta = pi/2-alpha

        # a/sin(alpha) = b/sin(beta) = c/sin(gamma)
        # b is thickness, and gamma is π/2 
        c = thickness/sin(beta)
        a = thickness*sin(alpha)/sin(beta)

        inkex.utils.debug(f"The triangle: a {a} alpha {alpha}({degrees(alpha)}) b {thickness} beta {beta}({degrees(beta)}) c {c} ")
        # inkex.utils.debug(f"l {l.angle} {sin(l.angle)} {cos(l.angle)} \n r {r.angle} {sin(r.angle)} {cos(r.angle)}")

        delta = self.getCommandDelta(leg)
        sign = '+' if sin(leg_line.angle) > 0 else '-'
        calc = (f"{delta[0]}", f"{{{delta[1]+a/2}{sign}{(0.5/sin(beta))*sin(alpha)}*thickness}}")
        #TODO: missing sin and cos factors here toi make it generic



        # delta_r = self.getCommandDelta(template[index+1])
        # calc_r = (f"{delta_r[0]}", f"{{{delta_r[1]+a/2}-{(0.5/sin(beta))*sin(alpha)}*thickness}}")

        inkex.utils.debug(f"Deltas: {delta}  \n Calculations {calc}")
        return calc

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

    # returns a command with tagged parameters including a calculation
    def tagCommandWithCalculation(self, command, calculation):
        if command.letter == 'l':
            return self.lineTemplate(calculation[0],calculation[1])
        elif command.letter == 'm':
            return self.moveTemplate(calculation[0],calculation[1])
        elif command.letter in ['v', 'h']:
            if command.letter == 'h':
                newCommand = self.horzTemplate(calculation[0])
            elif command.letter == 'v':
                newCommand = self.vertTemplate(calculation[0])
            return newCommand
        else: # if the command is not handled
            return command

    def tagSlitSegment(self, command, gap, centerpiece):
        # The close-command doesn't have any parameters that we would need to adjust
        if command.letter == "z":
            return("","")
        elif command.letter == "l" or command.letter == "h" or command.letter == "v" or command.letter == "t" or command.letter == "m":
            args = command.args
        elif command.letter == "s" or command.letter == "q":
            args = (command.args[2], command.args[3])
        elif command.letter == "c":
            args = (command.args[4], command.args[5])
        elif command.letter == "a":
            args = (command.args[5], command.args[6])
        # For lines we have to adjust args 0 and 1
        # for v and h we have to adjust arg 0
        # for c we have to adjust 4 and 5
        # for s it's 2 and 3
        # for q it's 2 and 3
        # for t it's 0 and 1
        # for a it's 5 and 6

        inkex.utils.debug(command)

        # Check whether that segment has already been tagged 
        if  "thickness" in str(command):

            thickness_term_x = args[0]

            # Get the terms of the calculation
            regex = r"(?P<offset>-?\d+(\.\d+)?)(?P<calc>(?P<factor>[-+]?\d+(\.\d+))?(?P<operator>[-+/\*]?)thickness)*"

            if "thickness" in args[0]:

                result_x = re.search(regex, args[0], re.MULTILINE)
                # inkex.utils.debug(result_x.groupdict())

                #The regex also matches when there is 

                # Mathematical notations are a bit tricky, as we need to look at a series of factors
                # The regex only matches if "thickness" is in there, so there is no factor 0
                if result_x.group('factor'):
                    angle_x = float(result_x.group('factor'))
                # If there is no factor, a.k.a. no number, we need to look at the operator to determine wether it is + or -
                else: 
                    angle_x = -1.0 if result_x.group('operator') == "-" else 1.0

                # Now that we have the terms of the calculation, we can adjust that already adjusted segment even further
                # the length is always the original length plus half the gap minus the cos/sin of the gaps angle times thickness
                # in this case we need to take the factors from the tagges calculation and just add the new ones on top

                length_x = float(result_x.group('offset')) + (gap.dx/2) 
                angle_x = truncate(angle_x - (cos(gap.angle)/2), 15)

                if angle_x == 0:
                    thickness_term_x = f"{length_x}"
                elif angle_x == 1:
                    thickness_term_x = f"{{{length_x}+thickness}}"
                elif angle_x == -1:
                    thickness_term_x = f"{{{length_x}-thickness}}"
                else:
                    thickness_term_x = "{{{}{:+}*thickness}}".format(length_x,angle_x)

            if len(args) > 1:
                thickness_term_y = args[1]
                if "thickness" in args[1]:
                    result_y = re.search(regex, args[1], re.MULTILINE)
                    # inkex.utils.debug(result_y.groupdict())

                    if result_y.group('factor'):
                        angle_y = float(result_y.group('factor'))
                    # If there is no factor, a.k.a. no number, we need to look at the operator to determine wether it is + or -
                    else: 
                        if result_y.group('operator') == "-":
                            angle_y = -1.0
                        elif result_y.group('operator') == "+":
                            angle_y = +1.0
                    
                    length_y = float(result_y.group('offset')) + (gap.dy/2)
                    angle_y = truncate(angle_y - (sin(gap.angle)/2), 15)

                    if angle_y == 0:
                        thickness_term_y = f"{length_y}"
                    elif angle_y == 1:
                        thickness_term_y = f"{{{length_y}+thickness}}"
                    elif angle_y == -1:
                        thickness_term_y = f"{{{length_y}-thickness}}"
                    else:
                        thickness_term_y = "{{{}{:+}*thickness}}".format(length_y,angle_y)
            else: 
                thickness_term_y = ""
            calculation = (thickness_term_x, thickness_term_y)
        else:
            angle_x = truncate(-cos(gap.angle)/2, 15)
            angle_y = truncate(-sin(gap.angle)/2, 15)
            length_x = float(args[0])+(gap.dx/2)

            # I know this is ugly, because this means that both h and v use the first parameter in the tuple, which is wrong for v where the first term should be 0
            if len(args) > 1:
                length_y = float(args[1])+(gap.dy/2)
                thickness_term_y = f"{length_y}" if angle_y == 0.0 else f"{{{length_y}+thickness}}" if angle_y == 1.0 else f"{{{length_y}-thickness}}" if angle_y == -1.0 else "{{{}{:+}*thickness}}".format(length_y,angle_y)
            else: 
                thickness_term_y = ""

            thickness_term_x = f"{length_x}" if angle_x == 0.0 else f"{{{length_x}+thickness}}" if angle_x == 1.0 else f"{{{length_x}-thickness}}" if angle_x == -1.0 else "{{{}{:+}*thickness}}".format(length_x,angle_x)
            calculation = (thickness_term_x, thickness_term_y)
            inkex.utils.debug(f"Segment is fresh {calculation} {gap} {gap.angle}")
        return calculation

    # returns a command with tagged parameters
    def tagCommand(self, command, thickness):
        if command.letter == 'l':
            x = command.args[0]
            y = command.args[1]

            # In non-orthogonal cases, there can be a minimal difference due to floating points
            difference = (x*x + y*y) - (thickness*thickness)

            if abs(difference) < 0.1:
                factor_x = truncate(x/thickness, 15)
                factor_y = truncate(y/thickness, 15)
                return self.lineTemplate("0" if factor_x == 0 else "{thickness}" if factor_x == 1 else "{-thickness}" if factor_x == -1 else "{{{}*thickness}}".format(factor_x),
                    "0" if factor_y == 0 else "{thickness}" if factor_y == 1 else "{-thickness}" if factor_y == -1 else "{{{}*thickness}}".format(factor_y))
            else:
                return command
        elif command.letter in ['v', 'h']:
            x = command.args[0]

            if  x * x == thickness * thickness:
                ratio = truncate(x / thickness, 15)
                pattern = ""
                if ratio == 1:
                    pattern = "{thickness}"
                elif ratio == -1:
                    pattern = "{-thickness}"
                else:
                    pattern = "{{{}*thickness}}".format( (x / thickness))
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
    def getCommandLength(self, command) -> float:
        dx,dy = self.getCommandDelta(command)
        return sqrt(dx**2 + dy**2)
        
    def getCommandDelta(self, command):
        if command.letter == 'l':
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

    # Return the endpoint coordinates of an absolute command
    def getCommandEndpoint(self, command, previous):
        if command.letter == "L":
            return (command.args)
        elif command.letter == "H":
            return command.to_line(previous).args
        elif command.letter == "V":
            return command.to_line(previous).args



    def drawDebugLine(self, layer, x1, y1, x2, y2, color):
        layer = self.svg.getElementById(layer)

        line = etree.SubElement(layer, "line")
        line.set("x1", x1 )
        line.set("y1", y1)
        line.set("x2", x2)
        line.set("y2", y2)
        line.set("stroke", color)

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper
    # The length of the command needs to be adjusted by dx and dy
    # def adjustCommandByDelta(self, command, dx, dy):
    #     if command.letter == 'l':

    #     if command.letter == 'h':

    #     if command.letter == 'v':




if __name__ == '__main__':
    LaserSVG().run()
