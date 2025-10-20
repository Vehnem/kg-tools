from pyjedai.block_cleaning import BlockFiltering

def clean(cleaned_blocks, data):
    bf = BlockFiltering(ratio=0.8)
    filtered_blocks = bf.process(cleaned_blocks, data, tqdm_disable=True)
    return filtered_blocks