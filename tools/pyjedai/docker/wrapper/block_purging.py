from pyjedai.block_cleaning import BlockPurging

BLOCK_PURGING_METHODS = {
    "block_purging": BlockPurging,
}


def purge(blocks, data, method="block_purging", method_params=None, tqdm_disable=True):
    if method not in BLOCK_PURGING_METHODS:
        raise ValueError(
            f"Unknown Block-Purging-Method '{method}'. "
            f"Available: {list(BLOCK_PURGING_METHODS)}"
        )

    bp = BLOCK_PURGING_METHODS[method](**(method_params or {}))
    cleaned_blocks = bp.process(blocks, data, tqdm_disable=tqdm_disable)
    return cleaned_blocks
