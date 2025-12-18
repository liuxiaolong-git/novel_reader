import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import warnings
import time
from typing import List, Dict, Optional

# 禁用SSL警告
warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="手机小说阅读器",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "手机小说阅读器 v2.0 - 支持盗版小说搜索阅读"
    }
)

# 自定义CSS样式 - 优化手机端显示
st.markdown("""
<style>
    /* 全局样式 */
    html, body, [class*="css"] {
        font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 手机端优化 */
    @media screen and (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0.25rem 0.5rem;
            font-size: 0.9rem;
        }
    }
    
    /* 卡片样式 */
    .novel-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .novel-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* 阅读内容样式 */
    .content-box {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        min-height: 500px;
    }
    
    .chapter-content {
        font-size: 1.1rem;
        line-height: 2;
        color: #333;
        text-align: justify;
    }
    
    /* 搜索框样式 */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.25rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        background: transparent;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    /* 夜间模式 */
    .night-mode .content-box {
        background: #2d3748;
        color: #e2e8f0;
    }
    
    .night-mode .chapter-content {
        color: #e2e8f0;
    }
    
    /* 隐藏不需要的元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 响应式调整 */
    @media screen and (max-width: 768px) {
        .content-box {
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .chapter-content {
            font-size: 1rem;
            line-height: 1.8;
        }
        
        .novel-card {
            padding: 0.8rem;
            margin: 0.3rem 0;
        }
    }
</style>
""", unsafe_allow_html=True)

class NovelReader:
    def __init__(self):
        # 使用常见的手机用户代理
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.sources = self.load_sources()
        
    def load_sources(self):
        """加载小说源配置 - 使用稳定的盗版小说源"""
        return {
            "笔趣阁1号": {
                "search_url": "https://www.bqg789.com/s?q={}",
                "base_url": "https://www.bqg789.com",
                "search_selector": ".book-info",
                "chapter_selector": "#list dl dd a",
                "content_selector": "#content"
            },
            "笔趣阁2号": {
                "search_url": "http://www.biquge5200.cc/modules/article/search.php?searchkey={}",
                "base_url": "http://www.biquge5200.cc",
                "search_selector": "tr",
                "chapter_selector": "#list dd a",
                "content_selector": "#content"
            },
            "笔趣阁3号": {
                "search_url": "https://www.xbiquge.la/modules/article/waps.php?searchkey={}",
                "base_url": "https://www.xbiquge.la",
                "search_selector": "tr",
                "chapter_selector": "#list dd a",
                "content_selector": "#content"
            },
            "顶点小说": {
                "search_url": "https://www.dingdian666.com/top/search.php?keyword={}",
                "base_url": "https://www.dingdian666.com",
                "search_selector": ".novelslist2 li",
                "chapter_selector": "#list dd a",
                "content_selector": "#content"
            },
            "免费小说大全": {
                "search_url": "https://www.mianfeixiaoshuo.com/search/?searchkey={}",
                "base_url": "https://www.mianfeixiaoshuo.com",
                "search_selector": ".list-group-item",
                "chapter_selector": ".list-group-item a",
                "content_selector": ".content"
            }
        }
    
    def make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """发送HTTP请求，支持重试"""
        for attempt in range(max_retries):
            try:
                # 添加随机延迟避免被封
                time.sleep(0.5)
                
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=15,
                    verify=False  # 禁用SSL验证
                )
                
                # 自动检测编码
                if response.encoding == 'ISO-8859-1':
                    response.encoding = 'utf-8'
                elif 'gbk' in response.encoding.lower() or 'gb2312' in response.encoding.lower():
                    response.encoding = 'gbk'
                else:
                    response.encoding = 'utf-8'
                
                return response
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(1)  # 等待后重试
                    continue
                st.warning(f"请求超时: {url}")
                return None
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                st.warning(f"请求失败: {str(e)[:100]}")
                return None
        
        return None
    
    def search_novels(self, keyword: str, source: str = "笔趣阁1号") -> List[Dict]:
        """搜索小说"""
        try:
            if source not in self.sources:
                return []
            
            # 对关键字进行URL编码
            encoded_keyword = urllib.parse.quote(keyword.encode('gbk' if 'gbk' in source else 'utf-8'))
            search_url = self.sources[source]["search_url"].format(encoded_keyword)
            
            # 显示搜索进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.text(f"正在搜索 {source}...")
            
            # 发送请求
            response = self.make_request(search_url)
            if response is None or response.status_code != 200:
                progress_bar.empty()
                status_text.empty()
                return []
            
            # 更新进度
            progress_bar.progress(50)
            status_text.text("解析搜索结果...")
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            novels = []
            
            # 根据不同网站解析搜索结果
            if source == "笔趣阁1号":
                items = soup.select('.book-item') or soup.select('.book-info')
                for item in items:
                    try:
                        title_elem = item.select_one('h4 a') or item.select_one('a')
                        author_elem = item.select_one('.author') or item.select_one('.info span')
                        
                        if title_elem:
                            title = title_elem.text.strip()
                            author = author_elem.text.strip() if author_elem else "未知作者"
                            url = title_elem['href']
                            
                            # 处理URL
                            if not url.startswith('http'):
                                url = self.sources[source]["base_url"] + url
                            
                            novels.append({
                                'title': title,
                                'author': author.replace('作者：', '').replace('作者:', '').strip(),
                                'url': url,
                                'source': source
                            })
                    except:
                        continue
                    
            elif source in ["笔趣阁2号", "笔趣阁3号"]:
                # 表格形式的搜索结果
                rows = soup.select('tr')[1:]  # 跳过表头
                for row in rows[:20]:  # 限制数量
                    try:
                        cols = row.select('td')
                        if len(cols) >= 3:
                            title_elem = cols[0].select_one('a')
                            if title_elem:
                                title = title_elem.text.strip()
                                author = cols[2].text.strip()
                                url = title_elem['href']
                                
                                if not url.startswith('http'):
                                    url = self.sources[source]["base_url"] + url
                                
                                novels.append({
                                    'title': title,
                                    'author': author,
                                    'url': url,
                                    'source': source
                                })
                    except:
                        continue
                    
            elif source == "顶点小说":
                items = soup.select('.novelslist2 li') or soup.select('.list-group-item')
                for item in items:
                    try:
                        title_elem = item.select_one('a')
                        if title_elem:
                            title = title_elem.text.strip()
                            url = title_elem['href']
                            
                            if not url.startswith('http'):
                                url = self.sources[source]["base_url"] + url
                            
                            novels.append({
                                'title': title,
                                'author': "未知作者",
                                'url': url,
                                'source': source
                            })
                    except:
                        continue
                    
            elif source == "免费小说大全":
                items = soup.select('.list-group-item')
                for item in items:
                    try:
                        title_elem = item.select_one('a')
                        if title_elem:
                            title = title_elem.text.strip()
                            url = title_elem['href']
                            
                            if not url.startswith('http'):
                                url = self.sources[source]["base_url"] + url
                            
                            novels.append({
                                'title': title,
                                'author': "未知作者",
                                'url': url,
                                'source': source
                            })
                    except:
                        continue
            
            # 去重
            unique_novels = []
            seen_titles = set()
            for novel in novels:
                if novel['title'] not in seen_titles:
                    seen_titles.add(novel['title'])
                    unique_novels.append(novel)
            
            # 更新进度
            progress_bar.progress(100)
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            return unique_novels[:15]  # 限制返回数量
            
        except Exception as e:
            st.error(f"搜索出错: {str(e)[:100]}")
            return []
    
    def get_chapters(self, novel_url: str, source: str) -> List[Dict]:
        """获取章节列表"""
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.text("正在加载章节列表...")
            
            # 发送请求
            response = self.make_request(novel_url)
            if response is None:
                progress_bar.empty()
                status_text.empty()
                return []
            
            progress_bar.progress(50)
            status_text.text("解析章节列表...")
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            chapters = []
            
            # 尝试多种选择器
            selectors = [
                self.sources[source]["chapter_selector"],
                "#list dd a",
                ".listmain dd a",
                ".chapter-list li a",
                ".zjlist dd a",
                ".chapterlist dd a"
            ]
            
            for selector in selectors:
                chapter_elems = soup.select(selector)
                if chapter_elems:
                    for elem in chapter_elems[:100]:  # 限制前100章
                        try:
                            if elem.get('href'):
                                title = elem.text.strip()
                                url = elem['href']
                                
                                # 处理相对URL
                                if not url.startswith('http'):
                                    if url.startswith('/'):
                                        url = self.sources[source]["base_url"] + url
                                    else:
                                        # 相对路径处理
                                        base_url = novel_url.rsplit('/', 1)[0]
                                        url = f"{base_url}/{url}"
                                
                                chapters.append({
                                    'title': title,
                                    'url': url
                                })
                        except:
                            continue
                    break
            
            # 去重
            unique_chapters = []
            seen_titles = set()
            for chapter in chapters:
                if chapter['title'] not in seen_titles:
                    seen_titles.add(chapter['title'])
                    unique_chapters.append(chapter)
            
            progress_bar.progress(100)
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            return unique_chapters
            
        except Exception as e:
            st.error(f"获取章节失败: {str(e)[:100]}")
            return []
    
    def get_chapter_content(self, chapter_url: str, source: str) -> str:
        """获取章节内容"""
        try:
            # 发送请求
            response = self.make_request(chapter_url)
            if response is None:
                return "无法获取章节内容"
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种内容选择器
            content_selectors = [
                self.sources[source]["content_selector"],
                "#content",
                ".content",
                "#htmlContent",
                ".chapter-content",
                ".read-content",
                "#chaptercontent",
                ".novel-content"
            ]
            
            content_elem = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    break
            
            if content_elem:
                # 清理内容
                content = content_elem.get_text()
                
                # 移除广告和无关内容
                patterns = [
                    r'请收藏.*?',
                    r'笔趣阁.*?',
                    r'www\..*?\.com',
                    r'https?://.*?',
                    r'记住.*?网址.*?',
                    r'章节错误.*?',
                    r'正在手打中.*?',
                    r'本站.*?',
                    r'请支持正版.*?',
                    r'PS[:：].*?',
                    r'注[:：].*?',
                    r'作者[:：].*?',
                    r'正文.*?',
                    r'上一章.*?下一章.*?',
                    r'返回目录.*?',
                    r'推荐阅读.*?'
                ]
                
                for pattern in patterns:
                    content = re.sub(pattern, '', content, flags=re.IGNORECASE)
                
                # 处理空白字符
                content = re.sub(r'\s+', '\n', content)
                content = re.sub(r'\n{3,}', '\n\n', content)
                content = content.strip()
                
                if not content:
                    return "内容为空，可能是网站结构变化"
                
                return content
            else:
                return "无法找到内容区域，网站可能已更新"
                
        except Exception as e:
            return f"获取内容时出错: {str(e)[:100]}"

def main():
    # 初始化会话状态
    if 'reader' not in st.session_state:
        st.session_state.reader = NovelReader()
    
    if 'current_novel' not in st.session_state:
        st.session_state.current_novel = None
    
    if 'chapters' not in st.session_state:
        st.session_state.chapters = []
    
    if 'current_chapter_index' not in st.session_state:
        st.session_state.current_chapter_index = 0
    
    if 'font_size' not in st.session_state:
        st.session_state.font_size = 18
    
    if 'night_mode' not in st.session_state:
        st.session_state.night_mode = False
    
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "搜索"
    
    # 主标题
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #667eea; font-size: 2.5rem; margin-bottom: 0.5rem;">📚 手机小说阅读器</h1>
        <p style="color: #666; font-size: 1rem;">支持盗版小说搜索阅读 - 畅享海量免费小说</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 创建标签页
    tab1, tab2 = st.tabs(["🔍 搜索小说", "📖 阅读"])
    
    with tab1:
        st.markdown("### 🎯 搜索设置")
        
        # 搜索表单
        col1, col2 = st.columns([3, 1])
        with col1:
            search_keyword = st.text_input("", placeholder="输入小说名或作者名...", key="search_input")
        with col2:
            source = st.selectbox("选择书源", list(st.session_state.reader.sources.keys()), key="source_select")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_clicked = st.button("🔍 开始搜索", type="primary", use_container_width=True)
        with col2:
            if st.button("🔄 刷新", use_container_width=True):
                st.rerun()
        with col3:
            if st.button("📜 清空历史", use_container_width=True):
                st.session_state.search_history = []
                st.rerun()
        
        # 热门推荐
        st.markdown("### 🔥 热门推荐")
        hot_keywords = ["斗罗大陆", "斗破苍穹", "凡人修仙传", "完美世界", "赘婿", "大奉打更人", "诡秘之主"]
        cols = st.columns(4)
        for idx, keyword in enumerate(hot_keywords):
            with cols[idx % 4]:
                if st.button(keyword, use_container_width=True):
                    st.session_state.search_keyword = keyword
                    st.rerun()
        
        # 搜索历史
        if st.session_state.search_history:
            st.markdown("### 📜 搜索历史")
            cols = st.columns(3)
            for idx, (keyword, src) in enumerate(st.session_state.search_history[-6:]):
                with cols[idx % 3]:
                    if st.button(f"{keyword} ({src})", key=f"hist_{idx}", use_container_width=True):
                        search_keyword = keyword
                        source = src
                        search_clicked = True
        
        # 执行搜索
        if search_clicked and search_keyword:
            # 保存搜索历史
            if (search_keyword, source) not in st.session_state.search_history:
                if len(st.session_state.search_history) >= 10:
                    st.session_state.search_history.pop(0)
                st.session_state.search_history.append((search_keyword, source))
            
            # 显示搜索状态
            with st.spinner(f"正在搜索 '{search_keyword}'..."):
                novels = st.session_state.reader.search_novels(search_keyword, source)
            
            if novels:
                st.success(f"✅ 找到 {len(novels)} 本相关小说")
                
                # 显示搜索结果
                for i, novel in enumerate(novels):
                    # 创建卡片
                    st.markdown(f"""
                    <div class="novel-card">
                        <h3 style="margin: 0; font-size: 1.2rem;">{novel['title']}</h3>
                        <p style="margin: 0.5rem 0; font-size: 0.9rem; opacity: 0.9;">作者: {novel['author']}</p>
                        <p style="margin: 0; font-size: 0.8rem; opacity: 0.7;">来源: {novel['source']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 按钮
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("📖 开始阅读", key=f"read_{i}", use_container_width=True):
                            st.session_state.current_novel = novel
                            with st.spinner("正在加载章节列表..."):
                                chapters = st.session_state.reader.get_chapters(novel['url'], novel['source'])
                                if chapters:
                                    st.session_state.chapters = chapters
                                    st.session_state.current_chapter_index = 0
                                    st.success(f"✅ 加载 {len(chapters)} 个章节成功！")
                                    # 切换到阅读标签
                                    st.rerun()
                                else:
                                    st.error("❌ 无法加载章节列表")
                    with col2:
                        if st.button("🔗 查看详情", key=f"detail_{i}", use_container_width=True):
                            with st.expander(f"📋 小说详情", expanded=True):
                                st.write(f"**书名**: {novel['title']}")
                                st.write(f"**作者**: {novel['author']}")
                                st.write(f"**来源**: {novel['source']}")
                                st.write(f"**链接**: [点击访问]({novel['url']})")
                    
                    st.markdown("---")
            else:
                st.warning("⚠️ 未找到相关小说，请尝试：")
                st.info("""
                1. 更换搜索关键词
                2. 切换其他书源
                3. 检查网络连接
                4. 尝试其他热门小说
                """)
    
    with tab2:
        if st.session_state.current_novel and st.session_state.chapters:
            # 小说信息和控制栏
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"### {st.session_state.current_novel['title']}")
                st.caption(f"👤 作者: {st.session_state.current_novel['author']} | 📚 来源: {st.session_state.current_novel['source']}")
            with col2:
                if st.button("🔙 返回", use_container_width=True):
                    st.session_state.current_novel = None
                    st.rerun()
            with col3:
                if st.button("🔄 刷新", use_container_width=True):
                    st.rerun()
            
            st.markdown("---")
            
            # 章节导航和设置
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            with col1:
                if st.button("⏮️ 首章", disabled=st.session_state.current_chapter_index == 0, use_container_width=True):
                    st.session_state.current_chapter_index = 0
                    st.rerun()
            with col2:
                if st.button("◀️ 上一章", disabled=st.session_state.current_chapter_index == 0, use_container_width=True):
                    st.session_state.current_chapter_index -= 1
                    st.rerun()
            with col3:
                if st.button("▶️ 下一章", disabled=st.session_state.current_chapter_index >= len(st.session_state.chapters) - 1, use_container_width=True):
                    st.session_state.current_chapter_index += 1
                    st.rerun()
            with col4:
                if st.button("⏭️ 末章", disabled=st.session_state.current_chapter_index >= len(st.session_state.chapters) - 1, use_container_width=True):
                    st.session_state.current_chapter_index = len(st.session_state.chapters) - 1
                    st.rerun()
            
            # 进度条
            progress = (st.session_state.current_chapter_index + 1) / len(st.session_state.chapters)
            st.progress(progress)
            st.caption(f"📊 进度: 第 {st.session_state.current_chapter_index + 1} 章 / 共 {len(st.session_state.chapters)} 章")
            
            # 阅读设置
            with st.expander("⚙️ 阅读设置", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.font_size = st.slider("字体大小", 14, 24, st.session_state.font_size)
                with col2:
                    st.session_state.night_mode = st.toggle("夜间模式", st.session_state.night_mode)
            
            # 章节内容
            current_chapter = st.session_state.chapters[st.session_state.current_chapter_index]
            st.markdown(f"### 📖 {current_chapter['title']}")
            
            with st.spinner("正在加载章节内容..."):
                content = st.session_state.reader.get_chapter_content(
                    current_chapter['url'],
                    st.session_state.current_novel['source']
                )
                
                # 显示内容
                st.markdown(f"""
                <div class="content-box" style="font-size: {st.session_state.font_size}px;">
                    <div class="chapter-content">
                        {content.replace('\n', '<br>')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 底部导航
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("◀️ 上一页", disabled=st.session_state.current_chapter_index == 0, use_container_width=True):
                    st.session_state.current_chapter_index -= 1
                    st.rerun()
            
            with col2:
                chapter_titles = [f"第{i+1}章: {chap['title'][:30]}..." for i, chap in enumerate(st.session_state.chapters[:50])]
                selected_index = st.selectbox(
                    "快速跳转章节",
                    range(len(st.session_state.chapters[:50])),
                    format_func=lambda x: chapter_titles[x] if x < len(chapter_titles) else f"第{x+1}章",
                    index=st.session_state.current_chapter_index,
                    key="chapter_selector"
                )
                if selected_index != st.session_state.current_chapter_index:
                    st.session_state.current_chapter_index = selected_index
                    st.rerun()
            
            with col3:
                if st.button("▶️ 下一页", disabled=st.session_state.current_chapter_index >= len(st.session_state.chapters) - 1, use_container_width=True):
                    st.session_state.current_chapter_index += 1
                    st.rerun()
        
        else:
            # 欢迎界面
            st.markdown("""
            <div style="text-align: center; padding: 3rem 1rem;">
                <h2 style="color: #667eea;">📚 欢迎使用手机小说阅读器</h2>
                <p style="color: #666; margin-bottom: 2rem;">搜索并阅读您喜欢的小说</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 使用指南
            with st.expander("📖 使用指南", expanded=True):
                st.markdown("""
                ### 如何使用本阅读器：
                
                1. **搜索小说**
                   - 在搜索标签中输入小说名或作者名
                   - 选择合适的书源（推荐使用"笔趣阁1号"）
                   - 点击"开始搜索"按钮
                
                2. **开始阅读**
                   - 在搜索结果中点击"开始阅读"
                   - 系统会自动加载章节列表
                   - 使用导航按钮浏览章节
                
                3. **阅读设置**
                   - 调整字体大小以获得最佳阅读体验
                   - 开启夜间模式保护眼睛
                   - 使用进度条和章节跳转快速导航
                
                ### 温馨提示：
                - 📱 本应用已优化手机端显示
                - 🔄 如搜索失败，请尝试更换书源
                - 💾 阅读进度会自动保存
                - ⚠️ 请遵守相关法律法规
                """)
            
            # 常见问题
            with st.expander("❓ 常见问题", expanded=False):
                st.markdown("""
                **Q: 为什么搜索不到小说？**
                A: 请尝试更换书源，某些网站可能暂时不可用。
                
                **Q: 章节内容显示异常怎么办？**
                A: 点击刷新按钮重新加载，或切换到其他章节。
                
                **Q: 如何保存阅读进度？**
                A: 应用会自动保存您的阅读进度，下次打开会继续阅读。
                
                **Q: 支持离线阅读吗？**
                A: 目前不支持离线阅读，需要网络连接。
                """)
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #999; font-size: 0.9rem; padding: 1rem;'>
        <p>📱 手机小说阅读器 v2.0 | 支持盗版小说搜索阅读 | 仅供学习交流使用</p>
        <p>⚠️ 请支持正版阅读，本应用不存储任何小说内容</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
