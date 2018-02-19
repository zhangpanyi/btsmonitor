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
    && make && make install

RUN pip3 install pyyaml==3.12 \
    && pip3 install aiomysql==0.0.12 \
    && pip3 install sqlalchemy==1.2.3 \
    && pip3 install pycrypto==2.6.1 \
    && pip3 install bitshares==0.1.11 \
    && pip3 install grpcio==1.9.1 \
    && pip3 install grpcio-tools==1.9.1

RUN rm -rf Python-3.6.3/

COPY ./ /root/btsmonitor/
COPY ./docker/locale.conf /etc/locale.conf
RUN source /etc/locale.conf

EXPOSE 17128

WORKDIR /root/btsmonitor/

ENTRYPOINT python3 main.py
