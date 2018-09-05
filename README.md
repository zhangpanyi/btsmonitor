# 介绍
btsmonitor 用于监控比特股账户资产变化，并可以通过HTTP POST方式通知其它服务。另外还提供了查询转账手续费、账户余额、资产转账接口。作为一个比特股中间件服务，人们通过它可以将比特股资产快速接入到自己的业务系统。相比 [python-bitshares](https://github.com/bitshares/python-bitshares) 库功能大而全，btsmonitor 功能更为单一，只支持转账和转账收款通知。优势在于IO操作全异步处理，可以大幅提高并发量。


# 运行环境
* python 3.6+
* aiohttp 3.3.2
* pyyaml 3.12
* websockets 5.0.1
* bitshares 0.1.17
* jsonrpcserver 3.5.6

```
git clone https://github.com/zhangpanyi/btsmonitor.git && cd btsmonitor
pip3 install aiohttp==3.3.2
pip3 install pyyaml==3.12
pip3 install websockets==5.0.1
pip3 install bitshares==0.1.17
pip3 install jsonrpcserver==3.5.6
```

# 配置文件
[server.yml.example](server.yml.example) 文件是 btsmonitor 服务的配置文件模板，需要执行命令 `python init_config.py` 生成配置文件。用户可以自行配置比特股接入点、账户、JSON-RPC服务等。

# Docker容器
```
sudo docker build -t="btsmonitor" -f docker/Dockerfile .
sudo docker run --name btsmonitor -d -p 18080:18080 btsmonitor
```

# JSON-RPC 接口

## 1. 获取账户

方法: `account`

**示例代码**

```
// 请求示例
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "account",
    "params": []
}

// 返回结果
{
    "jsonrpc": "2.0",
    "result": "test-bts2018",
    "id": 1
}
```

## 2. 获取资产余额

方法: `get_balances`

**示例代码**

```
// 请求示例
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "get_balances",
    "params": []
}

// 返回结果
{
    "jsonrpc": "2.0",
    "result": [
        {
            "id": "1.3.0",
            "symbol": "TEST",
            "amount": "99992.993"
        }
    ],
    "id": 1
}
```

## 3. 获取转账手续费

方法: `get_transfer_fees(symbols_or_ids : list)`

**示例代码**

```
// 请求示例
{
	"jsonrpc": "2.0",
	"id": 1,
	"method": "get_transfer_fees",
	"params": [["TEST"]]
}

// 返回结果
{
    "jsonrpc": "2.0",
    "result": [
        "0"
    ],
    "id": 1
}
```

## 4. 执行资产转账

方法: `transfer(to : string, symbol_or_id : string, amount : string, memo : string)`

**示例代码**

```
// 请求示例
{
	"jsonrpc": "2.0",
	"id": 1,
	"method": "transfer",
	"params": ["bts", "TEST", "1", "hello"]
}

// 返回结果
{
    "jsonrpc": "2.0",
    "result": "45f8cbbb8cd56c0e9b807f8c2d6c652084502a85",
    "id": 1
}
```
