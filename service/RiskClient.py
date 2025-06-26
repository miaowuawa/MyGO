from urllib.parse import urlencode

import requests
from typing import Optional, Dict, List, Any
import random
import time
import geetest

from util import BiliRequest


class RiskClient:
    def __init__(self, server_url):
        self.server_url = server_url.rstrip('/')

    def get_ctoken(self, screen_width=360, screen_height=640):
        """
        获取ctoken
        
        参数:
            screen_width (int): 屏幕宽度，默认360
            screen_height (int): 屏幕高度，默认640
            
        返回:
            str: 获取到的ctoken
            
        异常:
            Exception: 当请求失败时抛出
        """
        try:
            payload = {
                "screen_width": screen_width,
                "screen_height": screen_height
            }
            response = requests.post(f"{self.server_url}/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            # 根据README，响应中包含ctkid和ctoken
            return result
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取ctoken失败: {str(e)}")

    def refresh_ctoken(self, ctkid: str) -> Dict[str, str]:
        """
        通过ctkid刷新ctoken

        参数:
            ctkid (str): 之前获取的ctkid

        返回:
            Dict[str, str]: 包含新ctoken的字典

        异常:
            requests.exceptions.RequestException: 当请求失败时抛出
        """
        url = f"{self.server_url}/get/{ctkid}"

        try:
            response = requests.get(url)
            response.raise_for_status()  # 检查HTTP错误
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"刷新ctoken失败: {str(e)}")

    def get_cookie_ticket(self, user_agent: str, cookies: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        通过API获取Cookie_ticket

        参数:
            user_agent (str): 用户代理字符串
            cookies (List[Dict[str, str]]): Cookie数组，每个元素必须包含name和value字段，
                                          可选包含path、domain、expires、max_age、secure、http_only、same_site等字段

        返回:
            Dict[str, Any]: API响应结果，成功时返回服务器响应，失败时返回包含error字段的字典

        异常:
            Exception: 当请求过程中发生错误且无法获取服务器错误信息时抛出
        """
        url = f"{self.server_url}/getticket"
        
        # 验证cookies格式
        formatted_cookies = []
        for cookie in cookies:
            if not isinstance(cookie, dict) or 'name' not in cookie or 'value' not in cookie:
                return {"error": "Cookie格式错误: 每个cookie必须是包含name和value字段的字典"}
            
            # 创建符合http.Cookie结构的字典
            formatted_cookie = {
                "Name": cookie.get('name'),
                "Value": cookie.get('value')
            }
            
            # 添加可选字段
            if 'path' in cookie:
                formatted_cookie["Path"] = cookie['path']
            if 'domain' in cookie:
                formatted_cookie["Domain"] = cookie['domain']
            if 'expires' in cookie:
                formatted_cookie["Expires"] = cookie['expires']
            if 'max_age' in cookie:
                formatted_cookie["MaxAge"] = cookie['max_age']
            if 'secure' in cookie:
                formatted_cookie["Secure"] = cookie['secure']
            if 'http_only' in cookie:
                formatted_cookie["HttpOnly"] = cookie['http_only']
            if 'same_site' in cookie:
                formatted_cookie["SameSite"] = cookie['same_site']
                
            formatted_cookies.append(formatted_cookie)
        
        payload = {
            "user_agent": user_agent,
            "cookies": formatted_cookies
        }

        try:
            response = requests.post(url, json=payload)
            
            # 不立即调用raise_for_status，而是先检查状态码
            if response.status_code >= 400:
                # 尝试解析错误响应
                try:
                    error_data = response.json()
                    # 如果响应中包含error字段，则返回包含该错误信息的字典
                    if "error" in error_data:
                        return {"error": error_data["error"]}
                    # 否则返回整个错误响应
                    return {"error": f"服务器错误: {error_data}"}
                except ValueError:
                    # 如果无法解析JSON，则返回状态码和响应文本
                    return {"error": f"服务器错误 (状态码: {response.status_code}): {response.text}"}
            
            # 如果状态码正常，则返回解析后的JSON响应
            return response.json()
        except requests.exceptions.RequestException as e:
            # 网络错误或其他请求异常
            return {"error": f"请求错误: {str(e)}"}

    @staticmethod
    def fake_retry_click_position(width: int, height: int, start_timestamp_ms: int) -> Dict[str, int]:
        """
        伪造点击位置，适用于重试请求场景，y大概位于屏幕高度从上往下60%到70%之间，x大概位于屏幕宽度从中间开始向左/向右各10%以内的位置
        {
            "x": 240,
            "y": 637,
            "origin": 1750414952801,
            "now": 1750415029734
        }
        这个太简单，开源了
        """


        center_x = width // 2
        x_range = int(width * 0.1)
        x = random.randint(center_x - x_range, center_x + x_range)

        y_min = int(height * 0.6)
        y_max = int(height * 0.7)
        y = random.randint(y_min, y_max)

        return {
            "x": x,
            "y": y,
            "origin": start_timestamp_ms,
            "now": int(time.time() * 1000)
        }

    @staticmethod
    def fake_first_click_position(width: int, height: int, start_timestamp_ms: int) -> Dict[str, int]:
        """
        伪造首次点击位置，和重试请求一样，但是返回的位置应该在屏幕右测60%-80%，屏幕底部80%到100%之间
        这个太简单，开源了
        """
        x_min = int(width * 0.6)
        x_max = int(width * 0.8)
        x = random.randint(x_min, x_max)

        y_min = int(height * 0.8)
        y_max = height
        y = random.randint(y_min, y_max)

        return {
            "x": x,
            "y": y,
            "origin": start_timestamp_ms,
            "now": int(time.time() * 1000)
        }

    @staticmethod
    def fake_x_risk_header(uid:str,deviceid:str):
        """
        伪造x-risk-header，用于重试请求
        用户通过外部广告（渠道 ID=5）访问 B 站 → Cookie 中 opensource=5 → 渠道 ID 为 "5"
用户直接访问 https://www.bilibili.com/comic/ → 渠道 ID 为 "32"
用户通过商城 SDK 访问 B 站（非漫画路径）→ 渠道 ID 为 "1" 所以说渠道固定1
deviceid是buvid4
这个太简单，开源了
        """
        string = "appkey/27eb53fc9058f8c3 mVersion/301 model/iPhone%2011 mallVersion/8401000 brand/Apple osver/18.2 platform/h5 uid/{uid} channel/{channel} deviceId/{deviceid}".format(
            uid=uid,
            channel=1,
            deviceid= deviceid
        )
        return string

    def get_new_voucher(self, req:BiliRequest, project_id:int, screen_id:int) -> dict[str, str] | dict[str, str]:
        """
        破解geetest验证码，获取voucher
        """

        # 第一步，prepare
        prepare_url = f"https://show.bilibili.com/api/ticket/graph/prepare?project_id={project_id}&screen_id={screen_id}&timestamp={int(time.time() * 1000)}"
        prepare_res = req.get(prepare_url)
        if prepare_res.get('errno') != 0:
            return {"error": f"prepare接口错误: {prepare_res.get('msg', '未知错误')}"}
        if prepare_res.get('errno') == 0 and prepare_res.get('data') is None:
            return {"error": "prepare接口返回数据为空，被演了"}
        """
            {
              "errno": 0,
              "errtag": 0,
              "msg": "",
              "data": []
            } 这种返回说明被演了，data是空的
        """
        prepare_res = prepare_res.json()
        # 获取验证码参数
        data = prepare_res['data'][0] if isinstance(prepare_res['data'], list) else prepare_res['data']
        captcha_id = data['captcha_id']
        challenge = data['challenge']
        old_voucher = data['voucher']
        # 第二步，过验证码
        validate = geetest.Validator.Validator()
        result = validate.validate(gt=captcha_id, challenge=challenge)
        seccode = result + "|jordan"

        # 第三步，验证captcha对不对
        check_url = "https://show.bilibili.com/api/ticket/graph/check"
        check_data = {
            'project_id': project_id,
            'screen_id': screen_id,
            'voucher': old_voucher, #老的voucher和新的voucher别混了
            'challenge': challenge,
            'validate': validate,
            'seccode': seccode,
            'success': True
        }

        check_res = req.post(check_url, data=urlencode(check_data)).json()

        # 检查错误是否是0，data是否为空，是的话就被演了

        if check_res.get('errno') == 0 and prepare_res.get('data') is None:
            return {"error": "prepare接口返回数据为空，被演了"}
        if prepare_res.get('errno') != 0:
            return {"error": f"prepare接口错误: {prepare_res.get('msg', '未知错误')}"}
 
        return {
            "new_voucher": prepare_res["data"]["new_voucher"]
        }







