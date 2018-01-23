# 介绍
**btsmonitor** 的作用是监控比特股账户资金变化和转账。

# 搭建环境

## 获取代码
```
git clone https://zhangpanyi@bitbucket.org/zhangpanyi/wallet.git
cd walletmonitor
```

## CentOS 7
```
yum install docker -y
systemctl start docker.service
chkconfig docker on
```

# 启动服务

## 构建Docker镜像
```
sudo docker build -t="bitshares" -f docker/Dockerfile .
```

## Protobuf
```
python3 -m grpc_tools.protoc -I ./protobuf --python_out=./proto/ --grpc_python_out=./proto/ ./protobuf/casino.proto
python3 -m grpc_tools.protoc -I ./protobuf --python_out=./proto/ --grpc_python_out=./proto/ ./protobuf/wallet.proto
```

## 运行Docker容器
```
sudo docker run -itd -p 17128:17128 bitshares
```
