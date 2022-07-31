# Vertex buffer merge script - for use with 3dmigoto frame dumps from games that use separate buffers
# for each vertex element.  Execute from the directory of the indexed frame dump (not de-duped) and it will
# output any buffers it finds into the ./output directory.  Specifically for Kuro no Kiseki meshes with
# 7 vertex buffers; will completely discard buffers 4 and 5 as it only reads the first three and the last two.
# GitHub eArmada8/vbuffer_merge_split

import glob, os, re, shutil

def retrieve_indices():
    # Make a list of all vertex buffer indices in the current folder
    # NOTE: Will *not* include index buffers without vertex data! (i.e. ib files without corresponding vb files)
    return sorted([re.findall('^\d+', x)[0] for x in glob.glob('*-vb7*txt')])

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

    #Add vertex count into pre-baked header
    header1 = b'stride: 92\x0d\x0afirst vertex: 0\x0d\x0avertex count: '
    header2 = b'\x0d\x0afirst instance: 0\x0d\x0ainstance count: 1\x0d\x0atopology: trianglelist\x0d\x0aelement[0]:\x0d\x0a  SemanticName: POSITION\x0d\x0a  SemanticIndex: 0\x0d\x0a  Format: R32G32B32_FLOAT\x0d\x0a  InputSlot: 0\x0d\x0a  AlignedByteOffset: 0\x0d\x0a  InputSlotClass: per-vertex\x0d\x0a  InstanceDataStepRate: 0\x0d\x0aelement[1]:\x0d\x0a  SemanticName: NORMAL\x0d\x0a  SemanticIndex: 0\x0d\x0a  Format: R32G32B32_FLOAT\x0d\x0a  InputSlot: 0\x0d\x0a  AlignedByteOffset: 12\x0d\x0a  InputSlotClass: per-vertex\x0d\x0a  InstanceDataStepRate: 0\x0d\x0aelement[2]:\x0d\x0a  SemanticName: TANGENT\x0d\x0a  SemanticIndex: 0\x0d\x0a  Format: R32G32B32_FLOAT\x0d\x0a  InputSlot: 0\x0d\x0a  AlignedByteOffset: 24\x0d\x0a  InputSlotClass: per-vertex\x0d\x0a  InstanceDataStepRate: 0\x0d\x0aelement[3]:\x0d\x0a  SemanticName: TEXCOORD\x0d\x0a  SemanticIndex: 0\x0d\x0a  Format: R32G32_FLOAT\x0d\x0a  InputSlot: 0\x0d\x0a  AlignedByteOffset: 36\x0d\x0a  InputSlotClass: per-vertex\x0d\x0a  InstanceDataStepRate: 0\x0d\x0aelement[4]:\x0d\x0a  SemanticName: TEXCOORD\x0d\x0a  SemanticIndex: 1\x0d\x0a  Format: R32G32_FLOAT\x0d\x0a  InputSlot: 0\x0d\x0a  AlignedByteOffset: 44\x0d\x0a  InputSlotClass: per-vertex\x0d\x0a  InstanceDataStepRate: 0\x0d\x0aelement[5]:\x0d\x0a  SemanticName: TEXCOORD\x0d\x0a  SemanticIndex: 2\x0d\x0a  Format: R32G32_FLOAT\x0d\x0a  InputSlot: 0\x0d\x0a  AlignedByteOffset: 52\x0d\x0a  InputSlotClass: per-vertex\x0d\x0a  InstanceDataStepRate: 0\x0d\x0aelement[6]:\x0d\x0a  SemanticName: BLENDWEIGHTS\x0d\x0a  SemanticIndex: 0\x0d\x0a  Format: R32G32B32A32_FLOAT\x0d\x0a  InputSlot: 0\x0d\x0a  AlignedByteOffset: 60\x0d\x0a  InputSlotClass: per-vertex\x0d\x0a  InstanceDataStepRate: 0\x0d\x0aelement[7]:\x0d\x0a  SemanticName: BLENDINDICES\x0d\x0a  SemanticIndex: 0\x0d\x0a  Format: R32G32B32A32_UINT\x0d\x0a  InputSlot: 0\x0d\x0a  AlignedByteOffset: 76\x0d\x0a  InputSlotClass: per-vertex\x0d\x0a  InstanceDataStepRate: 0\x0d\x0a\x0d\x0avertex-data:\x0d\x0a\x0d\x0a'
    header = header1 + str(current_index).encode("utf8") + header2

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
