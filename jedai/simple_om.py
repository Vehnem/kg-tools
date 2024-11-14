import os
import sys
import pandas as pd
from pandas import DataFrame

from pyjedai.utils import (
    text_cleaning_method,
    print_clusters,
    print_blocks,
    print_candidate_pairs
)

from pyjedai.evaluation import Evaluation
from pyjedai.datamodel import Data


from pyjedai.schema.matching import ValentineMethodBuilder, ValentineSchemaMatching

class SimpleOM:

    def __init__(self, data) -> None:
        self.data = data

    def get_matches(self):
        sm = ValentineSchemaMatching(ValentineMethodBuilder.cupid_matcher())
        sm.process(self.data)
        matches = sm.get_matches()
        for t1, t2 in matches:
            yield {"columnA": t1[1], "columnB": t2[1], "score": matches[(t1,t2)]}


##
# Schema Matching
##





