import urllib.parse

url = "https://tiga260101.oss-cn-beijing.aliyuncs.com/knowledge/d86187f9-6bff-480b-9155-2d8628999ba7.pdf?response-content-type=application%2Fpdf&response-content-disposition=inline%3B%20filename%2A%3DUTF-8%27%27agent%25E7%25BB%25BC%25E8%25BF%25B0%25E4%25B8%25AD%25E6%2596%2587%25E7%25BF%25BB%25E8%25AF%2591---%25E6%259D%258E%25E9%25A3%259E%25E9%25A3%259E.pdf&OSSAccessKeyId=LTAI5tHNaG9KASNgMXK35DAN&Expires=1774763178&Signature=ZfFj4mZdAsdgRIdvty9zvYDBWtE%3D"

parsed = urllib.parse.urlparse(url)
qs = urllib.parse.parse_qs(parsed.query)

for k, v in qs.items():
    print(f"{k}: {v[0]}")
