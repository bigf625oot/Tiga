import oss2
import urllib.parse
auth = oss2.Auth('id', 'secret')
bucket = oss2.Bucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', 'bucket')
params = {'response-content-disposition': "inline; filename*=UTF-8''" + urllib.parse.quote('测试.pdf')}
print(bucket.sign_url('GET', 'key', 60, params=params))
