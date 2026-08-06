from pyjedai.comparison_cleaning import (
    WeightedEdgePruning,
    WeightedNodePruning,
    CardinalityEdgePruning,
    CardinalityNodePruning,
    BLAST,
    ReciprocalCardinalityNodePruning,
    ReciprocalWeightedNodePruning,
    ComparisonPropagation,
)

COMPARISON_CLEANING_METHODS = {
    "weighted_edge_pruning": WeightedEdgePruning,
    "weighted_node_pruning": WeightedNodePruning,
    "cardinality_edge_pruning": CardinalityEdgePruning,
    "cardinality_node_pruning": CardinalityNodePruning,
    "blast": BLAST,
    "reciprocal_cardinality_node_pruning": ReciprocalCardinalityNodePruning,
    "reciprocal_weighted_node_pruning": ReciprocalWeightedNodePruning,
    "comparison_propagation": ComparisonPropagation,
}


def clean(
    filtered_blocks,
    data,
    method="weighted_edge_pruning",
    method_params=None,
    tqdm_disable=True,
):
    if method not in COMPARISON_CLEANING_METHODS:
        raise ValueError(
            f"Unknown Comparison-Cleaning-Method '{method}'. "
            f"Available: {list(COMPARISON_CLEANING_METHODS)}"
        )

    mb = COMPARISON_CLEANING_METHODS[method](**(method_params or {}))
    candidate_pairs_blocks = mb.process(filtered_blocks, data, tqdm_disable=tqdm_disable)
    return candidate_pairs_blocks
