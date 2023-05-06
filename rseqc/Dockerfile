FROM python:latest

RUN wget -O RSeQC-5.0.1.tar.gz https://sourceforge.net/projects/rseqc/files/RSeQC-5.0.1.tar.gz/download &&\
    tar -vxzf RSeQC-5.0.1.tar.gz

RUN pip3 install RSeQC

WORKDIR ./
