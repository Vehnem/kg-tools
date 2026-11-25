#!/usr/bin/env bash
# run_logmap.sh — config-driven runner around the LogMap Java ontology matcher.
#
# Usage:
#   bash run_logmap.sh <ontology1> <ontology2> <output_dir> <config.conf> [reference.rdf]
#
# Without reference.rdf LogMap runs in MATCHER mode. With reference.rdf (OAEI
# RDF alignment format) it runs in EVALUATION mode and additionally writes
# <output_dir>/evaluation.csv. If the reference argument is empty or does not
# point to an existing file (e.g. an unset optional input of the KGpipe task),
# it is ignored and MATCHER mode is used.
#
# Requires bash >= 4 and LOGMAP_HOME pointing to a directory containing
# logmap-matcher.jar, java-dependencies/ and parameters.txt.
# All keys and values are documented in CONFIG_REFERENCE.md.

set -euo pipefail

fail() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*" >&2; }

if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
  echo "Usage: $0 <ontology1> <ontology2> <output_dir> <config.conf> [reference.rdf]" >&2
  exit 1
fi

ONTO1="$1"
ONTO2="$2"
OUTPUT_DIR="$3"
CONFIG_FILE="$4"
REFERENCE="${5:-}"

: "${LOGMAP_HOME:?LOGMAP_HOME must point to the directory with logmap-matcher.jar, java-dependencies/ and parameters.txt}"
JAR="${LOGMAP_HOME}/logmap-matcher.jar"
BASE_PARAMS="${LOGMAP_HOME}/parameters.txt"

[ -f "${ONTO1}" ] || fail "ontology1 not found or not a file: ${ONTO1}"
[ -f "${ONTO2}" ] || fail "ontology2 not found or not a file: ${ONTO2}"
[ -f "${CONFIG_FILE}" ] || fail "config not found or not a file: ${CONFIG_FILE}"
if [ -n "${REFERENCE}" ] && [ ! -f "${REFERENCE}" ]; then
  info "reference is not an existing file ('${REFERENCE}'), running in MATCHER mode without evaluation"
  REFERENCE=""
fi
[ -f "${JAR}" ] || fail "jar not found: ${JAR}"
[ -d "${LOGMAP_HOME}/java-dependencies" ] || fail "java-dependencies/ not found in ${LOGMAP_HOME}"
[ -f "${BASE_PARAMS}" ] || fail "parameters.txt not found: ${BASE_PARAMS}"

declare -A RUN_KEYS=(
  [classify]=bool
  [java_xms]=jmem
  [java_xmx]=jmem
  [entity_expansion_limit]=int
)

declare -A SCALAR_KEYS=(
  [print_output]=bool
  [bad_score_scope]=double
  [good_isub_anchors]=double
  [good_isub_candidates]=double
  [good_confidence]=double
  [good_sim_coocurrence]=double
  [min_conf_pro_map]=double
  [confidence_composed_mappings1]=double
  [confidence_composed_mappings2]=double
  [avoid_redundant_labels]=bool
  [use_stemming]=bool
  [max_redundancy_labels]=int
  [max_ambiguity]=int
  [good_ambiguity]=int
  [use_overlapping]=bool
  [min_size_overlapping]=int
  [output_class_mappings]=bool
  [property_matching]=bool
  [output_prop_mappings]=bool
  [instance_matching]=bool
  [output_instance_mappings]=bool
  [output_instance_mapping_files]=bool
  [reason_datatypes]=bool
  [reasoner]=string
  [perform_repair]=bool
  [glogal_info]=bool
  [timeout]=int
  [reverse_labels]=bool
  [output_equivalences_only]=bool
  [second_chance_conflicts]=bool
  [ratio_second_chance_discarded]=int
  [use_umls_lexicon]=bool
  [allow_bioportal]=bool
  [max_mediating_ontologies]=int
  [allow_interactivity]=bool
  [allow_multilingual]=bool
  [is_test_mode_multilingual]=bool
  [use_local_dict]=bool
  [call_online_translator]=bool
  [path_chinese_segmenter_dict]=string
  [path_multilingual_tmp]=string
  [path_multilingual_local]=string
  [path_mappings_categories]=string
  [target_lang]=string
  [translator_id]=int
  [restrict_individual_types]=bool
  [index_undeclared_abox_predicates]=bool
  [index_undeclared_abox_use_both_props]=bool
)

declare -A LIST_KEYS=(
  [annotation_URI]=1
  [category_URI]=1
  [data_assertion_URI_Indiv]=1
  [data_assertion_URI_Indiv_deep2]=1
  [object_assertion_URI_Indiv]=1
  [allowed_individual_type]=1
  [filter_entity]=1
)

check_type() {
  local key="$1" type="$2" value="$3"
  case "${type}" in
    bool)   [[ "${value}" == "true" || "${value}" == "false" ]] || fail "${key}: expected true|false, got '${value}'" ;;
    int)    [[ "${value}" =~ ^[0-9]+$ ]] || fail "${key}: expected non-negative integer, got '${value}'" ;;
    double) [[ "${value}" =~ ^[0-9]+(\.[0-9]+)?$ ]] || fail "${key}: expected non-negative decimal number, got '${value}'" ;;
    jmem)   [[ "${value}" =~ ^[0-9]+[kKmMgG]$ ]] || fail "${key}: expected JVM memory size like 500M or 8G, got '${value}'" ;;
    string) : ;;
  esac
}

trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "${s}"
}

declare -A RUN_VALUES=()
declare -A SCALAR_VALUES=()
declare -A LIST_VALUES=()

while IFS= read -r raw || [ -n "${raw}" ]; do
  raw="${raw%$'\r'}"
  line="$(trim "${raw}")"
  if [ -z "${line}" ] || [[ "${line}" == \#* ]]; then
    continue
  fi
  [[ "${line}" == *=* ]] || fail "invalid config line (expected key=value): ${line}"
  key="$(trim "${line%%=*}")"
  value="$(trim "${line#*=}")"
  [ -n "${value}" ] || fail "${key}: empty value (remove the line to use the default)"
  [[ "${value}" != *"|"* ]] || fail "${key}: value must not contain '|' (parameters.txt separator)"

  if [ -n "${RUN_KEYS[${key}]+x}" ]; then
    check_type "${key}" "${RUN_KEYS[${key}]}" "${value}"
    RUN_VALUES["${key}"]="${value}"
  elif [ -n "${SCALAR_KEYS[${key}]+x}" ]; then
    check_type "${key}" "${SCALAR_KEYS[${key}]}" "${value}"
    SCALAR_VALUES["${key}"]="${value}"
  elif [ -n "${LIST_KEYS[${key}]+x}" ]; then
    LIST_VALUES["${key}"]="${value}"
  else
    fail "unknown config key: ${key}"
  fi
done < "${CONFIG_FILE}"

[ -n "${RUN_VALUES[java_xmx]+x}" ] || fail "java_xmx is required in the config"
JAVA_XMS="${RUN_VALUES[java_xms]:-}"
JAVA_XMX="${RUN_VALUES[java_xmx]}"
ENTITY_LIMIT="${RUN_VALUES[entity_expansion_limit]:-}"
CLASSIFY="${RUN_VALUES[classify]:-true}"

if [ -n "${SCALAR_VALUES[reasoner]+x}" ]; then
  case "${SCALAR_VALUES[reasoner]}" in
    HermiT|ELK|Structural) ;;
    *) fail "reasoner: expected HermiT|ELK|Structural, got '${SCALAR_VALUES[reasoner]}'" ;;
  esac
fi

mkdir -p "${OUTPUT_DIR}"
OUTPUT_DIR="$(cd "${OUTPUT_DIR}" && pwd)"
ONTO1_ABS="$(cd "$(dirname "${ONTO1}")" && pwd)/$(basename "${ONTO1}")"
ONTO2_ABS="$(cd "$(dirname "${ONTO2}")" && pwd)/$(basename "${ONTO2}")"
if [ -n "${REFERENCE}" ]; then
  REFERENCE_ABS="$(cd "$(dirname "${REFERENCE}")" && pwd)/$(basename "${REFERENCE}")"
fi

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/logmap_XXXXXX")"
trap 'rm -rf "${WORKDIR}"' EXIT
cp "${BASE_PARAMS}" "${WORKDIR}/parameters.txt"

for key in "${!SCALAR_VALUES[@]}"; do
  grep -v -- "^${key}|" "${WORKDIR}/parameters.txt" > "${WORKDIR}/parameters.tmp" || true
  mv "${WORKDIR}/parameters.tmp" "${WORKDIR}/parameters.txt"
  printf '%s|%s\n' "${key}" "${SCALAR_VALUES[${key}]}" >> "${WORKDIR}/parameters.txt"
done

for key in "${!LIST_VALUES[@]}"; do
  grep -v -- "^${key}|" "${WORKDIR}/parameters.txt" > "${WORKDIR}/parameters.tmp" || true
  mv "${WORKDIR}/parameters.tmp" "${WORKDIR}/parameters.txt"
  IFS=',' read -r -a items <<< "${LIST_VALUES[${key}]}"
  for item in "${items[@]}"; do
    item="$(trim "${item}")"
    [ -n "${item}" ] && printf '%s|%s\n' "${key}" "${item}" >> "${WORKDIR}/parameters.txt"
  done
done

JAVA_ARGS=()
[ -n "${JAVA_XMS}" ] && JAVA_ARGS+=("-Xms${JAVA_XMS}")
JAVA_ARGS+=("-Xmx${JAVA_XMX}")
[ -n "${ENTITY_LIMIT}" ] && JAVA_ARGS+=("-DentityExpansionLimit=${ENTITY_LIMIT}")
JAVA_ARGS+=(
  "--add-opens=java.base/java.lang=ALL-UNNAMED"
  "-Duser.language=en"
  "-Duser.country=US"
  -jar "${JAR}"
)

if [ -n "${REFERENCE}" ]; then
  MODE="EVALUATION"
  LOGMAP_ARGS=(EVALUATION "file:${ONTO1_ABS}" "file:${ONTO2_ABS}" "${REFERENCE_ABS}" "${OUTPUT_DIR}/" "${CLASSIFY}")
else
  MODE="MATCHER"
  LOGMAP_ARGS=(MATCHER "file:${ONTO1_ABS}" "file:${ONTO2_ABS}" "${OUTPUT_DIR}/" "${CLASSIFY}")
fi

LOG_FILE="${OUTPUT_DIR}/logmap_stdout.log"
info "Running LogMap in ${MODE} mode"
info "Effective parameters.txt: ${WORKDIR}/parameters.txt"

(cd "${WORKDIR}" && java "${JAVA_ARGS[@]}" "${LOGMAP_ARGS[@]}") 2>&1 | tee "${LOG_FILE}" || true

if grep -q "LogMap 2 can operate as an ontology matching system" "${LOG_FILE}"; then
  fail "LogMap printed its usage text instead of running (the CLI swallows exceptions this way). See ${LOG_FILE}"
fi

[ -s "${OUTPUT_DIR}/logmap_mappings.rdf" ] || fail "expected output missing or empty: ${OUTPUT_DIR}/logmap_mappings.rdf (LogMap exits 0 on internal errors). See ${LOG_FILE}"
[ -e "${OUTPUT_DIR}/logmap_mappings.txt" ] || fail "expected output missing: ${OUTPUT_DIR}/logmap_mappings.txt (LogMap exits 0 on internal errors). See ${LOG_FILE}"
if [ ! -s "${OUTPUT_DIR}/logmap_mappings.txt" ]; then
  info "WARNING: LogMap finished but found 0 mappings (logmap_mappings.txt is empty). See ${LOG_FILE}"
fi

if [ "${MODE}" = "EVALUATION" ]; then
  scores="$(awk '/^Precision\tRecall\tF-score/ {getline; print; exit}' "${LOG_FILE}" | tr ',' '.')"
  [[ "${scores}" =~ ^[0-9.]+$'\t'[0-9.]+$'\t'[0-9.]+$ ]] || fail "could not parse Precision/Recall/F-score from ${LOG_FILE}"
  {
    echo "precision,recall,f1"
    printf '%s\n' "${scores}" | tr '\t' ','
  } > "${OUTPUT_DIR}/evaluation.csv"
  info "Wrote ${OUTPUT_DIR}/evaluation.csv"
fi

info "Done. $(wc -l < "${OUTPUT_DIR}/logmap_mappings.txt" | tr -d ' ') mappings in ${OUTPUT_DIR}/logmap_mappings.txt"