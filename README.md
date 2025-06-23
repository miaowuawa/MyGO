<div align="center">
  <a href="https://github.com/miaowuawa/MyGO" target="_blank">
<img src="https://img.picui.cn/free/2025/06/19/6852ee5eb6324.jpg" alt="mygo.jpg" title="mygo.jpg" height="160" width="160"/>  
  </a>
  <h1 id="koishi">MyGO</h1>

<p>
  <!-- GitHub Downloads -->
  <a href="https://github.com/miaowuawa/MyGO/releases">
    <img src="https://img.shields.io/github/downloads/miaowuawa/MyGO/total" alt="GitHub all releases">
  </a>
  <!-- GitHub Release Version -->
  <a href="https://github.com/miaowuawa/MyGO/releases">
    <img src="https://img.shields.io/github/v/release/miaowuawa/MyGO" alt="GitHub release (with filter)">
  </a>
  <!-- GitHub Issues -->
  <a href="https://github.com/miaowuawa/MyGO/issues">
    <img src="https://img.shields.io/github/issues/miaowuawa/MyGO" alt="GitHub issues">
  </a>
  <!-- GitHub Stars -->
  <a href="https://github.com/miaowuawa/MyGO/stargazers">
    <img src="https://img.shields.io/github/stars/miaowuawa/MyGO" alt="GitHub Repo stars">
  </a>
</p>

起源于MikuMifa的biliTickerBuy，让会员购抢票不再迷路
</div>

<br>
<b>在此感谢原作者MikuMifa为BW而做出的一切努力！这么多年来，你辛苦了！</b>

<br>
<br>

## 注意事项

- 本项目没有云控，但我们仍然不允许您使用此项目进行盈利性/商业化批量抢票。除非您承认，您失去了父母。
- 为防止黄牛滥用和自动化脚本泛滥，本项目暂不提供ctoken/ticket生成的核心代码实现。我们理解这可能会给正常用户带来一些不便，但这一措施能有效限制大规模自动化抢票行为。
- 此脚本只能作为**辅助**使用，使用此脚本**完全代替人工抢票**现阶段是不现实的
- 普通用户抢票间隔不建议小于**200**，被黑号/账号异常过的抢票间隔不要小于**250**
- 延迟越低，成功率越高，**临时封号/临时封实名危险越大**，自行权衡利弊

## 怎么用
- 下载exe并运行
- 如果浏览器无法打开，用chrome/edge浏览器输入“chrome://version"打开访问
- 然后复制”可执行文件路径“后面一长串到输入框
- 在登录账号后，不要关闭浏览器，那段时间不是让你干等的
- 首先按f12打开开发者模式，打开设备仿真（电脑手机的图标）
- 刷新页面，随便打开一个漫展活动场次
- 点击购买并到达支付页面，在手机端取消订单

### 如何获取ctoken？

您有以下两种方式获取ctoken：

#### 1. 自行逆向实现API

您需要自行逆向分析并实现以下API接口：

**生成ctoken接口**:
```
POST http://localhost:8080/generate
Content-Type: application/json

请求体:
{
  "screen_width": 1920,
  "screen_height": 1080
}

响应:
{
  "ctkid": "xXxXxXxXxXxXxXxXxXxX",
  "ctoken": "something"
}
```

**ctoken刷新接口**:
```
GET http://localhost:8080/get/xXxXxXxXxXxXxXxXxXxX

响应:
{
  "ctoken": "something"
}
```


```


#### 2. 通过官方API服务

我们提供稳定的官方API服务：
- Telegram联系: @miaowuawa
- QQ联系：2022505032
- 特点: 低延迟、高并发、免费使用
- 要求: 需要提供一些基本信息以验证身份

### 使用建议

1. 对于技术用户: 建议自行逆向实现，这样可以获得最佳性能和灵活性
2. 对于普通用户: 推荐使用官方API服务，简单可靠
3. 请合理使用，避免频繁请求

我们保留根据使用情况调整API访问策略的权利，以确保服务的公平性和可持续性。


## 💻 快速安装

[下载链接](https://github.com/miaowuawa/MyGO/releases) 

## 👀 使用说明书
没写好

## ❗ 项目问题

程序使用问题： [点此链接前往discussions](https://github.com/miaowuawa/MyGO/discussions)

反馈程序BUG或者提新功能建议： [点此链接向项目提出反馈BUG](https://github.com/miaowuawa/MyGO/issues/new/choose)



## 🤩 项目贡献者
### 前项目贡献者（BiliTickerBuy）
<a href="https://github.com/mikumifa/biliTickerBuy/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=mikumifa/biliTickerBuy&preview=true&max=&columns=" />
</a>
<br /><br />

### 本项目贡献者（MyGO）
<a href="https://github.com/miaowuawa/MyGO/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=miaowuawa/MyGO&preview=true&max=&columns=" />
</a>
<br /><br />

## ⭐️ Star History

### 前项目History（BiliTickerBuy）
[![Star History Chart](https://api.star-history.com/svg?repos=mikumifa/biliTickerBuy&type=Date)](https://www.star-history.com/#mikumifa/biliTickerBuy&Date)

### 本项目History（BiliTickerBuy）
[![Star History Chart](https://api.star-history.com/svg?repos=miaowuawa/MyGO&type=Date)](https://www.star-history.com/#miaowuawa/MyGO&Date)

## 📩 免责声明

详见[MIT License](./LICENSE)。
** 黄牛自重。 ** 
《治安管理处罚法》规定，伪造、变造、倒卖车票、船票、航空客票、文艺演出票、体育比赛入场券或其他有价票证、凭证的，处十日以上十五日以下拘留，可以并处一千元以下罚款；情节较轻的，处五日以上十日以下拘留，可以并处五百元以下罚款。
切勿进行盈利，所造成的后果与本人无关。

