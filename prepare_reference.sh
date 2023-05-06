#!/bin/bash
docker compose run samtools bash -c 'samtools faidx /opt/seq_data/reference/GCA_000001405.15_GRCh38_genomic.fna'
docker compose run star bash -c 'STAR --runThreadN 4 --runMode genomeGenerate --genomeDir /opt/seq_data/reference --genomeFastaFiles /opt/seq_data/reference/GCA_000001405.15_GRCh38_genomic.fna --sjdbGTFfile /opt/seq_data/reference/gencode.v38.basic.annotation.gtf'
