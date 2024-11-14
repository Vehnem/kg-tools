from simple_om import SimpleOM
from simple_em import SimpleEM

import pandas as pd
from pyjedai.datamodel import Data

pathToCsv1="./datasets/record_descriptions/1_abt.csv"
pathToCsv2="./datasets/record_descriptions/2_buy.csv"

dfA = pd.read_csv(pathToCsv1, sep=',', engine='python', na_filter=False, encoding='unicode_escape').astype(str)
dfB = pd.read_csv(pathToCsv2, sep=',', engine='python', na_filter=False, encoding='unicode_escape').astype(str)

# TODO detect id field else build new one

idA = 'id' 
if not idA in dfA: 
    dfA[idA] = dfA.index + 1


idB = 'id' 
if not idB in dfB: 
    dfB[idB] = dfB.index + dfA.size

attributes_1=list(dfA.columns.values)
attributes_1.remove('id')
attributes_2=list(dfB.columns.values)
attributes_2.remove('id')

data = Data(
            dataset_1=dfA,
            attributes_1=attributes_1,
            id_column_name_1=idA,
            dataset_2=dfB,
            attributes_2=attributes_2,
            id_column_name_2=idB
        )

om = SimpleOM(data)

attributeCandidates = set()

for m in om.get_matches():
    print(m)
    if(m['score'] > 0.8):
        attributeCandidates.add(m['columnA'])
        attributeCandidates.add(m['columnB'])

print(attributeCandidates)
attributeCandidates.remove('price')
attributeCandidates.remove('id')
# attributeCandidates.remove('subject_id')



em = SimpleEM(data)

pairs = [pair for pair in em.get_matches(sorted(list(attributeCandidates)))]

print(len(pairs))

for head in pairs[0:5]:
    print(data.entities.loc[head['idA']])
    print(data.entities.loc[head['idB']])
    print("===")

