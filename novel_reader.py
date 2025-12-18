import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import warnings
import time

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
        'About': "手机小说阅读器 v3.0 - 支持盗版小说搜索阅读"
    }
)

# 自定义CSS样式
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
    }
    
    /* 卡片样式 */
    .novel-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* 按钮修复 */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
    }
    
    /* 内容样式 */
    .content-box {
        background: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    
    /* 隐藏不需要的元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

class SimpleNovelReader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def search_novels(self, keyword: str) -> list:
        """搜索小说 - 使用稳定的源"""
        try:
            # 使用多个源进行搜索
            search_results = []
            
            # 源1: 笔趣阁
            try:
                url1 = f"https://www.bqg789.com/s?q={urllib.parse.quote(keyword)}"
                response = requests.get(url1, headers=self.headers, timeout=10, verify=False)
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.select('.book-item')
                
                for item in items[:5]:
                    title_elem = item.select_one('h4 a')
                    if title_elem:
                        search_results.append({
                            'title': title_elem.text.strip(),
                            'author': '未知作者',
                            'url': f"https://www.bqg789.com{title_elem['href']}",
                            'source': '笔趣阁'
                        })
            except:
                pass
            
            # 源2: 顶点小说
            try:
                url2 = f"http://www.xbiquge.la/modules/article/waps.php?searchkey={urllib.parse.quote(keyword)}"
                response = requests.get(url2, headers=self.headers, timeout=10, verify=False)
                response.encoding = 'gbk'
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.select('tr')[1:]  # 跳过表头
                
                for item in items[:5]:
                    cols = item.select('td')
                    if len(cols) >= 2:
                        title_elem = cols[0].select_one('a')
                        if title_elem:
                            search_results.append({
                                'title': title_elem.text.strip(),
                                'author': cols[2].text.strip() if len(cols) > 2 else '未知作者',
                                'url': title_elem['href'],
                                'source': '顶点小说'
                            })
            except:
                pass
            
            # 源3: 免费小说
            try:
                url3 = f"https://www.mianfeixiaoshuo.com/search/?searchkey={urllib.parse.quote(keyword)}"
                response = requests.get(url3, headers=self.headers, timeout=10, verify=False)
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.select('.list-group-item')
                
                for item in items[:5]:
                    title_elem = item.select_one('a')
                    if title_elem:
                        search_results.append({
                            'title': title_elem.text.strip(),
                            'author': '未知作者',
                            'url': title_elem['href'],
                            'source': '免费小说'
                        })
            except:
                pass
            
            return search_results
            
        except Exception as e:
            st.error(f"搜索失败: {str(e)}")
            return []
    
    def get_chapters(self, url: str) -> list:
        """获取章节列表"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            chapters = []
            
            # 尝试不同的选择器
            selectors = ['#list dd a', '.listmain dd a', '.chapter-list a', '.zjlist dd a']
            
            for selector in selectors:
                chapter_elems = soup.select(selector)
                if chapter_elems:
                    for elem in chapter_elems[:50]:  # 只取前50章
                        if elem.get('href'):
                            chapter_url = elem['href']
                            if not chapter_url.startswith('http'):
                                if chapter_url.startswith('/'):
                                    base_url = '/'.join(url.split('/')[:3])
                                    chapter_url = base_url + chapter_url
                                else:
                                    chapter_url = url.rsplit('/', 1)[0] + '/' + chapter_url
                            
                            chapters.append({
                                'title': elem.text.strip(),
                                'url': chapter_url
                            })
                    break
            
            return chapters
            
        except Exception as e:
            st.error(f"获取章节失败: {str(e)}")
            return []
    
    def get_chapter_content(self, url: str) -> str:
        """获取章节内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试不同的内容选择器
            content_selectors = ['#content', '.content', '#htmlContent', '.chapter-content']
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 清理内容
                    content = content_elem.get_text()
                    content = re.sub(r'\s+', '\n', content)
                    content = re.sub(r'\n{3,}', '\n\n', content)
                    content = re.sub(r'请收藏.*', '', content)
                    content = re.sub(r'笔趣阁.*', '', content)
                    content = content.strip()
                    return content
            
            return "无法获取内容"
            
        except Exception as e:
            return f"获取内容失败: {str(e)}"

def init_session_state():
    """初始化会话状态"""
    if 'reader' not in st.session_state:
        st.session_state.reader = SimpleNovelReader()
    
    if 'current_novel' not in st.session_state:
        st.session_state.current_novel = None
    
    if 'chapters' not in st.session_state:
        st.session_state.chapters = []
    
    if 'current_chapter_index' not in st.session_state:
        st.session_state.current_chapter_index = 0
    
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    if 'is_loading' not in st.session_state:
        st.session_state.is_loading = False

def main():
    # 初始化会话状态
    init_session_state()
    
    # 主标题
    st.title("📱 手机小说阅读器")
    
    # 创建标签页
    tab1, tab2 = st.tabs(["🔍 搜索小说", "📖 阅读"])
    
    with tab1:
        st.markdown("### 搜索小说")
        
        # 搜索框
        col1, col2 = st.columns([3, 1])
        with col1:
            search_keyword = st.text_input("", placeholder="输入小说名...")
        with col2:
            search_clicked = st.button("搜索", type="primary")
        
        # 热门搜索
        st.markdown("**热门搜索:**")
        hot_keywords = ["斗罗大陆", "斗破苍穹", "凡人修仙传", "完美世界"]
        cols = st.columns(4)
        for i, keyword in enumerate(hot_keywords):
            with cols[i]:
                if st.button(keyword, key=f"hot_{i}"):
                    search_keyword = keyword
                    st.session_state.is_loading = True
                    st.rerun()
        
        # 处理搜索
        if search_clicked and search_keyword:
            st.session_state.is_loading = True
        
        if st.session_state.is_loading:
            with st.spinner("搜索中..."):
                if search_keyword:
                    st.session_state.search_results = st.session_state.reader.search_novels(search_keyword)
                    st.session_state.is_loading = False
        
        # 显示搜索结果
        if st.session_state.search_results:
            st.markdown(f"### 搜索结果 ({len(st.session_state.search_results)}个)")
            
            for i, novel in enumerate(st.session_state.search_results):
                with st.container():
                    st.markdown(f"""
                    <div class="novel-card">
                        <h4>{novel['title']}</h4>
                        <p>作者: {novel['author']} | 来源: {novel['source']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("开始阅读", key=f"read_{i}"):
                            st.session_state.current_novel = novel
                            with st.spinner("加载章节中..."):
                                chapters = st.session_state.reader.get_chapters(novel['url'])
                                if chapters:
                                    st.session_state.chapters = chapters
                                    st.session_state.current_chapter_index = 0
                                    st.success("加载成功！切换到阅读标签")
                                    st.rerun()
                                else:
                                    st.error("无法加载章节列表")
                    
                    st.divider()
    
    with tab2:
        if st.session_state.current_novel and st.session_state.chapters:
            # 小说信息
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.subheader(st.session_state.current_novel['title'])
                st.caption(f"作者: {st.session_state.current_novel['author']} | 来源: {st.session_state.current_novel['source']}")
            
            # 章节导航
            if st.session_state.chapters:
                current_chapter = st.session_state.chapters[st.session_state.current_chapter_index]
                
                # 导航按钮
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("⏮️ 首章", key="first_chapter"):
                        if st.session_state.current_chapter_index > 0:
                            st.session_state.current_chapter_index = 0
                            st.rerun()
                
                with col2:
                    if st.button("◀️ 上一章", key="prev_chapter"):
                        if st.session_state.current_chapter_index > 0:
                            st.session_state.current_chapter_index -= 1
                            st.rerun()
                
                with col3:
                    if st.button("▶️ 下一章", key="next_chapter"):
                        if st.session_state.current_chapter_index < len(st.session_state.chapters) - 1:
                            st.session_state.current_chapter_index += 1
                            st.rerun()
                
                with col4:
                    if st.button("⏭️ 末章", key="last_chapter"):
                        if st.session_state.current_chapter_index < len(st.session_state.chapters) - 1:
                            st.session_state.current_chapter_index = len(st.session_state.chapters) - 1
                            st.rerun()
                
                # 显示章节标题和内容
                st.markdown(f"### {current_chapter['title']}")
                
                with st.spinner("加载内容中..."):
                    content = st.session_state.reader.get_chapter_content(current_chapter['url'])
                    st.markdown(f"""
                    <div class="content-box">
                        {content.replace('\n', '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
                
                # 进度显示
                progress = (st.session_state.current_chapter_index + 1) / len(st.session_state.chapters)
                st.progress(progress)
                st.caption(f"第 {st.session_state.current_chapter_index + 1} 章 / 共 {len(st.session_state.chapters)} 章")
                
                # 章节选择器
                chapter_options = [f"第{i+1}章: {chap['title'][:20]}..." for i, chap in enumerate(st.session_state.chapters[:30])]
                selected_index = st.selectbox(
                    "快速跳转",
                    range(len(st.session_state.chapters[:30])),
                    format_func=lambda x: chapter_options[x] if x < len(chapter_options) else f"第{x+1}章",
                    index=st.session_state.current_chapter_index if st.session_state.current_chapter_index < 30 else 0,
                    key="chapter_selector"
                )
                if selected_index != st.session_state.current_chapter_index:
                    st.session_state.current_chapter_index = selected_index
                    st.rerun()
        
        else:
            st.info("📖 还没有开始阅读小说")
            st.write("请在搜索标签中搜索并选择一本小说开始阅读")
            
            # 使用指南
            with st.expander("使用说明"):
                st.write("""
                1. **搜索小说**: 在搜索标签中输入小说名
                2. **选择小说**: 在搜索结果中点击"开始阅读"
                3. **阅读设置**: 使用导航按钮浏览章节
                4. **快速跳转**: 使用章节选择器跳转到指定章节
                
                **温馨提示**:
                - 如果搜索失败，请尝试更换关键词
                - 部分网站可能加载较慢，请耐心等待
                - 遇到问题可以刷新页面重试
                """)
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 12px;'>
        手机小说阅读器 v3.0 | 仅供学习交流使用
    </div>
    """, unsafe_allow_html=True)

# 确保应用正确运行
if __name__ == "__main__":
    main()
