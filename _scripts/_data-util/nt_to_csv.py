#!/usr/bin/env python3

from rdflib import Graph, URIRef, Literal
import pandas as pd
import argparse


ONTO = "http://www.okkam.org/ontology_restaurant1.owl#"


def short_name(uri):
    """
    Macht aus:
    http://www.okkam.org/oaie/restaurant1-Restaurant44

    -> Restaurant44
    """
    return str(uri).split("/")[-1]


def get_literal(graph, subject, predicate):
    """
    Holt String-Literal Werte
    """
    for obj in graph.objects(subject, URIRef(ONTO + predicate)):
        if isinstance(obj, Literal):
            return str(obj)

    return ""


def get_resource(graph, subject, predicate):
    """
    Holt URI Beziehungen
    """
    for obj in graph.objects(subject, URIRef(ONTO + predicate)):
        if isinstance(obj, URIRef):
            return obj

    return None


def extract_restaurants(nt_file, extended=False):

    g = Graph()

    print("Lade RDF...")
    g.parse(nt_file, format="nt")

    print(f"Tripel geladen: {len(g)}")


    restaurants = []


    # alle Restaurants finden
    for restaurant in g.subjects(
        URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        URIRef(ONTO + "Restaurant")
    ):

        row = {
            "restaurant": short_name(restaurant),
            "name": get_literal(g, restaurant, "name"),
            "phone_number": get_literal(g, restaurant, "phone_number"),
            "category": "",
            "street": "",
            "city": ""
        }

        if extended:
            category = get_resource(g, restaurant, "has_category")
            if category:
                row["category"] = get_literal(g, category, "name")
        else:
            row["category"] = get_literal(g, restaurant, "category")


        # Address auflösen
        address = get_resource(
            g,
            restaurant,
            "has_address"
        )


        if address:

            row["street"] = get_literal(
                g,
                address,
                "street"
            )

            if extended:
                row["city"] = get_literal(g, address, "city")
            else:
                city = get_resource(g, address, "is_in_city")

                if city:
                    row["city"] = get_literal(g, city, "name")


        restaurants.append(row)


    return restaurants



def main():

    parser = argparse.ArgumentParser(
        description="Convert restaurant RDF NT to CSV"
    )

    parser.add_argument(
        "input",
        help="input .nt file"
    )

    parser.add_argument(
        "output",
        help="output .csv file"
    )

    parser.add_argument(
        "--extended",
        action="store_true",
        help="Use extended restaurant ontology (Category entities, Address.city literal)"
    )

    args = parser.parse_args()


    data = extract_restaurants(args.input, args.extended)

    df = pd.DataFrame(data)

    df.to_csv(
        args.output,
        index=False,
        encoding="utf-8"
    )

    print(
        f"{len(df)} Restaurants geschrieben nach {args.output}"
    )


if __name__ == "__main__":
    main()