import time
import urllib
import hashlib

def app(env, start):
    for _ in range(1000):
        hashlib.sha256(b"heavy computation").hexdigest()
    
    time.sleep(0.05)
    
    get_requests = urllib.parse.parse_qs(env['QUERY_STRING'])
    post_requests_length = env.get('CONTENT_LENGTH', 0)
    
    if post_requests_length:
        post_requests_length = int(post_requests_length)
    
    post_requests_body = env['wsgi.input'].read(post_requests_length)
    
    try:
        post_str = post_requests_body.decode('utf-8')
        post_requests = urllib.parse.parse_qs(post_str)
    except (UnicodeDecodeError, ValueError):
        post_requests = {'_raw_body': [post_requests_body]}
    
    response_body = f"GET: {get_requests}\nPOST: {post_requests}"
    response_headers = [
        ('Content-Type', 'text/plain; charset=utf-8'),
        ('Cache-Control', 'public, max-age=300')
    ]
    
    start('200 OK', response_headers)
    return [response_body.encode('utf-8')]