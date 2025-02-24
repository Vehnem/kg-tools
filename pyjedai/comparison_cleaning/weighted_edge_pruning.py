from pyjedai.comparison_cleaning import WeightedEdgePruning

def clean(filtered_blocks, data):
    mb = WeightedEdgePruning(weighting_scheme='EJS')
    candidate_pairs_blocks = mb.process(filtered_blocks, data, tqdm_disable=True)
    return candidate_pairs_blocks