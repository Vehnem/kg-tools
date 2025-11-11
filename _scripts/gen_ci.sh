#!/bin/bash
# _scripts/gen_ci
# Generates a .gitlab-ci.yml, where every Tool gets a Job with Build & Test

set -e

OUTPUT=".gitlab-ci.yml"

echo "stages:" > "$OUTPUT"
echo "  - build_and_test" >> "$OUTPUT"
echo "" >> "$OUTPUT"

#tools=()
#for dir in */; do
#  dirname="${dir%/}"
#  first_char="${dirname:0:1}"
#  if [[ "$first_char" != "_" && "$first_char" != "." && -d "$dirname" ]]; then
#    tools+=("$dirname")
#  fi
#done

tools=("paris" "valentine" "pyjedai" "corenlp")

for tool in "${tools[@]}"; do
pkgs="bash make"
pkg_file="$tool/.packages"
  if [[ -f "$pkg_file" ]]; then
      extra=$(<"$pkg_file")
      pkgs="$pkgs $extra"
  fi
cat >> "$OUTPUT" <<EOF
$tool:
  stage: build_and_test
  image: docker:24.0.5
  script:
    - apk add --no-cache $pkgs
    - cd _scripts
    - echo "🔨 Building $tool"
    - bash build "$tool"
    - echo "🧪 Testing $tool"
    - bash test "$tool"
    - echo "Pushing to registry"
    - docker tag kgt/$tool 127.0.0.1:5000/kgt/$tool
    - docker push 127.0.0.1:5000/kgt/$tool
  rules:
    - changes:
        - $tool/**/*
        - _scripts/**/*

EOF
done

echo "Generated $OUTPUT with ${#tools[@]} tool jobs:"
printf ' - %s\n' "${tools[@]}"
