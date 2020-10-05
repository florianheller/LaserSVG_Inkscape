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
import re
from lxml import etree
from math import sqrt, atan2, pi, sin, cos, trunc, degrees, copysign

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
        pars.add_argument("--assume_parallel", default=False, help="Assume segment and slit base to be parallel.")
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        etree.register_namespace("laser", self.LASER_NAMESPACE)
        inkex.utils.NSS["laser"] = self.LASER_NAMESPACE

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
                        # inkex.utils.debug( '{0} - selected nodes of subpath {1}: {2}'.format(pathID, element, selected[element]))
                        # show the coordinates
                        for nodes in selected[element]:
                            coordinates = path.original_path.to_superpath()[element][nodes][1]
                            # inkex.utils.debug('{0} - selected node {1}: {2}'.format(pathID, nodes, coordinates))
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

    # These are subclasses that can handle non-numeric elements (e.g., {thickness}) in their arguments
    # For that, we create a template class with an appropriate toString method, and then just subclass both
    # to achieve the wanted behavior
    class template(object):
        def __str__(self):
            return self.letter + " " + ", ".join(map(str, self.args))
    class horzTemplate(template, inkex.paths.horz):
        pass
    class vertTemplate(template, inkex.paths.vert):
        pass
    class lineTemplate(template, inkex.paths.line):
        pass
    class moveTemplate(template, inkex.paths.move):
        pass
    class curveTemplate(template, inkex.paths.curve):
        pass

    # This method goes through all segments of a path and replaces those that are of length _length_ with a {thickness} label
    def tagSegments(self, path, length):

        template = inkex.paths.Path()
        for command in path.original_path.to_relative():
            # if the length matches, we replace the args with the according tags
           template.append(self.tagCommand(command, length))
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
        # Create an additional layer for the highlights or just 
        if self.document.getroot().find(f".//svg:g[@id='{layername}']", namespaces=inkex.utils.NSS) is not None:
            layer = self.svg.getElementById(layername)
        else:
            layer = self.svg.add(inkex.Group.new(readable_layername, is_layer=True))
            layer.set("id", layername)
           
        # Store away the absolute endpoints of the commands to be able to draw the highlights
        csp_abs = path.original_path.to_absolute().to_superpath()
        endpoints = [path.original_path.to_absolute()[0].args]
        for x in csp_abs.to_segments():
            if x.letter == 'L':
                endpoints.append((x.args[0], x.args[1]))
            elif x.letter == 'C':
                endpoints.append((x.args[4],x.args[5]))

        # Check for every path segment that is of size length
        for index,command in enumerate(path.original_path.to_relative()): #Easier in relative mode
            commandLength = self.getCommandLength(command)
            if commandLength is not None:
                if abs(commandLength-length) < 0.1:
                    if index < 2:
                        inkex.utils.debug(f"Warning: {command} it the {index} segment of the path {path}, which could be problematic.")
                # Now get the coordinates to draw a line from the absolute mode path
                    line = etree.SubElement(layer, "line")
                    if index > 1:
                        line.set("x1", endpoints[index][0])
                        line.set("y1", endpoints[index][1])
                        line.set("x2", endpoints[index-1][0])
                        line.set("y2", endpoints[index-1][1])
                    else:
                        #This is the first segment after the move command. 
                        line.set("x1", endpoints[index-1][0])
                        line.set("y1", endpoints[index-1][1])
                        line.set("x2", endpoints[index-1][0] + self.getCommandDelta(command)[0])
                        line.set("y2", endpoints[index-1][1] + self.getCommandDelta(command)[1])
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

    # The tagging of a slit is a bit more complicated as we need to adapt the two segments to the left and right respectively.
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
        # for segment in csp_abs.to_segments():
        #     inkex.utils.debug(segment)
            # for point in csp.control_points:
            #     inkex.utils.debug("{} {}".format(segment, point))
        # Store away the original control points in absolute values, we need these to draw the selection lines
        cps = []
        for cp in path.original_path.proxy_iterator():
            cps.append(cp.previous_end_point)

        for index,command in enumerate(path.original_path.to_relative()):
            if index in segments:
                # if index > 1:
                    # i = command.control_points(csp[index], csp[index-1], csp[index-2])
                    # inkex.utils.debug(cps[index])
                ll, l, center, r, rr, gap = None, None, None, None, None, None
                if index >=2 and template[index-2].letter != 'm': #It doesn't make sense to consider the initial move command
                    ll = inkex.transforms.DirectedLineSegment(cps[index-2],cps[index-1])
                if index >=1:
                    l = inkex.transforms.DirectedLineSegment(cps[index-1],cps[index])
                if index < len(cps)-1:
                    center = inkex.transforms.DirectedLineSegment(cps[index], cps[index+1])
                if index < len(cps)-2:
                    r = inkex.transforms.DirectedLineSegment(cps[index+1], cps[index+2])
                if index < len(cps)-3:
                    rr = inkex.transforms.DirectedLineSegment(cps[index+2],cps[index+3])                

                if index > 0 and index < len(cps)-2:
                    gap = inkex.transforms.DirectedLineSegment(cps[index-1],cps[index+2])

                # self.drawDebugLine("layer1", gap.x0, gap.y0, gap.x1, gap.y1, "green")

                #inkex.utils.debug("{} {} {}".format(ll.angle, ll.intersect(rr), rr.angle))

                # Set the length of the slit base
                template[index] = self.tagCommand(command, thickness)

                # The segment to the left and right of the base need to be adjusted. 
                # For that, we take the centerpoint of the slit base, and calculate how much change in x and y
                # this generates if we draw a vector of half the thickness from there with the same angle as the current base
                base_dx, base_dy = self.getCommandDelta(command)
                base_origin_x, base_origin_y = csp_abs[0][index-1][0][0], csp_abs[0][index-1][0][1]
                base_center= (base_origin_x+(base_dx/2), base_origin_y+(base_dy/2))

                # self.drawDebugLine("layer1" , centerpoint[0], centerpoint[1], centerpoint[0]+((5/2)*cos(c.angle)), centerpoint[1]+((5/2)*sin(c.angle)), "red")

                if ll is not None:
                    if (template[index-2].letter) == 'c':
                        # Calculate a point at the end of the curve
                        curveCommand = list(csp_abs.to_segments())[index-2]
                        (tx,ty) = self.bezierTangentXY((1, 1), cps[index-2], (curveCommand.x2, curveCommand.y2), (curveCommand.x3, curveCommand.y3), (curveCommand.x3, curveCommand.y3))
                        ll_angle = atan2(tx, tx)
                    else: 
                        ll_angle = ll.angle


                if rr is not None:
                    if (template[index+2].letter) == 'c':
                        # Calculate a point at the beginning of the curve
                        curveCommand = list(csp_abs.to_segments())[index+2]
                        (tx,ty) = self.bezierTangentXY((0, 0), cps[index+2], (curveCommand.x2, curveCommand.y2), (curveCommand.x3, curveCommand.y3), (curveCommand.x3, curveCommand.y3))
                        rr_angle = atan2(tx, tx)
                    else: 
                        rr_angle = rr.angle


                # If the segment leading to or from the slit is parallel to the slit base, we do not need to adjust the length of the slit walls
                if (ll != None and gap != None and (abs(ll_angle - center.angle)) > 0.0001) or self.options.assume_parallel == "false":
                    template[index-1] = self.tagCommandWithCalculation(template[index-1],self.shortenSlitLeg(template[index-1], gap, center, thickness, l))
                if (rr != None and (abs(rr.angle - center.angle)) > 0.0001) or self.options.assume_parallel == "false":
                    template[index+1] = self.tagCommandWithCalculation(template[index+1],self.shortenSlitLeg(template[index+1], gap, center, thickness, r))

                

                if index >=2 and gap is not None:
                    template[index-2] = self.tagCommandWithCalculation(template[index-2], self.tagSlitSegment(template[index-2],gap, center, thickness))
                if index < len(cps)-2 and gap is not None:
                    template[index+2] = self.tagCommandWithCalculation(template[index+2], self.tagSlitSegment(template[index+2],gap, center, thickness))
                # self.drawDebugLine("layer1", gap_center[0], gap_center[1], gap_center[0]+((5/2)*cos(gap.angle)),gap_center[1]+((5/2)*sin(c.angle)), "limegreen")
                

                # The new endpoint for the ll segment is thus gap_center.x-{thickness*cos(gap.angle),gap_center.y-{thickness*sin(gap.angle)}}
                path.set(inkex.addNS("template", self.LASER_PREFIX),template)

                # template[index-1] = self.tagCommandWithCalculation(command, )
                # inkex.utils.debug(template[index].end_point)

                # x = command.previous_end_point
                # inkex.utils.debug("{}".format(x))
                #segments-2 and +2 need to be shortened by 0.5*thickness to keep the slit centered
                #segments-1 and +1 need to be adjusted such that they match

    def shortenSlitLeg(self, leg, gap, centerpiece, thickness, leg_line):
        # We assume that the base and it's adjacent walls are orthogonal to each-other (90°)
        # This allows us to use the sinus-calulations in a triangle, as the sum of all inner angles in a triangle is 180, 
        # and one is fixed to 90, the last angle (opposite of alpha) is then 90-alpha

        # First we need to transform gap.angle into an inner angle if it is not already the case
        c_angle = pi + centerpiece.angle if centerpiece.angle < -pi/2 else pi - centerpiece.angle if centerpiece.angle > pi/2 else centerpiece.angle
        g_angle = pi + gap.angle if gap.angle < -pi/2 else pi - gap.angle if gap.angle > pi/2 else gap.angle

        alpha = abs(c_angle - g_angle)

        beta = pi/2-alpha
        beta = beta-pi if beta > pi/2 else beta+pi if beta < -pi/2 else beta

        # a/sin(alpha) = b/sin(beta) = c/sin(gamma)
        # b is thickness, and gamma is π/2 
        # c = thickness/sin(beta)
        a = thickness*sin(alpha)/sin(beta)

        # In the case of a triangle with beta = pi/2, the x and y components of c/2 are actually the same as for a/2 and b/2

        # Projection of a (calculated in a right triangle) into the global coordinate system
        delta_x = truncate((0.5 * sin(alpha) / sin(beta)) * cos(leg_line.angle), 5) 
        delta_y = truncate((0.5 * sin(alpha)  / sin(beta)) * sin(leg_line.angle), 5)

        start_x = truncate(leg_line.dx + (delta_x * thickness) * copysign(1, -(leg_line.angle*gap.angle)) , 5)
        start_y = truncate(leg_line.dy + (delta_y * thickness) * copysign(1, -(leg_line.angle*gap.angle)) , 5)

        if delta_x == 0:
            # If delta is 0, shouldn't that only be leg_line_x? Alpha would be 0 a.k.a. base and gap are parallel. 
            # meaning that there is no change in length depending on thickness.
            calc_x = start_x 
        else:
            calc_x = "{{{}{:+}*thickness}}".format(start_x, copysign(delta_x, -cos(gap.angle)))

        if delta_y == 0:
            calc_y = start_y 
        else:
            calc_y = "{{{}{:+}*thickness}}".format(start_y, copysign(delta_y, gap.angle))

        return (calc_x, calc_y)

    def tagSegmentsInPath(self, path, segments):
        template = path.copy().original_path.to_relative()
        for index,command in enumerate(path.original_path.to_relative()):
            if index in segments:
                template[index] = self.tagCommand(command, float(self.document.getroot().get("{}material-thickness".format(self.LASER))))

        path.set(inkex.addNS("template", self.LASER_PREFIX),template)

    # returns a command with tagged parameters including a calculation
    def tagCommandWithCalculation(self, command, calculation):
        if command.letter == 'l':
            return self.lineTemplate(calculation[0],calculation[1])
        elif command.letter == 'm':
            return self.moveTemplate(calculation[0],calculation[1])
        elif command.letter in ['v', 'h']:
            if command.letter == 'h':
                newCommand = self.horzTemplate(calculation[0]) if calculation[1] == "0" else self.lineTemplate(calculation[0],calculation[1])
            elif command.letter == 'v':
                newCommand = self.vertTemplate(calculation[1]) if calculation[0] == "0" else self.lineTemplate(calculation[0],calculation[1])
            return newCommand
        elif command.letter == 'c':
            return self.curveTemplate(command.args[0], command.args[1], command.args[2], command.args[3], calculation[0], calculation[1])
        else: # if the command is not handled
            return command

    def tagSlitSegment(self, command, gap, centerpiece, thickness):
        # The close-command doesn't have any parameters that we would need to adjust
        if command.letter == "z":
            return("","")
        elif command.letter == "l" or command.letter == "t" or command.letter == "m":
            args = command.args
        elif command.letter == "h":
            args = (command.args[0], 0)
        elif command.letter == "v":
            args = (0, command.args[0])
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

        # if the slit base and ll and rr are parallel, we don't need to do all the calculations
        if abs(centerpiece.angle - gap.angle) < 0.01:
            # inkex.utils.debug(f"Base {centerpiece.angle} and gap {gap.angle} are parallel ")
            angle_a = sin(gap.angle)

        else: 
            # First we need to transform gap.angle into an inner angle if it is not already the case
            # For that, we also need to consider the centerpiece angle, as alpha is their difference

            # alpha, beta, gamma are the inner angles of the triangle formed by the gap and a line closing the gap parallel to the slit base
            # we assume that slit base and walls are perpendicular, meaning that gamma = 90°



            c_angle = pi + centerpiece.angle if centerpiece.angle < -pi/2 else pi - centerpiece.angle if centerpiece.angle > pi/2 else centerpiece.angle
            g_angle = pi + gap.angle if gap.angle < -pi/2 else pi - gap.angle if gap.angle > pi/2 else gap.angle

            alpha = abs(c_angle - g_angle)

            #alpha = pi+gap.angle if gap.angle < -pi/2 else gap.angle - pi if gap.angle > pi/2 else gap.angle
            # test_alpha = pi+rtest if rtest < -pi/2 else pi - rtest if rtest > pi/2 else rtest
            beta = pi/2-alpha
            beta = beta-pi if beta > pi/2 else beta+pi if beta < -pi/2 else beta

            # inkex.utils.debug(f"The triangle: Alpha: {degrees(alpha)}  Beta: {degrees(beta)}, gap.angle {degrees(gap.angle)} base angle {degrees(centerpiece.angle)}")

            # a/sin(alpha) = b/sin(beta) = c/sin(gamma)
            # b is thickness, and gamma is π/2 
            c = thickness/sin(beta)
            a = thickness*sin(alpha)/sin(beta) 

            angle_a = sin(alpha)/sin(beta)
            angle_c = 1/sin(beta)

            angle_factor_x = 0.5 * cos(gap.angle)/sin(beta)
            angle_factor_y = 0.5 * sin(gap.angle)/sin(beta)

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

                length_x = float(result_x.group('offset')) + copysign(gap.dx/2, float(result_x.group('offset')))
                # inkex.utils.debug(f"Length_X debug offset:{float(result_x.group('offset'))} delta: {truncate(copysign(cos(centerpiece.angle)/2, float(result_x.group('offset'))),5)}")
                angle_x = angle_x + copysign(angle_factor_x, -float(result_x.group('offset')))

                if angle_x == 0:
                    thickness_term_x = f"{length_x}"
                elif angle_x == 1:
                    thickness_term_x = f"{{{length_x}+thickness}}"
                elif angle_x == -1:
                    thickness_term_x = f"{{{length_x}-thickness}}"
                else:
                    thickness_term_x = "{{{}{:+}*thickness}}".format(truncate(length_x, 5),truncate(angle_x, 5))

            if len(args) > 1:
                thickness_term_y = args[1]
                if "thickness" in args[1]:
                    result_y = re.search(regex, args[1], re.MULTILINE)

                    if result_y.group('factor'):
                        angle_y = float(result_y.group('factor'))
                    # If there is no factor, a.k.a. no number, we need to look at the operator to determine wether it is + or -
                    else: 
                        if result_y.group('operator') == "-":
                            angle_y = -1.0
                        elif result_y.group('operator') == "+":
                            angle_y = +1.0
                    
                    length_y = float(result_y.group('offset')) + copysign(gap.dy/2, float(result_y.group('offset')))
                    angle_y = angle_y + copysign(angle_factor_y, -gap.angle)

                    if angle_y == 0:
                        thickness_term_y = f"{length_y}"
                    elif angle_y == 1:
                        thickness_term_y = f"{{{length_y}+thickness}}"
                    elif angle_y == -1:
                        thickness_term_y = f"{{{length_y}-thickness}}"
                    else:
                        thickness_term_y = "{{{}{:+}*thickness}}".format(truncate(length_y, 5),truncate(angle_y, 5))
            else: 
                thickness_term_y = ""
            calculation = (thickness_term_x, thickness_term_y)
        else:
            # inkex.utils.debug(centerpiece)

            # Change in Y-direction is cos(centerpiece.angle)* {thickness} *sin(alpha)/sin(beta) 

            angle_x = copysign(angle_factor_x, -float(args[0]))
            angle_y = copysign(angle_factor_y, -gap.angle)

            length_x = copysign(float(args[0]) + gap.dx/2, float(args[0]))
            # inkex.utils.debug(f"Length calc {args[0]} {gap.dx/2} centerpiece angle {centerpiece.angle} gap angle {gap.angle} angle x {angle_x}")

            if len(args) > 1:
                length_y = copysign(float(args[1])+gap.dy/2, float(args[1]))
                thickness_term_y = f"{length_y}" if angle_y == 0.0 else f"{{{length_y}+thickness}}" if angle_y == 1.0 else f"{{{length_y}-thickness}}" if angle_y == -1.0 else "{{{}{:+}*thickness}}".format(truncate(length_y, 5),truncate(angle_y, 5))
            else: 
                thickness_term_y = ""

            thickness_term_x = f"{length_x}" if angle_x == 0.0 else f"{{{length_x}+thickness}}" if angle_x == 1.0 else f"{{{length_x}-thickness}}" if angle_x == -1.0 else "{{{}{:+}*thickness}}".format(truncate(length_x, 5),truncate(angle_x, 5))
            calculation = (thickness_term_x, thickness_term_y)
            # inkex.utils.debug(f"Segment is fresh {calculation}")
        return calculation

    # returns a command with tagged parameters
    def tagCommand(self, command, thickness):
        threshold = 0.1
        if command.letter == 'l':
            x = command.args[0]
            y = command.args[1]

            # In non-orthogonal cases, there can be a minimal difference due to floating points
            if abs((x*x + y*y) - (thickness*thickness)) < threshold:
                factor_x = truncate(x/thickness, 5)
                factor_y = truncate(y/thickness, 5)
                return self.lineTemplate("0" if factor_x == 0 else "{thickness}" if factor_x == 1 else "{-thickness}" if factor_x == -1 else "{{{}*thickness}}".format(factor_x),
                    "0" if factor_y == 0 else "{thickness}" if factor_y == 1 else "{-thickness}" if factor_y == -1 else "{{{}*thickness}}".format(factor_y))
            else:
                return command
        elif command.letter in ['v', 'h']:
            x = command.args[0]

            if  abs(x*x - thickness*thickness) < threshold:
                ratio = truncate(x / thickness, 3)
                pattern = ""
                if ratio == 1:
                    pattern = "{thickness}"
                elif ratio == -1:
                    pattern = "{-thickness}"
                else:
                    pattern = f"{{{ratio}*thickness}}"
                if command.letter == 'h':
                    newCommand = self.horzTemplate(pattern)
                elif command.letter == 'v':
                    newCommand = self.vertTemplate(pattern)

                return newCommand
            else: #if the length does not match
                return command
        elif command.letter == 'c':
            length = self.getCommandLength(command) 
            if  length is not None and abs(length-thickness) < threshold:
                ratio_x = command.args[4] / thickness
                term_x = "0" if ratio_x == 0 else "{thickness}" if ratio_x == 1 else "{-thickness}" if ratio_x == -1 else f"{{{ratio_x}*thickness}}"
                ratio_y = command.args[5] / thickness
                term_y = "0" if ratio_y == 0 else "{thickness}" if ratio_y == 1 else "{-thickness}" if ratio_y == -1 else f"{{{ratio_y}*thickness}}"
                newCommand = self.curveTemplate(command.args[0], command.args[1], command.args[2], command.args[3], term_x, term_y)
            else:
                return command

        else: # if the command is not handled
            return command

    # Get the length of a relative command segment
    # such that we don't have to handle all the different parameter locations
    def getCommandLength(self, command) -> float:
        dx,dy = self.getCommandDelta(command)
        if dx is not None and dy is not None:
            return sqrt(dx**2 + dy**2)
        else:    
            return None
        
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
            return (None, None)

    # based on MBBezierView.m    original BY MICHAL stackoverflow #4058979
    def bezierInterpolation(self, t, a, b, c, d):
        t2 = t * t
        t3 = t2 * t
        return a + (-a * 3 + t * (3 * a - a * t)) * t  + (3 * b + t * (-6 * b + b * 3 * t)) * t + (c * 3 - c * 3 * t) * t2 + d * t3

    # Same function but works on (x,y) coordinate pairs
    def bezierInterpolationXY(self, t, a, b, c, d):
        t2 = (t[0]*t[0], t[1] * t[1])
        t3 = ([t2[0] * t[0], t2[1] * t[1]])

        return (a[0] + (-a[0] * 3 + t[0] * (3 * a[0] - a[0] * t[0])) * t[0]  + (3 * b[0] + t[0] * (-6 * b[0] + b[0] * 3 * t[0])) * t[0] + (c[0] * 3 - c[0] * 3 * t[0]) * t2[0] + d * t3[0],
            a[1] + (-a[1] * 3 + t[1] * (3 * a[1] - a[1] * t[1])) * t[1]  + (3 * b[1] + t[1] * (-6 * b[1] + b[1] * 3 * t[1])) * t[1] + (c[1] * 3 - c[1] * 3 * t[1]) * t2[1] + d[1] * t3[1])


    def bezierTangent(self, t, a, b, c, d):
 
        # note that abcd are aka x0 x1 x2 x3

        # the four coefficients ..
        # A = x3 - 3 * x2 + 3 * x1 - x0
        # B = 3 * x2 - 6 * x1 + 3 * x0
        # C = 3 * x1 - 3 * x0
        # D = x0

        # and then...
        # Vx = 3At2 + 2Bt + C         

        # first calcuate what are usually know as the coeffients,
        # they are trivial based on the four control points:

        C1 = ( d - (3.0 * c) + (3.0 * b) - a )
        C2 = ( (3.0 * c) - (6.0 * b) + (3.0 * a) )
        C3 = ( (3.0 * b) - (3.0 * a) )
        C4 = ( a )  # (not needed for this calculation)

    

        # finally it is easy to calculate the slope element,
        # using those coefficients:

        return ( ( 3.0 * C1 * t* t ) + ( 2.0 * C2 * t ) + C3 )

        # note that this routine works for both the x and y side;
        # simply run this routine twice, once for x once for y
        # note that there are sometimes said to be 8 (not 4) coefficients,
        # these are simply the four for x and four for y,
        # calculated as above in each case.
 
    def bezierTangentXY(self, t, a, b, c, d):
        C1 = (( d[0] - (3.0 * c[0]) + (3.0 * b[0]) - a[0] ), ( d[1] - (3.0 * c[1]) + (3.0 * b[1]) - a[1] ))
        C2 = ( (3.0 * c[0]) - (6.0 * b[0]) + (3.0 * a[0]) , (3.0 * c[1]) - (6.0 * b[1]) + (3.0 * a[1]) )
        C3 = ( (3.0 * b[0]) - (3.0 * a[0]) , (3.0 * b[1]) - (3.0 * a[1]) )
        C4 = ( a[0] , a[1]);

        return (( ( 3.0 * C1[0] * t[0]* t[0] ) + ( 2.0 * C2[0] * t[0] ) + C3[0] ), ( ( 3.0 * C1[1] * t[1]* t[1] ) + ( 2.0 * C2[1] * t[1] ) + C3[1] ));


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
    return trunc(stepper * number) / stepper



if __name__ == '__main__':
    LaserSVG().run()
