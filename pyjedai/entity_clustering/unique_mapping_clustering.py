from pyjedai.clustering import UniqueMappingClustering

def cluster(pairs_graph, data):
    ccc = UniqueMappingClustering()
    clusters = ccc.process(pairs_graph, data, similarity_threshold=0.17)
    return clusters