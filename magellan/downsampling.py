import py_entitymatching as em

# Read the CSV files
A = em.read_csv_metadata('./bin/citeseer.csv',low_memory=False) # setting the parameter low_memory to False  to speed up loading.
B = em.read_csv_metadata('./bin/dblp.csv', low_memory=False)

print(f"Length A:{len(A)} Length B:{len(B)}")


em.set_key(A, 'id')
em.set_key(B, 'id')

# Downsample the datasets
sample_A, sample_B = em.down_sample(A, B, size=1000, y_param=1, show_progress=True)

# Display the number of tuples in the sampled datasets
print(f"Length Sample A:{len(sample_A)} Length Sample B:{len(sample_B)}")

