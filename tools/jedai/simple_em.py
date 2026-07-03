import os
import sys
import pandas as pd
from pandas import DataFrame
import networkx
from networkx import draw, Graph
import logging

###
# Data Reading
###

from pyjedai.datamodel import Data
from pyjedai.evaluation import Evaluation

###
# Block Building
###

from pyjedai.block_building import (
    StandardBlocking,
    QGramsBlocking,
    ExtendedQGramsBlocking,
    SuffixArraysBlocking,
    ExtendedSuffixArraysBlocking,
)
from pyjedai.vector_based_blocking import EmbeddingsNNBlockBuilding

###
# Block Cleaning
###

from pyjedai.block_cleaning import BlockPurging

###
# Block Filtering
###
from pyjedai.block_cleaning import BlockFiltering

###
# Meta Blocking
###

from pyjedai.comparison_cleaning import (
    WeightedEdgePruning,
    WeightedNodePruning,
    CardinalityEdgePruning,
    CardinalityNodePruning,
    BLAST,
    ReciprocalCardinalityNodePruning,
    ReciprocalWeightedNodePruning,
    ComparisonPropagation
)

###
# Entity Matching
###

from pyjedai.matching import EntityMatching

class SimpleEM:


    def __init__(self, data: Data):
        self.data: Data = data

    def block_building(self):
        logging.info("block building")

        qgb = SuffixArraysBlocking()
        self.blocks = qgb.build_blocks(self.data, attributes_1=self.data.attributes_1, attributes_2=self.data.attributes_2)

        # qgb.report()

    def block_cleaning(self):
        logging.info("block cleaning")

        cbbp = BlockPurging()
        self.cleaned_blocks = cbbp.process(self.blocks, self.data, tqdm_disable=False)

        # cbbp.report()

    def block_filtering(self):
        logging.info("block filtering")

        bf = BlockFiltering(ratio=0.8)
        self.filtered_blocks = bf.process(self.cleaned_blocks, self.data, tqdm_disable=False)

    def meta_blocking(self):
        logging.info("block meta")

        wep = CardinalityEdgePruning(weighting_scheme='X2')
        self.candidate_pairs_blocks = wep.process(self.filtered_blocks, self.data, tqdm_disable=True)

    def get_matches(self, attr, threshold=0.5):
        logging.info("entity matching")

        self.block_building()
        self.block_cleaning()
        self.block_filtering()
        self.meta_blocking()
        EM = EntityMatching(
            metric='dice',
            similarity_threshold=threshold,
            attributes = attr
        )
        self.pairs_graph = EM.predict(self.candidate_pairs_blocks, self.data, tqdm_disable=True)

        for pair in self.pairs_graph.edges:
            yield { 'idA': pair[0], 'idB' : pair[1] }

###
# Entity Clustering
###

# from pyjedai.clustering import ConnectedComponentsClustering

# ccc = ConnectedComponentsClustering()
# clusters = ccc.process(pairs_graph, data)

# df = data.entities

# for c in clusters:
#     lists = list(c)
#     for l in lists:
#         print(df.loc[int(l)])
#     print("======")

# print(data.entities.get(99))