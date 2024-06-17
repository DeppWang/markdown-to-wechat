from datetime import datetime, timedelta
import json
import os
import random
import string
import time

import requests

from sync import (
    NewClient,
    cache_update,
    fetch_attr,
    file_processed,
    get_images_from_markdown,
    init_cache,
    render_markdown,
    update_images_urls,
    upload_image,
)

OBSIDIAN_PATH = "/Users/depp/Documents/Obsidian"
OBSIDIAN_TO_WECHAT_TAG = "Obsidian-to-Wechat-Tag"


def get_obsidian_tags(file_path):
    """获取 Obsidian 文章的 tag"""

    first_line = ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip().replace(" ", "")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return [], False
    except Exception as e:
        print(f"Error opening/reading file: {e}")
        return [], False

    return [tag for tag in first_line.split("#") if tag]


def upload_media_news(file_name, file_path, english_title):
    """
    上传到微信公众号素材
    """
    with open(file_path, 'r') as f:
        data = f.read().splitlines(True)
    content = "".join(data[1:])
    images = get_images_from_markdown(content)
    if len(images) == 0:
        letters = string.ascii_lowercase
        seed = ''.join(random.choice(letters) for i in range(10))
        print(seed)
        images = ["https://picsum.photos/seed/" + seed + "/400/600"] + images
    uploaded_images = {}
    # print(images)
    for image in images:
        media_id = ""
        media_url = ""
        if image.startswith("http"):
            print(image)
            media_id, media_url = upload_image(image)
        uploaded_images[image] = [media_id, media_url]

    content = update_images_urls(content, uploaded_images)

    THUMB_MEDIA_ID = (len(images) > 0 and uploaded_images[images[0]][0]) or ""
    AUTHOR = "DeppWang"
    RESULT = render_markdown(content)

    digest = fetch_attr(content, "subtitle").strip().strip('"').strip("'")
    print("digest", digest)
    print(fetch_attr(content, "date")[:10])
    CONTENT_SOURCE_URL = "https://depp.wang/2024/{}".format(english_title)

    articles = {
        "articles": [
            {
                "title": os.path.splitext(file_name)[0],
                "thumb_media_id": THUMB_MEDIA_ID,
                "author": AUTHOR,
                "digest": digest,
                "show_cover_pic": 1,
                "content": RESULT,
                "content_source_url": CONTENT_SOURCE_URL,
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
    cache_update(file_path)
    return resp


def get_file_time(file_path):
    # 获取文件的最后修改时间戳
    modification_time = os.path.getmtime(file_path)

    # 将时间戳转换为可读的日期时间格式
    modification_datetime = datetime.fromtimestamp(modification_time)

    # 格式化日期为 %Y-%m-%d
    last_modified = modification_datetime.strftime("%Y-%m-%d")
    return last_modified


def exec(file_name, file_path):
    """执行"""

    tags = get_obsidian_tags(file_path=file_path)
    # 如果没有 Obsidian-to-HexoBlog-Tag 标签
    if OBSIDIAN_TO_WECHAT_TAG not in tags:
        return
    # print('has tag', file_path)
    english_title = tags[0]  # 第一个标签为英文名

    upload_media_news(file_name, file_path, english_title)


def obsidian_to_wechat(string_date):
    file_list = os.listdir(OBSIDIAN_PATH)
    for file_name in file_list:
        file_path = os.path.join(OBSIDIAN_PATH, file_name)
        if string_date not in get_file_time(file_path):
            continue
        file_suffix = os.path.splitext(file_name)[1]  # 笔记后缀
        if file_suffix != ".md":
            continue
        if os.path.isdir(file_path):
            continue
        # if file_processed(file_path):
        #     print("{} has been processed".format(file_path))
        #     continue
        exec(file_name, file_path)


if __name__ == "__main__":
    init_cache()
    start_time = time.time()  # 开始时间
    times = [datetime.now(), datetime.now() - timedelta(days=3)]
    for x in times:
        print("start time: {}".format(x.strftime("%m/%d/%Y, %H:%M:%S")))
        string_date = x.strftime("%Y-%m-%d")
        obsidian_to_wechat(string_date)
    end_time = time.time()  # 结束时间
    print("程序耗时%f秒." % (end_time - start_time))
