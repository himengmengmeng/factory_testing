# seller_models/utils.py
import jwt
from django.conf import settings

def decode_jwt(token):
    """
    解析JWT token并返回payload
    """
    try:
        # 注意：这里假设JWT使用HS256算法，如果使用其他算法需要调整
        # 实际使用时可能需要验证签名，但这里只做解析
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except jwt.InvalidTokenError:
        return None

def get_seller_id_from_token(access_token):
    """
    从access token中提取seller_id
    """
    decoded = decode_jwt(access_token)
    if decoded and 'seller_id' in decoded:
        return decoded['seller_id']
    return None