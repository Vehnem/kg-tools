import py_entitymatching as em
import ydata_profiling as pdp

# Get the paths of the input tables
path_A = './bin/citeseer_sample.csv'

# Read the CSV files and set 'ID' as the key attribute
A = em.read_csv_metadata(path_A, key='id')

pfr = pdp.ProfileReport(A)
pfr.to_file("./bin/tmp/example.html")

