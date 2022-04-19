# Vertex buffer split script - for use with Blender exports to 3dmigoto raw buffers (ib/vb/fmt files),
# this script will split the combined vertex buffer into individual buffers for games that use separate
# buffers for each vertex element.  Execute from the directory of the buffers and it will split any vb
# files it finds that has a corresponding fmt file.  It will also create a rudimentary ini file for use
# with 3dmigoto.  Has only been tested with TOCS4.
# GitHub eArmada8/vbuffer_merge_split

import glob, os, re

# R16_UINT is used for TOCS4, this string is pasted verbatim into the beginnings of the ini file
ib_format = 'R16_UINT'

def retrieve_meshes():
    # Make a list of all mesh groups in the current folder, both fmt and vb files are necessary for processing
    fmts = [x[:-4] for x in glob.glob('*fmt')]
    vbs = [x[:-3] for x in glob.glob('*vb')]
    return [value for value in fmts if value in vbs]

def split_vb_file_and_make_ini_file(meshname):
    #Take the raw combined buffer and split into individual raw buffers
    
    #Determine the offsets used in the combined buffer by parsing the FMT file
    offsets = []
    with open(meshname + '.fmt', 'r') as f:
    	for line in f:
    		if line[0:6] == 'stride':
    			combined_stride = int(line[8:-1])
    		if line[2:19] == 'AlignedByteOffset':
    			offsets.append(int(line[21:-1]))

    #Determine the strides to be used in the individual buffers
    strides = []
    for i in range(len(offsets)):
    	if i == len(offsets) - 1:
    		strides.append(combined_stride - offsets[i])
    	else:
    		strides.append(offsets[i+1] - offsets[i])
    
    #Read in the entire combined buffer
    with open(meshname + '.vb', 'rb') as f:
    	vb_read_buffer = f.read()
    
    #Count the total number of vertices
    vertex_count = int(len(vb_read_buffer)/combined_stride)
    
    #Write each individual vertex buffer file, one for each element
    for vertex_group in range(len(strides)):
    	write_data = b''
    	for i in range(vertex_count):
    		start_index = i * combined_stride + offsets[vertex_group]
    		write_data = write_data + vb_read_buffer[start_index:start_index+strides[vertex_group]]
    	with open(meshname + '.vb' + str(vertex_group), 'wb') as f:
    		f.write(write_data)
    
    #Create the beginnings of an ini file
    ini_text = []
    #ini file - VB Resources
    for vertex_group in range(len(strides)):
    	ini_text.append('[Resource_Model_' + meshname + '_VB' + str(vertex_group) + ']\n')
    	ini_text.append('type = Buffer\n')
    	ini_text.append('stride = ' + str(strides[vertex_group]) + '\n')
    	ini_text.append('filename = ' + meshname + '.vb' +str(vertex_group) + '\n')
    	ini_text.append('\n')
    
    #ini file - IB Resource
    ini_text.append('[Resource_Model_' + meshname + '_IB]\n')
    ini_text.append('type = Buffer\n')
    ini_text.append('format = ' + ib_format + '\n')
    ini_text.append('filename = ' + meshname + '.ib\n')
    ini_text.append('\n')
    
    #ini file - Texture Override
    ini_text.append(';[TextureOverride_' + meshname + ']\n')
    ini_text.append('; *** Hash needs to be filled in below\n')
    ini_text.append(';hash = _________\n')
    for vertex_group in range(len(strides)):
    	ini_text.append(';vb' + str(vertex_group) + ' = Resource_Model_' + meshname + '_VB' +str(vertex_group) + '\n')
    ini_text.append(';ib = Resource_Model_' + meshname + '_IB\n')
    ini_text.append(';handling = skip\n')
    ini_text.append(';drawindexed = auto\n')
    ini_text.append('\n')
    
    #ini file - Shader Override
    ini_text.append(';[ShaderOverride_' + meshname + ']\n')
    ini_text.append('; *** Hash needs to be filled in below.\n')
    ini_text.append('; *** Duplicate this section as needed if the texture is called by more than one pixel shader.\n')
    ini_text.append('; ***     (If duplicating, keep in mind each section needs its own unique name.)\n')
    ini_text.append(';hash = _________\n')
    ini_text.append('; *** Uncomment the lines below or insert run statement, depending on your 3dmigoto setup\n')
    for vertex_group in range(len(strides)):
    	ini_text.append(';checktextureoverride = vb' +str(vertex_group) + '\n')
    ini_text.append(';allow_duplicate_hash=true\n')
    
    #Write ini file
    with open(meshname + '.ini', 'w') as f:
    	f.write("".join(ini_text))
        
    return

# End of functions, begin main script

if __name__ == "__main__":
    # Set current directory
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    meshes = retrieve_meshes()
    for i in range(len(meshes)):
        #print('Processing mesh ' + meshes[i] + '...\n')
        split_vb_file_and_make_ini_file(meshes[i])
