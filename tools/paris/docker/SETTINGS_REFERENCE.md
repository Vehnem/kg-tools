# Configuration Reference — PARIS settings.ini

Full documentation of every field in `settings.ini.example`, as consumed by `wrapper/paris.sh`.

## How the wrapper uses this file

`paris.sh settings.ini input1.nt input2.nt outputfolder` copies
`settings.ini` to a temporary file and appends four lines to it:

```
factstore1=input1.nt
factstore2=input2.nt
resultTSV=outputfolder
home=outputfolder
```

Since PARIS's ini parser (`Parameters.init`, in the bundled `javatools`
library) processes the file line by line and simply overwrites the map
entry for each key it encounters, the last occurrence of a key wins. Any
values for `factstore1`, `factstore2`, `resultTSV`, or `home` already
present in `settings.ini.example` are therefore always overridden by the
command-line arguments.

## Field reference

Extracted directly from the constructor `Setting(File ini)` in
`Setting.java`, one `Parameters.getX("<key>", <default>)` call per field.

| Field                          | Type   | Default                       | Meaning                                                                                                                                                                                    |
|--------------------------------|--------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `factstore1`                   | path   | — (required)                  | First knowledge base. An N-Triples file or a folder containing several. Always overridden by the wrapper's 2nd argument.                                                                   |
| `factstore2`                   | path   | — (required)                  | Second knowledge base. Always overridden by the wrapper's 3rd argument.                                                                                                                    |
| `resultTSV`                    | path   | — (required)                  | Folder where the output TSV files are written. Always overridden by the wrapper's 4th argument.                                                                                            |
| `home`                         | path   | — (required)                  | Folder where PARIS writes its run log (`run_<name>_<timestamp>.txt`). Always overridden by the wrapper's 4th argument (same value as `resultTSV`).                                         |
| `endIteration`                 | int    | `10`                          | Number of iterations. More iterations let the alignment converge further, especially for relations/classes, at the cost of runtime.                                                        |
| `nThreads`                     | int    | number of available CPU cores | Number of parallel threads.                                                                                                                                                                |
| `joinLengthLimit`              | int    | `1`                           | Maximum length of relation paths (joins) considered when comparing facts. Higher values catch indirect relationships but are substantially slower.                                         |
| `sumJoinLengthLimit`           | int    | `2 × joinLengthLimit`         | Combined join-length limit summed across both sides.                                                                                                                                       |
| `bothWays`                     | bool   | `true`                        | Align in both directions (KB1→KB2 and KB2→KB1).                                                                                                                                            |
| `takeMax`                      | bool   | `true`                        | Internal aggregation control for equality computation (not further documented in the source).                                                                                              |
| `takeMaxMax`                   | bool   | `true`                        | As above, an additional aggregation stage.                                                                                                                                                 |
| `lastPassThreshold`            | int    | `0`                           | Restrict the final pass to the n best candidates. `0` disables this.                                                                                                                       |
| `interestingnessThreshold`     | bool   | `false`                       | Use interestingness thresholds on neighborhoods to prune unpromising joins early (performance optimization).                                                                               |
| `useNewEqualityProduct`        | bool   | `false`                       | Use a newer variant of the equality-propagation formula instead of the classical formula from the PARIS paper (VLDB 2012).                                                                 |
| `matrixSubRelationStores`      | bool   | `true`                        | Use dense (matrix-based) storage for relation alignments — faster when the knowledge bases have few relations.                                                                             |
| `normalizeStrings`             | bool   | `false`                       | Lowercase and strip non-alphanumeric characters before comparing strings. **Must be set before the fact stores are generated** — it affects how the `.nt` files are read in.               |
| `normalizeDatesToYears`        | bool   | `false`                       | Reduce dates to years only, useful when one KB has full dates and the other only years. Also must be set before fact-store generation.                                                     |
| `shinglingSize`                | int    | `4`                           | k-gram size used for shingling-based literal string comparison.                                                                                                                            |
| `shinglingFunctions`           | int    | `30`                          | Number of hash functions (MinHash-style approximate string similarity).                                                                                                                    |
| `shinglingTableSize`           | int    | `10485760`                    | Hash table size for the shingling index.                                                                                                                                                   |
| `shinglingThreads`             | int    | `4`                           | Threads dedicated to shingling precomputation.                                                                                                                                             |
| `precomputeShinglings`         | bool   | `false`                       | Precompute shingles ahead of time.                                                                                                                                                         |
| `shinglingSquare`              | bool   | `true`                        | Internal shingling parameter (not further documented in the source).                                                                                                                       |
| `penalizeApproxMatches`        | double | `1.1`                         | Divisor applied to approximate literal matches to slightly penalize them relative to exact matches.                                                                                        |
| `noApproxIfExact`              | bool   | `true`                        | Skip approximate literal matching entirely when an exact match already exists.                                                                                                             |
| `parallelFileLoad`             | bool   | `true`                        | Load the two fact stores in parallel.                                                                                                                                                      |
| `smoothNumerator`              | double | `0.0`                         | Laplace-style smoothing numerator for functionality estimates during the main run.                                                                                                         |
| `smoothDenominator`            | double | `10.0`                        | Corresponding smoothing denominator.                                                                                                                                                       |
| `smoothNumeratorSampling`      | double | `0.0`                         | Same as `smoothNumerator`, but used during the entity-sampling phase (see `sampleEntities`).                                                                                               |
| `smoothDenominatorSampling`    | double | `1.0`                         | Same as `smoothDenominator`, for the sampling phase.                                                                                                                                       |
| `debugEntity`                  | string | `null` (unset)                | If set, print verbose debug output only for the entity matching this string.                                                                                                               |
| `reportInterval`               | int    | `5000`                        | Print progress every N processed entities.                                                                                                                                                 |
| `sampleEntities`               | int    | `0`                           | Number of entities sampled per iteration when searching for join-relation alignments. `0` disables sampling (process all entities). Useful on very large KBs to speed up early iterations. |
| `shuffleEntities`              | bool   | `true`                        | Shuffle entity processing order on each run.                                                                                                                                               |
| `cleverMatching`               | bool   | `false`                       | Internal control flag (not further documented in the source).                                                                                                                              |
| `postLiteralDistanceThreshold` | double | `0.78`                        | Similarity threshold literals must exceed to count as an approximate match.                                                                                                                |
| `allowLoops`                   | bool   | `false`                       | Allow join paths that lead back to the starting entity (`x2 == y2`).                                                                                                                       |
| `printNeighborhoodsSampling`   | bool   | `false`                       | Debug output of neighborhoods during sampling.                                                                                                                                             |
| `optimizeNoJoins`              | bool   | `true`                        | Use an optimized code path when `joinLengthLimit` effectively disables joins (faster).                                                                                                     |
| `joinThreshold`                | double | `Config.IOTA` (= `0.1`)       | Threshold controlling which joins are explored at all.                                                                                                                                     |
| `debugSampling`                | bool   | `false`                       | Debug output during sampling.                                                                                                                                                              |
| `literalDistance`              | string | `identity`                    | String-distance function for literal comparison used for negative evidence. Only `identity` or `shingling` are valid — see warning below.                                                  |

## Important: boolean parsing

`Parameters.getBoolean` does **not** check whether the value equals
`"true"`. It checks the value against a fixed "no" list and treats
**everything else** as `true`:

So `bothWays=true`, `bothWays=yes`, `bothWays=active`, and even
`bothWays=banana` all evaluate to `true`. Only the exact words
`inactive`, `off`, `false`, `no`, or `none` (case-insensitive) evaluate to
`false`. A typo like `flase` will silently be treated as `true` rather
than raising an error — double-check spelling on boolean fields.


## Design constants not exposed through settings.ini

`Config.java` hardcodes additional parameters directly in the code (some
`final`, some mutable `static` fields, but none of them reachable through
the ini file):

| Constant                     | Value           | Meaning                                                                                        |
|------------------------------|-----------------|------------------------------------------------------------------------------------------------|
| `treatIdAsRelation`          | `false`         | Treat entity IDs as an additional relation.                                                    |
| `literalDistanceForEquality` | `true` (final)  | Use `literalDistance` for equality computation as well, not only for penalization.             |
| `literalDistanceThreshold`   | `0.5` (final)   | Threshold above which literals are considered as a possible match.                             |
| `THETA`                      | `0.1` (final)   | Anything below this threshold is ignored.                                                      |
| `subAndSuper`                | `true` (final)  | Take both sub- and super-relations into account for equality computation.                      |
| `IOTA`                       | `= THETA`       | Initial small value assigned to all relations.                                                 |
| `iotaDependenceOnLength`     | `20`            | Makes the initial small value depend on relation length.                                       |
| `doComputeClasses`           | `true`          | Whether class alignments are computed.                                                         |
| `useSuffixes`                | `false` (final) | Use suffixes to infer entity types.                                                            |
| `epsilon`                    | `1.01`          | Breaks ties between multiple perfect matches.                                                  |
| `ignoreClasses`              | `true`          | Ignore classes when aligning entities (only used for class alignment itself).                  |
| `realNormalizer`             | `true`          | Use the corrected normalizer instead of the buggy PARIS 0.1 version.                           |
| `bothWayFunctionalities`     | `false`         | Use inverse functionality in addition to regular functionality.                                |
| `allLengthOneAfterSample`    | `true`          | After the sampling phase, explore all length-one relations regardless of their sampling score. |

Changing these requires modifying the Java source and rebuilding PARIS —
they cannot be changed via the released `paris_0_3.jar`.

## PARIS invocation modes (for context)

| Argument count   | Mode                                                                                                                                                 |
|------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1                | `settings.ini` file — either empty (PARIS interactively asks for the required fields and writes them into the file) or already populated (our case). |
| 2                | Dump mode: `<factstore> <dumpfile>` — writes all entities of a fact store to a file, no alignment performed.                                         |
| 3                | Fast track: `<kb1> <kb2> <outputfolder>` — alignment with pure default values, no configuration possible. This is "Usage 2" in `docker_help`.        |

`paris_wrapper.sh` always uses the 1-argument mode (detailed track),
since only that mode accepts a configuration file.

## Full example

See `example-settings.ini` — every field above is already present with a working PARIS default value 
(except the four path fields)