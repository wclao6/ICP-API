# -- coding: utf-8 --**
# by wclao6
import base64
import hashlib
import json
import time
import uuid
import requests
import random
import socket
import sys 
from urllib import parse
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from flask import Flask, request, jsonify, render_template , make_response 
from flask_caching import Cache
from crack import Crack, generate_pointjson, checkImage



# 在文件顶部添加图标常量定义 
ICONS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "retry": "🔄",
    "lock": "🔒",
    "unlock": "🔓",
    "cache": "💾",
    "network": "🌐",
    "time": "⏱️",
    "stop": "⛔"
}

app = Flask(__name__)
cache = Cache(config={'CACHE_TYPE': 'FileSystemCache', 'CACHE_DIR': '/tmp/icp_app_cache'})
cache.init_app(app)

crack = Crack()


def aes_ecb_encrypt(plaintext: bytes, key: bytes, block_size=16):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key.encode()), modes.ECB(), backend=backend)
    padding_length = block_size - (len(plaintext) % block_size)
    padded = plaintext + bytes([padding_length]) * padding_length
    return base64.b64encode(cipher.encryptor().update(padded) + cipher.encryptor().finalize()).decode('utf-8')


def auth():
    t = str(round(time.time()))
    data = {
        "authKey": hashlib.md5(("testtest" + t).encode()).hexdigest(),
        "timeStamp": t
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://beian.miit.gov.cn/",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        time.sleep(0.4)
        resp = requests.post("https://hlwicpfwc.miit.gov.cn/icpproject_query/api/auth",
                             headers=headers, data=parse.urlencode(data)).json()
        return resp["params"]["bussiness"]
    except Exception as e:
        print(f"auth error: {e}")
        return -1


def getImage(token):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://beian.miit.gov.cn/",
        "Token": token
    }
    payload = {
        "clientUid": "point-" + str(uuid.uuid4())
    }
    try:
        time.sleep(0.4)
        resp = requests.post("https://hlwicpfwc.miit.gov.cn/icpproject_query/api/image/getCheckImagePoint",
                             headers=headers, json=payload).json()
        return resp["params"], payload["clientUid"]
    except Exception as e:
        print(f"getImage error: {e}")
        return -1, None

 
# 全局常量定义（提高可配置性）   
info_url = "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/icpAbbreviateInfo/queryByCondition" 
info_urlx = "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/icpAbbreviateInfo/queryDetailByAppAndMiniId" 

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://beian.miit.gov.cn/", 
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://beian.miit.gov.cn", 
    "Connection": "keep-alive"
}

#web查询方法
def queryWeb(sign, uuid_token, name, token, serviceType):
    headers = {
        **COMMON_HEADERS,
        "Token": token,
        "Sign": sign,
        "Uuid": uuid_token,
        "Cookie": "__jsluid_s=" + str(uuid.uuid4().hex[:32]) 
    }
    
    data = {
        "pageNum": "",
        "pageSize": "100",
        "unitName": name,
        "serviceType": serviceType
    }

    try:
        # 使用原始请求方式 
        time.sleep(0.8)
        resp = requests.post(info_url, headers=headers, data=json.dumps(data).replace(" ", ""))
        # 检查HTTP状态码
        if resp.status_code  != 200:
            print(f"{ICONS['error']} HTTP错误 | 状态码: {resp.status_code}  | 响应: {resp.text[:200]}") 
            return {"code": resp.status_code,  "msg": "HTTP错误"} 
        
        beian_info = resp.json() 
        
        # 检查响应结构 
        if not isinstance(beian_info, dict) or 'params' not in beian_info:
            print(f"{ICONS['warning']} 响应结构异常: {beian_info}")
            return {
                "code": beian_info.get('code'), 
                "msg": beian_info.get('msg') 
            }
        # 提取记录列表 
        records = beian_info['params'].get('list', [])
        total = beian_info['params'].get('total', 0)
        
        print(f"{ICONS['success']} 查询成功 | 共找到{len(records)}条记录 | 总数:{total}")
        domain_list = []
        # 处理每条记录
        for info_base in records:
            domain_list.append({  
                'domain_owner': info_base.get('unitName',  ''),
                'domain_name': info_base.get('domain',  ''),
                'domain_licence': info_base.get('mainLicence',  ''),
                'website_licence': info_base.get('serviceLicence',  ''),
                'domain_type': info_base.get('natureName',  ''),
                'domain_content_approved': info_base.get('contentTypeName',  '无'),
                'domain_status': info_base.get('limitAccess',  ''),
                'domain_approve_date': info_base.get('updateRecordTime',  '')
            })
            
    except Exception as e:
        print(f"{ICONS['error']} 查询出错: {str(e)}")
        return {"code": 500, "msg": f"查询出错: {str(e)}"}
    
    return {
        "code": 200, 
        "msg": "success", 
        "data": domain_list, 
        "total": len(domain_list)
    }

#app+wx查询方法
def queryAppWx(sign, uuid_token, name, token, serviceType):   
    headers = {
        **COMMON_HEADERS,
        "Token": token,
        "Sign": sign,
        "Uuid": uuid_token,
        "Cookie": "__jsluid_s=" + str(uuid.uuid4().hex[:32])
    }
    
    data = {
        "pageNum": "",  
        "pageSize": "100", 
        "unitName": name,
        "serviceType": serviceType
    }
    
    try:
        # 使用原始请求方式 
        resp = requests.post(info_url, headers=headers, data=json.dumps(data).replace(" ", ""))
        # 检查HTTP状态码
        if resp.status_code  != 200:
            print(f"{ICONS['error']} HTTP错误 | 状态码: {resp.status_code}  | 响应: {resp.text[:200]}") 
            return {"code": resp.status_code,  "msg": "HTTP错误"} 
        
        beian_info = resp.json() 
         
        # 检查响应结构 
        if not isinstance(beian_info, dict) or 'params' not in beian_info:
            print(f"{ICONS['warning']} 响应结构异常: {beian_info}")
            return {
                "code": beian_info.get('code'), 
                "msg": beian_info.get('msg') 
            }
        # 提取记录列表 
        records = beian_info['params'].get('list', [])
        total = beian_info['params'].get('total', 0)
        
        print(f"{ICONS['success']} 查询成功 | 共找到{len(records)}条记录 | 总数:{total}")
        domain_list = []
        # 循环dataId进行详细查询处理每条记录
        for info_base in records:
            datax = '{"serviceType":' + str(serviceType) + ',"dataId":"' + str(info_base['dataId']) + '"}'
            time.sleep(0.4)
            respx = requests.post(info_urlx, headers=headers,  data=datax.encode("utf-8"))

            # 检查HTTP状态码
            if respx.status_code  != 200:
                print(f"{ICONS['error']} HTTP错误 | 状态码: {respx.status_code}  | 响应: {respx.text[:200]}") 
                return {"code": respx.status_code,  "msg": "HTTP错误"} 
            
            beian_infox = respx.json() 
             
            # 检查响应结构 
            if not isinstance(beian_infox, dict) or 'params' not in beian_infox:
                print(f"{ICONS['warning']} 响应结构异常: {beian_infox}")
                return {
                    "code": beian_infox.get('code'), 
                    "msg": beian_infox.get('msg') 
                }
            recordsx = beian_infox['params']

            domain_list.append({  
                'domain_owner': recordsx.get('unitName',  ''),
                'domain_name': recordsx.get('serviceName',  ''),
                'domain_licence': recordsx.get('mainLicence',  ''),
                'website_licence': recordsx.get('serviceLicence',  ''),
                'domain_type': recordsx.get('natureName',  ''),
                'domain_content_approved': recordsx.get('contentTypeName',  '无'),
                'domain_status': recordsx.get('limitAccess',  ''),
                'domain_approve_date': recordsx.get('updateRecordTime',  '')
            })
            
    except Exception as e:
        print(f"{ICONS['error']} 查询出错: {str(e)}")
        return {"code": 500, "msg": f"查询出错: {str(e)}"}
    
    return {
        "code": 200, 
        "msg": "success", 
        "data": domain_list, 
        "total": len(domain_list)
    }

 
# 全局常量定义
MAX_ATTEMPTS = 20 
CACHE_KEY = 'sign_info'   
CACHE_TIMEOUT = 20  
 
def common_query_handler(item, query_func, serviceType):
    """通用查询处理器（支持凭证共享）"""
    attempt = 0 
    while attempt < MAX_ATTEMPTS:
        attempt += 1  
        print(f"\n{ICONS['retry']} 尝试 [{attempt}/{MAX_ATTEMPTS}] {'━'*20}")
        
        # ================= 阶段1：缓存凭证查询 =================
        cached_sign = cache.get(CACHE_KEY)   
        if cached_sign:
            try:
                sign_data = json.loads(cached_sign)  
                if not all(k in sign_data for k in ('sign', 'uuid', 'token')):
                    raise ValueError("缓存凭证结构不完整")
                
                print(f"{ICONS['cache']} 使用缓存凭证 | sign:{sign_data['sign'][:6]}.. uuid:{sign_data['uuid'][:8]}..")
                result = query_func(sign_data['sign'], sign_data['uuid'], item, sign_data['token'], serviceType)
                
                if isinstance(result, dict) and result.get('code')  in (429, 403):
                    print(f"{ICONS['stop']} 终止状态码 {result.get('code')}  | {ICONS['lock'] if result['code']==403 else ICONS['time']}")
                    return jsonify(result)
                
                if result['code'] == 200:
                    print(f"{ICONS['success']} 缓存凭证有效")
                    return jsonify(result)
                
                print(f"{ICONS['error']} 凭证失效 [{result['code']}]: {result.get('msg',' 未知错误')}")
                cache.delete(CACHE_KEY)  
                
            except json.JSONDecodeError:
                print(f"{ICONS['error']} JSON解析失败")
                cache.delete(CACHE_KEY)  
            except Exception as e:
                print(f"{ICONS['warning']} 异常 [{type(e).__name__}]: {str(e)}")
                traceback.print_exc()  
                cache.delete(CACHE_KEY)  
 
        # ================= 阶段2：新凭证获取 =================
        try:
            print(f"{ICONS['network']} 获取新凭证...")
            token, sign, uuid = fetch_new_credentials()
            time.sleep(0.8)    # 防止请求风暴 
            
            result = query_func(sign, uuid, item, token, serviceType)
            
            if isinstance(result, dict) and result.get('code')  in (429, 403):
                print(f"{ICONS['stop']} 终止状态码 {result.get('code')}  | {ICONS['lock'] if result['code']==403 else ICONS['time']}")
                return jsonify(result)   
 
            cache.set(  
                CACHE_KEY,
                json.dumps({'sign':  sign, 'uuid': uuid, 'token': token}),
                timeout=CACHE_TIMEOUT
            )
            print(f"{ICONS['time']} 凭证生效: {CACHE_TIMEOUT}秒")
            return jsonify(result)
            
        except Exception as e:
            error_type = type(e).__name__
            print(f"{ICONS['warning']} 异常 [{error_type}]: {str(e)}")
            wait_time = min(0.5 * (1.5 ** attempt), 2)
            print(f"{ICONS['time']} 等待 {wait_time:.1f}秒...")
            time.sleep(wait_time)  
            
    return jsonify({
        "error": "MaxAttemptsExceeded",
        "code": 429,
        "message": f"超过最大尝试次数({MAX_ATTEMPTS})"
    }), 429


def fetch_new_credentials():
    """统一凭证获取流程"""
    if (token := auth()) == -1:
        raise ValueError(f"{ICONS['error']} API令牌获取失败")
    print(f"{ICONS['success']} 获取API令牌 | token:{token[:8]}..")
    
    params, clientUid = getImage(token)
    if params == -1:
        raise ConnectionError(f"{ICONS['error']} 验证码获取失败")
    print(f"{ICONS['success']} 获取验证码 | uuid:{params['uuid'][:8]}.. key:{params['secretKey'][:6]}..")
    
    pointjson = generate_pointjson(
        params["bigImage"],
        params["smallImage"],
        params["secretKey"]
    )
    print(f"{ICONS['network']} 生成坐标数据 | 长度:{len(pointjson)}")
    
    if not (sign := checkImage(
        params["uuid"],
        params["secretKey"],
        clientUid,
        pointjson,
        token 
    )):
        raise RuntimeError(f"{ICONS['error']} 验证码识别失败")
        
    print(f"{ICONS['success']} 验证成功 | sign:{sign[:12]}..")
    return token, sign, params["uuid"]


# ==== 合法路由白名单 ====
ALLOWED_ROUTES = {
    '/': ['GET'],
    '/static/favicon.ico':  ['GET'],
    '/static/script.js':  ['GET'],
    '/static/styles.css':  ['GET'],
    '/buzhidaoa': ['GET'],
    '/queryweb/<item>': ['GET'],
    '/queryapp/<item>': ['GET'],
    '/querywx/<item>': ['GET']
}

"""增强型路由防火墙""" 
@app.before_request  
def firewall():
   
    path = request.path  
    method = request.method  
    client_ip = request.remote_addr  
    timestamp = time.strftime('%Y-%m-%d  %H:%M:%S')
    
    # 白名单检查逻辑
    is_allowed = any(
        (('<' in route and path.startswith(route.split('<')[0]))  or path == route)
        and method in methods 
        for route, methods in ALLOWED_ROUTES.items() 
    )
 
    if not is_allowed:
        # 记录非法访问尝试 
        print(f"⛔ [{timestamp}] 拦截非法访问 | IP: {client_ip} | {method} {path}")
        
        # 强制断开连接
        sock = request.environ.get('werkzeug.socket') 
        if sock:
            try:
                sock.setsockopt(socket.SOL_SOCKET,  socket.SO_LINGER, 
                               struct.pack('ii',  1, 0))
                sock.close() 
            except:
                pass 
        
        # 终止请求处理
        sys.exit(1) 

@app.route('/') 
def hehe():
    return "你就猜去吧"

@app.route('/buzhidaoa') 
def index():
    return render_template('index.html') 

@app.route('/queryweb/<item>') 
def query_web(item):
    """网站备案查询接口（共享凭证）"""
    return common_query_handler(item, queryWeb, 1)
 
@app.route('/queryapp/<item>') 
def query_app(item):
    """APP备案查询接口（共享凭证）"""
    return common_query_handler(item, queryAppWx, 6)
 
@app.route('/querywx/<item>') 
def query_wx(item):
    """小程序备案查询接口（共享凭证）"""
    return common_query_handler(item, queryAppWx, 7)


if __name__ == '__main__':
    app.json.ensure_ascii = False
    app.run(host='0.0.0.0', port=9527)
