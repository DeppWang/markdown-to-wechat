# markdown-to-wechat

代码中有硬编码部分，请自行更改。

## 安装

```bash
python3 -m venv venv
. venv/bin/activate
pip3 install markdown Pygments werobot pyquery
```

## 配置白名单和 token

公众号后台路径：设置和开发 -> 基本配置 ：填入服务器 IP，生成 token。

在 sync.py 中通过环境变量获取 app_id 和 secret:

```python
robot.config["APP_ID"] = os.getenv('WECHAT_APP_ID')
robot.config["APP_SECRET"] = os.getenv('WECHAT_APP_SECRET')
```

把 token 配置到服务器环境变量，然后在服务器上运行 `python3 sync.py` 即可。

## 问题

1. 公众号文章与个人博客内容可能不相同，如：video，youtube 与 bilibili，还是需要手动编辑；还是需要预览与发送。
2. mdnice 粘贴也要不了多少时间，也支持图片
3. 缺点：支持性不佳，代码块、有序列表、无序列表；本地执行-电脑 IP 经常变动（服务器运行可解决这个问题）；预览后的修改不能直接替换（可实现）；
4. 好处：标题、原文链接、头图

## Obsidian to Wechat

obsidian_to_wechat.py: 从 obsidian 发布到微信公众号