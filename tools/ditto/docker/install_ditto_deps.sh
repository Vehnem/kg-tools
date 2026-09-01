#!/usr/bin/env bash
#
# install_ditto_deps.sh <ditto_repo_dir>
# =======================================
# Installs Ditto's own Python dependencies into whatever `python`/`pip` is
# currently first on PATH - a venv when called from the Makefile, the
# container's system Python when called from the Dockerfile. This is the
# single place that knows how to work around the three issues in Ditto's
# own requirements.txt / README that a plain `pip install -r
# requirements.txt` does not handle:
#
#   1. requirements.txt pins `torch==1.9.0+cu111`, a CUDA-11.1-specific
#      wheel that is published only on PyTorch's own wheel index, never on
#      PyPI. `pip`/`uv` therefore always fail with "no version of
#      torch==1.9.0+cu111" / "No solution found", regardless of platform.
#      Fix: install a matching torch build from the correct index first,
#      then strip the pinned torch line before installing the rest.
#   2. Ditto needs NVIDIA's Apex (`from apex import amp` in matcher.py /
#      train_ditto.py) for `--fp16`. There is an unrelated, unmaintained
#      package also called `apex` on PyPI (a Pyramid web-session helper);
#      `pip install apex` installs that one by mistake and produces
#      `ImportError: cannot import name 'UnencryptedCookieSessionFactoryConfig'`.
#      Fix: never `pip install apex`; always build NVIDIA/apex from source.
#   3. Ditto's own README installs a spaCy model
#      (`python -m spacy download en_core_web_lg`) as part of setup. This
#      is required by ditto/knowledge.py's GeneralDKInjector
#      (optimizations.domain_knowledge.mode: general in ditto_config.yaml)
#      and is easy to miss since it is not in requirements.txt at all.
#   4. requirements.txt's spaCy stack (cymem, murmurhash, preshed, ...) is
#      old enough to have no pyproject.toml, so it is installed with
#      --no-build-isolation (see issue 3's rationale below). But pip
#      resolves/prepares sdist metadata for every requirement up front,
#      before installing any of them - so when preshed's setup.py runs
#      `cythonize(...)`, it tries `cimport cymem.cymem` /
#      `cimport murmurhash.mrmr` against packages that are not actually
#      installed into the environment yet, and fails with e.g.
#      "preshed/bloom.pxd:2:0: 'cymem/cymem.pxd' not found". requirements.txt's
#      own ordering does not help, because it is metadata *preparation*
#      that fails, not installation order.
#      Fix: install cymem and murmurhash (which have no such cimports
#      themselves) first, then preshed, before installing the rest.
#   5. apex's setup.py unconditionally calls get_cuda_bare_metal_version at
#      import time, regardless of which --*_ext flags are requested, purely
#      to print the CUDA version and pick a default TORCH_CUDA_ARCH_LIST. If
#      CUDA_HOME is None (no CUDA toolkit installed - the normal case for a
#      CPU-only build), that crashes with "TypeError: unsupported operand
#      type(s) for +: 'NoneType' and 'str'" instead of failing gracefully.
#      This is a long-standing, still-open upstream bug - see e.g.
#      https://github.com/NVIDIA/apex/issues/931,
#      https://github.com/NVIDIA/apex/issues/990,
#      https://github.com/NVIDIA/apex/pull/1610 (never merged).
#      Fix: for a --cpp_ext-only build (the default here), nvcc is never
#      actually invoked to compile anything, so we point CUDA_HOME at a
#      fake nvcc stub that only answers `-V` with a plausible version
#      string, letting setup.py's metadata preparation succeed.
#   6. apex's current master branch's setup.py itself now requires Python
#      3.10+: it has a top-level variable annotation `parallel: int | None
#      = None` (PEP 604 union syntax, part of a --parallel build-speed
#      option). On Python 3.7, `int | None` is evaluated eagerly (no
#      `from __future__ import annotations`) and raises "TypeError:
#      unsupported operand type(s) for |: 'type' and 'NoneType'" - apex has
#      no PyPI releases to fall back to a pin for. NVIDIA does tag commits
#      to match their NGC container releases (e.g. "23.05-devel"), though,
#      so we clone a fixed, older such tag instead of master.
#      Fix: `git clone --branch "${APEX_REF}"` a Python-3.7-era tag rather
#      than following master.
#
# Verified against https://github.com/megagonlabs/ditto (master) README,
# whose own install sequence is:
#   conda install -c conda-forge nvidia-apex
#   pip install -r requirements.txt
#   python -m spacy download en_core_web_lg
# This script reproduces that sequence for plain-pip environments (no
# conda available), in the same order.
set -euo pipefail

DITTO_HOME="${1:?Usage: install_ditto_deps.sh <ditto_repo_dir>}"

# requirements.txt pins torch==1.9.0+cu111, a CUDA-11.1-specific wheel that
# only ever existed on PyTorch's own wheel index, never on PyPI - so a plain
# `pip install -r requirements.txt` always fails with "no solution found",
# regardless of platform. On top of that, those specific 1.9.0 wheels are no
# longer reliably served by the legacy `-f .../torch_stable.html` listing
# either, and Python 3.7 itself caps which torch version is even available:
# PyTorch 2.0 raised its minimum supported Python version to 3.8 (dropping
# 3.7) - see https://github.com/pytorch/pytorch/issues/80513 - so the last
# torch release with Python-3.7 wheels is the 1.13.x series. So instead of
# fighting for the exact original 1.9.0 pin, this script installs the
# newest torch/torchvision/torchaudio trio that still supports Python 3.7,
# via PyTorch's modern --index-url mechanism (not the deprecated
# -f torch_stable.html one), then strips the old pinned torch line so the
# rest of requirements.txt installs normally.
TORCH_VERSION="${TORCH_VERSION:-1.13.1}"
TORCHVISION_VERSION="${TORCHVISION_VERSION:-0.14.1}"
TORCHAUDIO_VERSION="${TORCHAUDIO_VERSION:-0.13.1}"
# CPU by default: the reference Dockerfile's base image (python:3.7-slim)
# has no CUDA toolkit. For a CUDA build, override e.g.
# TORCH_INDEX_URL=https://download.pytorch.org/whl/cu117 (needs a matching
# CUDA-devel base image with nvcc - CUDA 11.1 wheels do not exist for
# torch 1.13.1; the closest official builds are cu116/cu117).
#TORCH_INDEX_URL="${TORCH_INDEX_URL:-https://download.pytorch.org/whl/cpu}"
TORCH_INDEX_URL=https://download.pytorch.org/whl/cu117

APEX_REPO_URL="${APEX_REPO_URL:-https://github.com/NVIDIA/apex.git}"
# apex's current master requires Python 3.10+ to even parse setup.py (see
# issue 6 above). "23.05-devel" is one of NVIDIA's NGC-container-matched
# tags (May 2023, torch/CUDA versions of that era) - old enough to predate
# the offending syntax, recent enough to still build against torch 1.13.1.
# Override if your torch/CUDA combination needs a different apex snapshot.
APEX_REF="${APEX_REF:-23.05-devel}"
# --cpp_ext only needs a C++ compiler (present via build-essential).
# --cuda_ext additionally needs nvcc matching the installed torch's CUDA
# build - only add it when TORCH_INDEX_URL points at a cuXXX index.
APEX_EXTENSIONS="${APEX_EXTENSIONS:---cpp_ext --cuda_ext}"

SPACY_MODEL="${SPACY_MODEL:-en_core_web_lg}"

echo ">>> [1/5] Removing any wrong PyPI 'apex' (name clash with NVIDIA/apex), if present"
pip uninstall -y apex >/dev/null 2>&1 || true

echo ">>> [2/5] Installing torch==${TORCH_VERSION} (+ matching torchvision/torchaudio) from ${TORCH_INDEX_URL}"
echo "    (requirements.txt's torch==1.9.0+cu111 pin no longer resolves; capped at 1.13.1 by Python 3.7 anyway)"
pip install --upgrade pip wheel
pip install --no-cache-dir \
    "torch==${TORCH_VERSION}" \
    "torchvision==${TORCHVISION_VERSION}" \
    "torchaudio==${TORCHAUDIO_VERSION}" \
    --index-url "${TORCH_INDEX_URL}"

echo ">>> [3/5] Installing setuptools/wheel/Cython pins needed to build the 2020-era sdists below"
echo "    gensim==3.8.1 (and other 2020-era deps in requirements.txt) ship no"
echo "    pyproject.toml; a fresh isolated build env for them can fail with"
echo "    'BackendUnavailable: Cannot import setuptools.build_meta', and very"
echo "    new setuptools releases have dropped legacy setup.py behaviour they"
echo "    rely on. Cython is pre-installed and pinned <3 since gensim 3.8.1's"
echo "    .pyx sources predate Cython 3's language_level default change."
pip install --no-cache-dir "setuptools<70" wheel "Cython<3"

echo ">>> [4/5] Pre-installing cymem + murmurhash, then preshed (spaCy's Cython build-order issue)"
echo "    preshed's setup.py cimports cymem.cymem / murmurhash.mrmr at build time; with"
echo "    --no-build-isolation those .pxd files must already be installed in this env when"
echo "    pip prepares preshed's metadata, which happens before pip installs anything from"
echo "    requirements.txt. Installing cymem/murmurhash (no such cimports themselves) first,"
echo "    then preshed on its own, avoids 'cymem/cymem.pxd not found' during cythonize."
for pkg in cymem murmurhash; do
  spec="$(grep -iE "^${pkg}([<>=~ ]|\$)" "${DITTO_HOME}/requirements.txt" | head -n1 || true)"
  pip install --no-cache-dir --no-build-isolation "${spec:-$pkg}"
done
preshed_spec="$(grep -iE '^preshed([<>=~ ]|$)' "${DITTO_HOME}/requirements.txt" | head -n1 || true)"
pip install --no-cache-dir --no-build-isolation "${preshed_spec:-preshed}"
# NOTE: if a later spaCy dependency (e.g. thinc, blis) fails the same way -
# "cimport ... not found" during its own metadata preparation - it needs the
# same treatment: add it to this pre-install block, installed *after* its
# own cimport'ed packages (cymem/murmurhash/preshed) are already in place.

echo ">>> [5/5] Installing the rest of Ditto's requirements.txt (torch/cymem/murmurhash/preshed stripped)"
grep -viE '^(torch|cymem|murmurhash|preshed)([<>=~ ]|$)' "${DITTO_HOME}/requirements.txt" > /tmp/ditto-requirements.rest.txt
pip install --no-cache-dir --no-build-isolation -r /tmp/ditto-requirements.rest.txt
rm -f /tmp/ditto-requirements.rest.txt

echo ">>> Building NVIDIA Apex from source (extensions: ${APEX_EXTENSIONS:-<python-only>})"
echo "    apex's setup.py unconditionally calls get_cuda_bare_metal_version(CUDA_HOME) at"
echo "    import time - regardless of which --*_ext flags are requested - just to print the"
echo "    version and pick a default TORCH_CUDA_ARCH_LIST. If CUDA_HOME is None (no CUDA"
echo "    toolkit installed, the normal case for a CPU-only build), that crashes with"
echo "    \"TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'\" instead of"
echo "    failing gracefully - a long-standing, still-open upstream bug (NVIDIA/apex#931,"
echo "    #990, #1610, #1822, ...). Since a --cpp_ext-only build (the default here) never"
echo "    actually invokes nvcc to compile anything, we work around it by pointing CUDA_HOME"
echo "    at a fake nvcc stub that just answers '-V' with a plausible version string."
if [[ "${APEX_EXTENSIONS}" != *"--cuda_ext"* ]] \
    && [ -z "${CUDA_HOME:-}" ] \
    && ! command -v nvcc >/dev/null 2>&1; then
  echo "    No real CUDA toolkit found and --cuda_ext not requested - using the fake nvcc stub"
  FAKE_CUDA_HOME="$(mktemp -d)/fake-cuda"
  mkdir -p "${FAKE_CUDA_HOME}/bin"
  cat > "${FAKE_CUDA_HOME}/bin/nvcc" <<'NVCC_STUB'
#!/usr/bin/env bash
# Fake nvcc: only ever asked for `-V` by apex's setup.py to read the CUDA
# version off stdout. Never actually invoked to compile anything in a
# --cpp_ext-only build.
cat <<'EOF'
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2023 NVIDIA Corporation
Built on Mon_Apr__3_17:16:06_PDT_2023
Cuda compilation tools, release 12.1, V12.1.105
Build cuda_12.1.r12.1/compiler.32688072_0
EOF
NVCC_STUB
  chmod +x "${FAKE_CUDA_HOME}/bin/nvcc"
  export CUDA_HOME="${FAKE_CUDA_HOME}"
elif [[ "${APEX_EXTENSIONS}" == *"--cuda_ext"* ]] && [ -z "${CUDA_HOME:-}" ] && ! command -v nvcc >/dev/null 2>&1; then
  echo "    WARNING: --cuda_ext was requested but no real CUDA toolkit / nvcc was found."
  echo "    Skipping the fake-nvcc workaround (it would only produce a broken build) -"
  echo "    install a real CUDA toolkit matching your torch build, or drop --cuda_ext."
fi

rm -rf /tmp/apex-build
git clone --depth 1 --branch "${APEX_REF}" "${APEX_REPO_URL}" /tmp/apex-build
(
  cd /tmp/apex-build
  CONFIG_SETTINGS_ARGS=()
  for ext in ${APEX_EXTENSIONS}; do
    CONFIG_SETTINGS_ARGS+=(--config-settings "--build-option=${ext}")
  done
  pip install -v --disable-pip-version-check --no-cache-dir --no-build-isolation \
    "${CONFIG_SETTINGS_ARGS[@]}" \
    ./
)
rm -rf /tmp/apex-build
[ -n "${FAKE_CUDA_HOME:-}" ] && rm -rf "$(dirname "${FAKE_CUDA_HOME}")"

pip install tensorboardX

echo ">>> Downloading the spaCy model Ditto's domain-knowledge injector needs (${SPACY_MODEL})"
python3 -m spacy download "${SPACY_MODEL}"

echo ">>> Downloading the NLTK stopwords corpus Ditto needs"
python3 -m nltk.downloader stopwords

echo ">>> Done."