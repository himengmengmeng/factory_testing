import requests
from django.conf import settings
from django.shortcuts import render

def model_list(request):
    # API端点
    url = "https://api-us.instaview.ai/zeus/v2/sellers/2iTvJIGGSgfDqljwS6RUFOGPm7X/variants"
    
    # 请求头 - 这些值应该从设置中获取，不要硬编码在代码中
    headers = {
        "X-API-Key": settings.API_KEY,
        "Partner-ID": settings.PARTNER_ID,
        "Client-ID": settings.CLIENT_ID
    }
    
    try:
        # 发送GET请求
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果请求失败将抛出异常
        
        # 解析JSON响应
        data = response.json()
        variants = data.get("variants", [])
        
    except requests.exceptions.RequestException as e:
        # 处理请求错误
        variants = []
        error_message = f"API请求失败: {str(e)}"
    
    # 渲染模板并传递数据
    context = {
        'variants': variants,
        'error': error_message if 'error_message' in locals() else None
    }
    return render(request, 'models/model_list.html', context)
