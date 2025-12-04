# GameScripts

在[DaCapo](https://github.com/Aues6uen11Z/DaCapo)上运行游戏自动化程序的权宜之计，不支持更改配置项，仅提供自动运行功能。

## 支持的游戏

- 原神：[BetterGI](https://github.com/babalae/better-genshin-impact)
- 绝区零：[ZenlessZoneZero-OneDragon](https://github.com/DoctorReid/ZenlessZoneZero-OneDragon)
- 鸣潮：[ok-wuthering-waves](https://github.com/ok-oldking/ok-wuthering-waves)

## 快速开始

0. 前置准备：
     1. 安装以上需要的项目，设置好配置项并成功运行一次
     2. 一条龙完成后的行为：BetterGI-**关闭游戏和软件**

1. 下载安装DaCapo[发布版](https://github.com/Aues6uen11Z/DaCapo/releases/latest)
2. 左下角设置按钮-创建新实例-从远程创建，名称随意，后面依次填写以下内容后点击创建：
   - 仓库地址：`https://github.com/Aues6uen11Z/GameScripts`或`https://gitee.com/aues6uen11z/GameScripts`，没梯子就用后者
   - 本地路径：`repos`
   - 分支：留空不填
   - 模板路径：`config`
3. 在更新页面点击右上角检查更新
4. 设置好`BetterGI.exe`/`OneDragon-Launcher.exe`/`ok-ww.exe`的文件路径
5. 开始运行

## 进阶

由于鸣潮可以后台运行，为了追求最高效率建议创建两个实例，一个实例单独启用鸣潮并设置后台运行，另一个实例启用其他任务并设置前台运行，即：

实例1：

- 使用上述方法创建
- 将鸣潮任务设置为不启用

实例2：

- 从已有模板创建新实例
- 不启用鸣潮以外任务
- 项目-通用-基本设置-后台程序勾选
- 项目-通用-基本设置-配置路径改为`./repos/GameScripts/config/ww.json`
- 游戏-鸣潮-任务设置-命令改为`py mian.py 2 ww`
