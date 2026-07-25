# simply_get_b_video
# B站 html5 MP4解析下载工具
利用 `platform=html5` 获取音视频合并MP4直链
> ⚠️ 重要限制：B站新版本视频**1080P及以上不再提供预合成一体MP4**，html5模式最高仅可获取720P。

## 使用说明
1. 打开B站
2. 浏览器F12 -> Network，点开一个请求，找到复制完整Cookie字符串和user-agent
3. 将代码内 COOKIE_RAW 替换为你的Cookie
4. 将代码内 user-agent 替换为你的user-agent
5. 安装requests模块
6. 运行脚本，输入B站视频链接

## ⚠️ 风险提醒
1. Cookie存在有效期，失效需要重新获取；
2. 防盗链MP4链接具备时效性；
3. 仅供个人学习，遵守B站用户协议，禁止商用。

## 参考
https://github.com/realysy/bili-apis **B站api支持**
