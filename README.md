# DJI_M2EA_process
This simple code allows to run a GUI for DJI Mavic 2 Entreprise Advanced (DJI M2EA) image processing.

## DJI M2EA limitations
As many DJI M2EA users now, the image options available on the controller are limited. In particular, there is no option to change the temperature range. The drone auto-adapts the temperature measurement range, which is quite annoying for photogrammetry applications.
Luckily, DJI provides a Thermal SDK, which is used here.

## App functionalities
First step: choosing a folder where DJI thermal files are stored (each file should be something like DJI_XXXX_T.JPG). Then choosing the constant temperature range (one of the image can be used to fetch minimum and maximum temperatures). Finally the colormap options (color scheme and 'above/below' temperatures colors).
