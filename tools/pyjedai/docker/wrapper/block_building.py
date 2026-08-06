import pyjedai.comparison_cleaning
from pyjedai.block_building import (
    StandardBlocking,
    QGramsBlocking,
    ExtendedQGramsBlocking,
    SuffixArraysBlocking,
    ExtendedSuffixArraysBlocking,
)

BLOCK_BUILDING_METHODS = {
    "standard_blocking": StandardBlocking,
    "qgrams_blocking": QGramsBlocking,
    "extended_qgrams_blocking": ExtendedQGramsBlocking,
    "suffix_arrays_blocking": SuffixArraysBlocking,
    "extended_suffix_arrays_blocking": ExtendedSuffixArraysBlocking,
}


def block(
    data,
    attributes1=None,
    attributes2=None,
    method="standard_blocking",
    method_params=None,
    tqdm_disable=True,
):
    if method not in BLOCK_BUILDING_METHODS:
        raise ValueError(
            f"Unknown Block-Building-Method '{method}'. "
            f"Available: {list(BLOCK_BUILDING_METHODS)}"
        )

    bb = BLOCK_BUILDING_METHODS[method](**(method_params or {}))

    if attributes1 is not None and attributes2 is not None:
        blocks = bb.build_blocks(
            data, attributes_1=attributes1, attributes_2=attributes2, tqdm_disable=tqdm_disable
        )
    else:
        blocks = bb.build_blocks(data, tqdm_disable=tqdm_disable)

    return blocks
