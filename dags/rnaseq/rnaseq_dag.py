import os
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.docker_operator import DockerOperator
from docker.types import Mount

from scripts.helpers import FilenamesCollector, ParametersCollector


with DAG(
    dag_id='rnaseq_dag',
    schedule_interval=None,
    start_date=datetime(1970, 5, 5),
    tags=['pipeline']
) as dag:

    filenames_collector = FilenamesCollector()
    DAG_PARAMETERS = ParametersCollector().parse_parameters_json()

    DAG_FILENAMES = {
        'base_name': filenames_collector.get_base_filename(),
        'reference': filenames_collector.get_reference_filename(),
        'reference_bed': filenames_collector.get_annotation_bed(),
        'reference_gtf': filenames_collector.get_annotation_gtf(),
        'fastq_1': filenames_collector.get_fastqs()[0],
        'fastq_2': filenames_collector.get_fastqs()[1],
    }
    cores = os.cpu_count()

    fastqc = DockerOperator(
        task_id="fastqc",
        image="staphb/fastqc",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'mkdir -p /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/quality && '
                f'fastqc /opt/seq_data/reads/{DAG_FILENAMES["fastq_1"]} --outdir /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/quality/ && '
                f'fastqc /opt/seq_data/reads/{DAG_FILENAMES["fastq_2"]} --outdir /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/quality/ \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    alignment = DockerOperator(
        task_id="alignment",
        image="rna-seq-pipeline_star",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'mkdir -p /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment && '
                f'STAR --genomeDir /opt/seq_data/reference/hg38 '
                f'--readFilesIn /opt/seq_data/reads/{DAG_FILENAMES["fastq_1"]} /opt/seq_data/reads/{DAG_FILENAMES["fastq_2"]} '
                f'--outFileNamePrefix /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/ --runThreadN {cores} '
                f'{DAG_PARAMETERS["alignment"]} \'',
        mounts=[
                 Mount(
                     source=f'{filenames_collector.get_path_to_project()}',
                     target='/opt/seq_data',
                     type='bind'
                 )
        ],
        network_mode='bridge'
    )

    alignment_qc = DockerOperator(
        task_id='alignment_qc',
        image="rna-seq-pipeline_rseqc",
        command=f'bash -c \'cd /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/quality && '
                f'/RSeQC-5.0.1/scripts/read_distribution.py '
                f'-i /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.out.bam ' 
                f'-r /opt/seq_data/reference/hg38/{DAG_FILENAMES["reference_bed"]} \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    realignment = DockerOperator(
        task_id='realignment_abra2',
        image='rna-seq-pipeline_abra2',
        command=f'bash -c \'mkdir -p /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/realignment && '
                f'java -Xmx16G -jar ./abra2-2.23.jar '
                f'--in /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.out.bam '
                f'--out /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/realignment/Aligned.sortedByCoord.Abra.out.bam '
                f'--ref /opt/seq_data/reference/hg38/{DAG_FILENAMES["reference_bed"]} '
                f'--threads $(({cores}-1)) --gtf /opt/seq_data/reference/hg38/{DAG_FILENAMES["reference_gtf"]} '
                f'--tmpdir opt/seq_data/run_{DAG_FILENAMES["base_name"]}/abra {DAG_PARAMETERS["realignment"]} \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    add_or_replace_read_groups = DockerOperator(
        task_id="add_or_replace_read_groups",
        image="broadinstitute/picard",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'mkdir -p /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk && '
                f'java -jar /usr/picard/picard.jar AddOrReplaceReadGroups '
                f'I=/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.out.bam '
                f'O=/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.out.bam '
                f'{DAG_PARAMETERS["add_or_replace_read_groups"]} \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    mark_duplicates = DockerOperator(
        task_id="mark_duplicates",
        image="broadinstitute/picard",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'java -jar /usr/picard/picard.jar MarkDuplicates '
                f'--CREATE_INDEX true -I /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.out.bam'
                f'-O /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.MarkDuplicates.out.bam \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    split_n_cigar_reads = DockerOperator(
        task_id="split_n_cigar_reads",
        image="broadinstitute/gatk",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'gatk SplitNCigarReads '
                f'-R /opt/seq_data/reference/hg38/{DAG_FILENAMES["reference"]} '
                f'-I /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.MarkDuplicates.out.bam '
                f'-O /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.MarkDuplicates.SplitNCigarReads.out.bam \'',
        mounts=[
                 Mount(
                     source=f'{filenames_collector.get_path_to_project()}',
                     target='/opt/seq_data',
                     type='bind'
                 )
        ],
        network_mode='bridge'
    )

    index_split_n_cigar_reads = DockerOperator(
        task_id="index_split_n_cigar_reads",
        image="rna-seq-pipeline_samtools",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'samtools index -@ $(({cores}-1)) '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.MarkDuplicates.SplitNCigarReads.out.bam \'',
        mounts=[
                 Mount(
                     source=f'{filenames_collector.get_path_to_project()}',
                     target='/opt/seq_data',
                     type='bind'
                 )
        ],
        network_mode='bridge'
    )

    base_recalibrator = DockerOperator(
        task_id="base_recalibrator",
        image="broadinstitute/gatk",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'gatk BaseRecalibrator '
                f'-I /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.MarkDuplicates.SplitNCigarReads.out.bam '
                f'-R /opt/seq_data/reference/hg38/{DAG_FILENAMES["reference"]} '
                f'{DAG_PARAMETERS["known_sites"]} '
                f'-O /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/recal_data.table \'',
        mounts=[
                 Mount(
                     source=f'{filenames_collector.get_path_to_project()}',
                     target='/opt/seq_data',
                     type='bind'
                 )
        ],
        network_mode='bridge'
    )

    apply_bqsr = DockerOperator(
        task_id="apply_bqsr",
        image="broadinstitute/gatk",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'gatk ApplyBQSR '
                f'-R /opt/seq_data/reference/hg38/{DAG_FILENAMES["reference"]} '
                f'-I /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.MarkDuplicates.SplitNCigarReads.out.bam '
                f'--bqsr-recal-file /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/recal_data.table '
                f'-O /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.MarkDuplicates.SplitNCigarReads.ApplyBQSR.out.bam \'',
        mounts=[
                 Mount(
                     source=f'{filenames_collector.get_path_to_project()}',
                     target='/opt/seq_data',
                     type='bind'
                 )
        ],
        network_mode='bridge'
    )

    index_applybqsr = DockerOperator(
        task_id="index_applybqsr",
        image="rna-seq-pipeline_samtools",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'samtools index -@ $(({cores}-1)) '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.MarkDuplicates.SplitNCigarReads.ApplyBQSR.out.bam \'',
        mounts=[
                 Mount(
                     source=f'{filenames_collector.get_path_to_project()}',
                     target='/opt/seq_data',
                     type='bind'
                 )
        ],
        network_mode='bridge'
    )

    run_haplotype_caller = DockerOperator(
        task_id="run_haplotype_caller",
        image="broadinstitute/gatk",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'mkdir /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants && '
                f'gatk HaplotypeCaller {DAG_PARAMETERS["haplotype_caller"]} '
                f'-R /opt/seq_data/reference/hg38/{DAG_FILENAMES["reference"]} '
                f'-I /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/gatk/Aligned.sortedByCoord.AORRG.MarkDuplicates.SplitNCigarReads.ApplyBQSR.out.bam '
                f'-O /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/haplotype_caller_temp_output.vcf \'',
        mounts=[
                 Mount(
                     source=f'{filenames_collector.get_path_to_project()}',
                     target='/opt/seq_data',
                     type='bind'
                 )
        ],
        network_mode='bridge'
    )

    variant_filtration = DockerOperator(
        task_id="variant_filtration",
        image="broadinstitute/gatk",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'gatk VariantFiltration {DAG_PARAMETERS["variant_filtration"]} '
                f'-R /opt/seq_data/reference/hg38/{DAG_FILENAMES["reference"]} '
                f'-I /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/haplotype_caller_temp_output.vcf '
                f'-O /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/haplotype_caller_output.vcf \'',
        mounts=[
                 Mount(
                     source=f'{filenames_collector.get_path_to_project()}',
                     target='/opt/seq_data',
                     type='bind'
                 )
        ],
        network_mode='bridge'
    )

    preprocess_bam = DockerOperator(
        task_id="preprocess_bam",
        image="broadinstitute/picard",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'java -jar /usr/picard/picard.jar AddOrReplaceReadGroups '
                f'I=/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.Abra.out.bam '
                f'O=/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.Abra.AORRG.out.bam '
                f'{DAG_PARAMETERS["add_or_replace_read_groups"]} && '
                f'java -jar /usr/picard/picard.jar MarkDuplicates '
                f'-I /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.Abra.AORRG.out.bam '
                f'-O /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.Abra.AORRG.MarkDuplicates.out.bam \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    index_preprocessed_bam = DockerOperator(
        task_id="index_preprocessed_bam",
        image="rna-seq-pipeline_samtools",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'samtools index -@ $(({cores}-1)) '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.Abra.AORRG.MarkDuplicates.out.bam \'',
        mounts=[
                 Mount(
                     source=f'{filenames_collector.get_path_to_project()}',
                     target='/opt/seq_data',
                     type='bind'
                 )
        ],
        network_mode='bridge'
    )

    calculate_coverage = DockerOperator(
        task_id="calculate_coverage",
        image="quay.io/biocontainers/mosdepth:0.2.4--he527e40_0",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'mkdir -p /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/deepvariant && '
                f'mosdepth --threads $(({cores}-1)) '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/deepvariant/cov_3x '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.Abra.AORRG.MarkDuplicates.out.bam \'',
        mounts=[
                 Mount(
                     source=f'{filenames_collector.get_path_to_project()}',
                     target='/opt/seq_data',
                     type='bind'
                 )
        ],
        network_mode='bridge'
    )

    define_coveraged_regions = DockerOperator(
        task_id="define_coverage_regions",
        image="quay.io/biocontainers/bedtools:2.23.0--h5b5514e_6",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \' '
                f'gzip -dc /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/deepvariant/cov_3x.per-base.bed.gz | egrep -v \'HLA|decoy|random|alt|chrUn|chrEBV\' | awk -v OFS="\t" -v min_coverage=3 \'$4 >= min_coverage { print }\' | bedtools merge -d 1 -c 4 -o mean -i - > /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/deepvariant/cov_3x.bed \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    run_deepvariant = DockerOperator(
        task_id="run_deepvariant",
        image="google/deepvariant",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/bash -c \'/opt/deepvariant/bin/run_deepvariant '
                f'--ref=/opt/seq_data/reference/hg38/{DAG_FILENAMES["reference"]} '
                f'--reads=/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.Abra.AORRG.MarkDuplicates.out.bam '
                f'--num_shards=$(({cores}-2)) '
                f'{DAG_PARAMETERS["deepvariant"]} '
                f'--regions=/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/deepvariant/cov_3x.bed '
                f'--output_vcf=/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/deepvariant_output.vcf '
                f'--logging_dir=/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/deepvariant/logs \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    run_freebayes = DockerOperator(
        task_id="run_freebayes",
        image="bmslab/freebayes",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'freebayes -f /opt/seq_data/reference/hg38/{DAG_FILENAMES["reference"]} '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/alignment/Aligned.sortedByCoord.Abra.AORRG.MarkDuplicates.out.bam > '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/freebayes_output.vcf \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    postprocess_deepvariant = DockerOperator(
        task_id="postprocess_deepvariant",
        image="pegi3s/vcftools",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'bgzip -c /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/deepvariant_output.vcf > '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/deepvariant_output.vcf.gz && '
                f'tabix /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/deepvariant_output.vcf.gz \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    postprocess_haplotype_caller = DockerOperator(
        task_id="postprocess_haplotype_caller",
        image="pegi3s/vcftools",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'bgzip -c /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/haplotype_caller_output.vcf > '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/haplotype_caller_output.vcf.gz && '
                f'tabix /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/haplotype_caller_output.vcf.gz \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    postprocess_freebayes = DockerOperator(
        task_id="postprocess_freebayes",
        image="pegi3s/vcftools",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'bgzip -c /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/freebayes_output.vcf > '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/freebayes_output.vcf.gz && '
                f'tabix /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/freebayes_output.vcf.gz \'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    isec_variants = DockerOperator(
        task_id="isec_variants",
        image="staphb/bcftools",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'bcftools isec -c both -p /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/ '
                f'-n+2 /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/deepvariant_output.vcf.gz '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/haplotype_caller_output.vcf.gz '
                f'/opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/freebayes_output.vcf.gz ',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    run_vep = DockerOperator(
        task_id="run_vep",
        image="rna-seq-pipeline_vep",
        api_version='auto',
        auto_remove=True,
        command=f'/bin/sh -c \'./vep --tab --everything --cache '
                f'-i /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/0000.vcf '
                f'-o /opt/seq_data/run_{DAG_FILENAMES["base_name"]}/variants/annotated_result.txt\'',
        mounts=[
            Mount(
                source=f'{filenames_collector.get_path_to_project()}',
                target='/opt/seq_data',
                type='bind'
            )
        ],
        network_mode='bridge'
    )

    fastqc >> alignment >> alignment_qc
    alignment_qc >> realignment >> preprocess_bam >> index_preprocessed_bam >> calculate_coverage >> define_coveraged_regions >> run_deepvariant
    index_preprocessed_bam >> run_freebayes
    alignment_qc >> add_or_replace_read_groups >> mark_duplicates >> split_n_cigar_reads >> index_split_n_cigar_reads
    index_split_n_cigar_reads >> base_recalibrator >> apply_bqsr >> index_applybqsr >> run_haplotype_caller
    run_haplotype_caller >> variant_filtration
    run_deepvariant >> postprocess_deepvariant
    run_freebayes >> postprocess_freebayes
    variant_filtration >> postprocess_haplotype_caller
    [postprocess_deepvariant, postprocess_freebayes, postprocess_haplotype_caller] >> isec_variants >> run_vep
