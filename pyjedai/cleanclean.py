import data_cleaning
import data_reading
from blocking import token_blocking
import block_purging
import block_cleaning
from comparison_cleaning import weighted_edge_pruning
import entity_matching
from entity_clustering import unique_mapping_clustering

data = data_reading.read()

data_cleaning.clean(data)

blocks = token_blocking.block(data)

cleaned_blocks = block_purging.purge(blocks, data)

filtered_blocks = block_cleaning.clean(cleaned_blocks, data)

candidate_pairs_blocks = weighted_edge_pruning.clean(filtered_blocks, data)

pairs_graph = entity_matching.match(candidate_pairs_blocks, data)

clusters = unique_mapping_clustering.cluster(pairs_graph, data)

