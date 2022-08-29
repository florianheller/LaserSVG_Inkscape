# LaserSVG Inkscape Plugins
Inkscape Extensions to Create and Edit LaserSVG-Files 

## Installation
Just download the contents of this repository as zip file, extract it, and copy the folder to your Inkscape extensions folder. You can find the location in the System panel of the Inkscape Settings. After copying the files, you need to restart Inkscape. 


## Using the plugin
After installing the plugin, you can find the following entries in the LaserSVG folder of the Inkscapes Plugin menu.

### Parameter Control
In this panel you can set the material thickness for the plugin to work on. Initially, set this to the thickness the design was made for. After tagging, changing the value also changes updates the drawing.


### Path editor
In this panel you can edit the settings for paths. 

### Primitive editor
This panel offers the settings for geometric primitives such as rectangles, circles, etc...

### Joints
Allows you to set the joint type a certain path segment should be replaced with. Allows end-users to customize the type of joint, e.g., a box is made with. 

# Debugging Plugins
While developing the LaserSVG extensions, I wrote some useful extensions that are not directly related to LaserSVG.

## To Relative
Converts the description of a path into relative commands. This is sometimes easier to read, if you want to know the length of some segments. 

## Clean
Removes all segments whose length is below a certain threshold (basically 0). Sometimes, anchor points hide below each other, which is hard to spot when editing the drawing, but makes automatic parametrization quite hard. 



# Acknowledgements
This project is part of my work at the Expertise Centre for Digital Media (EDM) at Hasselt University (UHasselt).