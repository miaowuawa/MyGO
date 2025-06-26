import importlib
import json
import random
import subprocess
import sys
import time
from datetime import datetime
from json import JSONDecodeError
from urllib.parse import urlencode

import qrcode
from loguru import logger
from playsound3 import playsound
from requests import HTTPError, RequestException

from util import ERRNO_DICT, NtfyUtil, PushPlusUtil, ServerChanUtil, time_service
from util import bili_ticket_gt_python
from util.BiliRequest import BiliRequest
from service.RiskClient import RiskClient

if bili_ticket_gt_python is not None:
    Amort = importlib.import_module("geetest.TripleValidator").TripleValidator()


def get_qrcode_url(_request, order_id) -> str:
    url = f"https://show.bilibili.com/api/ticket/order/getPayParam?order_id={order_id}"
    data = _request.get(url).json()
    if data.get("errno", data.get("code")) == 0:
        return data["data"]["code_url"]
    raise ValueError("获取二维码失败")



def buy_stream(
        tickets_info_str,
        time_start,
        interval,
        mode,
        total_attempts,
        audio_path,
        pushplusToken,
        serverchanKey,
        https_proxys,
        ntfy_url=None,
        ntfy_username=None,
        ntfy_password=None,
):
    global fesign, buvid3,riskHeader

    if bili_ticket_gt_python is None:
        yield "当前设备不支持本地过验证码，无法使用"
        return

    is_running = True
    left_time = total_attempts
    tickets_info = json.loads(tickets_info_str)
    is_hot_project = tickets_info["isHotProject"]
    cookies = tickets_info["cookies"]

    # 初始化RiskClient，从tickets_info中获取服务器地址
    tickets_info_dict = json.loads(tickets_info_str)
    if tickets_info_dict['ctoken_server']['url'] == "" and is_hot_project:
        logger.warning("防止风控，请在GUI中设置ctoken_server_url参数")
        risk_client = RiskClient("")
    else:
        risk_client = RiskClient(tickets_info_dict['ctoken_server']['url'])
    ctkid = None
    ctoken = ""
    fesign = None
    buvid3 = None

    # 调试输出cookie列表
    #logger.debug(f"完整cookie列表: {json.dumps(cookies, indent=2)}")

    # 查找需要的cookie，不区分大小写
    for cookie in cookies:
        cookie_name = cookie["name"].lower()
        if cookie_name == "fesign":
            fesign = cookie["value"]
            logger.debug(f"找到feSign: {fesign}")
        elif cookie_name == "buvid3":
            buvid3 = cookie["value"]
            logger.debug(f"找到buvid3: {buvid3}")

    # 检查是否找到必要cookie
    if not fesign or not buvid3:
        logger.warning(f"未找到feSign或buvid3 cookie，当前cookie名称: {[c['name'] for c in cookies]}")


    #这里这个ticket要检查一下，没有要获取

    #ticket = risk_client.get_cookie_ticket("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/137.0.0.0",cookies)

    # 向cookie中加入

    if fesign is None or buvid3 is None:
        yield "提示：您的cookie可能有问题，概率触发风控，但是不影响你抢票"
        yield " 如果开始时间还有很久，请重新获取一下cookie，注意一定要打开设备仿真下单一次"

    deviceid = fesign
    riskHeader = risk_client.fake_x_risk_header(buvid3, deviceid)
    phone = tickets_info.get("phone", None)
    tickets_info.pop("cookies", None)
    tickets_info["buyer_info"] = json.dumps(tickets_info["buyer_info"])
    tickets_info["deliver_info"] = json.dumps(tickets_info["deliver_info"])
    logger.info(f"使用代理：{https_proxys}")
    _request = BiliRequest(cookies=cookies, proxy=https_proxys)

    token_payload = {
        "count": tickets_info["count"],
        "screen_id": tickets_info["screen_id"],
        "order_type": 1,
        "project_id": tickets_info["project_id"],
        "sku_id": tickets_info["sku_id"],
        "token": "", # ctoken required here 4 HotProject
        "newRisk": True,
    }

    if time_start != "":
        timeoffset = time_service.get_timeoffset()
        yield "0) 等待开始时间"
        yield f"时间偏差已被设置为: {timeoffset}s"
        try:
            time_difference = (
                    datetime.strptime(time_start, "%Y-%m-%dT%H:%M:%S").timestamp()
                    - time.time()
                    + timeoffset
            )
        except ValueError:
            time_difference = (
                    datetime.strptime(time_start, "%Y-%m-%dT%H:%M").timestamp()
                    - time.time()
                    + timeoffset
            )
        start_time = time.perf_counter()
        end_time = start_time + time_difference
        while time.perf_counter() < end_time:
            pass


    while is_running:
        try:
            # 如果是热门项目且需要刷新ctoken
            if is_hot_project and tickets_info_dict['ctoken_server']['url'] != "":
                try:
                    if ctkid:
                        # 刷新ctoken
                        refresh_result = risk_client.refresh_ctoken(ctkid)
                        ctoken = refresh_result.get("ctoken", "")
                        yield f"刷新ctoken成功: {ctoken[:10]}..."
                    else:
                        # 首次获取ctoken
                        init_result = risk_client.get_ctoken(screen_width=tickets_info_dict['ctoken_server']['screen_width'],
                                                             screen_height=tickets_info_dict['ctoken_server']['screen_height'])
                        ctoken = init_result.get("ctoken", "")
                        ctkid = init_result.get("ctkid", "")
                        yield f"获取初始ctoken成功: {ctoken[:10]}..."

                    # 更新token_payload
                    token_payload["token"] = ctoken
                except Exception as e:
                    yield f"ctoken操作失败: {str(e)}"
                    yield "请检查ctoken服务器是否启动，地址配置是否正确"
                    if not ctoken:
                        continue  # 如果没有ctoken则跳过本次循环
            retry_count = 0
            yield "1）订单准备"
            if is_hot_project and tickets_info_dict['ctoken_server']['url'] != "":
                ctoken = risk_client.refresh_ctoken(ctkid)
            else:
                ctoken = ""
            request_result_normal = _request.post(
                url=f"https://show.bilibili.com/api/ticket/order/prepare?project_id={tickets_info['project_id']}&requestSource=neul-next",
                data=token_payload,
                isJson=True,
            )
            try:
                request_result = request_result_normal.json()
                yield f"请求头: {request_result_normal.headers} // 请求体: {request_result}"

                # 统一错误码检查
                errno = request_result.get("errno", 0)
                code = request_result.get("code", 0)

                # 检查是否为需要重试的错误码
                if code == 100001 or (errno != 0 and errno != 100048 and errno != 100079):
                    yield f"需要重试的错误码: errno={errno}, code={code}"
                    continue

                # 检查是否缺少必要字段
                if "data" not in request_result:
                    yield "错误: 响应缺少data字段"
                    continue
            except JSONDecodeError as e:
                yield f"JSON解析错误: {e}"
                continue
            except Exception as e:
                yield f"处理响应时发生异常: {e}"
                continue

            if code == -401:
                _url = "https://api.bilibili.com/x/gaia-vgate/v1/register"
                try:
                    _data = _request.post(
                        _url,
                        urlencode(request_result["data"]["ga_data"]["riskParams"]),
                    ).json()
                    yield f"验证码请求: {_data}"

                    # 检查验证码请求响应
                    if "data" not in _data or "token" not in _data["data"]:
                        yield "错误: 验证码请求响应缺少必要字段"
                        continue

                    csrf: str = _request.cookieManager.get_cookies_value("bili_jct")  # type: ignore
                    token: str = _data["data"]["token"]

                    try:
                        if _data["data"]["type"] == "geetest":
                            gt = _data["data"]["geetest"]["gt"]
                            challenge: str = _data["data"]["geetest"]["challenge"]
                            geetest_validate: str = Amort.validate(gt=gt, challenge=challenge)
                            geetest_seccode: str = geetest_validate + "|jordan"
                            yield f"geetest_validate: {geetest_validate},geetest_seccode: {geetest_seccode}"

                            _url = "https://api.bilibili.com/x/gaia-vgate/v1/validate"
                            _payload = {
                                "challenge": challenge,
                                "token": token,
                                "seccode": geetest_seccode,
                                "csrf": csrf,
                                "validate": geetest_validate,
                            }
                        elif _data["data"]["type"] == "phone":
                            _payload = {
                                "code": phone,
                                "csrf": csrf,
                                "token": token,
                            }
                        else:
                            yield "这是一个程序无法应对的验证码，脚本无法处理"
                            break

                        _data = _request.post(_url, urlencode(_payload)).json()
                        yield f"validate: {_data}"

                        # 检查验证结果
                        code_str = _data.get("errno") or _data.get("code")
                        if code_str is None:
                            yield "错误: 验证码响应中缺少errno和code字段"
                            continue

                        try:
                            code = int(code_str)
                        except (ValueError, TypeError) as e:
                            yield f"错误: 无法解析验证码错误码: {e}"
                            continue

                        if code == 0:
                            yield "验证码成功"
                        elif code == 100044:
                            yield "检测到100044错误码，尝试新的验证码处理方式"
                            voucher_result = risk_client.get_new_voucher(_request,tickets_info["project_id"],tickets_info["screen_id"])
                            if "error" in voucher_result:
                                yield f"新的验证码处理失败: {voucher_result['error']}"
                            else:
                                yield "新的验证码处理成功"
                                token_payload["voucher"] = voucher_result["voucher"]
                                continue
                        else:
                            yield f"验证码失败 {_data}"
                            continue

                    except Exception as e:
                        yield f"处理验证码时发生异常: {e}"
                        continue

                except Exception as e:
                    yield f"处理验证码结果时发生异常: {e}"
                    continue

                try:
                    prepare_response = _request.post(
                        url=f"https://show.bilibili.com/api/ticket/order/prepare?project_id={tickets_info['project_id']}",
                        data=token_payload,
                        isJson=True,
                    )
                    request_result = prepare_response.json()
                    yield f"prepare: {request_result}"

                    # 检查prepare响应
                    errno = request_result.get("errno", 0)
                    code = request_result.get("code", 0)
                    if errno != 0 or code != 0:
                        yield f"prepare请求失败: errno={errno}, code={code}"
                        continue

                except JSONDecodeError as e:
                    yield f"prepare响应JSON解析错误: {e}"
                    continue
                except Exception as e:
                    yield f"prepare请求异常: {e}"
                    continue


            tickets_info["again"] = 1
            tickets_info["ticket_agent"] = ""
            tickets_info["token"] = request_result["data"]["token"]
            if is_hot_project:
                tickets_info["ptoken"] = request_result["data"]["ptoken"].rstrip("=")  # 去掉尾部等号（如果有）

            confirm_url = f"https://show.bilibili.com/api/ticket/order/confirmInfo?token={tickets_info['token']}&timestamp={time.time() * 1000}&project_id={tickets_info['project_id']}&ptoken={tickets_info['ptoken']}"
            confirm_result = _request.get(url=confirm_url, data=tickets_info, isJson=True)
            yield "订单信息确认：完成，错误码" + str(confirm_result.status_code)

            yield "2）创建订单"

            tickets_info["timestamp"] = int(time.time()) * 100
            tickets_info["requestSource"] = "neul-next"
            tickets_info["newRisk"] = True
            tickets_info["coupon_code"] = "" # 优惠券码不使用
            tickets_info["deviceId"] = deviceid

            # 根据是否是重试请求设置不同的点击位置
            is_retry = retry_count > 0
            if is_retry:
                tickets_info["clickPosition"] = risk_client.fake_retry_click_position(
                    tickets_info_dict['ctoken_server']['screen_width'],
                    tickets_info_dict['ctoken_server']['screen_height'],
                    int(time.time() * 1000)
                )
            else:
                tickets_info["clickPosition"] = risk_client.fake_first_click_position(
                    tickets_info_dict['ctoken_server']['screen_width'],
                    tickets_info_dict['ctoken_server']['screen_height'],
                    int(time.time() * 1000)
                )

            payload = tickets_info
            result = None
            for attempt in range(1, 61):
                if not is_running:
                    yield "抢票结束"
                    break
                try:
                    if tickets_info["ctoken_server"]["url"] != "" and is_hot_project:
                        ctoken = risk_client.refresh_ctoken(ctkid=ctkid).get('ctoken','')
                    else:
                        ctoken = ""
                    payload['ctoken'] = ctoken
                    response = _request.post(
                        url=f"https://show.bilibili.com/api/ticket/order/createV2?project_id={tickets_info['project_id']}&ptoken={tickets_info['ptoken']}",
                        data=payload,
                        isJson=True,
                    )

                    # 添加调试信息
                    yield f"调试信息 - 请求URL: {response.url}"
                    yield f"调试信息 - 状态码: {response.status_code}"
                    yield f"调试信息 - 响应头: {response.headers}"

                    try:
                        ret = response.json()
                        yield f"调试信息 - 完整响应: {ret}"

                        # 检查errno和code字段
                        if "errno" in ret:
                            err = int(ret["errno"])
                        elif "code" in ret:
                            err = int(ret["code"])
                        else:
                            yield "错误: 响应中缺少errno和code字段"
                            yield f"调试信息 - 无效响应结构: {ret}"
                            continue

                        yield f"[尝试 {attempt}/60]  [{err}]({ERRNO_DICT.get(err, '未知错误码')}) | {ret}"

                    except JSONDecodeError as e:
                        yield f"[尝试 {attempt}/60] JSON解析错误: {e}"
                        yield f"调试信息 - 原始响应文本: {response.text}"
                        continue
                    except Exception as e:
                        yield f"[尝试 {attempt}/60] 处理响应时发生异常: {e}"
                        continue
                    retry_count += 1

                    if err == 100034:
                        yield f"更新票价为：{ret['data']['pay_money'] / 100}"
                        tickets_info["pay_money"] = ret["data"]["pay_money"]
                        payload = tickets_info

                    if err in [0, 100048, 100079]:
                        yield "请求成功，停止重试"
                        result = (ret, err)
                        break

                    if err == 100051:
                        break
                    time.sleep(get_delay(interval))

                except RequestException as e:
                    yield f"[尝试 {attempt}/60] 请求异常: {e}"
                    time.sleep(get_delay(interval))

                except Exception as e:
                    yield f"[尝试 {attempt}/60] 未知异常: {e}"
                    time.sleep(get_delay(interval))
            else:
                yield "重试次数过多，重新准备订单"
                continue
            if result is None:
                # if err == 100051:
                retry_count += 1
                yield "token过期，需要重新准备订单"
                continue

            request_result, errno = result
            if errno == 0:
                if "data" not in request_result or "orderId" not in request_result["data"]:
                    yield "错误: 订单创建响应缺少必要字段"
                    continue

                # 新增检查orderCreateTime和token字段
                required_fields = ["orderCreateTime", "token"]
                for field in required_fields:
                    if field not in request_result["data"]:
                        yield f"错误: 订单创建响应缺少{field}字段"
                        continue
            yield "3）抢票成功，尽快支付"
            yield request_result
            if ntfy_url:
                # 使用重复通知功能，每10秒发送一次，持续5分钟
                NtfyUtil.send_repeat_message(
                    ntfy_url,
                    f"抢票成功，bilibili会员购，请尽快前往订单中心付款",
                    title="Bili Ticket Payment Reminder",
                    username=ntfy_username,
                    password=ntfy_password,
                    interval_seconds=15,
                    duration_minutes=5
                )
                yield "已启动重复通知，将每15秒发送一次提醒，持续5分钟"

                if audio_path:
                    playsound(audio_path)
                break

            if mode == 1:
                left_time -= 1
                if left_time <= 0:
                    break
            break

        except JSONDecodeError as e:
            yield f"配置文件格式错误: {e}"
        except HTTPError as e:
            logger.exception(e)
            yield f"请求错误: {e}"
        except Exception as e:
            logger.exception(e)
            yield f"程序异常: {repr(e)}"


def buy(
        tickets_info_str,
        time_start,
        interval,
        mode,
        total_attempts,
        audio_path,
        pushplusToken,
        serverchanKey,
        https_proxys,
        ntfy_url=None,
        ntfy_username=None,
        ntfy_password=None,
):
    for msg in buy_stream(
            tickets_info_str,
            time_start,
            interval,
            mode,
            total_attempts,
            audio_path,
            pushplusToken,
            serverchanKey,
            https_proxys,
            ntfy_url,
            ntfy_username,
            ntfy_password,
    ):
        logger.info(msg)


def buy_new_terminal(
        endpoint_url,
        filename,
        tickets_info_str,
        time_start,
        interval,
        mode,
        total_attempts,
        audio_path,
        pushplusToken,
        serverchanKey,
        https_proxys,
        ntfy_url=None,
        ntfy_username=None,
        ntfy_password=None,
) -> subprocess.Popen:
    command = [sys.executable]
    if not getattr(sys, "frozen", False):
        command.extend(["main.py"])
    command.extend(
        [
            "buy",
            tickets_info_str,
            str(interval),
            str(mode),
            str(total_attempts),
        ]
    )
    if time_start:
        command.extend(["--time_start", time_start])
    if audio_path:
        command.extend(["--audio_path", audio_path])
    if pushplusToken:
        command.extend(["--pushplusToken", pushplusToken])
    if serverchanKey:
        command.extend(["--serverchanKey", serverchanKey])
    if ntfy_url:
        command.extend(["--ntfy_url", ntfy_url])
    if ntfy_username:
        command.extend(["--ntfy_username", ntfy_username])
    if ntfy_password:
        command.extend(["--ntfy_password", ntfy_password])
    if https_proxys:
        command.extend(["--https_proxys", https_proxys])
    command.extend(["--filename", filename])
    command.extend(["--endpoint_url", endpoint_url])
    proc = subprocess.Popen(command)
    return proc


def get_delay(interval):
    random_factor = random.uniform(0.8, 1.2)
    delay = max(50, interval * random_factor)
    return delay / 1000

