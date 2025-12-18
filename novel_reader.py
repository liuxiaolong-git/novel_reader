# requirements.txt
# streamlit
# requests
# beautifulsoup4
# lxml

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import Optional, List, Dict
import urllib.parse

# 页面配置 - 适配手机端
st.set_page_config(
    page_title="小说阅读器",
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
    }
    
    /* 搜索框样式 */
    .stTextInput > div > div > input {
        font-size: 16px;
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
</style>
""", unsafe_allow_html=True)

class NovelReader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.sources = self.load_sources()
        
    def load_sources(self):
        """加载小说源配置"""
        return {
            "笔趣阁": {
                "search_url": "https://www.biquge7.com/search?q={}",
                "base_url": "https://www.biquge7.com",
                "chapter_selector": ".listmain dd a",
                "content_selector": "#chaptercontent"
            },
            "小说楼": {
                "search_url": "https://www.xslou.com/modules/article/search.php?searchkey={}",
                "base_url": "https://www.xslou.com",
                "chapter_selector": ".zjlist dd a",
                "content_selector": "#content"
            }
        }
    
    def search_novels(self, keyword: str, source: str = "笔趣阁") -> List[Dict]:
        """搜索小说"""
        try:
            if source not in self.sources:
                return []
                
            search_url = self.sources[source]["search_url"].format(urllib.parse.quote(keyword))
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            novels = []
            
            if source == "笔趣阁":
                items = soup.select('.bookinfo')
                for item in items:
                    title_elem = item.select_one('h4 a')
                    author_elem = item.select_one('.author')
                    link_elem = item.select_one('a')
                    
                    if title_elem and link_elem:
                        novel = {
                            'title': title_elem.text.strip(),
                            'author': author_elem.text.replace('作者：', '').strip() if author_elem else '未知',
                            'url': self.sources[source]["base_url"] + link_elem['href'],
                            'source': source
                        }
                        novels.append(novel)
            
            elif source == "小说楼":
                items = soup.select('.grid tr')[1:]  # 跳过表头
                for item in items:
                    title_elem = item.select_one('td:nth-child(1) a')
                    author_elem = item.select_one('td:nth-child(3)')
                    
                    if title_elem:
                        novel = {
                            'title': title_elem.text.strip(),
                            'author': author_elem.text.strip() if author_elem else '未知',
                            'url': title_elem['href'],
                            'source': source
                        }
                        novels.append(novel)
            
            return novels[:20]  # 限制返回数量
            
        except Exception as e:
            st.error(f"搜索失败: {str(e)}")
            return []
    
    def get_chapters(self, novel_url: str, source: str) -> List[Dict]:
        """获取章节列表"""
        try:
            response = requests.get(novel_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            chapters = []
            
            if source == "笔趣阁":
                chapter_elems = soup.select(self.sources[source]["chapter_selector"])
                for elem in chapter_elems:
                    if elem.get('href') and not elem.get('href').startswith('javascript'):
                        chapter = {
                            'title': elem.text.strip(),
                            'url': self.sources[source]["base_url"] + elem['href'] if elem['href'].startswith('/') else elem['href']
                        }
                        chapters.append(chapter)
            
            elif source == "小说楼":
                chapter_elems = soup.select(self.sources[source]["chapter_selector"])
                for elem in chapter_elems:
                    if elem.get('href'):
                        chapter = {
                            'title': elem.text.strip(),
                            'url': elem['href'] if elem['href'].startswith('http') else self.sources[source]["base_url"] + elem['href']
                        }
                        chapters.append(chapter)
            
            return chapters
            
        except Exception as e:
            st.error(f"获取章节失败: {str(e)}")
            return []
    
    def get_chapter_content(self, chapter_url: str, source: str) -> str:
        """获取章节内容"""
        try:
            response = requests.get(chapter_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content_elem = soup.select_one(self.sources[source]["content_selector"])
            if content_elem:
                # 清理内容
                content = content_elem.get_text()
                content = re.sub(r'\s+', '\n', content)
                content = re.sub(r'[　]+', '', content)
                content = re.sub(r'请收藏本站：https://www.*', '', content)
                content = re.sub(r'笔趣阁.*', '', content)
                
                # 分割段落
                paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
                return '\n\n'.join(paragraphs)
            
            return "无法获取章节内容"
            
        except Exception as e:
            return f"获取内容失败: {str(e)}"

def main():
    # 初始化阅读器
    if 'reader' not in st.session_state:
        st.session_state.reader = NovelReader()
    
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
    
    # 标题
    st.title("📚 手机小说阅读器")
    
    # 侧边栏设置
    with st.sidebar:
        st.header("阅读设置")
        
        # 夜间模式切换
        night_mode = st.toggle("夜间模式", value=st.session_state.night_mode)
        if night_mode != st.session_state.night_mode:
            st.session_state.night_mode = night_mode
            st.rerun()
        
        # 字体大小调整
        font_size = st.slider("字体大小", 14, 24, st.session_state.font_size)
        if font_size != st.session_state.font_size:
            st.session_state.font_size = font_size
        
        st.markdown("---")
        st.markdown("### 当前阅读")
        if st.session_state.current_novel:
            st.write(f"**{st.session_state.current_novel['title']}**")
            st.write(f"作者: {st.session_state.current_novel['author']}")
            
            # 章节跳转
            if st.session_state.chapters:
                chapter_titles = [f"{i+1}. {chap['title']}" for i, chap in enumerate(st.session_state.chapters)]
                selected = st.selectbox(
                    "选择章节",
                    options=range(len(chapter_titles)),
                    format_func=lambda x: chapter_titles[x],
                    index=st.session_state.current_chapter_index
                )
                if selected != st.session_state.current_chapter_index:
                    st.session_state.current_chapter_index = selected
    
    # 主界面
    tab1, tab2 = st.tabs(["🔍 搜索小说", "📖 继续阅读"])
    
    with tab1:
        # 搜索区域
        col1, col2 = st.columns([3, 1])
        with col1:
            search_keyword = st.text_input("搜索小说", placeholder="输入小说名或作者")
        with col2:
            source = st.selectbox("书源", list(st.session_state.reader.sources.keys()))
        
        if search_keyword:
            if st.button("搜索", type="primary", use_container_width=True):
                with st.spinner("搜索中..."):
                    novels = st.session_state.reader.search_novels(search_keyword, source)
                    
                    if novels:
                        st.success(f"找到 {len(novels)} 本小说")
                        
                        # 显示搜索结果
                        for i, novel in enumerate(novels):
                            with st.container():
                                cols = st.columns([4, 1])
                                with cols[0]:
                                    st.write(f"**{novel['title']}**")
                                    st.write(f"作者: {novel['author']}")
                                    st.write(f"来源: {novel['source']}")
                                with cols[1]:
                                    if st.button("阅读", key=f"read_{i}"):
                                        # 保存当前小说信息
                                        st.session_state.current_novel = novel
                                        # 获取章节
                                        with st.spinner("加载章节中..."):
                                            chapters = st.session_state.reader.get_chapters(novel['url'], novel['source'])
                                            if chapters:
                                                st.session_state.chapters = chapters
                                                st.session_state.current_chapter_index = 0
                                                st.success("加载成功！切换到阅读标签")
                                                st.rerun()
                                            else:
                                                st.error("无法获取章节列表")
                                
                                st.divider()
                    else:
                        st.warning("未找到相关小说")
    
    with tab2:
        if st.session_state.current_novel and st.session_state.chapters:
            # 显示当前阅读的小说信息
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.subheader(st.session_state.current_novel['title'])
                st.caption(f"作者: {st.session_state.current_novel['author']} | 来源: {st.session_state.current_novel['source']}")
            
            # 导航按钮
            with col2:
                if st.button("上一章", use_container_width=True):
                    if st.session_state.current_chapter_index > 0:
                        st.session_state.current_chapter_index -= 1
                        st.rerun()
            
            with col3:
                if st.button("下一章", use_container_width=True):
                    if st.session_state.current_chapter_index < len(st.session_state.chapters) - 1:
                        st.session_state.current_chapter_index += 1
                        st.rerun()
            
            st.divider()
            
            # 显示章节标题
            current_chapter = st.session_state.chapters[st.session_state.current_chapter_index]
            st.markdown(f"### {current_chapter['title']}")
            
            # 显示内容
            with st.spinner("加载内容中..."):
                content = st.session_state.reader.get_chapter_content(
                    current_chapter['url'],
                    st.session_state.current_novel['source']
                )
                
                # 应用样式
                content_style = f"""
                <div class="novel-content" style="
                    font-size: {st.session_state.font_size}px;
                    {'background-color: #1a1a1a; color: #e0e0e0;' if st.session_state.night_mode else ''}
                ">
                    {content.replace('\n', '<br>')}
                </div>
                """
                st.markdown(content_style, unsafe_allow_html=True)
            
            # 底部导航
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("⏮️ 第一章", use_container_width=True):
                    st.session_state.current_chapter_index = 0
                    st.rerun()
            with col2:
                if st.button("◀️ 上一章", use_container_width=True):
                    if st.session_state.current_chapter_index > 0:
                        st.session_state.current_chapter_index -= 1
                        st.rerun()
            with col3:
                if st.button("▶️ 下一章", use_container_width=True):
                    if st.session_state.current_chapter_index < len(st.session_state.chapters) - 1:
                        st.session_state.current_chapter_index += 1
                        st.rerun()
            with col4:
                if st.button("⏭️ 最后一章", use_container_width=True):
                    st.session_state.current_chapter_index = len(st.session_state.chapters) - 1
                    st.rerun()
            
            # 显示进度
            progress = (st.session_state.current_chapter_index + 1) / len(st.session_state.chapters)
            st.progress(progress)
            st.caption(f"第 {st.session_state.current_chapter_index + 1} 章 / 共 {len(st.session_state.chapters)} 章")
        
        else:
            st.info("📖 还没有开始阅读小说")
            st.write("请在搜索标签中搜索并选择一本小说开始阅读")
            
            # 显示历史记录（如果有）
            if 'reading_history' in st.session_state:
                st.subheader("最近阅读")
                for novel in st.session_state.reading_history[:5]:
                    if st.button(f"{novel['title']} - {novel['author']}"):
                        st.session_state.current_novel = novel
                        st.rerun()

    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 12px;'>
        说明：本应用仅供学习交流使用，请支持正版阅读
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()