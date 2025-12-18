import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import warnings

# 禁用SSL警告
warnings.filterwarnings('ignore')

# 页面配置 - 适配手机端
st.set_page_config(
    page_title="手机小说阅读器",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS样式优化手机端显示
st.markdown("""
<style>
    /* 手机端优化 */
    @media (max-width: 768px) {
        .stApp {
            padding: 0.5rem;
        }
        .main > div {
            padding: 0.5rem;
        }
        h1 {
            font-size: 1.5rem !important;
        }
        h2 {
            font-size: 1.2rem !important;
        }
        h3 {
            font-size: 1rem !important;
        }
    }
    
    /* 阅读器样式 */
    .novel-content {
        font-size: 18px;
        line-height: 1.8;
        text-align: justify;
        padding: 20px;
        background-color: #f5f5f5;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .chapter-title {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* 按钮样式 */
    .stButton > button {
        width: 100%;
        margin: 5px 0;
        border-radius: 8px;
        font-size: 16px !important;
        height: 48px !important;
    }
    
    /* 搜索框样式 */
    .stTextInput > div > div > input {
        font-size: 18px !important;
        height: 50px !important;
    }
    
    /* 隐藏默认的Streamlit元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 夜间模式样式 */
    .night-mode {
        background-color: #1a1a1a !important;
        color: #e0e0e0 !important;
    }
    
    /* 小说卡片样式 */
    .novel-card {
        padding: 15px;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin: 10px 0;
        background-color: white;
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div {
        background-color: #3498db;
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3498db !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

class NovelReader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.sources = self.load_sources()
    
    def load_sources(self):
        """加载小说源配置"""
        return {
            "笔趣阁1": {
                "search_url": "https://www.bqktxt.com/search.php?q={}",
                "base_url": "https://www.bqktxt.com",
                "chapter_selector": ".list-chapter li a",
                "content_selector": "#content"
            },
            "笔趣阁2": {
                "search_url": "https://www.xbiquge.tw/search.php?keyword={}",
                "base_url": "https://www.xbiquge.tw",
                "chapter_selector": "#list dd a",
                "content_selector": "#content"
            },
            "免费小说": {
                "search_url": "https://www.mianfeixiaoshuo.com/search/?searchkey={}",
                "base_url": "https://www.mianfeixiaoshuo.com",
                "chapter_selector": ".list-group-item a",
                "content_selector": ".content"
            }
        }
    
    def safe_request(self, url, verify_ssl=False):
        """安全的请求函数"""
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=15,
                verify=verify_ssl
            )
            response.encoding = 'utf-8'
            return response
        except requests.exceptions.SSLError:
            # 如果SSL验证失败，尝试不验证
            try:
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=15,
                    verify=False
                )
                response.encoding = 'utf-8'
                return response
            except Exception as e:
                st.error(f"SSL错误: {str(e)[:100]}")
                return None
        except Exception as e:
            st.error(f"请求失败: {str(e)[:100]}")
            return None
    
    def search_novels(self, keyword, source="笔趣阁1"):
        """搜索小说"""
        try:
            if source not in self.sources:
                return []
            
            search_url = self.sources[source]["search_url"].format(urllib.parse.quote(keyword))
            
            with st.spinner(f"正在搜索{source}..."):
                response = self.safe_request(search_url, verify_ssl=False)
                
                if response is None or response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                novels = []
                
                # 根据不同的书源解析搜索结果
                if source == "笔趣阁1":
                    items = soup.select('.book-info')
                    for item in items:
                        title_elem = item.select_one('h4 a')
                        author_elem = item.select_one('.author')
                        if title_elem:
                            novels.append({
                                'title': title_elem.text.strip(),
                                'author': author_elem.text.strip() if author_elem else '未知',
                                'url': self.sources[source]["base_url"] + title_elem['href'],
                                'source': source
                            })
                
                elif source == "笔趣阁2":
                    items = soup.select('.result-item')
                    for item in items:
                        title_elem = item.select_one('.result-game-item-title-link')
                        author_elem = item.select_one('.result-game-item-info-tag:nth-child(1) span:nth-child(2)')
                        if title_elem:
                            novels.append({
                                'title': title_elem.get('title', '').strip(),
                                'author': author_elem.text.strip() if author_elem else '未知',
                                'url': title_elem['href'],
                                'source': source
                            })
                
                elif source == "免费小说":
                    items = soup.select('.book-list li')
                    for item in items:
                        title_elem = item.select_one('a')
                        if title_elem:
                            novels.append({
                                'title': title_elem.text.strip(),
                                'author': '未知',
                                'url': title_elem['href'],
                                'source': source
                            })
                
                return novels[:15]  # 限制返回数量
                
        except Exception as e:
            st.error(f"搜索出错: {str(e)[:100]}")
            return []
    
    def get_chapters(self, novel_url, source):
        """获取章节列表"""
        try:
            with st.spinner("加载章节列表中..."):
                response = self.safe_request(novel_url, verify_ssl=False)
                
                if response is None:
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                chapters = []
                
                # 根据书源解析章节
                chapter_elements = soup.select(self.sources[source]["chapter_selector"])
                
                for elem in chapter_elements[:100]:  # 限制前100章
                    if elem.get('href'):
                        chapter_url = elem['href']
                        if not chapter_url.startswith('http'):
                            if chapter_url.startswith('/'):
                                chapter_url = self.sources[source]["base_url"] + chapter_url
                            else:
                                chapter_url = novel_url.rsplit('/', 1)[0] + '/' + chapter_url
                        
                        chapters.append({
                            'title': elem.text.strip(),
                            'url': chapter_url
                        })
                
                return chapters
                
        except Exception as e:
            st.error(f"获取章节失败: {str(e)[:100]}")
            return []
    
    def get_chapter_content(self, chapter_url, source):
        """获取章节内容"""
        try:
            response = self.safe_request(chapter_url, verify_ssl=False)
            
            if response is None:
                return "无法获取章节内容"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试不同的内容选择器
            content_selectors = [
                self.sources[source]["content_selector"],
                "#chaptercontent",
                ".content",
                "#htmlContent",
                ".novel-content",
                ".chapter-content",
                ".read-content"
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
                    r'请收藏.*',
                    r'笔趣阁.*',
                    r'www\..*\.com',
                    r'https?://.*',
                    r'记住手机版网址.*',
                    r'推荐阅读.*',
                    r'章节错误.*',
                    r'正在手打中.*',
                    r'本站.*',
                    r'请支持正版.*',
                    r'PS:.*',
                    r'注：.*',
                    r'作者：.*',
                    r'正文.*'
                ]
                
                for pattern in patterns:
                    content = re.sub(pattern, '', content, flags=re.IGNORECASE)
                
                # 标准化空格和换行
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
    
    # 主标题
    st.title("📱 手机小说阅读器")
    st.markdown("---")
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 阅读设置")
        
        # 夜间模式
        st.session_state.night_mode = st.toggle("夜间模式", value=st.session_state.night_mode)
        
        # 字体大小
        st.session_state.font_size = st.slider(
            "字体大小", 
            min_value=14, 
            max_value=24, 
            value=st.session_state.font_size
        )
        
        st.markdown("---")
        st.header("📚 当前阅读")
        
        if st.session_state.current_novel:
            st.write(f"**{st.session_state.current_novel['title']}**")
            st.write(f"作者: {st.session_state.current_novel['author']}")
            st.write(f"来源: {st.session_state.current_novel['source']}")
            
            if st.button("重新加载章节", use_container_width=True):
                with st.spinner("重新加载中..."):
                    chapters = st.session_state.reader.get_chapters(
                        st.session_state.current_novel['url'],
                        st.session_state.current_novel['source']
                    )
                    if chapters:
                        st.session_state.chapters = chapters
                        st.session_state.current_chapter_index = 0
                        st.success("重新加载成功!")
                        st.rerun()
                    else:
                        st.error("重新加载失败")
            
            st.markdown("---")
            
            # 章节跳转
            if st.session_state.chapters:
                chapter_options = [f"{i+1}. {chap['title'][:20]}..." for i, chap in enumerate(st.session_state.chapters)]
                selected_index = st.selectbox(
                    "快速跳转章节",
                    options=range(len(st.session_state.chapters)),
                    format_func=lambda x: chapter_options[x] if x < len(chapter_options) else f"第{x+1}章",
                    index=st.session_state.current_chapter_index
                )
                if selected_index != st.session_state.current_chapter_index:
                    st.session_state.current_chapter_index = selected_index
                    st.rerun()
    
    # 主内容区 - 标签页
    tab_search, tab_read = st.tabs(["🔍 搜索小说", "📖 阅读"])
    
    with tab_search:
        st.header("搜索小说")
        
        # 搜索历史
        if st.session_state.search_history:
            with st.expander("📜 搜索历史"):
                for i, (keyword, source) in enumerate(st.session_state.search_history[-5:]):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.write(f"**{keyword}** ({source})")
                    with cols[1]:
                        if st.button("🔍", key=f"search_hist_{i}"):
                            st.rerun()
        
        # 搜索表单
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            search_keyword = st.text_input("输入小说名或作者", key="search_input")
        with col2:
            source = st.selectbox("选择书源", list(st.session_state.reader.sources.keys()))
        with col3:
            search_clicked = st.button("搜索", type="primary", use_container_width=True)
        
        if search_clicked and search_keyword:
            # 保存搜索历史
            if len(st.session_state.search_history) >= 10:
                st.session_state.search_history.pop(0)
            st.session_state.search_history.append((search_keyword, source))
            
            # 执行搜索
            novels = st.session_state.reader.search_novels(search_keyword, source)
            
            if novels:
                st.success(f"找到 {len(novels)} 本相关小说")
                
                for i, novel in enumerate(novels):
                    with st.container():
                        st.markdown(f"""
                        <div class="novel-card">
                            <h4>{novel['title']}</h4>
                            <p>作者: {novel['author']} | 来源: {novel['source']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            if st.button("开始阅读", key=f"read_{i}", use_container_width=True):
                                st.session_state.current_novel = novel
                                with st.spinner("正在加载章节..."):
                                    chapters = st.session_state.reader.get_chapters(novel['url'], novel['source'])
                                    if chapters:
                                        st.session_state.chapters = chapters
                                        st.session_state.current_chapter_index = 0
                                        st.success(f"加载 {len(chapters)} 个章节成功！")
                                        # 切换到阅读标签
                                        st.rerun()
                                    else:
                                        st.error("无法加载章节列表")
                        
                        with col2:
                            if st.button("查看详情", key=f"detail_{i}", use_container_width=True):
                                with st.expander(f"小说详情: {novel['title']}"):
                                    st.write(f"**标题**: {novel['title']}")
                                    st.write(f"**作者**: {novel['author']}")
                                    st.write(f"**来源**: {novel['source']}")
                                    st.write(f"**URL**: {novel['url']}")
                        
                        st.markdown("---")
            else:
                st.warning("未找到相关小说，请尝试：")
                st.write("1. 更换搜索关键词")
                st.write("2. 更换其他书源")
                st.write("3. 检查网络连接")
    
    with tab_read:
        if st.session_state.current_novel and st.session_state.chapters:
            # 小说信息栏
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(st.session_state.current_novel['title'])
                st.caption(f"作者: {st.session_state.current_novel['author']} | 来源: {st.session_state.current_novel['source']}")
            
            with col2:
                if st.button("返回搜索", use_container_width=True):
                    st.session_state.current_novel = None
                    st.rerun()
            
            st.markdown("---")
            
            # 章节导航
            if len(st.session_state.chapters) > 0:
                current_chapter = st.session_state.chapters[st.session_state.current_chapter_index]
                
                # 导航按钮
                col1, col2, col3, col4 = st.columns(4)
                
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
                
                # 章节标题和进度
                st.markdown(f"### 📖 {current_chapter['title']}")
                progress = (st.session_state.current_chapter_index + 1) / len(st.session_state.chapters)
                st.progress(progress)
                st.caption(f"进度: 第 {st.session_state.current_chapter_index + 1} 章 / 共 {len(st.session_state.chapters)} 章")
                
                st.markdown("---")
                
                # 章节内容
                with st.spinner("正在加载内容..."):
                    content = st.session_state.reader.get_chapter_content(
                        current_chapter['url'],
                        st.session_state.current_novel['source']
                    )
                    
                    # 应用样式
                    bg_color = "#1a1a1a" if st.session_state.night_mode else "#f5f5f5"
                    text_color = "#e0e0e0" if st.session_state.night_mode else "#333333"
                    
                    st.markdown(f"""
                    <div style="
                        font-size: {st.session_state.font_size}px;
                        line-height: 1.8;
                        text-align: justify;
                        padding: 20px;
                        background-color: {bg_color};
                        color: {text_color};
                        border-radius: 10px;
                        margin: 10px 0;
                    ">
                        {content.replace('\n', '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # 底部导航
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("◀️ 上一页", disabled=st.session_state.current_chapter_index == 0, use_container_width=True):
                        st.session_state.current_chapter_index -= 1
                        st.rerun()
                
                with col2:
                    chapter_select = st.selectbox(
                        "快速选择章节",
                        options=range(len(st.session_state.chapters)),
                        format_func=lambda x: f"第{x+1}章: {st.session_state.chapters[x]['title'][:30]}...",
                        index=st.session_state.current_chapter_index
                    )
                    if chapter_select != st.session_state.current_chapter_index:
                        st.session_state.current_chapter_index = chapter_select
                        st.rerun()
                
                with col3:
                    if st.button("▶️ 下一页", disabled=st.session_state.current_chapter_index >= len(st.session_state.chapters) - 1, use_container_width=True):
                        st.session_state.current_chapter_index += 1
                        st.rerun()
        else:
            st.info("📚 欢迎使用手机小说阅读器")
            st.write("请先搜索并选择一本小说开始阅读。")
            
            # 使用指南
            with st.expander("📖 使用指南"):
                st.write("""
                1. **搜索小说**: 在搜索标签中输入小说名或作者名
                2. **选择书源**: 如果某个书源搜索失败，可以尝试其他书源
                3. **开始阅读**: 点击"开始阅读"按钮加载章节
                4. **阅读设置**: 可以在侧边栏调整字体大小和夜间模式
                5. **章节导航**: 使用上下章按钮或章节列表进行导航
                
                **温馨提示**:
                - 部分小说网站可能需要等待几秒钟加载
                - 如果某个章节加载失败，可以尝试重新加载
                - 建议在WiFi环境下使用，节省流量
                """)
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 14px; padding: 20px;'>
        <p>📚 手机小说阅读器 v1.0 | 仅供学习交流使用 | 请支持正版阅读</p>
        <p>遇到问题？尝试刷新页面或更换书源</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
