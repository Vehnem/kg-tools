from pyjedai.clustering import BestMatchClustering, CenterClustering, ConnectedComponentsClustering, \
    CorrelationClustering, CutClustering, ExactClustering, KiralyMSMApproximateClustering, MarkovClustering, \
    MergeCenterClustering, RicochetSRClustering, RowColumnClustering, UniqueMappingClustering

CLUSTERING_METHODS = {
    "best_match_clustering": BestMatchClustering,
    "center_clustering": CenterClustering,
    "connected_components_clustering": ConnectedComponentsClustering,
    "correlation_clustering": CorrelationClustering,
    "cut_clustering": CutClustering,
    "exact_clustering": ExactClustering,
    "kiraly_msm_approximate_clustering": KiralyMSMApproximateClustering,
    "markov_clustering": MarkovClustering,
    "merge_center_clustering": MergeCenterClustering,
    "ricochet_sr_clustering": RicochetSRClustering,
    "row_column_clustering": RowColumnClustering,
    "unique_mapping_clustering": UniqueMappingClustering,
}

def cluster(pairs_graph, data, method="unique_mapping_clustering", method_params=None):
    if method not in CLUSTERING_METHODS:
        raise ValueError(
            f"Unknown Clustering-Method '{method}'. "
            f"Available: {list(CLUSTERING_METHODS)}"
        )

    cc = CLUSTERING_METHODS[method]()
    clusters = cc.process(pairs_graph, data, **(method_params or {}))
    return clusters
