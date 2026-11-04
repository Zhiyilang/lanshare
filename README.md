# lanshare · 零依赖局域网文件快传

<!-- ORDER-CTA -->
> **需要定制或代做？** 我承接 Excel 代做（¥50 起）/ 零依赖 Python 脚本定制（¥200 起）/ 影刀·UiBot 机器人（¥500 起）。
> **先报价后付款、无预付款**，微信 / 支付宝结算，询价发 **2383844705@qq.com**（标题写「接单 + 需求类型」）。
> 更多工具与报价见作品集：https://zhiyilang.github.io/


> 同 WiFi 下，一台电脑运行本程序，手机/其他电脑浏览器打开地址即可 **上传 / 下载 / 删除** 文件。**无需安装任何第三方库**，标准库即可运行。

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)](https://www.python.org)
[![零依赖](https://img.shields.io/badge/deps-zero%20stdlib-lightgrey.svg)](main.py)

---

## 为什么需要它

- 手机拍的照片想秒传到电脑？微信要联网、要登录、限速。
- 同事要你发个文件，U 盘找不到、AirDrop 只有苹果互通。
- 内网 / 无外网环境，需要临时传文件。

**lanshare = 你自己的迷你"隔空投送"**，跑在局域网内，文件不经过任何第三方服务器。

## 特性

- ✅ **零依赖**：只用 Python 标准库，任何装了 Python 的机器都能跑
- ✅ **跨平台**：Windows / macOS / Linux 通用
- ✅ **手机可用**：浏览器即客户端，无需装 App
- ✅ **中文文件名**：上传下载中文名文件无乱码
- ✅ **多选上传**、重名自动加 `(1)` 后缀
- ✅ **不联网外传**：纯局域网，隐私安全

## 安装

不需要安装。只要有 Python 3.8+：

```bash
python --version   # 确认有 Python 3.8+
```

## 使用

```bash
# 默认：共享当前目录，端口 8000
python lanshare.py

# 指定端口
python lanshare.py -p 9000

# 指定共享目录
python lanshare.py -d D:/共享文件夹
```

启动后终端会打印：

```
  本机地址 :  http://192.168.1.20:8000/
  本机回环 :  http://127.0.0.1:8000/
  共享目录 :  D:/桌面
```

**手机**连同一个 WiFi，浏览器打开 `http://192.168.1.20:8000/` 即可：

1. 点「选择文件」→ 上传，文件落到电脑共享目录
2. 点文件名旁的 📥 下载，把电脑文件取到手机
3. 不想要的则点「删除」

`Ctrl+C` 停止服务。

## 典型场景

| 场景 | 做法 |
|------|------|
| 手机 → 电脑传照片 | 手机浏览器开地址，上传 |
| 电脑 → 手机发文件 | 电脑运行，手机下载 |
| 会议室临时收文件 | 投影地址，大家扫码上传 |
| 内网无外网传数据 | 纯局域网，不经过公网 |

## 安全说明

- 服务绑定 `0.0.0.0`，仅同一局域网内可访问；**不要**在公网服务器上暴露此端口。
- 文件保存在你指定的共享目录，程序不做任何上传到外网的动作。
- 防目录穿越：只能操作共享目录内的文件。

## 与同类工具对比

| 工具 | 需要联网 | 需安装 | 第三方库 | 中文支持 |
|------|---------|--------|---------|---------|
| lanshare | ❌ 局域网 | ❌ | ❌ 零依赖 | ✅ |
| 微信文件传输 | ✅ | App | - | ✅ |
| Python http.server | ❌ | ❌ | ❌ | ⚠️ 无上传界面 |
| 各类网盘 | ✅ | 账号 | - | ✅ |

## 许可证

MIT —— 可自由用于个人和商业场景。

---

如果这个小工具帮到了你，欢迎请作者喝杯咖啡 ☕ → [爱发电](https://afdian.com/a/Zhiyilang)

<!-- cross-links -->

## 🔗 More zero-dependency tools

All of these are single-file, pure Python-stdlib CLIs — offline, no `pip install`, cross-platform:

- **billfusion** — Bill / CSV merging · <https://github.com/Zhiyilang/billfusion>
- **dupescan** — Duplicate file finder · <https://github.com/Zhiyilang/dupescan>
- **csvdiff** — CSV / JSON diff · <https://github.com/Zhiyilang/csvdiff>
- **md2html** — Markdown to HTML · <https://github.com/Zhiyilang/md2html>
- **dirsize** — Directory size analyzer · <https://github.com/Zhiyilang/dirsize>

Full portfolio & docs: <https://zhiyilang.github.io/>
