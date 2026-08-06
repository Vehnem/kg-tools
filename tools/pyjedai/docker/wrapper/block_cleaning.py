from pyjedai.block_cleaning import BlockFiltering

BLOCK_CLEANING_METHODS = {
    "block_filtering": BlockFiltering,
}

def clean(cleaned_blocks, data, method="block_filtering", method_params=None, tqdm_disable=True):
    if method not in BLOCK_CLEANING_METHODS:
        raise ValueError(
            f"Unknown Block-Cleaning-Method '{method}'. "
            f"Available: {list(BLOCK_CLEANING_METHODS)}"
        )

    bf = BLOCK_CLEANING_METHODS[method](**(method_params or {"ratio": 0.8}))
    filtered_blocks = bf.process(cleaned_blocks, data, tqdm_disable=tqdm_disable)
    return filtered_blocks
