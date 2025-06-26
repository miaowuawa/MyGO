import random

from util.BuvidSessionIdUtil import genSessionId


class UAGenerator:
    def __init__(self):
        self.common_resolutions = [
            # 常见手机竖屏分辨率(宽x高)
            "360x800", "375x812", "390x844",  # 中低端安卓/iPhone mini
            "414x896", "428x926",  # iPhone 11/12/13
            "393x873", "430x932",  # iPhone 14/15
            "412x915", "360x780",  # 主流安卓手机
            "412x869", "360x800"  # 常见安卓手机
        ]

    def generate_mobile_ua(self, buvid):
        """
        生成手机客户端User-Agent
        :return: 生成的User-Agent字符串
        """
        sessionId = genSessionId()
        # 随机选择手机类型和浏览器
        return (f"Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/620.1.16.10.11 (KHTML, "
                f"like Gecko) Mobile/22C152 BiliApp/84001100 os/ios model/iPhone 11 mobi_app/iphone build/84001100 "
                f"osVer/18.2 network/2 channel/AppStore Buvid/{buvid} c_locale/zh-Hans_CN s_locale/zh-Hans_CN "
                f"sessionID/{sessionId} disable_rcmd/0 themeId/1 sh/48 mallVersion/8401000 mVersion/301 "
                f"flutterNotch/1 magent/BILI_H5_IOS_18.2_8.40.1_84001100")


# 示例用法
if __name__ == "__main__":
    ua_gen = UAGenerator()
    print("iPhone UA:", ua_gen.generate_mobile_ua())
    print("Android UA:", ua_gen.generate_mobile_ua())
