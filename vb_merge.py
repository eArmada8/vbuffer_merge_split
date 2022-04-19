# Vertex buffer merge script - for use with 3dmigoto frame dumps from games that use separate buffers
# for each vertex element.  Execute from the directory of the indexed frame dump (not de-duped) and it will
# output any buffers it finds into the ./output directory.  Has only been tested with TOCS4.
# GitHub eArmada8/vbuffer_merge_split

import glob, os, re

def retrieve_indices():
    # Make a list of all vertex buffer indices in the current folder
    # NOTE: Will *not* include index buffers without vertex data! (i.e. ib files without corresponding vb files)
    return sorted([re.findall('^\d+', x)[0] for x in glob.glob('*-vb0*txt')])

def copy_ib_file_to_output(fileindex):
    # Copy the index buffer file to the output directory unmodified
    ib_filename = str(glob.glob(fileindex + '-ib*')[0])
    with open(ib_filename, 'r') as f:
        ib_file_data = f.read()
    with open('output/' + ib_filename, 'w') as f:
        f.write(ib_file_data)
    del ib_file_data
    return
    
def merge_vb_file_to_output(fileindex):
    # Take all the vertex buffer files for one index buffer and merge them into a single vertex buffer file
    #First, get a list of all the VB files
    vb_filenames = sorted(glob.glob(fileindex + '-vb*'))

    #Get the strides for each buffer
    strides = []
    for i in range(len(vb_filenames)):
        with open(vb_filenames[i], 'r') as f:
            for line in f:
                if line[0:6] == 'stride':
                    strides.append(int(line[8:-1]))
    
    #Calculate aligned byte offsets
    offsets = []
    for i in range(len(strides)):
        if i == 0:
            offsets.append(0)
        else:
            offsets.append(sum(strides[0:i]))
    
    #Create Header
    output = []
    with open(vb_filenames[0], 'r') as f:
        element = 0
        for line in f: #Evaluate each line, for modification as needed
            if line[0:6] == 'stride': #First line, replace with the merged stride
                output.append('stride: ' + str(sum(strides)) + '\n')
            elif line[0:8] == 'element[': #Set element to the section in which we are working (POSITION, TEXCOORD, etc) by number
                element = int(line[8:-3])
                output.append(str(line))
            elif line[2:12] == 'InputSlot:':
                output.append('  InputSlot: 0\n') #All input slots are changed to 0 since we only have one vb0 at the end
            elif line[2:19] == 'AlignedByteOffset':
                output.append('  AlignedByteOffset: ' + str(offsets[element]) + '\n') #Add the correct offset for each element
            else:
                output.append(str(line)) #all other lines are unchanged
            if line[0:11] == 'vertex-data':
                break
    output.append('\n')
    
    #Grab vertex data, file by file, into two dimensional list
    vertex_data = []
    for i in range(len(vb_filenames)):
        vertex_file_data = []
        with open(vb_filenames[i], 'r') as f:
            for line in f: 
                if line[0:3] == 'vb' + str(i):
                    raw_line = str(line)
                    vertex_file_data.append(raw_line.replace('vb' + str(i), 'vb0').replace(']+000', ']+' + str(offsets[i]).zfill(3)))
            vertex_data.append(vertex_file_data)
    
    #Build vertex list in format expected by Blender plugin
    for i in range(len(vertex_data[0])):
        for j in range(len(vertex_data)):
            try:
                output.append(vertex_data[j][i])
            except IndexError:
                pass
            continue
        #Blender plugin expects a blank line after every vertex group
        output.append('\n')
    
    with open('output/' + vb_filenames[0], 'w') as f:
        f.write("".join(output))
    return

# End of functions, begin main script

if __name__ == "__main__":
    # Set current directory
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    # Let's make an output directory, because otherwise we would have to delete / overwrite files
    if not os.path.exists('output'): 
        os.mkdir('output')

    indices = retrieve_indices()
    for i in range(len(indices)):
        #print('Processing index ' + indices[i] + '...\n')
        copy_ib_file_to_output(indices[i])
        #print('  Copying IB file ' + indices[i] + '...\n')
        merge_vb_file_to_output(indices[i])
        #print('  Processing VB file ' + indices[i] + '...\n')
