from pyjedai.block_building import StandardBlocking

def block(data, attributes1, attributes2):
    bb = StandardBlocking()
    if attributes1 is not None and attributes2 is not None:
        blocks = bb.build_blocks(data, attributes_1=attributes1, attributes_2=attributes2, tqdm_disable=True)
    else:
        blocks = bb.build_blocks(data, tqdm_disable=True)
    return blocks
