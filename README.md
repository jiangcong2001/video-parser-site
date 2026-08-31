# 🎬 Video Parser · 全网视频图片无水印解析

> 一个开源、本地可运行、可一键部署到免费云平台的视频/图片无水印解析工具，支持国内外 60+ 主流平台。

---

## ✨ 功能特性

| 能力 | 说明 |
|------|------|
| 🌍 **国内外通吃** | 抖音/快手/小红书/B站/视频号/微博等国内 33+ 平台；通过 yt-dlp 支持 Instagram/TikTok/YouTube/Twitter/X/Facebook/Reddit/Pinterest/Vimeo/Twitch 等海外 20+ 平台 |
| 🖼️ **视频+图集+音频** | 短视频、图文笔记、Live Photo 实况、背景音乐、字幕一键提取无水印原文件 |
| 💾 **一键下载** | 支持服务器代理流式下载到本地（云平台零存储占用），也支持本地/Docker 环境保存到服务器 |
| 🔌 **标准 JSON API** | `POST /api/parse`，方便对接小程序/APP/快捷指令/第三方工具 |
| 🐳 **Docker 部署** | 提供 Dockerfile + docker-compose，一条命令上线 |
| ☁️ **一键免费上云** | 内置 Render / Vercel 配置，点按钮即可上线到公网 |
| 🔒 **100% 本地解析** | 核心解析逻辑开源，不经过第三方 SaaS，保护隐私 |

---

## 🚀 快速开始

### 方式一：一键部署到免费云平台（推荐，无需服务器）

#### 🎯 Render（**推荐**，免费、支持Docker完整功能）

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/jiangcong2001/video-parser-site)

点击按钮 → 用 GitHub 登录 Render → 确认部署即可。
- 免费套餐会在闲置时休眠，首次访问需等待约 1 分钟冷启动
- 部署完成后 Render 会给你一个 `https://xxx.onrender.com` 的公网地址

#### ⚡ Vercel（秒级部署，Serverless）

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/jiangcong2001/video-parser-site)

点击按钮 → 用 GitHub 登录 Vercel → 确认导入即可。
- Vercel 函数执行超时为 60 秒，超大视频（>100MB）建议用 Render
- 部署完成后访问 `https://你的项目.vercel.app`

> **海外平台提示**：Render/Vercel 服务器都在海外，天然可访问 Instagram/TikTok/YouTube 等，无需额外代理。国内平台（抖音/小红书/B站等）解析同样可用。

---

### 方式二：本地运行

```bash
git clone https://github.com/jiangcong2001/video-parser-site.git
cd video-parser-site
pip install -r requirements.txt
python app.py
# 打开浏览器访问 http://127.0.0.1:8051
```

### 方式三：Docker 部署

```bash
docker-compose up -d --build
# 访问 http://服务器IP:8051
```

---

## 🔌 API 接口

### 解析接口

```http
POST /api/parse
Content-Type: application/json

{
  "text": "https://v.douyin.com/xxxxxx/  或粘贴整个分享文本"
}
```

**响应示例：**
```json
{
  "code": 200,
  "success": true,
  "message": "成功",
  "data": {
    "platform": "抖音",
    "title": "视频标题",
    "video_url": "https://...无水印直链...",
    "cover_url": "https://...封面...",
    "author": { "name": "作者名", "avatar": "https://..." },
    "image_list": [],
    "audio_url": null
  }
}
```

### 代理下载接口（云平台推荐）

```http
GET /api/download/fetch?url=<媒体URL>&filename=<文件名>&type=video|image|audio
```

服务器会流式转发媒体到浏览器，不占服务器磁盘。

### 健康检查

```http
GET /api/health
```

---

## 🌐 支持的平台

### 国内平台（自研解析）
抖音、快手、小红书、B 站、视频号、微博、西瓜视频、知乎、剪映、
Soul、闲鱼、豆包、即梦、可灵、最右、度加（千问）、虎牙、
美图、AcFun、QQ 小世界、腾讯频道、视频号、皮皮虾、皮皮搞笑、
全民 K 歌、新片场、快影、梨视频、好看视频、微信公众号、微视、
绿洲、抖音图文、小红书图文等 **33+ 平台**。

### 海外平台（基于 yt-dlp）
Instagram、TikTok、YouTube、Twitter/X、Facebook、Reddit、
Pinterest、Vimeo、Twitch、SoundCloud、Threads、Bilibili(海外)、
LinkedIn、Tumblr、Dailymotion 等 **20+ 平台**。

---

## ⚙️ 可选配置（.env 文件）

复制 `.env.example` 为 `.env`，按需填写：

```env
# 代理（用于访问海外平台，本地直连外网可留空；国内服务器需要时填写）
HTTPS_PROXY=http://127.0.0.1:7890
HTTP_PROXY=http://127.0.0.1:7890

# 小红书/抖音等 Cookie（部分内容需要登录才能获取）
XHS_COOKIE=你的小红书Cookie
DOUYIN_COOKIE=你的抖音Cookie

# 下载保存目录（默认自动适配）
DOWNLOAD_DIR=./downloads

# Flask 密钥
SECRET_KEY=自定义密钥
```

---

## 📁 项目结构

```
video-parser-site/
├── app.py                    # Flask 入口
├── api/index.py              # Vercel Serverless 入口
├── vercel.json               # Vercel 配置
├── render.yaml               # Render 一键部署配置
├── Procfile                  # 通用 PaaS 启动配置
├── gunicorn_config.py        # Gunicorn 生产配置
├── runtime.txt               # Python 版本锁定
├── requirements.txt          # 依赖清单
├── Dockerfile                # Docker 构建
├── docker-compose.yml        # Docker Compose
├── src/
│   ├── api/                  # API 路由（parse/download）
│   ├── parsers/              # 各平台解析器
│   ├── parser_factory.py     # 解析器工厂
│   └── web/                  # 前端页面路由
├── utils/                    # 工具函数（签名、抓包）
├── templates/landing.html    # 前端页面
├── static/                   # 静态资源
├── configs/                  # 配置常量
├── docs/                     # 文档
└── tests/                    # 测试用例
```

---

## ⚠️ 免责声明

- 本项目仅供**学习研究**使用
- 请尊重各平台版权与用户著作权，**请勿用于违规下载他人作品**
- 使用本工具造成的任何版权纠纷，由使用者自行承担
- 部分平台需要登录 Cookie 才能解析完整内容，请自行获取并在 `.env` 中配置

---

## 📄 开源协议

MIT License
