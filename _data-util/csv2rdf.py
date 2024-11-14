import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF

def csv_to_rdf(csv_path, subject_column, base_uri="http://example.org/"):
    # Load the CSV data
    df = pd.read_csv(csv_path, delimiter='|', engine='python', na_filter=False, encoding='unicode_escape')
    
    # Initialize the RDF graph
    g = Graph()
    
    # Define a namespace for the RDF graph based on the base URI
    ns = Namespace(base_uri)
    
    # Iterate over rows in the DataFrame
    for _, row in df.iterrows():
        # Define the subject URI based on the subject column's value
        subject = URIRef(ns[str(row[subject_column])])
        
        # For each column (excluding the subject column), create a predicate-object pair
        for col in df.columns:
            if col != subject_column:
                predicate = URIRef(ns[col])
                # Add the triple to the graph, assuming each value is a Literal
                if row[col] != '' or row[col] != None:
                    g.add((subject, predicate, Literal(row[col])))
    
    return g

# Example usage
rdf_graph = csv_to_rdf('/home/marvin/workspace/data/matching/buy.csv', 'id', base_uri="http://example.org/")

# Optionally, save to an RDF file
rdf_graph.serialize(destination='/home/marvin/workspace/data/matching/buy.nt', format='ntriples')
