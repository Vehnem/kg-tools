import pandas as pd
from pyjedai.datamodel import Data
from pyjedai.evaluation import Evaluation


def read():
    d1 = pd.read_csv("./bin/Abt.csv", sep=',', engine='python', na_filter=False,
                     encoding="ISO-8859-1")
    d2 = pd.read_csv("./bin/Buy.csv", sep=',', engine='python', na_filter=False,
                     encoding="ISO-8859-1")
    gt = pd.read_csv("./bin/abt_buy_perfectMapping.csv", sep=',', engine='python')

    data = Data(dataset_1=d1,
                id_column_name_1='id',
                dataset_2=d2,
                id_column_name_2='id',
                ground_truth=gt)
    return data