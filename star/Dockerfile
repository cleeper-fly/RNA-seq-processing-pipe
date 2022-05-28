FROM ubuntu:focal

LABEL description="Image for STAR aligner"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    bzip2 \
    cmake \
    default-jdk \
    git \
    libnss-sss \
    libtbb2 \
    libtbb-dev \
    ncurses-dev \
    python-dev \
    python3-pip \
    tzdata \
    unzip \
    wget \
    zlib1g \
    zlib1g-dev

# Star aligner
ENV star_version 2.7.10a
WORKDIR /workdir
ADD https://github.com/alexdobin/STAR/archive/${star_version}.tar.gz /usr/bin/
RUN tar -xzf /usr/bin/${star_version}.tar.gz -C /usr/bin/
RUN cp /usr/bin/STAR-${star_version}/bin/Linux_x86_64/* /usr/local/bin


##lsf time stamp bug
## borrow from cmiller
#
#RUN ln -sf /usr/share/zoneinfo/America/Chicago /etc/localtime
#RUN echo "America/Chicago" > /etc/timezone
#RUN dpkg-reconfigure --frontend noninteractive tzdata

RUN cd /workdir / && \
   rm -rf ${star_version}.tar.gz && \
   apt-get autoremove -y && \
   apt-get autoclean -y  && \
   apt-get clean

# Set default working path
WORKDIR /workdir

ENTRYPOINT /bin/bash