#!/usr/bin/env python3
"""One-time migration: move root-level tool dirs into tools/<id>/ layout."""

import shutil
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

TOOL_SPECS = {
    "paris": {
        "name": "PARIS",
        "kind": ["docker_cli"],
        "categories": ["EntityResolution", "SchemaAlignment"],
        "status": "maintained",
        "description": "Ontology and schema alignment via probabilistic matching.",
        "upstream": {
            "url": "https://github.com/dig-team/PARIS",
            "license": "MIT",
        },
        "execution": {
            "docker": {
                "image": "kgt/paris",
                "tag": "latest",
                "entrypoint": ["bash", "paris.sh"],
            }
        },
        "ci": {"docker_build": True, "docker_test": True},
        "testdata": {
            "repo": "https://github.com/Vehnem/kg-testdata",
            "paths": ["_snippets/paris/"],
        },
        "kgpipe": {
            "task_refs": ["paris_entity_matching", "paris_exchange"],
        },
        "has_docker": True,
    },
    "corenlp": {
        "name": "Stanford CoreNLP",
        "kind": ["docker_cli"],
        "categories": ["InformationExtraction"],
        "status": "maintained",
        "description": "OpenIE and KBP extraction wrappers using Stanford CoreNLP.",
        "upstream": {
            "url": "https://stanfordnlp.github.io/CoreNLP/",
            "license": "GPL-3.0",
        },
        "execution": {
            "docker": {
                "image": "kgt/corenlp",
                "tag": "latest",
                "entrypoint": ["bash", "corenlp.sh"],
            }
        },
        "ci": {"docker_build": True, "docker_test": True},
        "testdata": {
            "repo": "https://github.com/Vehnem/kg-testdata",
            "paths": ["_snippets/corenlp/"],
        },
        "kgpipe": {
            "task_refs": [
                "corenlp_openie_extraction",
                "corenlp_exchange",
                "corenlp_kbp_extraction",
            ],
        },
        "has_docker": True,
    },
    "valentine": {
        "name": "Valentine",
        "kind": ["docker_cli"],
        "categories": ["SchemaAlignment"],
        "status": "maintained",
        "description": "Schema matching for tabular data.",
        "upstream": {
            "url": "https://github.com/delftdata/valentine",
            "license": "Apache-2.0",
        },
        "execution": {
            "docker": {
                "image": "kgt/valentine",
                "tag": "latest",
                "entrypoint": ["bash", "valentine.sh"],
            }
        },
        "ci": {"docker_build": True, "docker_test": True},
        "testdata": {
            "repo": "https://github.com/Vehnem/kg-testdata",
            "paths": ["_snippets/valentine/"],
        },
        "kgpipe": {
            "task_refs": ["valentine_csv_matching", "valentine_csv_matching_v2"],
        },
        "has_docker": True,
    },
    "pyjedai": {
        "name": "PyJedAI",
        "kind": ["docker_cli"],
        "categories": ["EntityResolution"],
        "status": "maintained",
        "description": "Entity resolution toolkit (Python JedAI).",
        "upstream": {
            "url": "https://github.com/AI-team-UoA/pyJedAI",
            "license": "Apache-2.0",
        },
        "execution": {
            "docker": {
                "image": "kgt/pyjedai",
                "tag": "latest",
                "entrypoint": ["bash", "pyjedai.sh"],
            }
        },
        "ci": {"docker_build": True, "docker_test": True},
        "kgpipe": {
            "task_refs": ["pyjedai_entity_matching", "pyjedai_entity_matching_v2"],
        },
        "has_docker": True,
    },
    "agreementmaker": {
        "name": "AgreementMakerLight",
        "kind": ["docker_cli"],
        "categories": ["SchemaAlignment"],
        "status": "maintained",
        "description": "Ontology matching with AgreementMakerLight.",
        "execution": {
            "docker": {
                "image": "kgt/agreementmaker",
                "tag": "latest",
                "entrypoint": ["bash", "agreementmaker.sh"],
            }
        },
        "ci": {"docker_build": True, "docker_test": False},
        "kgpipe": {"task_refs": ["agreementmaker_ontology_matching"]},
        "has_docker": True,
    },
    "dbpedia-spotlight": {
        "name": "DBpedia Spotlight",
        "kind": ["docker_cli"],
        "categories": ["EntityLinking"],
        "status": "maintained",
        "description": "Entity linking service for DBpedia.",
        "upstream": {
            "url": "https://github.com/dbpedia-spotlight/dbpedia-spotlight",
            "license": "Apache-2.0",
        },
        "execution": {
            "docker": {
                "image": "kgt/dbpedia-spotlight",
                "tag": "latest",
            }
        },
        "ci": {"docker_build": True, "docker_test": False},
        "kgpipe": {
            "task_refs": [
                "dbpedia_spotlight_ner_nel",
                "dbpedia_spotlight_exchange",
            ],
        },
        "has_docker": True,
    },
    "pellet": {
        "name": "Pellet",
        "kind": ["docker_cli"],
        "categories": ["ReasoningValidation"],
        "status": "maintained",
        "description": "OWL DL reasoner for consistency checking.",
        "execution": {
            "docker": {"image": "kgt/pellet", "tag": "latest"},
        },
        "ci": {"docker_build": False, "docker_test": False},
        "has_docker": True,
    },
    "flora": {
        "name": "FLORA",
        "kind": ["docker_cli"],
        "categories": ["EntityResolution"],
        "status": "experimental",
        "execution": {
            "docker": {
                "image": "kgt/flora",
                "tag": "latest",
                "entrypoint": ["bash", "flora.sh"],
            }
        },
        "ci": {"docker_build": True, "docker_test": False},
        "has_docker": True,
        "source_dir": "FLORA",
    },
    "falcon": {
        "name": "FALCON",
        "kind": ["docker_api"],
        "categories": ["EntityLinking"],
        "status": "experimental",
        "description": "Entity linking via FALCON 2.0.",
        "upstream": {
            "url": "https://github.com/SDM-TIB/falcon2.0",
            "license": "MIT",
        },
        "execution": {
            "docker": {"image": "kgt/falcon", "tag": "latest"},
        },
        "ci": {"docker_build": True, "docker_test": False},
        "kgpipe": {"task_refs": ["falcon_ner_nel_rl", "falcon_exchange"]},
        "has_docker": True,
    },
    "stanford-openie": {
        "name": "Stanford OpenIE",
        "kind": ["docker_cli"],
        "categories": ["InformationExtraction"],
        "status": "deprecated",
        "description": "Legacy OpenIE wrapper; prefer corenlp.",
        "execution": {
            "docker": {"image": "kgt/stanford-openie", "tag": "latest"},
        },
        "ci": {"docker_build": True, "docker_test": False},
        "has_docker": True,
    },
    "limes": {
        "name": "LIMES",
        "kind": ["visualization", "docker_cli"],
        "categories": ["SchemaAlignment", "Visualization"],
        "status": "experimental",
        "description": "Link discovery and schema matching.",
        "execution": {
            "docker": {"image": "kgt/limes", "tag": "latest"},
        },
        "ci": {"docker_build": False, "docker_test": False},
        "has_docker": True,
    },
    "rebel": {
        "name": "REBEL",
        "kind": ["docker_cli"],
        "categories": ["InformationExtraction"],
        "status": "experimental",
        "description": "Relation extraction using REBEL.",
        "execution": {
            "docker": {"image": "kgt/rebel", "tag": "latest"},
        },
        "ci": {"docker_build": False, "docker_test": False},
        "kgpipe": {"task_refs": ["rebel_extraction"]},
        "has_docker": True,
    },
    "rdfunit": {
        "name": "RDFUnit",
        "kind": ["docker_cli"],
        "categories": ["ReasoningValidation"],
        "status": "experimental",
        "description": "RDF data quality assessment.",
        "execution": {
            "docker": {"image": "kgt/rdfunit", "tag": "latest"},
        },
        "ci": {"docker_build": False, "docker_test": False},
        "has_docker": True,
    },
    "rmlmapper": {
        "name": "RMLMapper",
        "kind": ["docker_cli"],
        "categories": ["StructureTransformation"],
        "status": "experimental",
        "description": "RML mapping to RDF.",
        "execution": {
            "docker": {"image": "kgt/rmlmapper", "tag": "latest"},
        },
        "ci": {"docker_build": False, "docker_test": False},
        "has_docker": True,
    },
    "rel": {
        "name": "REL",
        "kind": ["docker_cli"],
        "categories": ["EntityLinking"],
        "status": "experimental",
        "execution": {
            "docker": {"image": "kgt/rel", "tag": "latest"},
        },
        "ci": {"docker_build": False, "docker_test": False},
        "has_docker": True,
    },
    "magellan": {
        "name": "Magellan",
        "kind": ["python_package"],
        "categories": ["EntityResolution"],
        "status": "experimental",
        "description": "Data integration and matching toolkit.",
        "ci": {"docker_build": False, "docker_test": False},
        "has_docker": False,
    },
    "jedai": {
        "name": "JedAI",
        "kind": ["python_package"],
        "categories": ["EntityResolution"],
        "status": "deprecated",
        "description": "Legacy JedAI scripts; prefer pyjedai.",
        "ci": {"docker_build": False, "docker_test": False},
        "has_docker": False,
    },
    "dedup": {
        "name": "Dedup",
        "kind": ["dataset_utility"],
        "categories": ["EntityResolution", "DatasetUtility"],
        "status": "experimental",
        "description": "Deduplication utility scripts.",
        "ci": {"docker_build": False, "docker_test": False},
        "has_docker": False,
    },
    "deepmatcher": {
        "name": "DeepMatcher",
        "kind": ["python_package"],
        "categories": ["EntityResolution"],
        "status": "experimental",
        "description": "Deep learning entity matching (documentation stub).",
        "ci": {"docker_build": False, "docker_test": False},
        "has_docker": False,
    },
    "karma": {
        "name": "Karma",
        "kind": ["python_package"],
        "categories": ["StructureTransformation"],
        "status": "experimental",
        "description": "Wrapper placeholder for Web-Karma.",
        "ci": {"docker_build": False, "docker_test": False},
        "has_docker": False,
    },
}


def write_manifest(tool_dir, spec):
    manifest = {k: v for k, v in spec.items() if k not in ("has_docker", "source_dir")}
    manifest["id"] = tool_dir.name
    with open(str(tool_dir / "tool.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False, allow_unicode=True)


def migrate_tool(tool_id, spec):
    src = REPO_ROOT / spec.get("source_dir", tool_id)
    if not src.is_dir():
        print("Skip missing: {}".format(tool_id))
        return

    dest = REPO_ROOT / "tools" / tool_id
    if dest.exists():
        print("Already migrated: {}".format(tool_id))
        return

    dest.mkdir(parents=True)

    if spec.get("has_docker"):
        docker_dest = dest / "docker"
        docker_dest.mkdir()
        for item in src.iterdir():
            if item.name == "README.md":
                shutil.move(str(item), str(dest / "README.md"))
            else:
                shutil.move(str(item), str(docker_dest / item.name))
    else:
        for item in src.iterdir():
            shutil.move(str(item), str(dest / item.name))

    if not (dest / "README.md").exists():
        with open(str(dest / "README.md"), "w", encoding="utf-8") as f:
            f.write("# {}\n\nSee tool.yaml for catalog metadata.\n".format(spec["name"]))

    write_manifest(dest, spec)
    if src.exists():
        shutil.rmtree(str(src))
    print("Migrated: {}".format(tool_id))


def main():
    (REPO_ROOT / "tools").mkdir(exist_ok=True)
    for tool_id, spec in TOOL_SPECS.items():
        migrate_tool(tool_id, spec)


if __name__ == "__main__":
    main()
