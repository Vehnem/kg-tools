from pyjedai.block_building import StandardBlocking

def block(data, attributes1, attributes2):
    bb = StandardBlocking()
    blocks = bb.build_blocks(data, attributes_1=attributes1, attributes_2=attributes2, tqdm_disable=True)
    return blocks
