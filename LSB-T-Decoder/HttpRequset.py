# -*- coding:utf-8 -*-
import requests

# post_data_type 一般用 1 post_data不会做url编码


def req(url, cellphone_mode=False, not_encode=0, cookies='', header={}, method=0, post_data_type=0, post_data='', post_json={}, return_cookies='', proxy='', proxy_type='', timeout=10, file_name='', allow_redirects=False):
    tmp_header = {}
    proxies = {}
    tmp_cookies = {}
    tmp_post_data = {}
    if 'User-Agent' in header and header['User-Agent'] != '':
        pass
    elif 'user-agent' in header and header['user-agent'] != '':
        pass
    else:
        if cellphone_mode == False:
            tmp_header['User-Agent'] = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/68.0.3440.106 Chrome/68.0.3440.106 Safari/537.36'
        else:
            tmp_header['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'

    tmp_header = dict(tmp_header, **header)
    if cookies:
        for line in cookies.split(';'):
            if line.strip() == '':
                continue

            name, value = line.strip().split('=', 1)
            tmp_cookies[name] = value

#    if post_data:
#        for line in post_data.split('&'):
#            name,value=line.strip().split('=',1)
#            tmp_post_data[name] = value

    if proxy and proxy_type:
        proxies[proxy_type] = proxy
    if method == 0:  # get方式访问
        #print (tmp_cookies)
        if file_name == '':
            r = requests.get(
                url, headers=tmp_header, cookies=tmp_cookies, proxies=proxies, timeout=timeout, allow_redirects=allow_redirects)
        else:
            r = requests.get(url, headers=tmp_header, cookies=tmp_cookies,
                             proxies=proxies, timeout=timeout, stream=True, allow_redirects=allow_redirects)
        #print (r.text)
    if method == 1:  # post方式访问
        if post_data:
            for line in post_data.split('&'):
                #print (line)
                name, value = line.strip().split('=', 1)
                tmp_post_data[name] = value
        #print (tmp_post_data)

        if post_data_type == 0:
            r = requests.post(url, headers=tmp_header, cookies=tmp_cookies,
                              proxies=proxies, data=tmp_post_data, timeout=timeout, allow_redirects=allow_redirects)
        elif post_data_type == 1:
            # post内容不做url编码
            r = requests.post(url, headers=tmp_header, cookies=tmp_cookies, proxies=proxies,
                              data=post_data, timeout=timeout, allow_redirects=allow_redirects)
        else:
            r = requests.post(url, headers=tmp_header, cookies=tmp_cookies,
                              proxies=proxies, json=post_json, timeout=timeout, allow_redirects=allow_redirects)
    if file_name != '':
        tmp_return_cookies = r.cookies.get_dict()

        for tmp_a in tmp_return_cookies:
            return_cookies += tmp_a + "=" + tmp_return_cookies[tmp_a] + "; "

    if not_encode == 0 and file_name == '':
        if r.text.find('charset=gbk') != -1 or r.text.find('charset=gb2312') != -1 or r.text.find('charset="gbk"') != -1:
            r.encoding = "gbk"
        else:
            r.encoding = "utf-8"
    if file_name == '':
        return r.text, return_cookies, r.headers
    else:
        with open(file_name, "wb") as file:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
