FROM python:3.6

RUN pip3 install aiohttp==3.3.2 \
    && pip3 install pyyaml==3.12 \
    && pip3 install websockets==5.0.1 \
    && pip3 install bitshares==0.1.17 \
    && pip3 install jsonrpcserver==3.5.6

COPY . /root/btsmonitor/
WORKDIR /root/btsmonitor/

EXPOSE 18080

ENTRYPOINT [ "python3", "main.py" ]
