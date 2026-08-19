#!/usr/bin/env bash
# Usage:
#   bash agreementmaker.sh settings.ini source.owl target.owl output.rdf
#
# Optional repair/reference alignment:
#   bash agreementmaker.sh settings.ini source.owl target.owl output.rdf input.rdf

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AML_JAR="${AML_JAR:-$SCRIPT_DIR/AgreementMakerLight.jar}"

SETTINGS="${1:-}"
SOURCE="${2:-}"
TARGET="${3:-}"
OUTPUT="${4:-}"
INPUT_ALIGNMENT="${5:-}"

if [[ -z "$SETTINGS" || -z "$SOURCE" || -z "$TARGET" || -z "$OUTPUT" ]]; then
    echo "Usage: $0 settings.ini source.owl target.owl output.rdf [input_alignment.rdf]" >&2
    exit 1
fi

if [[ ! -f "$SETTINGS" ]]; then
    echo "ERROR: settings.ini not found: $SETTINGS" >&2
    exit 1
fi

if [[ ! -f "$AML_JAR" ]]; then
    echo "ERROR: AgreementMakerLight.jar not found: $AML_JAR" >&2
    echo "Set AML_JAR=/path/to/AgreementMakerLight.jar to override it." >&2
    exit 1
fi


SETTINGS="$(cd "$(dirname "$SETTINGS")" && pwd)/$(basename "$SETTINGS")"
SOURCE="$(realpath "$SOURCE")"
TARGET="$(realpath "$TARGET")"
OUTPUT="$(realpath -m "$OUTPUT")"

if [[ -n "$INPUT_ALIGNMENT" ]]; then
    INPUT_ALIGNMENT="$(realpath "$INPUT_ALIGNMENT")"
fi

# AML expects its manual configuration at store/config.ini.
# Keep the original config.ini intact and restore it after the run.
STORE_DIR="$SCRIPT_DIR/store"
AML_CONFIG="$STORE_DIR/config.ini"
TMP_DIR="$(mktemp -d)"
BACKUP_CONFIG="$TMP_DIR/config.ini.backup"
TEMP_CONFIG="$TMP_DIR/config.ini"

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$STORE_DIR"

if [[ -f "$AML_CONFIG" ]]; then
    cp "$AML_CONFIG" "$BACKUP_CONFIG"
fi

restore_config() {
    if [[ -f "$BACKUP_CONFIG" ]]; then
        cp "$BACKUP_CONFIG" "$AML_CONFIG"
    else
        rm -f "$AML_CONFIG"
    fi
}
trap 'restore_config; cleanup' EXIT

# Copy the user configuration. The wrapper does not reinterpret AML settings:
# AML receives the original ini values unchanged.
cp "$SETTINGS" "$TEMP_CONFIG"
cp "$TEMP_CONFIG" "$AML_CONFIG"

# Optional wrapper metadata can be used to select the AML execution mode.
# If absent, automatic mode is used.
MODE="$(awk -F= '
    /^[[:space:]]*mode[[:space:]]*=/ {
        value=$2
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
        print tolower(value)
        exit
    }
' "$SETTINGS")"

MODE="${MODE:-auto}"

case "$MODE" in
    auto)
        MODE_ARGS=(-a)
        ;;
    manual)
        MODE_ARGS=(-m)
        ;;
    repair)
        if [[ -z "$INPUT_ALIGNMENT" ]]; then
            echo "ERROR: repair mode requires input_alignment.rdf as the 5th argument." >&2
            exit 1
        fi
        MODE_ARGS=(-i "$INPUT_ALIGNMENT" -r)
        ;;
    *)
        echo "ERROR: unsupported mode '$MODE'. Use auto, manual, or repair." >&2
        exit 1
        ;;
esac

CMD=(
    java
    -jar
    "$AML_JAR"
    -s "$SOURCE"
    -t "$TARGET"
    "${MODE_ARGS[@]}"
    -o "$OUTPUT"
)

echo "Running AgreementMakerLight:"
printf '  %q' "${CMD[@]}"
echo

"${CMD[@]}"
