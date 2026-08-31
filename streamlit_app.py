"""
Streamlit 版本入口 - 适配 Streamlit Community Cloud 免费部署
一键部署：https://share.streamlit.io
"""
import os
import sys
import json
import time
import tempfile
import logging
from datetime import datetime

# 确保项目根目录在 sys.path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

# 下载目录用临时目录
os.environ.setdefault("DOWNLOAD_DIR", tempfile.gettempdir())
os.environ.setdefault("FLASK_ENV", "production")

# 加载 .env（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)

import streamlit as st
import requests

# ========== 页面配置 ==========
st.set_page_config(
    page_title="🎬 Video Parser · 全网视频无水印解析",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .main > div { padding-top: 2rem; }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 12px;
        font-weight: 600; padding: 0.6rem 1rem; width: 100%;
    }
    .stButton > button:hover { opacity: 0.9; }
    .platform-badge {
        display: inline-block; padding: 3px 10px; border-radius: 12px;
        font-size: 12px; margin: 2px;
        background: rgba(102,126,234,0.15); color: #667eea;
    }
    .success-box {
        padding: 1rem; border-radius: 12px;
        background: rgba(16,185,129,0.1);
        border-left: 4px solid #10b981; margin: 1rem 0;
    }
    .footer { text-align:center; color:#9ca3af; font-size:12px; margin-top:3rem; }
</style>
""", unsafe_allow_html=True)

# ========== 解析函数（直接复用项目核心逻辑）==========
@st.cache_resource(show_spinner=False)
def get_parse_function():
    """加载解析核心函数（只加载一次）"""
    from utils.web_fetcher import WebFetcher, UrlParser, YTDLP_PLATFORMS
    from src.parser_factory import ParserFactory

    def parse_text(text: str) -> dict:
        share_url = UrlParser.get_url(text)
        if not share_url:
            return {"success": False, "error": "未找到有效的分享链接"}

        initial_platform = UrlParser.get_platform(share_url)
        if initial_platform in YTDLP_PLATFORMS:
            platform = initial_platform
            real_url = share_url
            redirect_url = share_url
        else:
            redirect_url = WebFetcher.fetch_redirect_url(share_url)
            if not redirect_url:
                return {"success": False, "error": "无法访问该分享链接，请检查链接是否正确"}
            platform = UrlParser.get_platform(redirect_url)
            real_url = UrlParser.extract_video_address(redirect_url)

        if not platform:
            return {"success": False, "error": "该平台暂不支持"}

        parser = ParserFactory.create_parser(platform, real_url)

        def safe(fn, default=None):
            if not fn or not callable(fn):
                return default
            try:
                v = fn()
                return v
            except Exception:
                return default

        # 重试机制
        max_attempts = 3 if platform == '小红书' else 1
        content_data = {}
        for i in range(max_attempts):
            content_data = {
                'title': safe(parser.get_title_content, ''),
                'video_url': safe(parser.get_real_video_url, ''),
                'video_list': safe(getattr(parser, 'get_video_list', None), []),
                'cover_url': safe(parser.get_cover_photo_url, ''),
                'author': safe(getattr(parser, 'get_author_info', None), ''),
                'image_list': safe(getattr(parser, 'get_image_list', None), []),
                'audio_url': safe(getattr(parser, 'get_audio_url', None)),
            }
            if not content_data['video_url'] and content_data['video_list']:
                content_data['video_url'] = content_data['video_list'][0]
            has_content = (
                content_data['video_url'] or content_data['video_list']
                or content_data['image_list'] or content_data['audio_url']
            )
            if has_content:
                break

        if not (content_data['video_url'] or content_data['video_list']
                or content_data['image_list'] or content_data['audio_url']):
            if platform == '小红书':
                return {"success": False, "error": "需要小红书登录Cookie，请参考README配置"}
            return {"success": False, "error": "解析失败，请检查链接或稍后重试"}

        # 处理结果
        def to_https(u):
            return UrlParser.convert_to_https(u) if u else u

        images = []
        for img in (content_data.get('image_list') or []):
            if isinstance(img, dict):
                images.append({'url': to_https(img.get('url'))})
            else:
                images.append({'url': to_https(img)})

        videos = []
        vlist = content_data.get('video_list') or []
        primary = to_https(content_data.get('video_url'))
        if primary:
            vlist = [primary] + [u for u in vlist if u and u != primary]
        videos = [{'url': to_https(u)} for u in vlist if u]
        videos = list({v['url']: v for v in videos}.values())

        music = {}
        if content_data.get('audio_url'):
            music = {'url': to_https(content_data['audio_url'])}

        return {
            "success": True,
            "data": {
                "platform": platform,
                "title": content_data.get('title') or '未命名',
                "author": content_data.get('author') or '',
                "cover": to_https(content_data.get('cover_url')),
                "videos": videos,
                "images": images,
                "music": music,
            }
        }

    return parse_text

# ========== 平台列表 ==========
DOMESTIC = ["抖音","快手","小红书","B站","视频号","微博","西瓜视频","今日头条",
            "知乎","最右","皮皮虾","好看视频","AcFun","豆瓣","虎扑","贴吧","陌陌",
            "Soul","闲鱼","淘宝逛逛","得物","剪映","豆包","即梦AI","可灵AI"]
OVERSEAS = ["Instagram","TikTok","YouTube","Twitter/X","Facebook","Reddit",
            "Pinterest","Vimeo","Twitch","SoundCloud","Threads","LinkedIn",
            "Dailymotion","Tumblr","VK","Rumble"]

# ========== 主界面 ==========
st.title("🎬 Video Parser")
st.markdown("**全网视频图片无水印解析 · 一键下载原文件**")
st.markdown(
    f'<div class="platform-badge">🇨🇳 国内 {len(DOMESTIC)}+ 平台</div>'
    f'<div class="platform-badge">🌍 海外 {len(OVERSEAS)}+ 平台</div>'
    f'<div class="platform-badge">💾 一键保存</div>'
    f'<div class="platform-badge">🔒 隐私保护</div>',
    unsafe_allow_html=True,
)
st.markdown("---")

url = st.text_input(
    "🔗 粘贴视频/图文分享链接",
    placeholder="例如：https://v.douyin.com/xxxxxx/ 或 https://www.instagram.com/reel/xxxxxx/",
)

col1, col2 = st.columns([3, 1])
with col1:
    parse_btn = st.button("🚀 开始解析", use_container_width=True, type="primary")
with col2:
    clear_btn = st.button("🗑️ 清空", use_container_width=True)

if parse_btn and url.strip():
    with st.spinner("⏳ 正在解析中..."):
        try:
            parse_fn = get_parse_function()
            result = parse_fn(url.strip())

            if result.get("success"):
                data = result["data"]
                st.markdown(
                    f'<div class="success-box">✅ 解析成功！平台：<b>{data["platform"]}</b></div>',
                    unsafe_allow_html=True,
                )

                st.subheader(f"📝 {data.get('title','未命名')}")
                if data.get("author"):
                    st.caption(f"👤 {data['author']}")

                # 视频
                for i, v in enumerate(data.get("videos", [])):
                    vurl = v.get("url", "")
                    if not vurl:
                        continue
                    st.markdown(f"#### 🎥 视频 {i+1}")
                    try:
                        st.video(vurl)
                    except Exception:
                        st.markdown(f"[▶️ 在新窗口播放]({vurl})")
                    try:
                        with st.spinner(f"正在获取视频文件..."):
                            r = requests.get(vurl, stream=True, timeout=60,
                                           headers={"User-Agent": "Mozilla/5.0"})
                            r.raise_for_status()
                            st.download_button(
                                label=f"⬇️ 下载视频 {i+1}",
                                data=r.content,
                                file_name=f"video_{int(time.time())}_{i+1}.mp4",
                                mime="video/mp4",
                                use_container_width=True,
                                key=f"v_dl_{i}",
                            )
                    except Exception as e:
                        st.markdown(f"[🔗 右键另存为]({vurl})")

                # 图片
                imgs = data.get("images", [])
                if imgs:
                    st.markdown(f"#### 🖼️ 图片（共{len(imgs)}张）")
                    cols = st.columns(min(3, len(imgs)))
                    for i, img in enumerate(imgs):
                        img_url = img.get("url", "") if isinstance(img, dict) else img
                        if not img_url:
                            continue
                        with cols[i % 3]:
                            try:
                                st.image(img_url, use_column_width=True)
                                r = requests.get(img_url, timeout=30,
                                               headers={"User-Agent": "Mozilla/5.0"})
                                st.download_button(
                                    label=f"⬇️ 图{i+1}",
                                    data=r.content,
                                    file_name=f"image_{int(time.time())}_{i+1}.jpg",
                                    mime="image/jpeg",
                                    use_container_width=True,
                                    key=f"img_{i}",
                                )
                            except Exception:
                                st.markdown(f"[🔗 查看原图]({img_url})")

                # 音频
                music = data.get("music", {})
                if music and music.get("url"):
                    st.markdown("#### 🎵 背景音乐")
                    try:
                        st.audio(music["url"])
                        r = requests.get(music["url"], timeout=30,
                                       headers={"User-Agent": "Mozilla/5.0"})
                        st.download_button(
                            "⬇️ 下载音频",
                            data=r.content,
                            file_name=f"music_{int(time.time())}.mp3",
                            mime="audio/mpeg",
                            use_container_width=True,
                        )
                    except Exception:
                        st.markdown(f"[🔗 音频链接]({music['url']})")
            else:
                st.error(f"❌ {result.get('error','解析失败')}")
        except Exception as e:
            st.error(f"❌ 发生错误：{str(e)}")
            st.info("💡 海外平台需要服务器可访问外网；国内平台若失败请检查链接或配置Cookie。")
elif parse_btn:
    st.warning("⚠️ 请先输入视频/图文链接")

st.markdown("---")

with st.expander("📖 使用说明 & 支持平台"):
    st.markdown("""
**使用方法**：APP内分享→复制链接→粘贴到上面→点「开始解析」→下载保存
""")
    st.markdown("**🇨🇳 国内平台**：" + "、".join(f"`{p}`" for p in DOMESTIC))
    st.markdown("**🌍 海外平台**：" + "、".join(f"`{p}`" for p in OVERSEAS))

with st.expander("⚠️ 免责声明"):
    st.markdown("""
本工具仅供**个人学习研究**使用。请遵守各平台用户协议与法律法规，
下载的内容**不得用于商业用途**，尊重原创作者版权。
因违规使用造成的法律责任由使用者自行承担。
""")

st.markdown(
    '<div class="footer">🎬 Video Parser · 开源免费 · 仅供学习研究<br/>'
    '<a href="https://github.com/jiangcong2001/video-parser-site" target="_blank">⭐ GitHub 仓库</a></div>',
    unsafe_allow_html=True,
)
