#!/bin/bash
# _scripts/gen_ci
# Generates a .gitlab-ci.yml, where every Tool gets a Job with Build & Test

set -e

OUTPUT=".gitlab-ci.yml"

echo "stages:" > "$OUTPUT"
echo "  - build_and_test" >> "$OUTPUT"
echo "" >> "$OUTPUT"

tools=()
for dir in */; do
  dirname="${dir%/}"
  first_char="${dirname:0:1}"
  if [[ "$first_char" != "_" && "$first_char" != "." && -d "$dirname" ]]; then
    tools+=("$dirname")
  fi
done

for tool in "${tools[@]}"; do
cat >> "$OUTPUT" <<EOF
$tool:
  stage: build_and_test
  image: docker:24.0.5
  script:
    - apk add --no-cache bash make
    - cd _scripts
    - echo "🔨 Building $tool"
    - bash build "$tool"
    - echo "🧪 Testing $tool"
    - bash test "$tool"
  artifacts:
    expire_in: 1 week

EOF
done

echo "Generated $OUTPUT with ${#tools[@]} tool jobs:"
printf ' - %s\n' "${tools[@]}"
