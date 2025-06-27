from urllib.parse import urlencode

import gradio as gr
from service.RiskClient import RiskClient
from tab.go import ways, ways_detail
from util import main_request
import time


def function_test_tab():
    with gr.Column():

        # 新增ctoken测试功能
        with gr.Row():
            gr.Markdown("### ctoken获取测试")
        with gr.Row():
            ctoken_server_ui = gr.Textbox(
                label="ctoken服务器地址，没有不填",
                value="",
                placeholder="请输入ctoken服务器地址，使用官方本地版则填写http://localhost:8080"
            )
            ctoken_test_btn = gr.Button("测试获取ctoken", variant="primary")
            ctoken_output_ui = gr.Textbox(label="ctoken获取结果", interactive=False)

        # ctoken测试功能逻辑
        def test_ctoken(server_url):
            try:
                client = RiskClient(server_url)
                ctoken = client.get_ctoken()
                return f"获取成功: {ctoken}"
            except Exception as e:
                return f"获取失败: {str(e)}"

        ctoken_test_btn.click(
            fn=test_ctoken,
            inputs=[ctoken_server_ui],
            outputs=[ctoken_output_ui]
        )
        with gr.Row():
            gr.Markdown("### 通过验证码测试")
    _request = main_request
    # 验证码选择
    way_select_ui = gr.Radio(
        ways, label="验证码", info="过验证码的方式", type="index", value=ways[0]
    )

    select_way = 0

    def choose_option(way):
        nonlocal select_way
        select_way = way

    way_select_ui.change(choose_option, inputs=way_select_ui, outputs=[])

    test_get_challenge_btn = gr.Button("开始测试")
    test_log = gr.JSON(label="测试结果（显示验证码过期则说明成功）")

    def test_get_challenge():
        test_res = _request.get(
            "https://passport.bilibili.com/x/passport-login/captcha?source=main_web"
        ).json()
        test_challenge = test_res["data"]["geetest"]["challenge"]
        test_gt = test_res["data"]["geetest"]["gt"]
        test_token = test_res["data"]["token"]
        test_csrf = _request.cookieManager.get_cookies_value("bili_jct")
        test_geetest_validate = ""
        test_geetest_seccode = ""
        validator = ways_detail[select_way]
        test_geetest_validate = validator.validate(gt=test_gt, challenge=test_challenge)
        test_geetest_seccode = test_geetest_validate + "|jordan"

        _url = "https://api.bilibili.com/x/gaia-vgate/v1/validate"
        _payload = {
            "challenge": test_challenge,
            "token": test_token,
            "seccode": test_geetest_seccode,
            "csrf": test_csrf,
            "validate": test_geetest_validate,
        }
        test_data = _request.post(_url, urlencode(_payload))
        yield [
            gr.update(value=test_data.json()),
        ]

    test_get_challenge_btn.click(
        fn=test_get_challenge,
        inputs=[],
        outputs=[test_log],
    )

    # 新增通过cookie获取ticket测试功能
    with gr.Row():
        gr.Markdown("### 通过cookie获取ticket测试")
    with gr.Row():
        ticket_server_ui = gr.Textbox(
            label="服务器地址",
            value="",
            placeholder="请输入服务器地址"
        )
        user_agent_ui = gr.Textbox(
            label="User-Agent",
            value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            placeholder="请输入User-Agent"
        )
    with gr.Row():
        cookies_ui = gr.Textbox(
            label="Cookies (JSON格式)",
            value='[{"name":"SESSDATA","value":"xxx"},{"name":"bili_jct","value":"xxx"}]',
            placeholder="请输入Cookies JSON数组，必须包含name和value字段",
            lines=5
        )
        gr.Markdown("""
        **Cookie格式说明**:
        - 必须是JSON数组格式
        - 每个Cookie必须包含name和value字段
        - 可选字段: path, domain, expires, max_age, secure, http_only, same_site
        
        示例:
        ```json
        [
          {"name":"SESSDATA","value":"your_sessdata_value"},
          {"name":"bili_jct","value":"your_bili_jct_value"}
        ]
        ```
        """)
    with gr.Row():
        ticket_test_btn = gr.Button("测试获取ticket", variant="primary")
        ticket_output_ui = gr.Textbox(label="ticket获取结果", interactive=False, lines=5)

    # ticket测试功能逻辑
    def test_get_ticket(server_url, user_agent, cookies_json):
        try:
            import json
            cookies = json.loads(cookies_json)
            client = RiskClient(server_url)
            result = client.get_cookie_ticket(user_agent, cookies)
            
            # 检查结果中是否包含error字段
            if "error" in result:
                return f"获取ticket失败: {result['error']}"
            else:
                return json.dumps(result, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            return f"JSON解析错误: {str(e)}"
        except Exception as e:
            return f"未知错误: {str(e)}"

    ticket_test_btn.click(
        fn=test_get_ticket,
        inputs=[ticket_server_ui, user_agent_ui, cookies_ui],
        outputs=[ticket_output_ui]
    )
    # 新版验证码测试功能逻辑
    def test_new_captcha(project_id, screen_id):
        try:
            # 1. 请求prepare接口
            prepare_url = f"https://show.bilibili.com/api/ticket/graph/prepare?project_id={project_id}&screen_id={screen_id}&timestamp={int(time.time() * 1000)}"
            prepare_res = _request.get(prepare_url).json()

            if prepare_res.get('errno') != 0:
                return {"error": f"prepare接口错误: {prepare_res.get('message', '未知错误')}"}
            yield prepare_res

            # 获取验证码参数
            data = prepare_res['data'][0] if isinstance(prepare_res['data'], list) else prepare_res['data']
            captcha_id = data['captcha_id']
            challenge = data['challenge']
            old_voucher = data['voucher']

            # 2. 过验证码
            validator = ways_detail[select_way]
            validate = validator.validate(gt=captcha_id, challenge=challenge)
            seccode = validate + "|jordan"

            # 3. 请求check接口
            check_url = "https://show.bilibili.com/api/ticket/graph/check"
            check_data = {
                'project_id': project_id,
                'screen_id': screen_id,
                'voucher': old_voucher,
                'challenge': challenge,
                'validate': validate,
                'seccode': seccode,
                'success': True
            }
            check_res = _request.post(check_url, data=urlencode(check_data)).json()

            return {
                "prepare_result": prepare_res,
                "check_result": check_res
            }
        except IndexError:
            return {"error": "验证码方式选择无效，请确保已选择正确的验证码方式"}
        except Exception as e:
            return {"error": f"处理过程中发生错误: {str(e)}"}

    # 新增新版验证码测试功能
    with gr.Row():
        gr.Markdown("### 新版验证码测试")
    with gr.Row():
        new_captcha_project_id = gr.Textbox(
            label="项目ID",
            placeholder="请输入项目ID"
        )
        new_captcha_screen_id = gr.Textbox(
            label="场次ID",
            placeholder="请输入场次ID"
        )
    with gr.Row():
        new_captcha_test_btn = gr.Button("测试新版验证码", variant="primary")
        new_captcha_output_ui = gr.JSON(label="验证码测试结果")
        new_captcha_test_btn.click(
            fn=test_new_captcha,
            inputs=[new_captcha_project_id, new_captcha_screen_id],
            outputs=[new_captcha_output_ui]
        )

