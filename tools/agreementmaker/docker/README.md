# AgreementMakerLight Pipeline

Configurable ontology alignment using AgreementMakerLight (AML), driven by
AML's native `settings.ini` / `store/config.ini` configuration.

## Repository layout

```text
.
├── Dockerfile
├── example-settings.ini
├── Makefile
├── README.md
├── SETTINGS_REFERENCE.md
└── wrapper
    └── agreementmaker.sh
```

| File                        | Purpose                                                                                                                                                  |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Dockerfile`                | Builds a minimal image containing AML plus the wrapper script (multi-stage build, no extra download tooling in the final image).                         |
| `Makefile`                  | Automates local setup/test and the Docker build/test workflow (see below).                                                                               |
| `example-settings.ini`      | Example configuration file. AML-specific settings belong here.                                                                                           |
| `SETTINGS_REFERENCE.md`     | Reference listing every setting, its allowed values, and what each value means.                                                                          |
| `wrapper/agreementmaker.sh` | Shell wrapper around `AgreementMakerLight.jar`; copies the supplied settings file to `store/config.ini` and adds the source/target/output CLI arguments. |

`AgreementMakerLight.jar` itself is not part of the repository — it is
downloaded either by `make download` (local use) or during the Docker build.

## Requirements

**Local use:**
- Java
- Bash
- `wget`, `unzip`

**Docker use:**
- Docker only — Java and the JAR are already inside the image.

The wrapper does not require Python, YAML, or any additional configuration
parser.

## Using the Makefile

The `Makefile` covers both the local and the Docker-based workflow.

| Target              | What it does                                                                                                                                              |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `make download`     | Downloads and unpacks AML into `bin/AML_v3.2/` and copies `wrapper/agreementmaker.sh` next to the JAR.                                                    |
| `make test`         | Copies test data (`source.rdf`, `target.rdf`, `settings.ini`) from `$KG_TESTDATA` into `bin/AML_v3.2/` and runs the wrapper, writing `target/output.rdf`. |
| `make all`          | Runs `download` followed by `test`.                                                                                                                       |
| `make clean`        | Removes `bin/` and `target/`.                                                                                                                             |
| `make docker_build` | Builds the Docker image as `kgt/agreementmaker:latest`.                                                                                                   |
| `make docker_test`  | Copies test data into `target/`, mounts it into the container, and runs the wrapper inside the image, writing `target/output2.rdf`.                       |
| `make docker_help`  | Prints example `docker run` invocations for auto and repair mode.                                                                                         |

`KG_TESTDATA` defaults to `$HOME/kg-testdata` and can be overridden, e.g.:

```bash
make test KG_TESTDATA=/path/to/testdata
```

### Local quickstart via Makefile

```bash
make download   # fetches AML into bin/AML_v3.2/
make test       # runs a match using $KG_TESTDATA test fixtures
```

### Docker quickstart via Makefile

```bash
make docker_build
make docker_test
```

## Using the Dockerfile directly

The image is built as a two-stage build: a `builder` stage downloads and
unpacks the AML release, and the final stage (based on a slim Java 8 JRE
Alpine image) only contains the unpacked AML files, the wrapper script,
`bash`, and `coreutils` (needed for GNU `realpath -m`, which the wrapper
relies on).

Build:

```bash
docker build -t kgt/agreementmaker:latest .
```

Run automatic matching, mounting a local directory with your input files as
`/data`:

```bash
docker run --rm -v "$(pwd)":/data kgt/agreementmaker:latest \
  bash agreementmaker.sh /data/settings.ini /data/source.owl /data/target.owl /data/output.rdf
```

Run repair mode:

```bash
docker run --rm -v "$(pwd)":/data kgt/agreementmaker:latest \
  bash agreementmaker.sh /data/settings.ini /data/source.owl /data/target.owl /data/output.rdf /data/input.rdf
```

(`make docker_help` prints these two examples as well.)

## Running the wrapper manually (without Docker or Make)

Make the wrapper executable:

```bash
chmod +x wrapper/agreementmaker.sh
```

Run automatic matching:

```bash
bash wrapper/agreementmaker.sh   example-settings.ini   path/to/source.owl   path/to/target.owl   path/to/alignment.rdf
```

Equivalent AML command:

```bash
java -jar AgreementMakerLight.jar   -s path/to/source.owl   -t path/to/target.owl   -a   -o path/to/alignment.rdf
```

This requires `AgreementMakerLight.jar` to be present next to
`agreementmaker.sh` (as it is after `make download`, or inside the Docker
image), or `AML_JAR` to point at it explicitly (see below).

## Using your own settings

Copy the example:

```bash
cp example-settings.ini my-settings.ini
```

Put the AML configuration supported by your exact AML release into
`my-settings.ini`. See `SETTINGS_REFERENCE.md` for the meaning of each
setting.

Then:

```bash
bash wrapper/agreementmaker.sh   my-settings.ini   path/to/source.owl   path/to/target.owl   path/to/alignment.rdf
```

The wrapper copies the settings to:

```text
store/config.ini
```

before starting AML.

## Manual mode

Set:

```ini
mode=manual
```

Then run:

```bash
bash wrapper/agreementmaker.sh   my-settings.ini   source.owl   target.owl   alignment.rdf
```

The wrapper executes AML with:

```text
-m
```

AML therefore uses the matcher configuration from:

```text
store/config.ini
```

## Repair mode

Set:

```ini
mode=repair
```

Then provide the existing alignment as the fifth argument:

```bash
bash wrapper/agreementmaker.sh   my-settings.ini   source.owl   target.owl   repaired.rdf   existing-alignment.rdf
```

The wrapper executes:

```bash
java -jar AgreementMakerLight.jar   -s source.owl   -t target.owl   -i existing-alignment.rdf   -r   -o repaired.rdf
```

## Configuration model

There is exactly one AML settings source:

```text
settings.ini
```

The wrapper temporarily installs it as:

```text
store/config.ini
```

The source/target/output paths and execution mode are supplied separately
because they are AML CLI parameters, not matcher configuration.

Conceptually:

```text
                         +----------------------+
settings.ini ------------> store/config.ini    |
                         +----------+-----------+
                                    |
                                    v
source.owl ----------------------> AML
target.owl ----------------------> AML
output.rdf ----------------------> AML
input.rdf -----------------------> AML (repair only)
mode=auto/manual/repair ----------> -a/-m/-r
```

## Existing `store/config.ini`

If `store/config.ini` already exists, the wrapper creates a temporary backup
before replacing it.

After AML exits, the original configuration is restored.

This means the repository (or the Docker image) can keep a persistent
default `store/config.ini` without permanently modifying it for every run.

## AML JAR location

By default the wrapper expects:

```text
AgreementMakerLight.jar
```

next to `agreementmaker.sh`. This is where `make download` places it
(`bin/AML_v3.2/`) and where the Dockerfile places it (`/app/AML_v3.2/`).

A different location can be selected with:

```bash
AML_JAR=/path/to/AgreementMakerLight.jar bash wrapper/agreementmaker.sh settings.ini source.owl target.owl output.rdf
```

## Important

`example-settings.ini` deliberately does not attempt to invent a complete
AML configuration schema.

Use the `config.ini` shipped with your exact AML release as the authoritative
source for AML-specific settings. Copy those settings into
`example-settings.ini` or your own settings file.

The wrapper passes AML settings through unchanged.

## Usage summary

Automatic:

```bash
bash wrapper/agreementmaker.sh settings.ini source.owl target.owl output.rdf
```

Manual:

```ini
mode=manual
```

```bash
bash wrapper/agreementmaker.sh settings.ini source.owl target.owl output.rdf
```

Repair:

```ini
mode=repair
```

```bash
bash wrapper/agreementmaker.sh settings.ini source.owl target.owl repaired.rdf input.rdf
```

## Background: how settings relate to AML's internal matchers

AML does not expose one INI switch per internal Java matcher class. Instead,
the settings in `SETTINGS_REFERENCE.md` (`word_matcher`, `string_matcher`,
`struct_matcher`, `bk_sources`, `match_properties`, `selection_type`,
`repair_alignment`, ...) each configure a *stage* of AML's matching
pipeline. AML itself decides, within that stage, which concrete internal
matchers to run.

Simplified pipeline view:

```text
                    AgreementMakerLight
                           |
                    Profiling / Config
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
     Lexicon         RelationshipMap       ValueMap
        |                  |                  |
   +----+----+        +----+----+        +----+----+
   |         |        |         |        |         |
   v         v        v         v        v         v
Lexical    Word     Neighbor  Block    Value   ValueString
String     etc.     Similarity Rematch  etc.     etc.
Mediating
WordNet
Thesaurus
Acronym
...
                          |
                       Selection
                          |
                        Repair
                          |
                       Alignment
```

### Matchers operating on the Lexicon

Controlled indirectly via `word_matcher`, `string_matcher`, `string_measure`,
and `bk_sources`:

- LexicalMatcher
- SpacelessLexicalMatcher
- WordMatcher
- StringMatcher
- MediatingMatcher
- MediatingXRefMatcher
- WordNetMatcher
- BackgroundKnowledgeMatcher
- ThesaurusMatcher
- AcronymMatcher
- HybridStringMatcher
- MultiWordMatcher

### Matchers operating on the RelationshipMap

Controlled indirectly via `struct_matcher`:

- NeighborSimilarityMatcher
- BlockRematcher
- InstanceBasedClassMatcher

### Matchers operating on the ValueMap

Not directly exposed by any setting in this pipeline's `config.ini`:

- ValueMatcher
- ValueStringMatcher
- Value2LexiconMatcher
- ProcessMatcher

### Example: overriding automatic profiling

Instead of full automatic mode, individual pipeline stages can be
overridden while leaving others on `auto`:

```ini
word_matcher=by_name
string_matcher=local
string_measure=Jaro-Winkler
struct_matcher=ancestors
match_properties=true
selection_type=hybrid
repair_alignment=true
bk_sources=none
use_translator=false
```

### Limits of this configuration file

There is no way, using only these settings, to run a single specific
internal matcher (e.g. "only `WordMatcher`, everything else disabled").
Setting every other stage to `none`/`false` reduces AML's overall pipeline,
but does not guarantee that AML executes exactly one named Java class —
AML still composes the pipeline internally based on profile and
configuration. Targeting one specific matcher class requires using the AML
Java API directly instead of the CLI/wrapper.