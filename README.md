# 介绍
**btsmonitor** 的作用是监控比特股账户资金变化和转账，作为第三方应用充值和提现比特股资产的基础服务。IO操作全异步处理，有效地提升了并发量。

# 搭建环境

## 获取代码
```
git clone https://github.com/zhangpanyi/btsmonitor.git
cd btsmonitor
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
