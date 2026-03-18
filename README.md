# Obsidian to WeChat

一键将 Obsidian 笔记发布到微信公众号草稿箱。

写完笔记，打个标签，运行脚本，草稿就自动出现在公众号后台了——不用复制粘贴，不用手动排版。

## 它做了什么

1. 扫描 Obsidian 笔记目录，找到最近 3 天内修改过、且带有 `Obsidian-to-Wechat-Tag` 标签的文章
2. 将 Markdown 转换成微信公众号兼容的排版样式（标题、代码块、链接等都会自动美化）
3. 自动下载文章中的图片，上传到微信素材库
4. 调用微信 API，创建公众号草稿（已有草稿会自动更新，不会重复创建）

你只需要在公众号后台预览、微调后发送即可。

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv venv
. venv/bin/activate
pip install markdown Pygments werobot pyquery requests
```

### 2. 配置微信公众号

在公众号后台（设置和开发 → 基本配置）中：
- 将你的服务器 IP 加入白名单
- 获取 AppID 和 AppSecret

然后设置环境变量：

```bash
export WECHAT_APP_ID="你的AppID"
export WECHAT_APP_SECRET="你的AppSecret"
```

### 3. 修改硬编码路径

在 `obsidian_to_wechat.py` 中修改以下常量，改成你自己的路径和信息：

```python
OBSIDIAN_PATH = "/你的/Obsidian/笔记目录"
AUTHOR = "你的名字"
CONTENT_SOURCE_URL = "https://你的博客地址/..."
```

### 4. 给文章打标签

在 Obsidian 笔记的**第一行**添加标签 `Obsidian-to-Wechat-Tag`，表示这篇文章需要发布到公众号。

### 5. 运行

```bash
python3 obsidian_to_wechat.py
```

脚本会自动处理带标签的文章，创建草稿到公众号后台。

## 工作原理

```
Obsidian 笔记 (.md)
    ↓ 扫描最近 3 天修改的文件
    ↓ 过滤带有指定标签的文章
    ↓ 提取并上传图片到微信素材库
    ↓ Markdown → 微信兼容 HTML（自动排版美化）
    ↓ 调用微信 API 创建/更新草稿
公众号草稿箱 ✓
```

## 项目结构

```
obsidian_to_wechat.py   # Obsidian 入口，主要使用这个
sync.py                 # 核心库：Markdown 渲染、图片上传、微信 API 封装
assets/*.tmpl           # HTML/CSS 排版模板（段落、代码、标题、链接等样式）
cache.bin               # 缓存文件，记录已处理的文章，避免重复上传
```

## 注意事项

- 公众号文章与博客内容可能有差异（如视频平台不同），发布前建议在后台预览确认
- 如果本地运行遇到 IP 变动问题，可以用 VPN 解决：设置微信 API 请求走代理，这样对微信 API 来说始终是一个固定的 IP，再将这个固定 IP 加到公众号白名单即可
