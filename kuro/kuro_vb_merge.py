# Vertex buffer merge script - for use with 3dmigoto frame dumps from games that use separate buffers
# for each vertex element.  Execute from the directory of the indexed frame dump (not de-duped) and it will
# output any buffers it finds into the ./output directory.  Specifically for Kuro no Kiseki meshes with
# vb0-vb7 vertex buffers (8-part buffers).
# GitHub eArmada8/vbuffer_merge_split

import glob, os, re, shutil

def retrieve_indices():
    # Make a list of all vertex buffer indices in the current folder (only include 8-part vertex buffers)
    # NOTE: Will *not* include index buffers without vertex data! (i.e. ib files without corresponding vb files)
    return(sorted([re.findall('^\d+', x)[0] for x in glob.glob('*-vb2*txt')]))

def copy_ib_file_to_output(fileindex):
    # Copy the index buffer file to the output directory unmodified, if it exists
    ib_filename = str(glob.glob(fileindex + '-ib*txt')[0])
    if os.path.exists(ib_filename):
        shutil.copy2(ib_filename, 'output/' + ib_filename)
    return

def stride_from_format(dxgi_format):
    return(int(sum([int(x) for x in re.findall("[0-9]+",dxgi_format)])/8))

def remove_semantic_names (header):
    new_header = b''
    current_offset = 0
    next_sem = 1
    while next_sem > 0:
        next_sem = header.find(b'SemanticName', current_offset)
        if next_sem > 0:
            new_header += header[current_offset:next_sem] + b'SemanticName: UNKNOWN'
            current_offset = header.find(b'SemanticIndex', next_sem) - 4
        else:
            new_header += header[current_offset:len(header)]
    return(new_header)

def guess_semantic_names (fmt_struct):
    for i in range(len(fmt_struct['elements'])):
        if fmt_struct['elements'][i]['Format'] == 'R32G32B32_FLOAT':
            if fmt_struct['elements'][i]['InputSlot'] == 0:
                fmt_struct['elements'][i]['SemanticName'] = 'POSITION'
            elif fmt_struct['elements'][i]['InputSlot'] == 1:
                fmt_struct['elements'][i]['SemanticName'] = 'NORMAL'
            elif fmt_struct['elements'][i]['InputSlot'] == 2:
                fmt_struct['elements'][i]['SemanticName'] = 'TANGENT'
        elif fmt_struct['elements'][i]['Format'] == 'R32G32_FLOAT':
            fmt_struct['elements'][i]['SemanticName'] = 'TEXCOORD'
        elif fmt_struct['elements'][i]['Format'] == 'R32G32B32A32_FLOAT':
            if i == len(fmt_struct['elements']) - 2:
                fmt_struct['elements'][i]['SemanticName'] = 'BLENDWEIGHTS'
            else:
                fmt_struct['elements'][i]['SemanticName'] = 'COLOR'
        elif fmt_struct['elements'][i]['Format'] == 'R32G32B32A32_UINT':
            fmt_struct['elements'][i]['SemanticName'] = 'BLENDINDICES'
        elif fmt_struct['elements'][i]['Format'] == 'B8G8R8A8_UNORM':
            fmt_struct['elements'][i]['SemanticName'] = 'COLOR'
    return(fmt_struct)

def fix_strides (fmt_struct):
    stride = 0
    for i in range(len(fmt_struct['elements'])):
        fmt_struct['elements'][i]['AlignedByteOffset'] = stride
        fmt_struct['elements'][i]['InputSlot'] = 0
        stride += stride_from_format(fmt_struct['elements'][i]['Format'])
    fmt_struct['stride'] = stride
    return(fmt_struct)

def read_fmt (header, combined_stride = True):
    fmt_struct = {}
    headerlines = remove_semantic_names(header).decode('utf-8').strip().replace('\r','').split('\n')
    elements = []
    element_num = -1
    for line in range(len(headerlines)):
        if headerlines[line][0:7] == 'element': # Moving on to the next element
            if element_num > -1: # If this not the first element, append the previous element
                elements.append(element)
            element = {}
            element_num = int(headerlines[line].split('[')[-1][:-2])
        else:
            linekey, lineval = headerlines[line].strip().split(': ')[0:2]
            if lineval.isnumeric():
                lineval = int(lineval)
            if element_num == -1:
                fmt_struct[linekey] = lineval
            else:
                element[linekey] = lineval
    elements.append(element)
    fmt_struct['elements'] = elements
    fmt_struct = guess_semantic_names(fmt_struct)
    if combined_stride == True:
        fmt_struct = fix_strides(fmt_struct)
    return(fmt_struct)

def make_header(fmt_struct):
    header = ''
    for key in fmt_struct:
        if not key == 'elements':
            header += key + ': ' + str(fmt_struct[key]) + '\n'
        else:
            pass
    for i in range(len(fmt_struct['elements'])):
        header += 'element[' + str(i) + ']:\n'
        for key in fmt_struct['elements'][i]:
            header += '  ' + key + ': ' + str(fmt_struct['elements'][i][key]) + '\n'
    header += '\nvertex-data:\n\n'
    return(header)

def merge_vb_file_to_output(fileindex):
    # Take all the vertex buffer files for one index buffer and merge them into a single vertex buffer file
    # First, get a list of all the VB files
    vb_filenames = sorted(glob.glob(fileindex + '-vb*txt'))

    #Get header for merged buffer
    with open(vb_filenames[0], 'rb') as f:
        filedata = f.read()
        fmt = read_fmt(filedata[:filedata.find(b'vertex-data')], combined_stride = True)
        del(filedata)

    #Grab vertex data, file by file, into two dimensional list
    line_headers = [(x['SemanticName']+str(x['SemanticIndex'])).encode() if x['SemanticIndex'] > 0 else x['SemanticName'].encode() for x in fmt['elements']]
    vertex_data = []
    for i in range(len(vb_filenames)):
        merged_vertex_file_data = []
        split_vertex_file_data = []
        with open(vb_filenames[i], 'rb') as f:
            vb_data = f.read()
            #Get header for split buffer
            base_fmt = read_fmt(vb_data[:vb_data.find(b'vertex-data')], combined_stride = False)
            current_index = 0
            current_offset = vb_data.find(b'vertex-data', 0) # Jump to start of vertex data
            while current_offset > 0:
                try:
                    current_offset = vb_data.find(b': ', vb_data.find(b'\x0d\x0a\x76\x62', current_offset + 1)) # Jump to next vertex
                    next_offset = vb_data.find(b'\x0d\x0a', current_offset + 1)
                    merged_vertex_file_data.append(b'vb0[' + str(current_index).encode("utf8") + b']+' \
                    + str(fmt['elements'][i]['AlignedByteOffset']).zfill(3).encode("utf8") + b' ' + line_headers[i] + b': ' \
                    + vb_data[current_offset:next_offset].split(b': ')[1] + b'\x0d\x0a')
                    split_vertex_file_data.append(b'vb0[' + str(current_index).encode("utf8") + b']+' \
                    + str(base_fmt['elements'][i]['AlignedByteOffset']).zfill(3).encode("utf8") + b' ' + line_headers[i] + b': ' \
                    + vb_data[current_offset:next_offset].split(b': ')[1] + b'\x0d\x0a')
                    current_index = current_index + 1
                except IndexError:
                    pass
                continue
            vertex_data.append(merged_vertex_file_data)
            fixed_buffer = b'\x0d\x0a'.join(split_vertex_file_data) + b'\x0d\x0a'
            with open(vb_filenames[i], 'wb') as f:
                f.write(make_header(base_fmt).encode()+fixed_buffer)

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
        f.write(make_header(fmt).encode()+vertex_output)
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
