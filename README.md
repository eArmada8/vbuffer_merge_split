# vbuffer_merge_split
Small python scripts to merge and split raw vertex buffers used by DarkStarSword's 3dmigoto plugin for Blender

README (vbuffer_merge_split) - GitHub eArmada8/vbuffer_merge_split

A small pair of python scripts to accompany DarkStarSword's 3dmigoto plugin for Blender.  With games that use individual vertex buffers for every element rather than a combined layout, the plugin gives the fatal error "Only draw calls using a single vertex buffer and a single index buffer are supported for now."  These scripts get around this restriction.

The plugin: https://github.com/DarkStarSword/3d-fixes/blob/master/blender_3dmigoto.py (tested on commit eb3eabc)

Disclaimer: I have only used this script on Trails of Cold Steel IV.  I do not know if it will work for any other game.  Please modify as you see fit.

vb_merge.py:  Run in the directory of the frame dump (txt format), and it will attempt to merge every .vb* group it finds.  Outputs into ./output as otherwise it would have to overwrite the .vb0 file.  (This script can take a while to run if you run it on a raw dump, as ToCS4 can dump several hundred files in a scene.  You may want to run this on just the buffers of interest.)

vb_split.py:  Run in the directory of the .ib/.vb/.fmt files that Blender spits out using the 3dmigoto plugin.  It will split the .vb file into individual buffers (.vb0, .vb1, .vb2, etc) using the structure laid out in the .fmt file.  It will also generate a rudimentary .ini file for 3dmigoto, filling in the filenames and strides - 3dmigoto will not process the .ini file however until all the relevant overrides are uncommented.  This is necessary because the script cannot automatically determine the hashes for the texture and pixel shader that you need to override.*

(*Generally you can find the hashes from the INPUT .ib file you processed with the merge script.  If the filename of the .ib file is '000123-ib=4121437a-vs=a4cbed5960571258-ps=8c1693fc42196c3d.txt' for example, the texture hash is 4121437a and the pixel shader hash is 8c1693fc42196c3d.  BUT you may need to go hunting for hashes within the game if these hashes don't work as expected.  I found in ToCs4 that occasionally more than one pixel shader used a texture, so the .ini file needed extra shader override sections.)

Enjoy!  I am not a programmer and this script admittedly has very little error checking.  I'm mainly sharing this in the hope that better programmers than I can improve / debug this script.  Having said that, it has worked for me so far.  I have tested it on several ToCS4 dumps, using the plug-in above and Blender 2.83 LTS.
