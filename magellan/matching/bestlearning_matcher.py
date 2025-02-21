import py_entitymatching as em
import os
import pandas as pd

# Set the seed value
seed = 0

current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the paths of the input tables
path_A = os.path.join(current_dir, '../bin/dblp_demo.csv')
path_B = os.path.join(current_dir, '../bin/acm_demo.csv')
path_labeled_data = os.path.join(current_dir, '../bin/labeled_data_demo.csv')

# Read the CSV files and set 'id' as the key attribute
A = em.read_csv_metadata(path_A, key='id')
B = em.read_csv_metadata(path_B, key='id')

# Load the pre-labeled data
S = em.read_csv_metadata(path_labeled_data,
                         key='_id',
                         ltable=A, rtable=B,
                         fk_ltable='ltable_id', fk_rtable='rtable_id')


# Split S into I an J
IJ = em.split_train_test(S, train_proportion=0.5, random_state=0)
I = IJ['train']
J = IJ['test']


# Create a set of ML-matchers
dt = em.DTMatcher(name='DecisionTree', random_state=0)
svm = em.SVMMatcher(name='SVM', random_state=0)
rf = em.RFMatcher(name='RF', random_state=0)
lg = em.LogRegMatcher(name='LogReg', random_state=0)
ln = em.LinRegMatcher(name='LinReg')

# Generate a set of features
F = em.get_features_for_matching(A, B, validate_inferred_attr_types=False)

# Convert the I into a set of feature vectors using F
H = em.extract_feature_vecs(I,
                            feature_table=F,
                            attrs_after='label',
                            show_progress=False)

# Impute feature vectors with the mean of the column values.

H = em.impute_table(H,
                exclude_attrs=['_id', 'ltable_id', 'rtable_id', 'label'],
                strategy='mean')


# Select the best ML matcher using CrossValidation
result = em.select_matcher([dt, rf, svm, ln, lg], table=H,
        exclude_attrs=['_id', 'ltable_id', 'rtable_id', 'label'],
        k=5,
        target_attr='label', metric_to_select_matcher='f1', random_state=0)
print(result['cv_stats'])
print(result['drill_down_cv_stats']['precision'])
#result['drill_down_cv_stats']['recall']
#result['drill_down_cv_stats']['f1']



#Debug X Random Forest
# Split H into P and Q
PQ = em.split_train_test(H, train_proportion=0.5, random_state=0)
P = PQ['train']
Q = PQ['test']


# Debug RF matcher using GUI
em.vis_debug_rf(rf, P, Q,
        exclude_attrs=['_id', 'ltable_id', 'rtable_id', 'label'],
        target_attr='label')



# Add a feature to do Jaccard on title + authors and add it to F

# Create a feature declaratively
sim = em.get_sim_funs_for_matching()
tok = em.get_tokenizers_for_matching()
feature_string = """jaccard(wspace((ltuple['title'] + ' ' + ltuple['authors']).lower()), 
                            wspace((rtuple['title'] + ' ' + rtuple['authors']).lower()))"""
feature = em.get_feature_fn(feature_string, sim, tok)

# Add feature to F
em.add_feature(F, 'jac_ws_title_authors', feature)

# Convert I into feature vectors using updated F
H = em.extract_feature_vecs(I,
                            feature_table=F,
                            attrs_after='label',
                            show_progress=False)



# Check whether the updated F improves X (Random Forest)
result = em.select_matcher([rf], table=H,
        exclude_attrs=['_id', 'ltable_id', 'rtable_id', 'label'],
        k=5,
        target_attr='label', metric_to_select_matcher='f1', random_state=0)
print(result['drill_down_cv_stats']['f1'])


# Select the best matcher again using CV
result = em.select_matcher([dt, rf, svm, ln, lg], table=H,
        exclude_attrs=['_id', 'ltable_id', 'rtable_id', 'label'],
        k=5,
        target_attr='label', metric_to_select_matcher='f1', random_state=0)
print(result['cv_stats'])
print(result['drill_down_cv_stats']['precision'])
#result['drill_down_cv_stats']['recall']
#result['drill_down_cv_stats']['f1']



