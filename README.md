# ICP-Checker（魔改版）

一个简单的API，用于查询网站或企业的ICP备案信息。

适用于2025年新版的`工信部ICP/IP地址/域名信息备案管理系统`。

# 特征

✅ 通过 `https://beian.miit.gov.cn/` 查询信息，确保与管局实际信息一致。

✅ 支持查询 网站、APP、小程序的ICP备案信息

✅ 支持自动完成点选验证，存在不小失败率；对于单个查询会循环识别20次直到成功。

✅ 缓存密钥，提高效率；官网凭证现在10-30秒失效。

✅ 提供web页面，便于单个查询

🆕 使用API提供服务，便于集成

🆕 提供路由白名单，加强安全性


# 使用方法

python ICP-Checker.py 

# web页面

http://127.0.0.1:9527/buzhidaoa

# 接口

查询web（支持公司名、主域名、备案号）
http://127.0.0.1:9527/queryweb/xxxxx

查询app（支持公司名、name、备案号）
http://127.0.0.1:9527/queryapp/xxxxx

查询小程序（支持公司名、name、备案号）
http://127.0.0.1:9527/queryweb/xxxxx

# 说明

⚠ 项目仅用于学习交流，不可用于商业及非法用途。

⚠ 此项目是基于https://github.com/openeasm/ICP-API
分支的魔改

# 依赖

建议使用
python3.10版本

永久配置清华镜像源
pip config set global.index-url  https://pypi.tuna.tsinghua.edu.cn/simple

安装依赖包
pip install -r requirements.txt



 
