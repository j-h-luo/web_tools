import re
import requests
from urllib.parse import urlparse

OUTPUT_FILE = "valid_keys.txt"

API_TEMPLATES = {
    "amap": [
        ("高德 Web API", "https://restapi.amap.com/v3/direction/walking?origin=116.434307,39.90909&destination=116.434446,39.90816&key={value}"),
        ("高德 JS API", "https://restapi.amap.com/v3/geocode/regeo?key={value}&s=rsv3&location=116.434446,39.90816&callback=jsonp_258885_&platform=JS"),
        ("高德小程序", "https://restapi.amap.com/v3/geocode/regeo?key={value}&location=117.19674%2C39.14784&extensions=a11&s=rsx&platform=WXJS&appname=c589cf63f592ac13bcab35f8cd18f495&sdkversion=1.2.0&logversion=2.0")
    ],
    "baidu": [
        ("百度 Web API", "https://api.map.baidu.com/place/v2/search?query=ATM机&tag=银行&region=北京&output=json&ak={value}"),
        ("百度 iOS API", "https://api.map.baidu.com/place/v2/search?query=ATM#l&tag=Rf&region=#L#&output=json&ak={value}=iPhone7%2C2&mcode=com.didapinche.taxi&os=12.5.6")
    ],
    "tencent": [
        ("腾讯 Web API", "https://apis.map.qq.com/ws/place/v1/search?keyword=酒店&boundary=nearby(39.908491,116.374328,1000)&key={value}")
    ]
}

INVALID_KEY_HINTS = [
    "INVALID_USER_KEY", "INVALID_USERAK", "key is illegal", "ak非法",
    "无效的ak", "无效的key", "权限校验失败", "开发者权限", "未授权"
]

def extract_key_and_api(html):
    pattern = r'(https?:)?//([^\s"\'<>]+?(?:key|ak)=([a-zA-Z0-9\-_]+))'
    matches = re.findall(pattern, html)
    results = []
    for _, full_url, key in matches:
        parsed = urlparse("//" + full_url if not full_url.startswith("http") else full_url)
        domain_path = parsed.netloc + parsed.path
        results.append((domain_path, key))
    return results

def identify_vendor(domain_path):
    if "amap.com" in domain_path:
        return "amap"
    elif "baidu.com" in domain_path:
        return "baidu"
    elif "map.qq.com" in domain_path or "qq.com" in domain_path:
        return "tencent"
    else:
        return None

def is_key_valid(response_text):
    invalid_key_hints = [
        "INVALID_USER_KEY", "INVALID_USERAK", "key is illegal", "ak非法",
        "无效的ak", "无效的key", "权限校验失败", "开发者权限", "未授权"
    ]
    parameter_error_hints = [
        "参数不存在", "参数错误", "缺少参数", "禁用", "parameter missing", "disabled"
    ]

    text = response_text.lower()

    if any(bad.lower() in text for bad in invalid_key_hints):
        return "invalid"
    elif any(param.lower() in text for param in parameter_error_hints):
        return "param_error"
    else:
        return "valid"

def test_key(vendor, key, origin_url):
    valid_results = []
    if vendor not in API_TEMPLATES:
        print("    [警告] 未识别服务商，跳过")
        return valid_results

    print(f"  [测试中] 测试 {vendor.upper()} key: {key}")
    for api_name, template in API_TEMPLATES[vendor]:
        test_url = template.replace("{value}", key)
        try:
            resp = requests.get(test_url, timeout=5)
            status = is_key_valid(resp.text)

            if status == "valid":
                print(f"    [有效] 可用 → {api_name}")
                valid_results.append({
                    "vendor": vendor,
                    "api_name": api_name,
                    "key": key,
                    "source": origin_url,
                    "test_url": test_url
                })
            elif status == "param_error":
                print(f"    [警告] 参数问题 → {api_name}")
            else:
                print(f"    [无效] 不可用 → {api_name}")
        except Exception as e:
            print(f"    [警告] 请求失败 → {api_name} ：{e}")
    return valid_results

def save_valid_keys(valid_list):
    if not valid_list:
        return
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for item in valid_list:
            f.write(f"[{item['vendor']}] {item['api_name']}\n")
            f.write(f"Source: {item['source']}\n")
            f.write(f"Key: {item['key']}\n")
            f.write(f"Tested URL: {item['test_url']}\n")
            f.write("-" * 40 + "\n")

def main():
    domain = input("请输入要检测的域名（例如 example.com）: ").strip()
    if not domain.startswith("http"):
        domain = "http://" + domain

    print(f"[*] 正在请求网页源码：{domain}")
    try:
        html = requests.get(domain, timeout=8).text
        found = extract_key_and_api(html)
        if not found:
            print("[-] 未发现带 key= 或 ak= 的链接")
            return

        all_valid = []
        print(f"[发现] 共发现 {len(found)} 个疑似 key 链接")
        for path, key in found:
            print(f"\n[+] 链接：{path}")
            print(f"    提取 key: {key}")
            vendor = identify_vendor(path)
            results = test_key(vendor, key, path)
            all_valid.extend(results)

        if all_valid:
            print(f"\n[+] 共发现 {len(all_valid)} 个有效 key，已保存到 {OUTPUT_FILE}")
            save_valid_keys(all_valid)
        else:
            print("\n[未发现] 可用 key")

    except Exception as e:
        print(f"[!] 页面请求失败: {e}")

if __name__ == "__main__":
    main()
