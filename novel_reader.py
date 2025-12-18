import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

# 禁用SSL警告
warnings.filterwarnings('ignore')

# 页面配置 - 专为手机优化
st.set_page_config(
    page_title="小说阅读器",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# 自定义CSS - 手机端优化
st.markdown("""
<style>
    /* 全局样式 */
    html, body, [class*="css"] {
        font-family: 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
    }
    
    /* 手机端优化 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem;
            max-width: 100%;
        }
        
        h1 {
            font-size: 1.5rem !important;
            text-align: center;
            margin-top: 0.5rem;
        }
        
        h2 {
            font-size: 1.2rem !important;
        }
        
        h3 {
            font-size: 1rem !important;
        }
        
        .stButton > button {
            font-size: 14px;
            padding: 8px 12px;
        }
    }
    
    /* 搜索框样式 */
    .stTextInput > div > div > input {
        font-size: 16px;
        border-radius: 20px;
        padding: 12px 16px;
        border: 2px solid #e0e0e0;
    }
    
    /* 按钮样式 */
    .stButton > button {
        border-radius: 10px;
        border: none;
        font-weight: 500;
        transition: all 0.3s ease;
        margin: 4px 0;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .read-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* 小说卡片样式 */
    .novel-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .novel-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* 章节样式 */
    .chapter-item {
        padding: 12px 16px;
        border-bottom: 1px solid #eee;
        margin: 4px 0;
        border-radius: 8px;
        background: #f8f9fa;
        transition: all 0.2s ease;
    }
    
    .chapter-item:hover {
        background: #e9ecef;
        transform: translateX(5px);
    }
    
    /* 内容区域样式 */
    .content-area {
        font-size: 18px;
        line-height: 1.8;
        text-align: justify;
        padding: 20px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        margin: 10px 0;
        min-height: 60vh;
    }
    
    .night-mode .content-area {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: #e0e0e0;
    }
    
    /* 进度条样式 */
    .progress-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 10px;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
    }
    
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 底部导航 */
    .bottom-nav {
        display: flex;
        justify-content: space-around;
        padding: 10px;
        background: white;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
    
    .nav-btn {
        flex: 1;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        margin: 0 4px;
    }
</style>
""", unsafe_allow_html=True)

class MultiSourceNovelReader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
        }
        self.sources = self.get_sources()
    
    def get_sources(self):
        """获取所有可用的数据源"""
        return [
            {
                "name": "笔趣阁1",
                "search_url": "https://www.biquge7.com/search?q={}",
                "base_url": "https://www.biquge7.com",
                "chapter_selector": ".listmain dd a",
                "content_selector": "#chaptercontent",
                "search_selector": ".bookinfo",
                "title_selector": "h4 a",
                "author_selector": ".author"
            },
            {
                "name": "笔趣阁2",
                "search_url": "https://www.b5200.org/modules/article/search.php?searchkey={}",
                "base_url": "https://www.b5200.org",
                "chapter_selector": ".listmain dd a",
                "content_selector": "#content",
                "search_selector": ".grid tr",
                "title_selector": "td:nth-child(1) a",
                "author_selector": "td:nth-child(3)"
            },
            {
                "name": "小说楼",
                "search_url": "http://www.xslou.com/modules/article/search.php?searchkey={}",
                "base_url": "http://www.xslou.com",
                "chapter_selector": ".zjlist dd a",
                "content_selector": "#content",
                "search_selector": ".grid tr",
                "title_selector": "td:nth-child(1) a",
                "author_selector": "td:nth-child(3)"
            },
            {
                "name": "新笔趣阁",
                "search_url": "https://www.xbiquge.so/search.php?keyword={}",
                "base_url": "https://www.xbiquge.so",
                "chapter_selector": ".listmain dd a",
                "content_selector": "#content",
                "search_selector": ".grid tr",
                "title_selector": "td:nth-child(1) a",
                "author_selector": "td:nth-child(3)"
            }
        ]
    
    def search_single_source(self, source, keyword):
        """单个数据源搜索"""
        try:
            url = source["search_url"].format(urllib.parse.quote(keyword))
            response = requests.get(url, headers=self.headers, timeout=5, verify=False)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            novels = []
            items = soup.select(source["search_selector"])
            
            for item in items[:5]:  # 每个源只取前5个结果
                try:
                    title_elem = item.select_one(source["title_selector"])
                    author_elem = item.select_one(source["author_selector"])
                    
                    if title_elem and title_elem.text.strip():
                        novel = {
                            'title': title_elem.text.strip(),
                            'author': author_elem.text.strip() if author_elem else '未知',
                            'url': title_elem.get('href', ''),
                            'source': source["name"],
                            'base_url': source["base_url"]
                        }
                        
                        # 处理相对URL
                        if novel['url'] and not novel['url'].startswith('http'):
                            novel['url'] = source["base_url"] + novel['url']
                        
                        novels.append(novel)
                except:
                    continue
            
            return novels
        except:
            return []
    
    def search_all_sources(self, keyword):
        """并行搜索所有数据源"""
        all_novels = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for source in self.sources:
                future = executor.submit(self.search_single_source, source, keyword)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    novels = future.result(timeout=10)
                    all_novels.extend(novels)
                except:
                    continue
        
        # 去重（基于标题）
        seen_titles = set()
        unique_novels = []
        for novel in all_novels:
            title = novel['title']
            if title not in seen_titles:
                seen_titles.add(title)
                unique_novels.append(novel)
        
        return unique_novels[:20]  # 限制总结果数
    
    def get_chapters(self, novel_url, source_name):
        """获取章节列表"""
        try:
            # 找到对应的源配置
            source_config = None
            for source in self.sources:
                if source["name"] == source_name:
                    source_config = source
                    break
            
            if not source_config:
                return []
            
            response = requests.get(novel_url, headers=self.headers, timeout=10, verify=False)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            chapters = []
            chapter_elems = soup.select(source_config["chapter_selector"])
            
            for elem in chapter_elems[:100]:  # 限制前100章
                if elem.get('href'):
                    chapter = {
                        'title': elem.text.strip(),
                        'url': elem['href']
                    }
                    
                    # 处理相对URL
                    if chapter['url'] and not chapter['url'].startswith('http'):
                        chapter['url'] = source_config["base_url"] + chapter['url']
                    
                    chapters.append(chapter)
            
            return chapters
        except Exception as e:
            st.error(f"获取章节失败: {str(e)}")
            return []
    
    def get_chapter_content(self, chapter_url, source_name):
        """获取章节内容"""
        try:
            # 找到对应的源配置
            source_config = None
            for source in self.sources:
                if source["name"] == source_name:
                    source_config = source
                    break
            
            if not source_config:
                return "无法获取内容"
            
            response = requests.get(chapter_url, headers=self.headers, timeout=10, verify=False)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content_elem = soup.select_one(source_config["content_selector"])
            if content_elem:
                content = content_elem.get_text()
                # 清理内容
                content = re.sub(r'\s+', '\n', content)
                content = re.sub(r'[　]+', '', content)
                content = re.sub(r'请收藏.*', '', content)
                content = re.sub(r'笔趣阁.*', '', content)
                content = re.sub(r'www\..*\.(com|cn|net|org)', '', content)
                content = re.sub(r'https?://', '', content)
                
                # 分割段落
                paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
                return '\n\n'.join(paragraphs)
            
            return "无法获取章节内容"
        except Exception as e:
            return f"获取内容失败: {str(e)}"

def main():
    # 初始化
    if 'reader' not in st.session_state:
        st.session_state.reader = MultiSourceNovelReader()
    
    if 'night_mode' not in st.session_state:
        st.session_state.night_mode = False
    
    if 'font_size' not in st.session_state:
        st.session_state.font_size = 18
    
    if 'current_novel' not in st.session_state:
        st.session_state.current_novel = None
    
    if 'chapters' not in st.session_state:
        st.session_state.chapters = []
    
    if 'current_chapter_index' not in st.session_state:
        st.session_state.current_chapter_index = 0
    
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    # 主界面
    st.title("📚 手机小说阅读器")
    st.caption("输入书名搜索，选择喜欢的源开始阅读")
    
    # 搜索区域
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            search_keyword = st.text_input(
                "🔍 搜索小说",
                placeholder="输入小说名，如：斗罗大陆",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("搜索", use_container_width=True):
                if search_keyword:
                    with st.spinner("搜索中..."):
                        results = st.session_state.reader.search_all_sources(search_keyword)
                        st.session_state.search_results = results
    
    # 显示搜索结果
    if st.session_state.search_results:
        st.subheader(f"📖 搜索结果 ({len(st.session_state.search_results)} 本)")
        
        # 按两列布局显示搜索结果
        cols = st.columns(2)
        for i, novel in enumerate(st.session_state.search_results):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div class="novel-card">
                        <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">
                            {novel['title']}
                        </div>
                        <div style="color: #666; font-size: 12px; margin-bottom: 8px;">
                            👤 {novel['author']}
                        </div>
                        <div style="color: #888; font-size: 11px;">
                            📍 {novel['source']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 阅读按钮
                    if st.button("开始阅读", key=f"read_{i}", use_container_width=True):
                        st.session_state.current_novel = novel
                        with st.spinner("加载章节中..."):
                            chapters = st.session_state.reader.get_chapters(
                                novel['url'],
                                novel['source']
                            )
                            if chapters:
                                st.session_state.chapters = chapters
                                st.session_state.current_chapter_index = 0
                                st.success("加载成功！")
                                st.rerun()
                            else:
                                st.error("无法获取章节列表")
        
        st.divider()
    
    # 阅读界面
    if st.session_state.current_novel and st.session_state.chapters:
        # 顶部导航
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.subheader(st.session_state.current_novel['title'])
            st.caption(f"作者: {st.session_state.current_novel['author']} | 源: {st.session_state.current_novel['source']}")
        
        with col2:
            if st.button("🔙", help="返回", use_container_width=True):
                st.session_state.current_novel = None
                st.session_state.chapters = []
                st.rerun()
        
        # 设置按钮
        with col3:
            settings_expander = st.popover("⚙️")
            with settings_expander:
                night_mode = st.toggle("夜间模式", value=st.session_state.night_mode)
                if night_mode != st.session_state.night_mode:
                    st.session_state.night_mode = night_mode
                    st.rerun()
                
                font_size = st.slider("字体大小", 14, 24, st.session_state.font_size)
                if font_size != st.session_state.font_size:
                    st.session_state.font_size = font_size
        
        # 章节选择
        with col4:
            chapter_expander = st.popover("📑")
            with chapter_expander:
                if st.session_state.chapters:
                    for i, chapter in enumerate(st.session_state.chapters[:30]):  # 显示前30章
                        if st.button(
                            chapter['title'][:20] + ("..." if len(chapter['title']) > 20 else ""),
                            key=f"chap_{i}",
                            use_container_width=True
                        ):
                            st.session_state.current_chapter_index = i
                            st.rerun()
        
        st.divider()
        
        # 章节内容
        current_chapter = st.session_state.chapters[st.session_state.current_chapter_index]
        
        # 章节导航
        nav_cols = st.columns(4)
        with nav_cols[0]:
            if st.button("⏮️ 首章", disabled=st.session_state.current_chapter_index == 0, use_container_width=True):
                st.session_state.current_chapter_index = 0
                st.rerun()
        with nav_cols[1]:
            if st.button("◀️ 上一章", disabled=st.session_state.current_chapter_index == 0, use_container_width=True):
                st.session_state.current_chapter_index -= 1
                st.rerun()
        with nav_cols[2]:
            if st.button("▶️ 下一章", 
                        disabled=st.session_state.current_chapter_index == len(st.session_state.chapters) - 1,
                        use_container_width=True):
                st.session_state.current_chapter_index += 1
                st.rerun()
        with nav_cols[3]:
            if st.button("⏭️ 末章", 
                        disabled=st.session_state.current_chapter_index == len(st.session_state.chapters) - 1,
                        use_container_width=True):
                st.session_state.current_chapter_index = len(st.session_state.chapters) - 1
                st.rerun()
        
        # 章节标题
        st.markdown(f"### 📖 {current_chapter['title']}")
        
        # 阅读内容
        with st.spinner("加载内容..."):
            content = st.session_state.reader.get_chapter_content(
                current_chapter['url'],
                st.session_state.current_novel['source']
            )
            
            # 应用样式
            content_style = f"""
            <div class="content-area" style="
                font-size: {st.session_state.font_size}px;
            ">
                {content.replace('\n', '<br>')}
            </div>
            """
            st.markdown(content_style, unsafe_allow_html=True)
        
        # 进度显示
        progress = (st.session_state.current_chapter_index + 1) / len(st.session_state.chapters)
        st.progress(progress)
        
        # 底部导航（用于手机端）
        st.markdown("""
        <div class="bottom-nav">
            <div class="nav-btn" style="background: #f0f0f0;">📚 书架</div>
            <div class="nav-btn" style="background: #667eea; color: white;">📖 阅读</div>
            <div class="nav-btn" style="background: #f0f0f0;">🔍 搜索</div>
            <div class="nav-btn" style="background: #f0f0f0;">⚙️ 设置</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 底部间距（给固定导航栏留出空间）
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    else:
        # 欢迎界面
        if not st.session_state.search_results:
            st.markdown("""
            <div style="text-align: center; padding: 40px 20px;">
                <div style="font-size: 48px; margin-bottom: 20px;">📚</div>
                <h3>欢迎使用手机小说阅读器</h3>
                <p style="color: #666;">输入小说名称搜索，支持多个书源</p>
                <p style="color: #888; font-size: 12px;">示例：斗破苍穹、完美世界、凡人修仙传</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 热门推荐
            st.subheader("🔥 热门推荐")
            hot_novels = [
                {"title": "斗破苍穹", "author": "天蚕土豆"},
                {"title": "凡人修仙传", "author": "忘语"},
                {"title": "完美世界", "author": "辰东"},
                {"title": "遮天", "author": "辰东"},
                {"title": "圣墟", "author": "辰东"},
                {"title": "星辰变", "author": "我吃西红柿"},
            ]
            
            cols = st.columns(2)
            for i, novel in enumerate(hot_novels):
                with cols[i % 2]:
                    if st.button(f"📖 {novel['title']}\n👤 {novel['author']}", use_container_width=True):
                        st.session_state.search_results = st.session_state.reader.search_all_sources(novel['title'])
                        st.rerun()
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; font-size: 12px; padding: 10px;'>
        本应用仅供学习交流使用，请支持正版阅读<br>
        自动搜索多个书源，选择最合适的进行阅读
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
