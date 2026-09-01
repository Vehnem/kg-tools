FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Build deps for compiling Python from source + original deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git build-essential wget ca-certificates \
        libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
        libsqlite3-dev libncurses5-dev libncursesw5-dev \
        xz-utils tk-dev libffi-dev liblzma-dev libgdbm-dev uuid-dev \
    && rm -rf /var/lib/apt/lists/*

# Build and install Python 3.7.7 from source
ARG PYTHON_VERSION=3.7.7
RUN wget -q https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz \
    && tar -xzf Python-${PYTHON_VERSION}.tgz \
    && cd Python-${PYTHON_VERSION} \
    && ./configure --enable-optimizations --with-ensurepip=install \
    && make -j"$(nproc)" \
    && make altinstall \
    && cd .. \
    && rm -rf Python-${PYTHON_VERSION} Python-${PYTHON_VERSION}.tgz \
    && ln -sf /usr/local/bin/python3.7 /usr/bin/python3 \
    && ln -sf /usr/local/bin/python3.7 /usr/bin/python \
    && ln -sf /usr/local/bin/pip3.7 /usr/bin/pip3 \
    && ln -sf /usr/local/bin/pip3.7 /usr/bin/pip

WORKDIR /wrapper

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir pyyaml

ARG DITTO_REPO_URL=https://github.com/megagonlabs/ditto.git
ARG DITTO_REF=master
ENV DITTO_HOME=/wrapper/ditto

ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu121
ARG APEX_EXTENSIONS="--cpp_ext --cuda_ext"
ENV TORCH_INDEX_URL=${TORCH_INDEX_URL}
ENV APEX_EXTENSIONS=${APEX_EXTENSIONS}

ARG TORCH_CUDA_ARCH_LIST=""
ENV TORCH_CUDA_ARCH_LIST=${TORCH_CUDA_ARCH_LIST}

COPY install_ditto_deps.sh .
RUN chmod +x install_ditto_deps.sh

RUN git clone --depth 1 --branch ${DITTO_REF} ${DITTO_REPO_URL} ${DITTO_HOME} \
    && ./install_ditto_deps.sh ${DITTO_HOME} \
    && rm -rf ${DITTO_HOME}/.git

COPY wrapper/run_ditto.py .
COPY wrapper/ditto.sh .
COPY config-example.yaml .

RUN chmod +x ditto.sh

ENTRYPOINT ["/bin/bash"]