FROM alpine
ARG ABRA2_VERSION=2.23
ENV ABRA2_VERSION ${ABRA2_VERSION}
ENV JAVA_OPTS "-Xmx16G"

RUN apk -U add \
     libc6-compat \
     openjdk8

ADD https://github.com/mozack/abra2/releases/download/v${ABRA2_VERSION}/abra2-${ABRA2_VERSION}.jar /

RUN chmod 755 /abra2-${ABRA2_VERSION}.jar

WORKDIR ./
