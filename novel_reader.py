import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import warnings

# 禁用SSL警告
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="手机小说阅读器",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 优化CSS
st.markdown("""
<style>
    .main > div {
        padding: 1rem;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

class SimpleNovelReader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def search_biquge(self, keyword):
        """使用笔趣阁搜索（无SSL问题）"""
        try:
            url = f"https://www.biquge7.com/search?q={urllib.parse.quote(keyword)}"
            response = requests.get(url, headers=self.headers, timeout=10, verify=False)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            novels = []
            items = soup.select('.bookinfo')
            
            for item in items[:10]:  # 只取前10个结果
                title_elem = item.select_one('h4 a')
                author_elem = item.select_one('.author')
                
                if title_elem:
                    novel = {
                        'title': title_elem.text.strip(),
                        'author': author_elem.text.replace('作者：', '').strip() if author_elem else '未知',
                        'url': 'https://www.biquge7.com' + title_elem['href'],
                        'source': '笔趣阁'
                    }
                    novels.append(novel)
            
            return novels
        except Exception as e:
            st.error(f"搜索失败: {str(e)}")
            return []
    
    def get_chapters_biquge(self, url):
        """获取笔趣阁章节列表"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10, verify=False)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            chapters = []
            chapter_elems = soup.select('.listmain dd a')
            
            for elem in chapter_elems[:50]:  # 只取前50章
                if elem.get('href'):
                    chapter = {
                        'title': elem.text.strip(),
                        'url': 'https://www.biquge7.com' + elem['href'] if elem['href'].startswith('/') else elem['href']
                    }
                    chapters.append(chapter)
            
            return chapters
        except Exception as e:
            st.error(f"获取章节失败: {str(e)}")
            return []
    
    def get_content_biquge(self, url):
        """获取笔趣阁内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10, verify=False)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content_elem = soup.select_one('#chaptercontent')
            if content_elem:
                content = content_elem.get_text()
                # 清理内容
                content = re.sub(r'\s+', '\n', content)
                content = re.sub(r'请收藏.*', '', content)
                content = re.sub(r'笔趣阁.*', '', content)
                return content
            return "无法获取内容"
        except Exception as e:
            return f"获取内容失败: {str(e)}"

def main():
    if 'reader' not in st.session_state:
        st.session_state.reader = SimpleNovelReader()
    
    if 'current_novel' not in st.session_state:
        st.session_state.current_novel = None
    
    if 'chapters' not in st.session_state:
        st.session_state.chapters = []
    
    if 'current_chapter' not in st.session_state:
        st.session_state.current_chapter = 0
    
    st.title("📱 手机小说阅读器")
    
    # 搜索界面
    keyword = st.text_input("搜索小说", placeholder="输入小说名称")
    
    if keyword:
        if st.button("搜索", type="primary"):
            with st.spinner("搜索中..."):
                novels = st.session_state.reader.search_biquge(keyword)
                
                if novels:
                    st.success(f"找到 {len(novels)} 本小说")
                    
                    for novel in novels:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{novel['title']}**")
                            st.write(f"作者: {novel['author']}")
                        with col2:
                            if st.button("阅读", key=f"read_{novel['title']}"):
                                st.session_state.current_novel = novel
                                chapters = st.session_state.reader.get_chapters_biquge(novel['url'])
                                if chapters:
                                    st.session_state.chapters = chapters
                                    st.session_state.current_chapter = 0
                                    st.rerun()
                                else:
                                    st.error("无法加载章节")
                        st.divider()
                else:
                    st.warning("未找到相关小说")
    
    # 阅读界面
    if st.session_state.current_novel and st.session_state.chapters:
        st.subheader(st.session_state.current_novel['title'])
        
        # 章节导航
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("上一章") and st.session_state.current_chapter > 0:
                st.session_state.current_chapter -= 1
                st.rerun()
        with col2:
            st.write(f"第 {st.session_state.current_chapter + 1} 章")
        with col3:
            if st.button("下一章") and st.session_state.current_chapter < len(st.session_state.chapters) - 1:
                st.session_state.current_chapter += 1
                st.rerun()
        
        # 显示内容
        chapter = st.session_state.chapters[st.session_state.current_chapter]
        st.write(f"### {chapter['title']}")
        
        with st.spinner("加载中..."):
            content = st.session_state.reader.get_content_biquge(chapter['url'])
            st.text_area("内容", content, height=400)
        
        # 章节列表
        with st.expander("章节列表"):
            for i, chap in enumerate(st.session_state.chapters[:30]):
                if st.button(chap['title'], key=f"chap_{i}"):
                    st.session_state.current_chapter = i
                    st.rerun()

if __name__ == "__main__":
    main()
