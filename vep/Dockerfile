FROM ensemblorg/ensembl-vep

ARG DEBIAN_FRONTEND=noninteractive

USER root

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    wget \
    curl

#muted for testing
#RUN curl -O http://ftp.ensembl.org/pub/release-106/variation/indexed_vep_cache/homo_sapiens_vep_106_GRCh38.tar.gz
#RUN tar xzf homo_sapiens_vep_106_GRCh38.tar.gz

ENTRYPOINT ./vep