import oss2
auth = oss2.Auth('id', 'secret')
req = oss2.http.Request('GET', 'http://bucket.oss-cn-hangzhou.aliyuncs.com/key', params={'response-content-disposition': "inline; filename*=UTF-8''%E6%B5%8B%E8%AF%95.pdf"})
auth._sign_request(req, 'bucket', 'key')
print('StringToSign:', req.headers.get('Authorization'))
