import oss2

auth = oss2.Auth('LTAI5tHNaG9KASNgMXK35DAN', 'dummy_secret')
bucket = oss2.Bucket(auth, 'http://oss-cn-beijing.aliyuncs.com', 'tiga260101')

params = {
    'response-content-type': 'application/pdf',
    'response-content-disposition': "inline; filename*=UTF-8''agent%E7%BB%BC%E8%BF%B0%E4%B8%AD%E6%96%87%E7%BF%BB%E8%AF%91---%E6%9D%8E%E9%A3%9E%E9%A3%9E.pdf"
}

url = bucket.sign_url('GET', 'knowledge/d86187f9-6bff-480b-9155-2d8628999ba7.pdf', 3600, slash_safe=True, params=params)
print(url)
