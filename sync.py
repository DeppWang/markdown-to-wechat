#!/usr/bin/python3
# public/upload_news.py
# -*- coding: utf-8 -*-
"""
推送文章到微信公众号
"""
# from calendar import c
from datetime import datetime
from datetime import timedelta
import re
import subprocess

# from weakref import ref
from pyquery import PyQuery
import time
import urllib
import urllib.parse
import markdown
from markdown.extensions import codehilite
import os
import hashlib
import pickle
from pathlib import Path
from werobot import WeRoBot
import requests
import json
import urllib.request

CACHE = {}

CACHE_STORE = "cache.bin"
BLOG_URL = "https://depp.wang"
AUTHOR = "DeppWang"
HEXO_BLOG_POST_PATH = "../HexoBlog/source/_posts"


def dump_cache():
    fp = open(CACHE_STORE, "wb")
    pickle.dump(CACHE, fp)


def init_cache():
    global CACHE
    if os.path.exists(CACHE_STORE):
        fp = open(CACHE_STORE, "rb")
        CACHE = pickle.load(fp)
        # print(CACHE)
        return
    dump_cache()


def cache_get(key):
    if key in CACHE:
        return CACHE[key]
    return None


def file_digest(file_path):
    """
    计算文件的md5值
    """
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        md5.update(f.read())
    return md5.hexdigest()


def cache_update(file_path):
    digest = file_digest(file_path)
    CACHE[digest] = "{}:{}".format(file_path, datetime.now())
    dump_cache()


def file_processed(file_path):
    digest = file_digest(file_path)
    return cache_get(digest) != None


def pull_code():
    # 定义 git pull 命令
    command = ["git", "pull", "origin", "master"]
    # 指定工作目录
    working_dir = "/Users/depp/GitHub/HexoBlog/"
    # 执行命令
    result = subprocess.run(command, capture_output=True, text=True, cwd=working_dir)
    if result.returncode == 0:
        print("Git pull 成功")
        print(result.stdout)  # 输出命令执行的标准输出
        return True
    else:
        print("Git pull 失败")
        print(result.stderr)  # 输出命令执行的错误信息
        return False


class NewClient:
    def __init__(self):
        self.__accessToken = ""
        self.__leftTime = 0

    def __real_get_access_token(self):
        postUrl = (
            "https://api.weixin.qq.com/cgi-bin/token?grant_type="
            "client_credential&appid=%s&secret=%s"
            % (os.getenv("WECHAT_APP_ID"), os.getenv("WECHAT_APP_SECRET"))
        )
        urlResp = urllib.request.urlopen(postUrl)
        urlResp = json.loads(urlResp.read())
        self.__accessToken = urlResp["access_token"]
        self.__leftTime = urlResp["expires_in"]

    def get_access_token(self):
        if self.__leftTime < 10:
            self.__real_get_access_token()
        return self.__accessToken


def Client():
    robot = WeRoBot()
    robot.config["APP_ID"] = os.getenv("WECHAT_APP_ID")
    robot.config["APP_SECRET"] = os.getenv("WECHAT_APP_SECRET")
    client = robot.client
    token = client.grant_token()
    return client, token


def replace_para(content):
    res = []
    for line in content.split("\n"):
        if line.startswith("<p>"):
            line = line.replace("<p>", gen_css("para"))
        res.append(line)
    return "\n".join(res)


def replace_code(content):
    content = content.replace("<code>", gen_css("code"))
    return content


def replace_header(content):
    res = []
    for line in content.split("\n"):
        l = line.strip()
        if l.startswith("<h") and l.endswith(">") > 0:
            tag = l.split(" ")[0].replace("<", "")
            value = l.split(">")[1].split("<")[0]
            digit = tag[1]
            font = (
                (18 + (4 - int(tag[1])) * 2) if (digit >= "0" and digit <= "9") else 18
            )
            res.append(gen_css("sub", tag, font, value, tag))
        else:
            res.append(line)
    return "\n".join(res)


def replace_links(content):
    pq = PyQuery(open("origin.html").read())
    links = pq("a")
    refs = []
    index = 1
    if len(links) == 0:
        return content
    for l in links.items():
        link = gen_css("link", l.text(), index)
        index += 1
        refs.append([l.attr("href"), l.text(), link])

    for r in refs:
        orig = '<a href="{}">{}</a>'.format(r[0], r[1])
        content = content.replace(orig, r[2])
    content = content + "\n" + gen_css("ref_header")
    index = 1
    for r in refs:
        l = r[2]
        line = gen_css("ref_link", index, r[1], r[0])
        index += 1
        content += line + "\n"
    return content


def format_fix(content):
    content = content.replace("background: #272822", gen_css("code"))
    content = content.replace(
        """<pre style="line-height: 125%">""",
        """<pre style="line-height: 125%; color: white; font-size: 11px;">""",
    )
    return content


def fix_image(content):
    pq = PyQuery(open("origin.html").read())
    imgs = pq("img")
    for line in imgs.items():
        link = """<img alt="{}" src="{}" />""".format(
            line.attr("alt"), line.attr("src")
        )
        img_tag = '<img src="{}" alt="{}" style="display: block; margin-top: 0px; margin-right: auto; margin-bottom: 0px; margin-left: auto; max-width: 100%; border-top-style: none; border-bottom-style: none; border-left-style: none; border-right-style: none; border-top-width: 3px; border-bottom-width: 3px; border-left-width: 3px; border-right-width: 3px; border-top-color: rgba(0, 0, 0, 0.4); border-bottom-color: rgba(0, 0, 0, 0.4); border-left-color: rgba(0, 0, 0, 0.4); border-right-color: rgba(0, 0, 0, 0.4); border-top-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px; border-bottom-left-radius: 0px; object-fit: fill; box-shadow: rgba(0, 0, 0, 0) 0px 0px 0px 0px;">'.format(
            line.attr("src"), line.attr("alt") or ""
        )
        figure = gen_css("figure", img_tag, line.attr("alt") or "")
        content = content.replace(link, figure)
    return content


def replace_strong(content):
    strong_style = 'style="color: rgb(0, 0, 0); font-weight: bold; background-attachment: scroll; background-clip: border-box; background-color: rgba(0, 0, 0, 0); background-image: none; background-origin: padding-box; background-position-x: left; background-position-y: top; background-repeat: no-repeat; background-size: auto; width: auto; height: auto; margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; padding-top: 0px; padding-bottom: 0px; padding-left: 0px; padding-right: 0px; border-top-style: none; border-bottom-style: none; border-left-style: none; border-right-style: none; border-top-width: 3px; border-bottom-width: 3px; border-left-width: 3px; border-right-width: 3px; border-top-color: rgba(0, 0, 0, 0.4); border-bottom-color: rgba(0, 0, 0, 0.4); border-left-color: rgba(0, 0, 0, 0.4); border-right-color: rgba(0, 0, 0, 0.4); border-top-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px; border-bottom-left-radius: 0px;"'
    content = content.replace("<strong>", "<strong {}>".format(strong_style))
    return content


def replace_list(content):
    ul_style = 'style="list-style-type: disc; margin-top: 8px; margin-bottom: 8px; margin-left: 0px; margin-right: 0px; padding-top: 0px; padding-bottom: 0px; padding-left: 25px; padding-right: 0px; color: rgb(0, 0, 0);"'
    ol_style = 'style="list-style-type: decimal; margin-top: 8px; margin-bottom: 8px; margin-left: 0px; margin-right: 0px; padding-top: 0px; padding-bottom: 0px; padding-left: 25px; padding-right: 0px; color: rgb(0, 0, 0);"'
    li_section_style = 'style="margin-top: 5px; margin-bottom: 5px; color: rgb(1, 1, 1); font-size: 16px; line-height: 1.8em; letter-spacing: 0em; text-align: left; font-weight: normal;"'
    content = content.replace("<ul>", "<ul {}>".format(ul_style))
    content = content.replace("<ol>", "<ol {}>".format(ol_style))
    content = content.replace("<li>", "<li><section {}>".format(li_section_style))
    content = content.replace("</li>", "</section></li>")
    # Compact list HTML: remove newlines between list elements
    # WeChat's ProseMirror editor converts newlines into empty <li> items
    content = content.replace("</li>\n<li>", "</li><li>")
    content = re.sub(r'(<ul[^>]*>)\s*<li>', r'\1<li>', content)
    content = re.sub(r'(<ol[^>]*>)\s*<li>', r'\1<li>', content)
    content = content.replace("</li>\n</ul>", "</li></ul>")
    content = content.replace("</li>\n</ol>", "</li></ol>")
    return content


def fix_figure_in_para(content):
    """Remove <p> wrappers around <figure> elements.
    Markdown renders images as <p><img/></p>, and after fix_image
    this becomes <p><figure>...</figure></p>. A block <figure> inside
    <p> is invalid HTML and breaks WeChat rendering."""
    content = re.sub(
        r'<p[^>]*>\s*(<figure[\s\S]*?</figure>)\s*</p>',
        r'\1',
        content
    )
    return content


def gen_css(path, *args):
    tmpl = open("./assets/{}.tmpl".format(path), "r").read().strip()
    return tmpl.format(*args)


def css_beautify(content):
    content = replace_para(content)
    content = replace_code(content)
    content = replace_header(content)
    content = replace_links(content)
    content = format_fix(content)
    content = fix_image(content)
    content = fix_figure_in_para(content)
    content = replace_strong(content)
    content = replace_list(content)
    content = gen_css("header") + content + "</section>"
    return content


def upload_image_from_path(image_path):
    image_digest = file_digest(image_path)
    res = cache_get(image_digest)
    if res != None:
        return res[0], res[1]
    client, _ = Client()
    print("上传: {}".format(image_path))
    media_json = client.upload_permanent_media(
        "image", open(image_path, "rb")
    )  # 永久素材
    media_id = media_json["media_id"]
    media_url = media_json["url"]
    CACHE[image_digest] = [media_id, media_url]
    dump_cache()
    print("file: {} => media_id: {}".format(image_path, media_id))
    return media_id, media_url


def upload_image(img_url):
    """
    * 上传临时素材
    * 1、临时素材media_id是可复用的。
    * 2、媒体文件在微信后台保存时间为3天，即3天后media_id失效。
    * 3、上传临时素材的格式、大小限制与公众平台官网一致。
    """
    resp = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    parsed = urllib.parse.urlparse(img_url)
    name = os.path.basename(parsed.path)
    if not name:
        name = hashlib.md5(img_url.encode("utf-8")).hexdigest()
    f_name = "tmp/{}".format(name)
    if "." not in name:
        f_name = f_name + ".png"
    with open(f_name, "wb") as f:
        f.write(resp.content)
    return upload_image_from_path(f_name)


def get_images_from_markdown(content):
    lines = content.split("\n")
    images = []
    for line in lines:
        line = line.strip()
        if line.startswith("![") and line.endswith(")"):
            image = line.split("(")[1].split(")")[0].strip()
            images.append(image)
    return images


def fetch_attr(content, key):
    """
    从markdown文件中提取属性
    """
    lines = content.split("\n")
    for line in lines:
        if line.startswith(key):
            return line.split(":")[1].strip()
    return ""


def render_markdown(content):
    exts = [
        "markdown.extensions.extra",
        "markdown.extensions.tables",
        "markdown.extensions.toc",
        "markdown.extensions.sane_lists",
        codehilite.makeExtension(
            guess_lang=False, noclasses=True, pygments_style="monokai"
        ),
    ]
    html = markdown.markdown(content, extensions=exts)
    open("origin.html", "w").write(html)
    return css_beautify(html)


def update_images_urls(content, uploaded_images):
    for image, meta in uploaded_images.items():
        orig = "({})".format(image)
        new = "({})".format(meta[1])
        # print("{} -> {}".format(orig, new))
        content = content.replace(orig, new)
    return content


def upload_media_news(post_path):
    """
    上传到微信公众号素材
    """
    content = open(post_path, "r").read()
    TITLE = fetch_attr(content, "title").strip('"').strip("'")
    gen_cover = fetch_attr(content, "gen_cover").strip('"')
    images = get_images_from_markdown(content)
    print("TITLE", TITLE)
    if len(images) == 0 or gen_cover == "true":
        images = ["https://source.unsplash.com/random/600x400"] + images
    uploaded_images = {}
    # print(images)
    for image in images:
        media_id = ""
        media_url = ""
        if image.startswith("http"):
            media_id, media_url = upload_image(image)
            # print('image')
        else:
            media_id, media_url = upload_image_from_path("../HexoBlog/source" + image)
        uploaded_images[image] = [media_id, media_url]

    content = update_images_urls(content, uploaded_images)

    THUMB_MEDIA_ID = (len(images) > 0 and uploaded_images[images[0]][0]) or ""

    RESULT = render_markdown("".join(content.split("---\n")[2:]))

    digest = fetch_attr(content, "subtitle").strip().strip('"').strip("'")
    print("digest", digest)
    print(fetch_attr(content, "date")[:10])
    date = datetime.strptime(fetch_attr(content, "date")[:10], "%Y-%m-%d")
    if date > datetime.strptime("2024-4-5", "%Y-%m-%d"):
        date_str = str(date.year)
    else:
        date_str = date.strftime("%Y/%m/%d")
    english_title = fetch_attr(content, "english_title").strip()
    CONTENT_SOURCE_URL = "{}/{}/{}".format(BLOG_URL, date_str, english_title)

    articles = {
        "articles": [
            {
                "title": TITLE,
                "thumb_media_id": THUMB_MEDIA_ID,
                "author": AUTHOR,
                "digest": "",
                "show_cover_pic": 1,
                "content": RESULT,
                "content_source_url": CONTENT_SOURCE_URL,
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
            }
            # 若新增的是多图文素材，则此处应有几段articles结构，最多8段
        ]
    }

    fp = open("./result.html", "w")
    fp.write(RESULT)
    fp.close()

    client = NewClient()
    token = client.get_access_token()
    headers = {"Content-type": "text/plain; charset=utf-8"}
    datas = json.dumps(articles, ensure_ascii=False).encode("utf-8")

    postUrl = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=%s" % token
    r = requests.post(postUrl, data=datas, headers=headers)
    resp = json.loads(r.text)
    print(resp)
    media_id = resp["media_id"]
    cache_update(post_path)
    return resp


def hexo_to_wechat(string_date):
    pull_code()
    pathlist = Path(HEXO_BLOG_POST_PATH).glob("**/*.md")
    for path in pathlist:
        # print('path', path)
        path_str = str(path)
        if file_processed(path_str):
            print("{} has been processed".format(path_str))
            continue
        content = open(path_str, "r").read()
        date = fetch_attr(content, "date").strip()
        if string_date in date:
            print("file date", date)
            print("path_str", path_str)
            news_json = upload_media_news(path_str)
            print(news_json)
            print("successful")


if __name__ == "__main__":
    init_cache()
    start_time = time.time()  # 开始时间
    times = [datetime.now(), datetime.now() - timedelta(days=7)]
    for x in times:
        print("start time: {}".format(x.strftime("%m/%d/%Y, %H:%M:%S")))
        string_date = x.strftime("%Y-%m-%d")
        hexo_to_wechat(string_date)
    end_time = time.time()  # 结束时间
    print("程序耗时%f秒." % (end_time - start_time))
