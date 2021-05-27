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

1. 首先下载[我饿了快捷指令](https://www.icloud.com/shortcuts/f74e95a28e934b209ce72f774c8126f0)，然后根据导入问题做配置，遇到最后那个选择快捷指令的导入可以先暂时跳过
2. 然后下载[Rasa Chatbot快捷指令](https://www.icloud.com/shortcuts/27d85db243c8467491dc85c0ac0fda4e)，根据导入问题做配置，遇到最后一个选择打开支付宝二维码快捷指令的问题可以先暂时跳过
3. 回到我饿了快捷指令，把最后的运行快捷指令修改成指向Rasa Chatbot快捷指令
4. 如果是想在Siri使用的话，下载[这个快捷指令](https://www.icloud.com/shortcuts/a5e41709944d49659a716a31ea30718f)，如果想在Homepod使用的话，下载[这个快捷指令](https://www.icloud.com/shortcuts/153fe2db070143b185a0fa999f18f9d5)。打开之后把Rasa Chatbot快捷指令里面，打开URL的快捷指令（在如果url有任何值下面），改成指向你刚刚下载的快捷指令
5. Homepod使用的话最后下载[这个快捷指令](https://www.icloud.com/shortcuts/50be6eb6fb3247ea867ea2c9f5c311ee)。最后需要用这个快捷指令打开在剪贴板里面的支付宝二维码
# 开源证书

[MIT](./LICENSE)
