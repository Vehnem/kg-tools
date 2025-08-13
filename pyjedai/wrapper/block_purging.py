from pyjedai.block_cleaning import BlockPurging

def purge(blocks, data):
    bp = BlockPurging()
    cleaned_blocks = bp.process(blocks, data, tqdm_disable=False)
    return cleaned_blocks