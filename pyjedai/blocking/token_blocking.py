from pyjedai.block_building import StandardBlocking

def block(data):
    bb = StandardBlocking()
    blocks = bb.build_blocks(data, attributes_1=['name'], attributes_2=['name'])
    return blocks