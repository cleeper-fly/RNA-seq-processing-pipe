#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"/seq_data/reference/hg38
wget https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.15_GRCh38/GCA_000001405.15_GRCh38_genomic.fna.gz
gunzip GCA_000001405.15_GRCh38_genomic.fna.gz
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_38/gencode.v38.basic.annotation.gtf.gz
gunzip gencode.v38.basic.annotation.gtf.gz
wget https://sourceforge.net/projects/rseqc/files/BED/Human_Homo_sapiens/hg38_GENCODE.v38.bed.gz
gunzip hg38_GENCODE.v38.bed.gz
cd ../
mkdir known_sites
cd known_sites
wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/hapmap_3.3.hg38.vcf.gz
gunzip hapmap_3.3.hg38.vcf.gz
wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/hapmap_3.3.hg38.vcf.gz.tbi
wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Homo_sapiens_assembly38.dbsnp138.vcf.idx
wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Homo_sapiens_assembly38.dbsnp138.vcf
wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Mills_and_1000G_gold_standard.indels.hg38.vcf.gz.tbi
wget https://storage.googleapis.com/genomics-public-data/resources/broad/hg38/v0/Mills_and_1000G_gold_standard.indels.hg38.vcf.gz
gunzip Mills_and_1000G_gold_standard.indels.hg38.vcf.gz
cd ../
mkdir rna_seq_model
cd rna_seq_model
curl https://storage.googleapis.com/deepvariant/models/DeepVariant/1.4.0/DeepVariant-inception_v3-1.4.0+data-rnaseq_standard/model.ckpt.data-00000-of-00001 > model.ckpt.data-00000-of-00001
curl https://storage.googleapis.com/deepvariant/models/DeepVariant/1.4.0/DeepVariant-inception_v3-1.4.0+data-rnaseq_standard/model.ckpt.example_info.json > model.ckpt.example_info.json
curl https://storage.googleapis.com/deepvariant/models/DeepVariant/1.4.0/DeepVariant-inception_v3-1.4.0+data-rnaseq_standard/model.ckpt.index > model.ckpt.index
curl https://storage.googleapis.com/deepvariant/models/DeepVariant/1.4.0/DeepVariant-inception_v3-1.4.0+data-rnaseq_standard/model.ckpt.meta > model.ckpt.meta

