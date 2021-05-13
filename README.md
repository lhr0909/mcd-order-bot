# mcd-order-bot

这是一个可以自动点麦当劳外卖的聊天机器人。

[Bilibili视频链接](https://www.bilibili.com/video/BV1FA411G7QW/)

# 安装和使用

当前版本暂时只可以在本地的机器跑，并且本人由于没有Windows，所以现阶段只能保证在Linux和MacOS下面运行。以下的步骤也是针对Linux和MacOS的。欢迎添加issue补充Windows的安装使用步骤，或者咨询我，我们可以一起看看。

## 安装依赖

1. Docker - 具体安装步骤请见 https://docs.docker.com/engine/install/
2. Python v3.7.9 - 强烈建议通过[Pyenv]()管理Python版本。
3. Poetry - 通过 `pip install poetry` 安装

上述依赖就绪之后，运行以下命令：

```shell
docker compose up -d
poetry install
```

会自动从网上下载所需要的服务依赖和Python依赖。

最后，安装playwright所需的Chromium浏览器：

```shell
poetry run playright install
```

## 使用方法

我提供了一个 `Makefile` 里面记录了常用的命令。 `make` 要求安装以下工具：

MacOS下，安装XCode并且安装命令行工具。

Linux下，以Ubuntu为例，建议直接安装 `build-essential`

```shell
sudo apt-get install -y build-essential
```

有了make命令之后，我们可以先训练一个模型：

```shell
make train
```

模型训练出来之后我们可以在Rasa X里面测试一下：

```shell
make apiserver actionserver x -j3 # 这个命令会同时运行API Server, Action Server和Rasa X
```

这时候浏览器会打开，只需要等个一两分钟，聊天界面就会出现。需要聊到机器人说“打开了麦当劳的官网”，需要在弹出的浏览器里面登录一下金拱门。这个浏览器会记住登录的状态。理论上可以保持两周。

这个时候我们就可以配置Siri了。

## Siri快捷指令

这部分暂时TODO，我需要加一些自动配置项，然后添加共享链接。过两天会加上。

# 开源证书

[MIT](./LICENSE)
