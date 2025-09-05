from itsdangerous import URLSafeTimedSerializer
salt='otpverify'
def entoken(data):
    serializer=URLSafeTimedSerializer('code@123')
    return serializer.dumps(data,salt=salt)
def dntoken(data):
    serializer=URLSafeTimedSerializer('code@123')
    return serializer.loads(data,salt=salt)