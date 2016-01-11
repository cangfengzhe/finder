import urllib.request
import pickle
import logging

def log(file_name, logger_name = 'root'):
    '''
    封装一个log包，方便今后使用
    '''
    logger=logging.getLogger(logger_name)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    handler=logging.FileHandler(file_name)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.NOTSET)
    return logger



def open_url(url, encode='utf-8', data=None, headers={}, proxy_ip=None, proxy_port=None):
    """
    对 urllib.request 进行的简单封装
    :param url: 需要打开的网址
    :param data: post 传递的数据
    :param headers: 头文件
    :return: 返回html代码
    """
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        response = urllib.request.urlopen(request)

        if proxy_ip:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy_ip + ':' + proxy_port})
            proxy_auth_handler = urllib.request.ProxyBasicAuthHandler()
            opener = urllib.request.build_opener(proxy_handler, proxy_auth_handler)
            response = opener.open(request)
        html = response.read().decode(encode)

    except Exception as e:
        print(e)
        html = None
    return html


def save():
    pass


# 将数据库返回值的变为list（仅是第一列）
def tuple2list(tuple_list):
    out = []
    for xx in tuple_list:
        out.append(xx[0])
    return out


def save(obj, path):
    with open(path, 'wb') as f:
        pickle.dump(obj, f)


def load(path):
    with open(path, 'rb') as f:
        out = pickle.load(f)
    return out


if __name__ == '__main__':
    html = open_url('http://www.baidu.com')
    print(html)