# Useful Knowledge Graph Integration Tools

> This repository contains a collection of tools that implement specific tasks for data integration targeting knowledge graph structures.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
  - [API Wrapper](#api-wrapper)
  - [Parameters](#parameters)
- [List of Tools](#list-of-tools)
  - [Structure Transformation](#structure-transformation)
  - [Entity and Relation Extraction](#entity-and-relation-extraction)
  - [Schema and Entity Resolution](#schema-and-entity-resolution)
- [Directory Structure](#directory-structure)
- [Contributing](#contributing)
- [License](#license)

## Introduction

This repository contains a collection of tools designed to assist with data integration tasks aimed at constructing or manipulating knowledge graph structures. These tools cover various aspects of data integration, including structure transformation, entity and relation extraction, and schema and entity resolution.

## Installation

To get started with these tools, ensure you have [Python](https://www.python.org/downloads/) and [Docker](https://www.docker.com/get-started) installed on your system.

Clone the repository:

```bash
git clone https://github.com/vehnem/kg-tools.git
cd kg-tools
```

## Usage

We use Python and Docker to wrap each tool as a web service, enabling remote access to their capabilities from other projects.

```bash
# Example command to start the Blacksheep Application with Uvicorn, with automatic reload on file change
uvicorn server:app --port 8000 --reload
```


```bash
# Example request to run Stanford-OpenIE
curl "http://127.0.0.1:8000/run-openie?input=Barack%20Obama%20was%20born%20in%20Hawaii."
```

### API Wrapper

The `_api-wrapper` encapsulates the usage of individual tools into a web service. This allows you to call the tools remotely and integrate them into your data processing pipelines.

```bash
# Example command to start the API wrapper
python api_wrapper.py
```

### Parameters

Each tool may require different types of input data to function properly, including payloads/datasets, configuration files, and parameters. Please refer to the documentation of each tool for specific usage instructions.

## List of Tools

We categorize each tool based on its functionality. Tools with the `_` suffix are utilities with their codebase currently located directly in this repository.

### Structure Transformation

- **_data-util**: Utility functions for data manipulation and transformation.
- **rmlmapper**: A tool for mapping data to RDF using RML mappings.

### Entity and Relation Extraction

- **stanford-corenlp openie**: Open Information Extraction using Stanford CoreNLP.

### Schema and Entity Resolution

- **jedai**: A toolkit for entity resolution and data cleaning.
- **paris**: An algorithm for aligning ontologies and schemas.

## Directory Structure

- Tool binaries should be placed in `binaries/` or `bin/` directories.

## Contributing

Contributions are welcome! Please read our [contribution guidelines](CONTRIBUTING.md) for more details.

## License TODO

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
