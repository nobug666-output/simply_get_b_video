# 使用platform=html5的方式处理，直接返回mp4，无需合成m4s文件,最多返回720p的MP4
import requests
import json
import time
import urllib.parse
from hashlib import md5

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]

# 使用方式：将下方字符串替换为浏览器复制完整Cookie（不要从网络面板复制）
COOKIE_RAW = """浏览器复制完整Cookie"""
cookies_dict = {}
for i in COOKIE_RAW.split('; '):
    if '=' in i:
        k, v = i.split('=', 1)
        cookies_dict[k] = v

headers = {
    #浏览器复制完整请求头替换下面user-agent
    'user-agent': '完整请求头',
    'accept': 'application/json, text/plain, */*',
    'referer': 'https://www.bilibili.com'
}
REQUEST_TIMEOUT = 15

# 获取mixin_key函数
def get_mixin_key():
    url = 'https://api.bilibili.com/x/web-interface/nav'
    try:
        res = requests.get(url=url, headers=headers, cookies=cookies_dict, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        text = json.loads(res.text)
        if text.get("code") != 0:
            if text.get("code") == -101:
                raise Exception("Cookie已失效！请重新从浏览器复制Cookie字符串")
            raise Exception(f"获取wbi密钥失败, code:{text['code']}, msg:{text.get('message')}")

        img_token = text['data']['wbi_img']['img_url'].split('wbi/')[1].split('.')[0]
        sub_token = text['data']['wbi_img']['sub_url'].split('wbi/')[1].split('.')[0]
        raw_wbi_key = img_token + sub_token
        mixin_key = ""
        for elem in MIXIN_KEY_ENC_TAB:
            mixin_key += raw_wbi_key[elem]
        return mixin_key[:32]
    except Exception as e:
        raise Exception(f"获取mixin_key异常：{str(e)}")

# 分离bvid函数，增强兼容性
def get_bvid(url):
    if "video/BV" not in url:
        raise ValueError("链接格式错误，请输入标准B站视频链接")
    base = url.split('video/')[1]
    #此时会出现两种情况BVxxx/?或BVxxx?
    if base[12] == '/':
        return base.split('/?')[0]
    else:
        return base.split('?')[0]

# 获取cid函数,返回cid列表
def get_cid(bvid):
    result = []
    url = 'https://api.bilibili.com/x/web-interface/view'
    params = {
        'bvid': bvid
    }
    try:
        res = requests.get(url=url, headers=headers, cookies=cookies_dict, params=params, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        text = json.loads(res.text)
        if text.get("code") != 0:
            raise Exception(f"获取视频信息失败, code:{text['code']}, msg:{text.get('message')}")
        pages = text['data']['pages']
        for page in pages:
            result.append(page['cid'])
        return result
    except Exception as e:
        raise Exception(f"获取cid异常：{str(e)}")

# 获取w_rid参数函数
def get_w_rid(url, target_cid):
    bvid = get_bvid(url=url)
    wts = int(time.time())
    params = {
        "bvid": bvid,
        "cid": target_cid,  
        "qn": 80,
        "platform": "html5",
        "fnver": 0,
        "wts": wts
    }
    query = urllib.parse.urlencode(params)
    mixin_key = get_mixin_key()
    w_rid = md5((query + mixin_key).encode()).hexdigest()
    params['w_rid'] = w_rid
    params = dict(sorted(params.items()))
    return params

# 获取MP4并且流式下载
def get_video(url):
    # 处理多P逻辑
    bvid = get_bvid(url)
    cid_list = get_cid(bvid)
    print(f"检测视频分P数量：{len(cid_list)}")
    if len(cid_list) > 1:
        print(f"CID列表：{cid_list}")
        select_idx = int(input("请输入下载分P序号（从0开始）："))
        target_cid = cid_list[select_idx]
    else:
        target_cid = cid_list[0]

    video_api = 'https://api.bilibili.com/x/player/wbi/playurl'
    params = get_w_rid(url=url, target_cid=target_cid)
    try:
        res = requests.get(url=video_api, headers=headers, cookies=cookies_dict, params=params, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        text = json.loads(res.text)
        if text.get("code") != 0:
            raise Exception(f"播放接口请求失败, code:{text['code']}, msg:{text.get('message')}")

        data = text['data']
        # 判断是否存在合并MP4资源
        if "durl" not in data or len(data["durl"]) == 0:
            raise Exception("当前视频没有预合成一体MP4！html5模式无法下载，请使用DASH(m4s)方案")

        mp4_url = data['durl'][0]['url']
        quality = data['quality']
        print(f"成功获取MP4直链，当前画质编号：{quality}（html5模式上限720P）")

        save_name = f"{bvid}_cid{target_cid}.mp4"
        # 流式下载，防止大视频占用内存
        print(f"开始下载 -> {save_name}")
        video_resp = requests.get(mp4_url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)
        video_resp.raise_for_status()
        chunk_size = 1024 * 1024
        with open(save_name, 'wb') as f:
            for chunk in video_resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        print(f'视频下载完成，画质为{quality}')

    except Exception as e:
        print(f"下载失败：{str(e)}")


if __name__ == '__main__':
    try:
        input_url = input('请输入B站视频网址：').strip()
        get_video(input_url)
    except Exception as err:
        print(f"程序运行异常：{err}")