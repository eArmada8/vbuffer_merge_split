# Vertex buffer merge script - for use with 3dmigoto frame dumps from games that use separate buffers
# for each vertex element.  Execute from the directory of the indexed frame dump (not de-duped) and it will
# output any buffers it finds into the ./output directory.  Specifically for Kuro no Kiseki meshes with
# 7 vertex buffers.
# GitHub eArmada8/vbuffer_merge_split

import glob, os, re, shutil

def retrieve_indices():
    # Make a list of all vertex buffer indices in the current folder (only include 8-part vertex buffers)
    # NOTE: Will *not* include index buffers without vertex data! (i.e. ib files without corresponding vb files)
    list = sorted([re.findall('^\d+', x)[0] for x in glob.glob('*-vb7*txt')])
    list_to_exclude = [re.findall('^\d+', x)[0] for x in glob.glob('*-vb8*txt')]
    return [x for x in list if x not in list_to_exclude]

def copy_ib_file_to_output(fileindex):
    # Copy the index buffer file to the output directory unmodified, if it exists
    ib_filename = str(glob.glob(fileindex + '-ib*txt')[0])
    if os.path.exists(ib_filename):
        shutil.copy2(ib_filename, 'output/' + ib_filename)
    return
    
def merge_vb_file_to_output(fileindex):
    # Take all the vertex buffer files for one index buffer and merge them into a single vertex buffer file
    # First, get a list of all the VB files
    vb_filenames = sorted(glob.glob(fileindex + '-vb*txt'))

    #Get the strides for each buffer
    strides = []
    for i in range(len(vb_filenames)):
        with open(vb_filenames[i], 'rb') as f:
            vb_data = f.read()
        strides.append(int(vb_data[vb_data.find(b'stride:')+8:vb_data.find(b'\x0d\x0a')]))

    #Calculate aligned byte offsets
    offsets = []
    for i in range(len(strides)):
        if i == 0:
            offsets.append(0)
        else:
            offsets.append(sum(strides[0:i]))

    #Create Header
    semantics = [b'POSITION', b'NORMAL', b'TANGENT', b'TEXCOORD', b'TEXCOORD', b'TEXCOORD', b'BLENDWEIGHTS', b'BLENDINDICES']
    output = []
    with open(vb_filenames[0], 'rb') as f:
        vb_data = f.read()
        end_of_header = vb_data.find(b'\x0d\x0avb', 0)+2
        header = bytearray(vb_data[0:end_of_header])
        header[header.find(b'stride:')+8:header.find(b'\x0d\x0a')] = str(sum(strides)).encode() #First line, replace with the merged stride

    #Replace Semantic name, input slot and aligned byte offset for each element
    current_offset = header.find(b'element[')
    while current_offset > 0:
        current_element = int(header[current_offset+8:current_offset+9])
        start_of_name = header.find(b'SemanticName',current_offset)+14 #Will set element to the section in which we are working (POSITION, TEXCOORD, etc) by number as all ripped names are garbage
        end_of_name = header.find(b'\x0d\x0a', start_of_name)
        start_of_inputslot = header.find(b'InputSlot',current_offset)+11 #Will change all input slots to 0 since we only have one vb0 at the end
        end_of_inputslot = header.find(b'\x0d\x0a', start_of_inputslot)
        start_of_alignedbyteoffset = header.find(b'AlignedByteOffset',current_offset)+19 #Will need to add the correct offset for each element
        end_of_alignedbyteoffset = header.find(b'\x0d\x0a', start_of_alignedbyteoffset)
        header = header[:start_of_name] + semantics[current_element] + header[end_of_name:start_of_inputslot] + b'0' + header[end_of_inputslot:start_of_alignedbyteoffset] + str(offsets[current_element]).encode() + header[end_of_alignedbyteoffset:]
        current_offset = header.find(b'element[', current_offset + 1)

    #Grab vertex data, file by file, into two dimensional list
    line_headers = [b']+000 POSITION: ', b']+012 NORMAL: ', b']+024 TANGENT: ', b']+036 TEXCOORD: ', b']+044 TEXCOORD1: ', b']+052 TEXCOORD2: ', b']+060 BLENDWEIGHTS: ', b']+076 BLENDINDICES: ']
    vertex_data = []
    for i in range(len(vb_filenames)):
        vertex_file_data = []
        with open(vb_filenames[i], 'rb') as f:
            vb_data = f.read()
            current_index = 0
            current_offset = vb_data.find(b'vertex-data', 0) # Jump to start of vertex data
            while current_offset > 0:
                try:
                    current_offset = vb_data.find(b': ', vb_data.find(b'\x0d\x0a\x76\x62', current_offset + 1)) # Jump to next vertex
                    next_offset = vb_data.find(b'\x0d\x0a', current_offset + 1)
                    vertex_file_data.append(b'vb0[' + str(current_index).encode("utf8") + line_headers[i] + vb_data[current_offset:next_offset].split(b': ')[1] + b'\x0d\x0a')
                    current_index = current_index + 1
                except IndexError:
                    pass
                continue
            vertex_data.append(vertex_file_data)

    #Build vertex list in format expected by Blender plugin
    vertex_output = bytearray()
    for i in range(len(vertex_data[0])):
        for j in range(len(vertex_data)):
            try:
                vertex_output.extend(vertex_data[j][i])
            except IndexError:
                pass
            continue
        #Blender plugin expects a blank line after every vertex group
        vertex_output.extend(b'\x0d\x0a')

    with open('output/' + vb_filenames[0], 'wb') as f:
        f.write(header+vertex_output)
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
