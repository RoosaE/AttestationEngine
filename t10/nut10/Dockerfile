# Copyright 2021 Nokia
# Licensed under the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

FROM docker.io/ubuntu:18.04

LABEL version="1.0"

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV LANGUAGE C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1




################################################################################
#
# Build TPMs tools:  TPM2-TSS, ABRMD, TPM2-TOOLS
#
################################################################################

RUN apt update


RUN apt -y install \
  autoconf-archive \
  libcmocka0 \
  libcmocka-dev \
  procps \
  iproute2 \
  build-essential \
  git \
  pkg-config \
  gcc \
  libtool \
  automake \
  libssl-dev \
  uthash-dev \
  autoconf \
  doxygen \
  libjson-c-dev \
  libini-config-dev \
  libcurl4-openssl-dev \
  libltdl-dev \
  libglib2.0-dev

RUN mkdir tpm2
WORKDIR /tpm2

WORKDIR /tpm2
RUN git clone https://github.com/tpm2-software/tpm2-tss.git && \
    git clone https://github.com/tpm2-software/tpm2-abrmd.git && \
    git clone https://github.com/tpm2-software/tpm2-tools.git

WORKDIR /tpm2/tpm2-tss
RUN ./bootstrap && \
    ./configure --with-udevrulesprefix && \
    make -j4 && \
    make install


WORKDIR /tpm2/tpm2-abrmd
RUN ./bootstrap && \
    ./configure --with-dbuspolicydir=/etc/dbus-1/system.d && \
    make -j4 && \
    make install


WORKDIR /tpm2/tpm2-tools
RUN ./bootstrap && \
    ./configure && \
    make -j4 && \
    make install




################################################################################
#
# Build additional tools:  IMA, TXT
#
################################################################################

RUN apt install wget

#
# Part 7: build Linux IMA tools
# https://sourceforge.net/p/linux-ima/wiki/Home/
#
# NB: these will not be relevant on some systems, eg: Windows, Linux without IMA etc
#
# Make install doesn't work because cp -t doesn't work under Alpine Linux's BusyBox, hence the explicit cp statements
#

WORKDIR /ima
RUN wget -O ltp-ima-standalone-v2.tar.gz http://downloads.sf.net/project/linux-ima/linux-ima/ltp-ima-standalone-v2.tar.gz
RUN tar -xvzf ltp-ima-standalone-v2.tar.gz
WORKDIR /ima/ima-tests
RUN make
RUN make install


#
# Part 8: build Intel TXT tools
# https://sourceforge.net/projects/tboot/
#
# The TXT tools are included in the whole tboot project
#
# NB: these will not be relevant on some systems, eg: Windows, non TXT x86 etc
#

WORKDIR /txt
RUN wget https://sourceforge.net/projects/tboot/files/tboot/tboot-1.10.3.tar.gz
RUN tar -xzvf tboot-1.10.3.tar.gz
WORKDIR /txt/tboot-1.10.3
RUN make
#RUN make install


################################################################################
#
# Build the trust agent
#
################################################################################


RUN apt -y install python3 python3-pip 

WORKDIR /nut10

RUN pip3 install flask
RUN pip3 install pyyaml
RUN pip3 install requests

ADD endpoints/ ./endpoints
ADD claims ./claims
ADD tpm ./tpm



ADD t10.conf /etc/t10.conf
ADD ta.py .
ADD ta_config.cfg .

EXPOSE 8530

CMD [ "python3", "ta.py"]
