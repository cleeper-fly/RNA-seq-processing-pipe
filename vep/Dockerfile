FROM ensemblorg/ensembl-vep

ARG DEBIAN_FRONTEND=noninteractive

USER root

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    wget \
    curl \
    samtools

USER vep

RUN perl IMSTALL.pl \
    --AUTO fcp \
    --NO_UPDATE \
    --ASSEMBLY GRCh38 \
    --PLUGINSDIR /root/.vep/Plugins \
    --CACHEDIR /root/.vep/ \
    --PLUGINS all \
    --SPECIES homo_sapiense && \
    vep -id rs699 \
    -- cache \
    --nearest_symbol \
    -o 'STDOUT' \
    --no-stats \
    > /dev/null
