# Ys VIII pc port vb cleanup script.  Requires lib_fmtibvb as it writes raw buffers.  Currently only
# processes buffers with a stride of 88 bytes, which all seem to share a common structure.
#
# GitHub eArmada8/vbuffer_merge_split

import os, glob
from lib_fmtibvb import *

def retrieve_indices():
    # Make a list of all vertex buffer indices in the current folder
    # NOTE: Will *not* include index buffers without vertex data! (i.e. ib files without corresponding vb files)
    return sorted([re.findall('^\d+', x)[0] for x in glob.glob('*-vb0*txt')])

def make_fmt():
    return({'stride': '88', 'topology': 'trianglelist', 'format': 'DXGI_FORMAT_R32_UINT',\
        'elements': [{'id': '0', 'SemanticName': 'POSITION', 'SemanticIndex': '0',\
        'Format': 'R32G32B32A32_FLOAT', 'InputSlot': '0', 'AlignedByteOffset': '0',\
        'InputSlotClass': 'per-vertex', 'InstanceDataStepRate': '0'}, {'id': '1',\
        'SemanticName': 'UNKNOWN', 'SemanticIndex': '0',\
        'Format': 'R32G32B32A32_FLOAT', 'InputSlot': '0', 'AlignedByteOffset': '16',\
        'InputSlotClass': 'per-vertex', 'InstanceDataStepRate': '0'}, {'id': '2',\
        'SemanticName': 'NORMAL', 'SemanticIndex': '0', 'Format': 'R8G8B8A8_SNORM',\
        'InputSlot': '0', 'AlignedByteOffset': '32', 'InputSlotClass': 'per-vertex',\
        'InstanceDataStepRate': '0'}, {'id': '3',\
        'SemanticName': 'UNKNOWN', 'SemanticIndex': '1', 'Format': 'R8G8B8A8_SNORM',\
        'InputSlot': '0', 'AlignedByteOffset': '36', 'InputSlotClass': 'per-vertex',\
        'InstanceDataStepRate': '0'}, {'id': '4', 'SemanticName': 'COLOR', 'SemanticIndex': '0',\
        'Format': 'R8G8B8A8_UNORM', 'InputSlot': '0', 'AlignedByteOffset': '40',\
        'InputSlotClass': 'per-vertex', 'InstanceDataStepRate': '0'}, {'id': '5',\
        'SemanticName': 'COLOR', 'SemanticIndex': '1', 'Format': 'R8G8B8A8_UNORM',\
        'InputSlot': '0', 'AlignedByteOffset': '44', 'InputSlotClass': 'per-vertex',\
        'InstanceDataStepRate': '0'}, {'id': '6', 'SemanticName': 'TEXCOORD',\
        'SemanticIndex': '0', 'Format': 'R32G32_FLOAT', 'InputSlot': '0',\
        'AlignedByteOffset': '48', 'InputSlotClass': 'per-vertex',\
        'InstanceDataStepRate': '0'}, {'id': '7', 'SemanticName': 'UNKNOWN',\
        'SemanticIndex': '2', 'Format': 'R32G32_FLOAT', 'InputSlot': '0',\
        'AlignedByteOffset': '56', 'InputSlotClass': 'per-vertex', 'InstanceDataStepRate': '0'},\
        {'id': '8', 'SemanticName': 'TEXCOORD', 'SemanticIndex': '1', 'Format': 'R32G32_FLOAT',\
        'InputSlot': '0', 'AlignedByteOffset': '64', 'InputSlotClass': 'per-vertex',\
        'InstanceDataStepRate': '0'}, {'id': '9', 'SemanticName': 'UNKNOWN', 'SemanticIndex': '3',\
        'Format': 'R32G32_FLOAT', 'InputSlot': '0', 'AlignedByteOffset': '72',\
        'InputSlotClass': 'per-vertex', 'InstanceDataStepRate': '0'}, {'id': '10',\
        'SemanticName': 'BLENDWEIGHTS', 'SemanticIndex': '0', 'Format': 'R8G8B8A8_UNORM',\
        'InputSlot': '0', 'AlignedByteOffset': '80', 'InputSlotClass': 'per-vertex',\
        'InstanceDataStepRate': '0'}, {'id': '11', 'SemanticName': 'BLENDINDICES',\
        'SemanticIndex': '0', 'Format': 'R8G8B8A8_UINT', 'InputSlot': '0',\
        'AlignedByteOffset': '84', 'InputSlotClass': 'per-vertex', 'InstanceDataStepRate': '0'}]})

def read_vb(filename):
    orig_offset = ['+000', '+016', '+032', '+036', '+040', '+044', '+048', '+56', '+064', '+072', '+080', '+084']
    SemanticName = ['POSITION', 'UNKNOWN', 'NORMAL', 'UNKNOWN', 'COLOR', 'COLOR',\
        'TEXCOORD', 'UNKNOWN', 'TEXCOORD', 'UNKNOWN', 'BLENDWEIGHTS', 'BLENDINDICES']
    SemanticIndex = ['0', '0,', '0', '1', '0', '1', '0', '2', '1', '3', '0', '0']
    ExpectedElementLength = [4,4,4,4,4,4,2,2,2,2,4,4] # 1 = Scalar, 2 = Vec2, 3 = Vec3, 4 = Vec4
    Format = [0,0,0,0,0,0,0,1,0,1,0,1] #0 = float, 1 = int
    Blanks = [[0,0,0,1], [0,0,0,0], [0,0,0,1], [0,0,0,0], [1,1,1,1], [0,0,0,1],\
        [0,0], [0,0], [0,0], [0,0], [0,0,0,0], [0,0,0,0]]
    with open(filename,'r') as f:
        lines = f.read().split('\n')
    vertex_count = [int(x.split(': ')[1]) for x in lines if 'vertex count' in x][0]
    if lines[0] == 'stride: 88':
        vb = []
        for i in range(len(orig_offset)):
            raw_values = [x.split(': ')[1].split(', ') for x in lines if orig_offset[i] in x]
            if len(raw_values) == 0: # Fill in the blanks, literally
                raw_values = [Blanks[i] for x in range(vertex_count)]
            for j in range(len(raw_values)):
                if Format[i] == 0:
                    raw_values[j] = [float(x) for x in raw_values[j]]
                elif Format[i] == 1:
                    raw_values[j] = [int(x) for x in raw_values[j]]
            if len(raw_values[0]) < ExpectedElementLength[i]: # Add values if too short (e.g. Vec3 to Vec4)
                missing_length = ExpectedElementLength[i] - len(raw_values[0])
                raw_values = [x+Blanks[i][-missing_length:] for x in raw_values]
            vb.append({'SemanticName': SemanticName[i], 'SemanticIndex': SemanticIndex[i],\
                'Buffer': raw_values})
        return(vb)
    else:
        return(False)

def read_ib(filename):
    with open(filename,'r') as f:
        lines = f.read().split('\n\n')[1].split('\n')
    if lines[-1] == '':
        lines = lines[:-1]
    raw_values = [x.split(' ') for x in lines]
    for i in range(len(raw_values)):
        raw_values[i] = [int(x) for x in raw_values[i]]
    return(raw_values)

if __name__ == "__main__":
    # Set current directory
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    # Let's make an output directory, because otherwise we would have to delete / overwrite files
    if not os.path.exists('output'): 
        os.mkdir('output')

    fmt = make_fmt()
    indices = retrieve_indices()
    for i in range(len(indices)):
        vb = read_vb(glob.glob(indices[i] + '-vb*txt')[0])
        if vb != False:
            #print("Processing {0}...".format(indices[i]))
            ib = read_ib(glob.glob(indices[i] + '-ib*txt')[0])
            write_fmt(fmt, 'output/{0}.fmt'.format(indices[i]))
            write_ib(ib, 'output/{0}.ib'.format(indices[i]), fmt)
            write_vb(vb, 'output/{0}.vb'.format(indices[i]), fmt)
