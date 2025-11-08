import time
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .utils import get_seller_id_from_token
import os
import csv
import json
import pandas as pd
import uuid
import threading
from django.http import JsonResponse,HttpResponse
from datetime import datetime





"""
def model_list(request):
    # API端点
    url = "https://api-us.instaview.ai/zeus/v2/sellers/2iTvJIGGSgfDqljwS6RUFOGPm7X/variants"
    
    # 请求头 - 这些值应该从设置中获取，不要硬编码在代码中
    headers = {
        "X-API-Key": settings.API_KEY,
        "Partner-ID": "instaview",
        "Client-ID": "seller"
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
        error_message = f"Failed to call the API: {str(e)}"
    
    # 渲染模板并传递数据
    context = {
        'variants': variants,
        'error': error_message if 'error_message' in locals() else None
    }
    return render(request, 'models/model_list.html', context)

"""





# 基础API URL
BASE_URL = "https://api-us.instaview.ai"

def refresh_access_token(refresh_token):
    """
    使用refresh_token刷新access_token的函数
    """
    url = f"{BASE_URL}/zeus/v2/sellers/auth/login"
    headers = {
        "Content-Type": "application/json",
        "Client-ID": settings.CLIENT_ID,
        "Partner-ID": settings.PARTNER_ID,
        "X-Request-ID": f"req-refresh-{int(time.time())}"
    }
    
    data = {
        "email": "",
        "grant_type": "refresh_token",
        "password": "",
        "refresh_token": refresh_token
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        token_data = response.json()
        
        # 处理时间戳 - 检查是否是毫秒格式
        access_token_exp = token_data.get('access_token_exp')
        refresh_token_exp = token_data.get('refresh_token_exp')
        
        # 如果时间戳是毫秒格式，转换为秒
        if access_token_exp and access_token_exp > 1e10:  # 如果大于10^10，可能是毫秒
            token_data['access_token_exp'] = access_token_exp / 1000
            
        if refresh_token_exp and refresh_token_exp > 1e10:  # 如果大于10^10，可能是毫秒
            token_data['refresh_token_exp'] = refresh_token_exp / 1000
            
        return token_data
    except requests.exceptions.RequestException as e:
        print(f"刷新token失败: {e}")
        return None




# views.py
@csrf_exempt
def login_view(request):
    """
    登录视图
    """
    # 检查是否有退出参数
    if request.GET.get('logout'):
        request.session.flush()
        messages.info(request, "您已成功退出登录")
        return redirect('login')
    
    # 如果用户已登录，直接重定向到设备列表
    if request.session.get('access_token'):
        return redirect('variant_list')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, "邮箱和密码不能为空")
            return render(request, 'seller_login.html')
        
        # 构建登录请求
        url = f"{BASE_URL}/zeus/v2/sellers/auth/login"
        headers = {
            "Content-Type": "application/json",
            "Client-ID": settings.CLIENT_ID,
            "Partner-ID": settings.PARTNER_ID,
            "X-Request-ID": f"req-{int(time.time())}"  # 使用时间戳作为请求ID
        }
        
        data = {
            "email": email,
            "grant_type": "password",
            "password": password,
            "refresh_token": ""
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # 解析响应
            auth_data = response.json()
            
            # 保存token到session
            request.session['access_token'] = auth_data.get('access_token')
            request.session['refresh_token'] = auth_data.get('refresh_token')
            request.session['first_name'] = auth_data.get('first_name')
            request.session['last_name'] = auth_data.get('last_name')
            
            # 处理时间戳 - 检查是否是毫秒格式
            access_token_exp = auth_data.get('access_token_exp')
            refresh_token_exp = auth_data.get('refresh_token_exp')
            
            # 如果时间戳是毫秒格式，转换为秒
            if access_token_exp and access_token_exp > 1e10:  # 如果大于10^10，可能是毫秒
                access_token_exp = access_token_exp / 1000
                
            if refresh_token_exp and refresh_token_exp > 1e10:  # 如果大于10^10，可能是毫秒
                refresh_token_exp = refresh_token_exp / 1000
                
            request.session['access_token_exp'] = access_token_exp
            request.session['refresh_token_exp'] = refresh_token_exp
            
            # 设置session过期时间为access_token过期时间
            if access_token_exp:
                expiry_time = access_token_exp - time.time()
                if expiry_time > 0:
                    request.session.set_expiry(expiry_time)
            
            # 重定向到设备变体列表页面
            messages.success(request, "登录成功")
            return redirect('variant_list')
            
        except requests.exceptions.RequestException as e:
            error_msg = "登录失败: 请检查邮箱和密码是否正确"
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    error_msg = f"登录失败: {error_detail.get('message', str(e))}"
                except:
                    error_msg = f"登录失败: {str(e)}"
            messages.error(request, error_msg)
    
    return render(request, 'seller_login.html')







def variant_list(request):
    """
    设备变体列表视图
    """
    # 1. 检查用户是否已登录
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, "请先登录")
        return redirect('login')
    
    # 2. 检查是否需要刷新token
    token_exp = request.session.get('access_token_exp')
    refresh_token = request.session.get('refresh_token')
    
    # 如果token即将过期(提前1天)且有refresh_token，则刷新token
    if token_exp and refresh_token and token_exp - time.time() < 24 * 60 * 60:
        new_token_data = refresh_access_token(refresh_token)
        if new_token_data:
            # 更新session中的token信息
            request.session['access_token'] = new_token_data.get('access_token')
            request.session['refresh_token'] = new_token_data.get('refresh_token', refresh_token)
            request.session['access_token_exp'] = new_token_data.get('access_token_exp')
            request.session['refresh_token_exp'] = new_token_data.get('refresh_token_exp')
            
            # 更新access_token变量以供后续使用
            access_token = new_token_data.get('access_token')
            
            # 更新session过期时间
            if new_token_data.get('access_token_exp'):
                expiry_time = new_token_data.get('access_token_exp') - time.time()
                if expiry_time > 0:
                    request.session.set_expiry(expiry_time)
        else:
            # 刷新失败，清除session并重定向到登录
            request.session.flush()
            messages.error(request, "会话已过期，请重新登录")
            return redirect('login')
    
    # 3. 从token中获取seller_id
    seller_id = get_seller_id_from_token(access_token)
    if not seller_id:
        messages.error(request, "无法从token中获取seller信息")
        return redirect('login')
    
    # 4. 获取分页参数
    try:
        page = max(1, int(request.GET.get('page', 1)))
        limit = max(1, min(100, int(request.GET.get('limit', 10))))  # 限制每页最多100条
    except ValueError:
        page = 1
        limit = 10
        
    skip = (page - 1) * limit
    
    # 5. 获取搜索参数
    search_query = request.GET.get('search', '').strip()
    
    # 6. 构建API请求
    url = f"{BASE_URL}/zeus/v2/sellers/{seller_id}/device-variants"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Partner-ID": settings.PARTNER_ID,
        "Client-ID": settings.CLIENT_ID
    }
    
    params = {
        "skip": skip,
        "limit": limit
    }
    
    # 7. 如果有搜索查询，添加到参数中
    if search_query:
        params["search"] = search_query
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        total_count = data.get("total_count", 0)
        
        # 8. 计算分页信息
        total_pages = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 1
        
        # 9. 确保当前页不超过总页数
        if page > total_pages:
            page = total_pages
            skip = (page - 1) * limit
            # 重新请求正确页面的数据
            params["skip"] = skip
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
        
        # 10. 应用客户端搜索（如果API不支持搜索）
        if search_query and not params.get("search"):
            items = [item for item in items if 
                    search_query.lower() in item.get("name", "").lower() or 
                    search_query.lower() in item.get("model", {}).get("model_name", "").lower()]
            total_count = len(items)
            total_pages = max(1, (total_count + limit - 1) // limit) if total_count > 0 else 1
        
        # 11. 生成页码范围（关键步骤：替代get_range过滤器）
        page_range = range(1, total_pages + 1)
        
        context = {
            'items': items,
            'current_page': page,
            'total_pages': total_pages,
            'page_range': page_range,  # 添加页码范围
            'limit': limit,
            'search_query': search_query,
            'total_count': total_count
        }
        
        return render(request, 'variant_list.html', context)
        
    except requests.exceptions.RequestException as e:
        error_msg = f"获取设备列表失败: {str(e)}"
        
        # 如果是认证错误，清除session并重定向到登录
        if hasattr(e, 'response') and e.response and e.response.status_code in [401, 403]:
            request.session.flush()
            messages.error(request, "认证已过期，请重新登录")
            return redirect('login')
        
        # 尝试获取更详细的错误信息
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                error_msg = f"获取设备列表失败: {error_detail.get('message', str(e))}"
            except:
                pass
        
        messages.error(request, error_msg)
        return render(request, 'variant_list.html', {'items': [], 'total_count': 0})
    












"""
    检查DID绑定状态并执行相应绑定操作
    通过GET请求传递参数
"""



# 存储处理进度的全局变量（生产环境建议使用Redis或数据库）
PROGRESS_STORE = {}

def device_check_tool(request):
    """设备检查工具主页面"""
    return render(request, 'device_check.html')

@csrf_exempt
def check_and_bind_devices(request):
    """检查DID绑定状态并执行相应操作"""
    if request.method == 'POST':
        try:
            # 获取用户输入的参数
            data = json.loads(request.body)
            base_url = data.get('base_url')
            seller_id = data.get('seller_id')
            api_key = data.get('api_key')
            target_variant_id = data.get('target_variant_id')
            
            # 验证必需参数
            if not all([base_url, seller_id, api_key, target_variant_id]):
                return JsonResponse({
                    'status': 'error',
                    'message': '缺少必需参数'
                }, status=400)
            
            # CSV文件路径
            csv_file_path = os.path.join(settings.BASE_DIR, 'DID_check.csv')
            
            # 检查文件是否存在
            if not os.path.exists(csv_file_path):
                return JsonResponse({
                    'status': 'error',
                    'message': f'CSV文件不存在: {csv_file_path}'
                }, status=400)
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 初始化进度
            PROGRESS_STORE[task_id] = {
                'current': 0,
                'total': 0,
                'status': 'processing',
                'results': []
            }
            
            # 在后台处理任务
            thread = threading.Thread(
                target=process_devices_task,
                args=(task_id, base_url, seller_id, api_key, target_variant_id, csv_file_path)
            )
            thread.daemon = True
            thread.start()
            
            return JsonResponse({
                'status': 'started',
                'task_id': task_id,
                'message': '任务已开始处理'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'处理过程中发生异常: {str(e)}'
            }, status=500)
    
    else:
        return JsonResponse({
            'status': 'error',
            'message': '只支持POST请求'
        }, status=405)

def process_devices_task(task_id, base_url, seller_id, api_key, target_variant_id, csv_file_path):
    """后台处理任务"""
    try:
        # 读取CSV文件
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = list(csv.DictReader(csvfile))
            total_rows = len(csv_reader)
            
            # 更新总进度
            PROGRESS_STORE[task_id]['total'] = total_rows
            
            for row_num, row in enumerate(csv_reader, 1):
                device_id = row.get('Device Id', '').strip()
                access_key = row.get('Access Key', '').strip()
                
                # 更新当前进度
                PROGRESS_STORE[task_id]['current'] = row_num
                
                if not device_id:
                    PROGRESS_STORE[task_id]['results'].append({
                        'row': row_num,
                        'device_id': device_id,
                        'status': 'error',
                        'message': 'Device Id为空',
                        'action': 'skipped'
                    })
                    continue
                
                # 设备处理逻辑
                result = process_single_device(
                    base_url, seller_id, api_key, target_variant_id, 
                    device_id, row_num
                )
                PROGRESS_STORE[task_id]['results'].append(result)
        
        # 标记任务完成
        PROGRESS_STORE[task_id]['status'] = 'completed'
        
    except Exception as e:
        PROGRESS_STORE[task_id]['status'] = 'error'
        PROGRESS_STORE[task_id]['error'] = str(e)

def process_single_device(base_url, seller_id, api_key, target_variant_id, device_id, row_num):
    """处理单个设备"""
    try:
        # 第一步：检查设备绑定状态
        check_url = f"{base_url}/zeus/v2/sellers/{seller_id}/devices/{device_id}"
        headers = {
            'X-API-Key': api_key,
            'Partner-ID': 'instaview',
            'Client-ID': 'seller'
        }
        
        response = requests.get(check_url, headers=headers, timeout=(10, 30))
        
        if response.status_code == 200:
            # 设备已绑定
            device_data = response.json()
            current_variant_id = device_data.get('device_variant_id')
            
            if current_variant_id == target_variant_id:
                # 已经是目标variant id，无需操作
                return {
                    'row': row_num,
                    'device_id': device_id,
                    'status': 'success',
                    'message': f'已绑定目标variant id: {target_variant_id}',
                    'action': 'none'
                }
            else:
                # 需要更新variant id
                update_url = f"{base_url}/zeus/v2/sellers/{seller_id}/floating-did/update-variant"
                update_data = {
                    "did": device_id,
                    "variant_id": target_variant_id
                }
                
                update_response = requests.post(
                    update_url, 
                    headers=headers, 
                    json=update_data,
                    timeout=(10, 30)
                )
                
                if update_response.status_code == 200:
                    return {
                        'row': row_num,
                        'device_id': device_id,
                        'status': 'success',
                        'message': f'成功更新variant id为: {target_variant_id}',
                        'action': 'updated'
                    }
                else:
                    return {
                        'row': row_num,
                        'device_id': device_id,
                        'status': 'error',
                        'message': f'更新失败: {update_response.status_code} - {update_response.text}',
                        'action': 'update_failed'
                    }
        
        elif response.status_code == 404:
            # 设备未绑定，需要绑定
            bind_url = f"{base_url}/zeus/v2/sellers/{seller_id}/devices/assign-dids"
            bind_data = {
                "did": device_id,
                "variant_id": target_variant_id
            }
            
            bind_response = requests.post(
                bind_url, 
                headers=headers, 
                json=bind_data,
                timeout=(10, 30)
            )
            
            if bind_response.status_code == 200:
                return {
                    'row': row_num,
                    'device_id': device_id,
                    'status': 'success',
                    'message': f'成功绑定variant id: {target_variant_id}',
                    'action': 'bound'
                }
            else:
                return {
                    'row': row_num,
                    'device_id': device_id,
                    'status': 'error',
                    'message': f'绑定失败: {bind_response.status_code} - {bind_response.text}',
                    'action': 'bind_failed'
                }
        
        else:
            # 其他错误
            return {
                'row': row_num,
                'device_id': device_id,
                'status': 'error',
                'message': f'检查状态失败: {response.status_code} - {response.text}',
                'action': 'check_failed'
            }
    
    except requests.exceptions.RequestException as e:
        return {
            'row': row_num,
            'device_id': device_id,
            'status': 'error',
            'message': f'请求异常: {str(e)}',
            'action': 'request_error'
        }

@csrf_exempt
def get_progress(request):
    """获取任务进度"""
    task_id = request.GET.get('task_id')
    
    if not task_id or task_id not in PROGRESS_STORE:
        return JsonResponse({
            'status': 'error',
            'message': '任务不存在'
        }, status=404)
    
    progress_data = PROGRESS_STORE[task_id]
    
    return JsonResponse({
        'status': progress_data['status'],
        'progress': {
            'current': progress_data['current'],
            'total': progress_data['total']
        },
        'results': progress_data['results'][-10:],  # 返回最近10条结果
        'error': progress_data.get('error')
    })

@csrf_exempt
def export_results(request):
    """导出处理结果到Excel"""
    task_id = request.GET.get('task_id')
    
    if not task_id or task_id not in PROGRESS_STORE:
        return JsonResponse({
            'status': 'error',
            'message': '任务不存在'
        }, status=404)
    
    results = PROGRESS_STORE[task_id]['results']
    
    if not results:
        return JsonResponse({
            'status': 'error',
            'message': '没有可导出的结果'
        })
    
    # 转换为DataFrame
    df = pd.DataFrame(results)
    
    # 创建HTTP响应
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"device_check_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    # 写入Excel
    df.to_excel(response, index=False)
    
    return response

@csrf_exempt
def retry_failed_devices(request):
    """重试失败的任务"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            failed_devices = data.get('failed_devices', [])
            base_url = data.get('base_url')
            seller_id = data.get('seller_id')
            api_key = data.get('api_key')
            target_variant_id = data.get('target_variant_id')
            
            results = []
            for device_info in failed_devices:
                device_id = device_info.get('device_id')
                row_num = device_info.get('row')
                
                result = process_single_device(
                    base_url, seller_id, api_key, target_variant_id, 
                    device_id, row_num
                )
                results.append(result)
            
            return JsonResponse({
                'status': 'completed',
                'results': results
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'重试过程中发生异常: {str(e)}'
            }, status=500)




