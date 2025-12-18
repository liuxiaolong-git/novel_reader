import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import warnings
import random
import time

# 禁用SSL警告
warnings.filterwarnings('ignore')

# 设置页面
st.set_page_config(
    page_title="手机小说阅读器",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 简洁的CSS
st.markdown("""
<style>
    .main {
        padding: 10px;
    }
    
    .novel-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background: #f9f9f9;
    }
    
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 10px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        margin: 5px 0;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

class NovelReader:
    def __init__(self):
        # 使用多个User-Agent轮换
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }
    
    def search_novels(self, keyword):
        """搜索小说 - 使用多个数据源"""
        all_novels = []
        
        # 尝试多个数据源
        sources = [
            self._search_source1,
            self._search_source2,
            self._search_source3
        ]
        
        for source_func in sources:
            try:
                novels = source_func(keyword)
                if novels:
                    all_novels.extend(novels)
                    break  # 只要有一个源成功就返回
            except:
                continue
        
        return all_novels[:10]  # 只返回前10个结果
    
    def _search_source1(self, keyword):
        """数据源1：笔趣阁（当前最稳定的源）"""
        try:
            # 使用最稳定的笔趣阁域名
            url = "http://www.b520.cc/modules/article/search.php"
            params = {
                'searchkey': keyword.encode('gbk'),
                'submit': ''
            }
            
            headers = self.get_headers()
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            response = requests.post(
                url, 
                data=params,
                headers=headers, 
                timeout=8,
                verify=False
            )
            
            # 尝试多种编码
            encodings = ['gbk', 'gb2312', 'utf-8', 'gb18030']
            for encoding in encodings:
                try:
                    response.encoding = encoding
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    novels = []
                    # 解析搜索结果表格
                    rows = soup.select('table.grid tr')[1:]  # 跳过表头
                    
                    for row in rows[:10]:  # 只取前10个结果
                        cells = row.select('td')
                        if len(cells) >= 3:
                            title_elem = cells[0].select_one('a')
                            author_elem = cells[2]
                            
                            if title_elem:
                                novels.append({
                                    'title': title_elem.text.strip(),
                                    'author': author_elem.text.strip(),
                                    'url': title_elem['href'],
                                    'source': '笔趣阁1'
                                })
                    
                    if novels:
                        return novels
                except:
                    continue
                    
        except Exception as e:
            print(f"源1搜索失败: {str(e)[:50]}")
        
        return []
    
    def _search_source2(self, keyword):
        """数据源2：另一个笔趣阁"""
        try:
            # 使用不同的笔趣阁域名
            url = f"https://www.xbiquge.la/modules/article/waps.php?searchkey={urllib.parse.quote(keyword)}"
            
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=8,
                verify=False
            )
            
            # 尝试GBK编码
            response.encoding = 'gbk'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            novels = []
            # 解析表格
            rows = soup.select('table.grid tr')[1:]  # 跳过表头
            
            for row in rows[:10]:
                cells = row.select('td')
                if len(cells) >= 3:
                    title_elem = cells[0].select_one('a')
                    author_elem = cells[2]
                    
                    if title_elem:
                        novels.append({
                            'title': title_elem.text.strip(),
                            'author': author_elem.text.strip(),
                            'url': title_elem['href'],
                            'source': '笔趣阁2'
                        })
            
            return novels
            
        except Exception as e:
            print(f"源2搜索失败: {str(e)[:50]}")
            return []
    
    def _search_source3(self, keyword):
        """数据源3：备用源"""
        try:
            # 使用另一个备用源
            url = f"https://www.bqg789.com/s?q={urllib.parse.quote(keyword)}"
            
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=8,
                verify=False
            )
            
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            novels = []
            items = soup.select('.book-item, .book-info')
            
            for item in items[:10]:
                title_elem = item.select_one('h4 a, h3 a, .title a')
                if title_elem:
                    author_elem = item.select_one('.author, .info, span')
                    novels.append({
                        'title': title_elem.text.strip(),
                        'author': author_elem.text.strip() if author_elem else '未知',
                        'url': title_elem['href'],
                        'source': '备用源'
                    })
            
            return novels
            
        except Exception as e:
            print(f"源3搜索失败: {str(e)[:50]}")
            return []
    
    def get_chapters(self, url):
        """获取章节列表"""
        try:
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=10,
                verify=False
            )
            
            # 尝试多种编码
            for encoding in ['gbk', 'utf-8', 'gb2312']:
                try:
                    response.encoding = encoding
                    break
                except:
                    continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种章节选择器
            chapter_selectors = [
                '#list dd a',
                '.listmain dd a',
                '#chapterlist li a',
                '.chapterlist dd a',
                '.zjlist dd a'
            ]
            
            for selector in chapter_selectors:
                chapter_elements = soup.select(selector)
                if chapter_elements:
                    chapters = []
                    base_url = '/'.join(url.split('/')[:3])  # 获取基础URL
                    
                    for elem in chapter_elements[:100]:  # 限制前100章
                        if elem.get('href'):
                            chapter_url = elem['href']
                            if not chapter_url.startswith('http'):
                                if chapter_url.startswith('/'):
                                    chapter_url = base_url + chapter_url
                                else:
                                    chapter_url = url.rsplit('/', 1)[0] + '/' + chapter_url
                            
                            chapters.append({
                                'title': elem.text.strip(),
                                'url': chapter_url
                            })
                    
                    return chapters
            
            return []
            
        except Exception as e:
            st.error(f"获取章节失败: {str(e)[:100]}")
            return []
    
    def get_chapter_content(self, url):
        """获取章节内容"""
        try:
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=10,
                verify=False
            )
            
            # 尝试多种编码
            for encoding in ['gbk', 'utf-8', 'gb2312']:
                try:
                    response.encoding = encoding
                    break
                except:
                    continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种内容选择器
            content_selectors = [
                '#content',
                '.content',
                '#htmlContent',
                '#chaptercontent',
                '.chapter-content',
                '.read-content',
                '.novel-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 清理内容
                    content = content_elem.get_text()
                    
                    # 移除广告和无关内容
                    patterns = [
                        r'请收藏.*',
                        r'笔趣阁.*',
                        r'www\..*\.com',
                        r'https?://.*',
                        r'记住.*网址.*',
                        r'章节错误.*',
                        r'正在手打中.*',
                        r'本站.*',
                        r'请支持正版.*'
                    ]
                    
                    for pattern in patterns:
                        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
                    
                    # 处理空白字符
                    content = re.sub(r'\s+', '\n', content)
                    content = re.sub(r'\n{3,}', '\n\n', content)
                    content = content.strip()
                    
                    if content:
                        return content
            
            return "无法获取内容，可能是网站结构变化"
            
        except Exception as e:
            return f"获取内容失败: {str(e)[:100]}"

def main():
    # 初始化会话状态
    if 'reader' not in st.session_state:
        st.session_state.reader = NovelReader()
    
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    if 'current_novel' not in st.session_state:
        st.session_state.current_novel = None
    
    if 'chapters' not in st.session_state:
        st.session_state.chapters = []
    
    if 'current_chapter_index' not in st.session_state:
        st.session_state.current_chapter_index = 0
    
    # 主界面
    st.title("📱 手机小说阅读器")
    
    # 搜索部分
    st.header("搜索小说")
    
    # 搜索框
    search_input = st.text_input("输入小说名称或作者", placeholder="例如：斗罗大陆")
    
    # 热门搜索建议
    st.write("热门搜索：")
    hot_search = ["斗罗大陆", "斗破苍穹", "凡人修仙传", "完美世界", "大奉打更人", "诡秘之主"]
    cols = st.columns(3)
    for i, keyword in enumerate(hot_search):
        with cols[i % 3]:
            if st.button(keyword, key=f"hot_{i}"):
                search_input = keyword
    
    # 搜索按钮
    if st.button("搜索", type="primary"):
        if search_input:
            with st.spinner(f"正在搜索 '{search_input}'..."):
                # 设置超时保护
                try:
                    results = st.session_state.reader.search_novels(search_input)
                    st.session_state.search_results = results
                    
                    if results:
                        st.success(f"找到 {len(results)} 个结果")
                    else:
                        st.warning("没有找到相关小说，请尝试：")
                        st.info("""
                        1. 检查关键词是否正确
                        2. 尝试其他热门小说
                        3. 网络连接可能有问题
                        """)
                except Exception as e:
                    st.error(f"搜索出错: {str(e)[:100]}")
        else:
            st.warning("请输入搜索关键词")
    
    # 显示搜索结果
    if st.session_state.search_results:
        st.header("搜索结果")
        
        for i, novel in enumerate(st.session_state.search_results):
            with st.container():
                st.markdown(f"""
                <div class="novel-card">
                    <h4>{novel['title']}</h4>
                    <p>作者: {novel['author']}</p>
                    <p>来源: {novel['source']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 阅读按钮
                if st.button("开始阅读", key=f"read_{i}"):
                    st.session_state.current_novel = novel
                    
                    with st.spinner("正在加载章节..."):
                        chapters = st.session_state.reader.get_chapters(novel['url'])
                        if chapters:
                            st.session_state.chapters = chapters
                            st.session_state.current_chapter_index = 0
                            st.success(f"成功加载 {len(chapters)} 个章节")
                        else:
                            st.error("无法加载章节列表")
                
                st.divider()
    
    # 阅读部分
    if st.session_state.current_novel and st.session_state.chapters:
        st.header("阅读界面")
        
        # 小说信息
        novel = st.session_state.current_novel
        st.subheader(novel['title'])
        st.caption(f"作者: {novel['author']} | 来源: {novel['source']}")
        
        # 章节导航
        if st.session_state.chapters:
            current_chapter = st.session_state.chapters[st.session_state.current_chapter_index]
            
            # 导航按钮
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("首页", disabled=st.session_state.current_chapter_index == 0):
                    st.session_state.current_chapter_index = 0
            
            with col2:
                if st.button("上一章", disabled=st.session_state.current_chapter_index == 0):
                    st.session_state.current_chapter_index -= 1
            
            with col3:
                if st.button("下一章", disabled=st.session_state.current_chapter_index >= len(st.session_state.chapters) - 1):
                    st.session_state.current_chapter_index += 1
            
            with col4:
                if st.button("末页", disabled=st.session_state.current_chapter_index >= len(st.session_state.chapters) - 1):
                    st.session_state.current_chapter_index = len(st.session_state.chapters) - 1
            
            # 章节标题
            st.markdown(f"### {current_chapter['title']}")
            
            # 加载内容
            with st.spinner("正在加载内容..."):
                content = st.session_state.reader.get_chapter_content(current_chapter['url'])
                
                # 显示内容
                st.text_area(
                    "内容",
                    content,
                    height=400,
                    key=f"content_{st.session_state.current_chapter_index}"
                )
            
            # 进度显示
            progress = (st.session_state.current_chapter_index + 1) / len(st.session_state.chapters)
            st.progress(progress)
            st.caption(f"第 {st.session_state.current_chapter_index + 1} 章 / 共 {len(st.session_state.chapters)} 章")
            
            # 章节选择
            chapter_titles = [
                f"{i+1}. {chap['title'][:30]}..." 
                for i, chap in enumerate(st.session_state.chapters[:50])
            ]
            
            selected = st.selectbox(
                "快速跳转",
                range(len(st.session_state.chapters[:50])),
                format_func=lambda x: chapter_titles[x] if x < len(chapter_titles) else f"第{x+1}章",
                index=st.session_state.current_chapter_index
            )
            
            if selected != st.session_state.current_chapter_index:
                st.session_state.current_chapter_index = selected
    
    # 页脚
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 12px;'>
        手机小说阅读器 | 仅供学习交流使用
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
