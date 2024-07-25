# Vertex buffer merge script - for use with 3dmigoto frame dumps from games that use more than one vertex
# buffer input slot.  Execute from the directory of the indexed frame dump (not de-duped) and it will
# output any buffers it finds into the ./output directory.  It will discard values that overread a buffer.
# GitHub eArmada8/vbuffer_merge_split

import glob, os, re, copy, json

def retrieve_indices():
    # Make a list of all vertex buffer indices in the current folder
    # NOTE: Will *not* include index buffers without vertex data! (i.e. ib files without corresponding vb files)
    return sorted([re.findall(r'\d+', x)[0] for x in glob.glob('*-vb0*txt')])

def copy_ib_file_to_output(fileindex):
    # Copy the index buffer file to the output directory unmodified, if it exists
    ib_filename = str(glob.glob(fileindex + '-ib*txt')[0])
    if os.path.exists(ib_filename):
        with open(ib_filename, 'r') as f:
            ib_file_data = f.read()
        with open('output/' + ib_filename, 'w') as f:
            f.write(ib_file_data)
        del ib_file_data
    return

def stride_from_format(dxgi_format):
    return(int(sum([int(x) for x in re.findall("[0-9]+",dxgi_format)])/8))

def read_fmt(header):
    fmt_struct = {}
    headerlines = header.decode('utf-8').strip().replace('\r','').split('\n')
    elements = []
    element_num = -1
    for line in range(len(headerlines)):
        if headerlines[line][0:7] == 'element': # Moving on to the next element
            if element_num > -1: # If this not the first element, append the previous element
                elements.append(element)
            element = {}
            element_num = int(headerlines[line].split('[')[-1][:-2])
        else:
            try:
                linekey, lineval = headerlines[line].strip().split(': ')[0:2]
            except ValueError:
                linekey, lineval = headerlines[line].strip().split(':')[0], ''
            if lineval.isnumeric():
                lineval = int(lineval)
            if element_num == -1:
                fmt_struct[linekey] = lineval
            else:
                element[linekey] = lineval
    elements.append(element)
    fmt_struct['elements'] = elements
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
    #First, get a list of all the VB files
    vb_filenames = sorted(glob.glob(fileindex + '-vb*txt'))

    #Get Header
    with open(vb_filenames[0], 'rb') as f:
        filedata = f.read()
        fmt = read_fmt(filedata[:filedata.find(b'vertex-data')])
        del(filedata)

    valid_elements = [] # These will be inserted (and thus ordered) by file then by offset
    vertex_data = []
    last_vertex = 0
    original_strides = []
    for i in range(len(vb_filenames)):
        valid_input_slot = True
        #Determine valid offsets (sometimes 3DMigoto re-reads the same values if the game does not give good offsets
        elements = [element for element in fmt['elements'] if element['InputSlot'] == i]
        offsets = [element['AlignedByteOffset'] for element in elements]
        used_offsets = []
        for j in range(len(elements)):
            if not elements[j]['AlignedByteOffset'] in used_offsets:
                valid_elements.append(elements[j])
                used_offsets.append(elements[j]['AlignedByteOffset'])
        vertices = {}
        for j in range(len(used_offsets)):
            vertices[used_offsets[j]] = {}
        #Grab vertex data
        current_vertex = -1
        v_semantics = []
        with open(vb_filenames[i], 'r') as f:
            for line in f:
                if line[0:6] == 'stride': #First line, replace with the merged stride
                    original_strides.append(int(line.strip().split(': ')[1]))
                    if original_strides[-1] == 0:
                        valid_input_slot = False
                        break #If the entire buffer is empty, skip this file
                if line[0:2] == 'vb':
                    vertex_num, vertex_offset = [int(x) for x in line[4:].split(' ')[0].split(']+')]
                    if vertex_num != current_vertex:
                        #Reset invalid offset detector
                        used_offset_counter = []
                        current_vertex = vertex_num
                    if not vertex_offset in used_offset_counter:
                        vertices[vertex_offset][vertex_num] = line.split(': ')[1].strip()
                        used_offset_counter.append(vertex_offset)
                        #Add semantic to list if first vertex
                        if vertex_num == 0:
                            v_semantics.append(line.split(': ')[0].split(' ')[1])
        if valid_input_slot == True: # If the entire buffer is empty, skip all semantics
            for j in range(len(used_offsets)):
                last_vertex = max(last_vertex, max(vertices[used_offsets[j]].keys()))
                vertex_data.append({'Semantic': v_semantics[j], 'InputSlot': i,\
                    'OriginalOffset': used_offsets[j], 'Vertices': vertices[used_offsets[j]]})



    #Generate new element list
    new_elements = []
    for i in range(len(valid_elements)):
        new_element = copy.deepcopy(valid_elements[i]) # Make a copy so we still have the original
        new_element['AlignedByteOffset'] += sum(original_strides[0:new_element['InputSlot']])
        new_element['InputSlot'] = 0
        new_elements.append(new_element)
    new_fmt = copy.deepcopy(fmt)
    new_fmt['stride'] = sum(original_strides)
    new_fmt['elements'] = new_elements
    
    #Create combined VB
    with open('output/' + vb_filenames[0], 'w') as f:
        f.write(make_header(new_fmt))
        for j in range(last_vertex+1):
            for i in range(len(vertex_data)):
                if j in vertex_data[i]['Vertices'].keys():
                    f.write('vb0[' + str(j) + ']+' + str(new_fmt['elements'][i]['AlignedByteOffset']).zfill(3)\
                        + ' ' + vertex_data[i]['Semantic'] + ': ' + vertex_data[i]['Vertices'][j] + '\n')
            #Blender plugin expects a blank line after every vertex group
            f.write('\n')

    with open('output/{0}.splitdata'.format(fileindex), 'w') as f:
        f.write(json.dumps(original_strides))
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
