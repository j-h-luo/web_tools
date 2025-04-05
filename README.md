# ak&key_search

## 功能：

扫描用户提供的域名，检测源码中是否存在ak&key泄露，给出泄露的访问链接。

## 方式：

**提供fofa语法：**(body="webapi.amap.com" || body="api.map.baidu.com" || body="apid.map.qq.com" || body="map.qq.com/api/js?v=") && is_domain=true

1、输入待检测的域名

2、脚本运行，如果检测到秘钥泄露将会输出在txt文件中

![屏幕截图 2025-04-05 165430](C:\Users\86183\Pictures\Screenshots\屏幕截图 2025-04-05 165430.png)



3、最后我们可以通过txt文件中的链接访问服务器资源