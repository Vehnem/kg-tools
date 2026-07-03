import py_entitymatching as em
import os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the paths of the input tables
path_A = os.path.join(current_dir, '../bin/citeseer_sample.csv')
path_B = os.path.join(current_dir, '../bin/dblp_sample.csv')

# Read the CSV files and set 'id' as the key attribute
A = em.read_csv_metadata(path_A, key='id')
B = em.read_csv_metadata(path_B, key='id')

print(A.head())
print(B.head())


#Block Tables to Produce a Candidate Set of Tuple Pairs

# Instantiate overlap blocker object
ob = em.OverlapBlocker()

# Specify the tokenization to be 'word' level and set overlap_size to be 3.
C1 = ob.block_tables(A, B, 'title', 'title', word_level=True, overlap_size=3,
                    l_output_attrs=['title', 'authors', 'year'],
                    r_output_attrs=['title', 'authors', 'year'],
                    show_progress=False)
print(f"C1 : {C1.head()}")

# Set the word_level to be False and set the value of q (using q_val)
C2 = ob.block_tables(A, B, 'title', 'title', word_level=False, q_val=3, overlap_size=3,
                    l_output_attrs=['title', 'authors', 'year'],
                    r_output_attrs=['title', 'authors', 'year'],
                    show_progress=False)
print(f"C2 : {C2.head()}")


# Include Franciso as one of the stop words
ob.stop_words.append('francisco')

# Set the parameter to remove stop words to False
C3 = ob.block_tables(A, B, 'title', 'title', word_level=True, overlap_size=3, rem_stop_words=False,
                    l_output_attrs=['title', 'authors', 'year'],
                    r_output_attrs=['title', 'authors', 'year'],
                    show_progress=False)
print(f"C3 : {C3.head()}")


# You can set allow_missing_values to be True to include all possible tuple pairs with missing values.
C4 = ob.block_tables(A, B, 'title', 'title', word_level=True, overlap_size=3, allow_missing=True,
                    l_output_attrs=['title', 'authors', 'year'],
                    r_output_attrs=['title', 'authors', 'year'],
                    show_progress=False)
print(f"C4 : {C4.head()}")


# Block a Candidata Set To Produce Reduced Set of Tuple Pairs

#Instantiate the overlap blocker
ob = em.OverlapBlocker()

# Specify the tokenization to be 'word' level and set overlap_size to be 1.
C5 = ob.block_candset(C1, 'title', 'title', word_level=True, overlap_size=1, show_progress=False)
print(f"C5 : {C5.head()}")

# Specify the tokenization to be 'word' level and set overlap_size to be 1.
C6 = ob.block_candset(C1, 'title', 'title', word_level=False, q_val= 3, overlap_size=1, show_progress=False)
print(f"C6 : {C6.head()}")

#As we saw with block_tables, you can include all the possible tuple pairs with the missing values using allow_missing parameter block the candidate set with the updated set of stop words.
C7 = ob.block_candset(C4, 'title', 'title', word_level=True, overlap_size=1, allow_missing=True, show_progress=False)
print(f"C7 : {C7.head()}")


#Block Two tuples To Check If a Tuple Pair Would Get Blocked

# Display the first tuple from table A
print(A.loc[[0]])

# Display the first tuple from table B
print(B.loc[[0]])

# Instantiate Attr. Equivalence Blocker
ob = em.OverlapBlocker()

# Apply blocking to a tuple pair from the input tables on zipcode and get blocking status
status = ob.block_tuples(A.loc[0], B.loc[0],'title', 'title', overlap_size=1)

# Print the blocking status
print(status)


