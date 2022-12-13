# Vertex buffer merge script - for use with 3dmigoto frame dumps from games that use more than one vertex
# buffer input slot.  Execute from the directory of the indexed frame dump (not de-duped) and it will
# output any buffers it finds into the ./output directory.  It will discard values that overread a buffer.
# GitHub eArmada8/vbuffer_merge_split

import glob, os, re, copy

def retrieve_indices():
    # Make a list of all vertex buffer indices in the current folder
    # NOTE: Will *not* include index buffers without vertex data! (i.e. ib files without corresponding vb files)
    return sorted([re.findall('^\d+', x)[0] for x in glob.glob('*-vb0*txt')])

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
            linekey, lineval = headerlines[line].strip().split(': ')[0:2]
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
    for i in range(len(vb_filenames)):
        with open(vb_filenames[i], 'r') as f:
            lines = [line for line in f]
        #Obtain valid offsets (sometimes 3DMigoto re-reads the same values if the game does not give good offsets
        elements = [element for element in fmt['elements'] if element['InputSlot'] == i]
        offsets = [element['AlignedByteOffset'] for element in elements]
        used_offsets = []
        for j in range(len(elements)):
            if not elements[j]['AlignedByteOffset'] in used_offsets:
                valid_elements.append(elements[j])
                used_offsets.append(elements[j]['AlignedByteOffset'])
        #Grab vertex data
        for j in range(len(used_offsets)):
            bufferlines = [line for line in lines if '+'+str(used_offsets[j]).zfill(3) in line]
            vertices = {}
            used_vertices = [] # Similar strategy to solving the re-used offset problem, only allow one vertex per vertex number
            for k in range(len(bufferlines)):
                vertex_num = int(bufferlines[k].split('[')[1].split(']')[0])
                if not vertex_num in used_vertices:
                    vertices[vertex_num] = bufferlines[k].split(': ')[1].strip()
                    used_vertices.append(vertex_num)
            last_vertex = max(last_vertex, max(vertices.keys()))
            vertex_data.append({'Semantic': bufferlines[0].split(': ')[0].split(' ')[1], 'InputSlot': i,\
                'OriginalOffset': j, 'Vertices': vertices})

    #Generate new element list
    current_offset = 0
    new_elements = []
    for i in range(len(valid_elements)):
        new_element = copy.deepcopy(valid_elements[i]) # Make a copy so we still have the original
        new_element['InputSlot'] = 0
        new_element['AlignedByteOffset'] = current_offset
        current_offset += stride_from_format(new_element['Format'])
        new_elements.append(new_element)
    new_fmt = copy.deepcopy(fmt)
    new_fmt['stride'] = current_offset
    new_fmt['elements'] = new_elements
    
    #Create combined VB
    output = make_header(new_fmt)
    for j in range(last_vertex+1):
        for i in range(len(valid_elements)):
            if j in vertex_data[i]['Vertices'].keys():
                output += 'vb0[' + str(j) + ']+' + str(new_fmt['elements'][i]['AlignedByteOffset']).zfill(3)\
                    + ' ' + vertex_data[i]['Semantic'] + ': ' + vertex_data[i]['Vertices'][j] + '\n'
        #Blender plugin expects a blank line after every vertex group
        output += '\n'
    
    with open('output/' + vb_filenames[0], 'w') as f:
        f.write(output)
    with open('output/{0}.orig_fmt'.format(fileindex), 'w') as f:
        f.write(make_header(fmt)[:-15])
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
