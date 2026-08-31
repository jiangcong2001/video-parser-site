# 🎬 Video Parser · 全网视频图片无水印解析网站

一个开箱即用的开源视频/图片无水印解析网站，支持国内外 60+ 主流平台，带 Web 界面、一键保存功能和标准 JSON API。

> ⚠️ **声明**：本项目仅供学习研究使用，请尊重原创版权，请勿用于商业用途或二次传播他人作品。

---

## ✨ 特性

- 🌍 **国内外通吃**：国内覆盖抖音/快手/小红书/B站/微博/视频号/知乎/西瓜等 33+ 平台；国外通过 yt-dlp 支持 Instagram / TikTok / YouTube / Twitter/X / Facebook / Reddit / Pinterest / Vimeo / Twitch / SoundCloud / Threads / Tumblr / Dailymotion / VK 等主流平台
- 🖼️ **视频+图集+音频全覆盖**：无水印视频、图文笔记、Live Photo 实况、背景音乐都能解析
- 💾 **一键保存到服务器**：解析后可一键下载保存到服务器 `downloads/` 目录
- 🎨 **现代化 Web 界面**：深色渐变UI，支持预览、打开、保存
- 🔌 **标准 RESTful API**：可对接小程序、APP、iOS 快捷指令
- 🐳 **Docker 一键部署**：附 Dockerfile + docker-compose
- 🔒 **100% 本地解析**：核心逻辑开源本地运行，不经过第三方 SaaS

---

## 📸 支持的平台

### 🇨🇳 国内平台（33+）

抖音 · 小红书 · 快手 · 哔哩哔哩 · 视频号 · 微信公众号 · 微博 · 西瓜视频 · 知乎
· 好看视频 · 微视 · 梨视频 · AcFun · 皮皮搞笑 · 皮皮虾 · 绿洲 · 美拍 · 全民K歌
· 新片场 · 最右 · 虎牙 · 汽水音乐 · 腾讯频道 · 剪映/CapCut · 快影 · Soul · 闲鱼
· 豆包 · 即梦AI · 可灵AI · 通义千问 · 夸克AI · 小云雀AI

### 🌐 国外平台（通过 yt-dlp）

Instagram · TikTok · YouTube · Twitter/X · Facebook · Reddit · Pinterest · Vimeo
· Twitch · SoundCloud · Threads · Tumblr · Dailymotion · VK · OK.ru · Snapchat
· LinkedIn · Spotify · CapCut（国际版）· 以及更多 yt-dlp 支持的站点

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 克隆仓库
git clone https://github.com/jiangcong2001/video-parser-site.git
cd video-parser-site

# 一键启动
docker-compose up -d --build
```

访问 http://你的服务器IP:8051 即可使用。

### 方式二：本地 Python 运行

```bash
# 环境要求：Python 3.10+
git clone https://github.com/jiangcong2001/video-parser-site.git
cd video-parser-site

# 安装依赖（包括 yt-dlp）
pip install -r requirements.txt

# 可选：配置 Cookie（部分平台如小红书、视频号需要登录态）
cp .env.example .env
# 编辑 .env，填入需要的 Cookie

# 启动
python app.py
# 或生产环境
gunicorn --workers 3 --bind 0.0.0.0:8051 --timeout 120 app:app
```

打开浏览器访问 http://127.0.0.1:8051

> 💡 YouTube/Instagram/TikTok 等国外平台解析需要服务器能访问外网，国内服务器请配置代理。
> 可设置环境变量 `HTTPS_PROXY=http://127.0.0.1:7890` 给 yt-dlp 使用。

---

## 🔌 API 接口

### 1. 解析视频/图片

**POST** `/api/parse`

请求体（JSON）：
```json
{
  "text": "https://v.douyin.com/xxxxxx/ 任意包含分享链接的文字"
}
```

成功响应：
```json
{
  "code": 200,
  "success": true,
  "message": "成功",
  "data": {
    "platform": "抖音",
    "title": "视频标题",
    "video_url": "https://...无水印视频直链.mp4",
    "audio_url": "https://...音频.m4a",
    "cover_url": "https://...封面.jpg",
    "author": {"name": "作者", "avatar": "头像URL", "uid": "..."},
    "image_list": []
  }
}
```

### 2. 保存媒体到服务器

**POST** `/api/download/save`

```json
{
  "url": "媒体直链",
  "title": "文件名前缀",
  "type": "video"
}
```

### 3. 获取已保存文件列表

**GET** `/api/download/list`

### 4. 下载已保存文件

**GET** `/api/download/file/<filename>`

### 5. 健康检查

**GET** `/api/health`

---

## 📁 项目结构

```
video-parser-site/
├── app.py                  # Flask 入口
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── downloads/              # 保存的视频/图片
├── logs/                   # 日志
├── configs/                # 配置（域名映射、UA、日志）
├── src/
│   ├── api/
│   │   ├── parse.py        # 解析API
│   │   └── download.py     # 下载保存API
│   ├── parsers/            # 各平台解析器
│   │   ├── base_parser.py
│   │   ├── douyin_parser.py
│   │   ├── xiaohongshu_parser.py
│   │   ├── kuaishou_parser.py
│   │   ├── ytdlp_parser.py # 🆕 yt-dlp国外平台解析器
│   │   └── ...
│   ├── parser_factory.py   # 解析器工厂
│   └── web/
│       └── views.py        # 页面路由
├── utils/
│   └── web_fetcher.py      # URL识别/重定向/平台判断
├── templates/
│   └── landing.html        # 🆕 全新现代化前端页面
└── static/
```

---

## 🔧 配置 Cookie（可选）

部分平台（小红书、视频号、抖音长视频等）需要登录Cookie才能正常解析：

复制 `.env.example` 为 `.env`，填入对应Cookie：

```env
DOUYIN_COOKIE=你的抖音cookie
XIAOHONGSHU_COOKIE=你的小红书cookie
WECHAT_CHANNELS_COOKIE=你的视频号cookie
```

如何获取Cookie：用浏览器登录对应网站 → F12打开开发者工具 → Network → 刷新 → 找到任意请求 → 复制请求头里的 `Cookie` 值。

---

## 📝 开源协议

MIT License

---

## 🙏 致谢

- 国内平台解析基于 [ucmao/media-parser](https://github.com/ucmao/media-parser)（MIT）二次开发扩展
- 国外平台解析基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp)（Unlicense License）
