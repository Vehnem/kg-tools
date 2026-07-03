import py_entitymatching as em

# Get the paths of the input tables
path_A = './bin/citeseer_sample.csv'

A = em.read_csv_metadata(path_A, key='id')

# Invoke the open refine gui for data exploration
#p = em.data_explore_openrefine(A, name='Table')

# Save the project back to our dataframe
# after calling export_pandas_frame, the openRefine project will be deleted automatically
#A = p.export_pandas_frame()


# Invoke the pandastable gui for data exploration
# The process will be blocked until closing the GUI
em.data_explore_pandastable(A)

print(A.head())