import pandas as pd
from pyjedai.datamodel import Data
from pyjedai.evaluation import Evaluation


def read(file_path_1, file_path_2,
         ground_truth_path=None,
         id_column_name_1=None, id_column_name_2=None):
    def safe_read_csv(path):
        try:
            return pd.read_csv(path, sep=',', engine='python', na_filter=False, encoding='utf-8')
        except UnicodeDecodeError:
            return pd.read_csv(path, sep=',', engine='python', na_filter=False, encoding='ISO-8859-1')

    d1 = safe_read_csv(file_path_1)
    d2 = safe_read_csv(file_path_2)

    gt = safe_read_csv(ground_truth_path) if ground_truth_path else None

    if id_column_name_1 is None:
        id_column_name_1 = d1.columns[0]
    if id_column_name_2 is None:
        id_column_name_2 = d2.columns[0]

    data = Data(dataset_1=d1,
                id_column_name_1=id_column_name_1,
                dataset_2=d2,
                id_column_name_2=id_column_name_2,
                ground_truth=gt)

    return data