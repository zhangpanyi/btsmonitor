FROM centos:7

RUN yum install gcc -y
RUN yum install git -y
RUN yum install make -y
RUN yum install wget -y
RUN yum install sqlite-devel -y
RUN yum install openssl-devel -y

RUN wget https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tgz -O - | tar -xz \
    && cd Python-3.6.3 \
    && ./configure --enable-optimizations --enable-loadable-sqlite-extensions \
    && make && make install \
    && pip3 install pyyaml \
    && pip3 install aiomysql \
    && pip3 install sqlalchemy \
    && pip3 install pycrypto \
    && pip3 install bitshares \
    && pip3 install grpcio \
    && pip3 install grpcio-tools

RUN rm -rf Python-3.6.3/

COPY ./ /root/wallet/
COPY ./docker/locale.conf /etc/locale.conf
RUN source /etc/locale.conf

EXPOSE 17128

WORKDIR /root/wallet/

ENTRYPOINT python3 wallet.py
