# GameScripts

在[DaCapo](https://github.com/Aues6uen11Z/DaCapo)上运行游戏自动化程序的权宜之计，不支持更改配置项，仅提供自动运行功能。

# 支持的游戏

- 原神：[BetterGI](https://github.com/babalae/better-genshin-impact)
- 绝区零：[ZenlessZoneZero-OneDragon](https://github.com/DoctorReid/ZenlessZoneZero-OneDragon)

# 使用方法

0. 前置准备：
    1. 安装[python](https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip)，切记勾选添加到环境变量
    2. 安装以上需要的项目，设置好配置项并成功运行一次
    3. 一条龙完成后的行为：BetterGI-**关闭游戏和软件**，绝区零一条龙-**关闭游戏**
    
1. 下载安装DaCapo[发布版](https://github.com/Aues6uen11Z/DaCapo/releases/latest)
2. 左下角设置按钮-创建新实例-从远程创建，名称随意，后面依次填写以下内容后点击创建：
   - 仓库地址：`https://github.com/Aues6uen11Z/GameScripts`或`https://gitee.com/aues6uen11z/GameScripts`，没梯子就用后者
   - 本地路径：`repos`
   - 分支：留空不填
   - 模板路径：`config`
3. 在更新页面点击右上角检查更新
4. 设置好`BetterGI.exe`和`OneDragon Scheduler.exe`的文件路径
5. 开始运行

