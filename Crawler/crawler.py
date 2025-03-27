import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

class RuanYiFengCrawler:
    def __init__(self, base_url="https://www.ruanyifeng.com/blog"):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited = set()
        self.to_visit = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.output_dir = "ruanyifeng_blog"
        
    def sanitize_filename(self, filename):
        """清理文件名中的非法字符"""
        return re.sub(r'[\\/*?:"<>|]', "_", filename).strip()
    
    def create_output_dir(self):
        """创建输出目录"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def save_html(self, url, html):
        """保存HTML到文件"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        # 如果是文章页，按日期和标题组织文件名
        if len(path_parts) >= 3 and path_parts[0] == 'blog' and path_parts[1] == 'archives':
            # 尝试从HTML中提取标题
            soup = BeautifulSoup(html, 'html.parser')
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else path_parts[-1]
            title = self.sanitize_filename(title)
            
            # 尝试从URL中提取日期
            date_str = path_parts[2] if len(path_parts) > 2 else "unknown_date"
            try:
                datetime.strptime(date_str, "%Y/%m")
                filename = f"{date_str.replace('/', '-')}_{title}.html"
            except ValueError:
                filename = f"{title}.html"
        else:
            # 其他页面按路径保存
            filename = "_".join(path_parts) + ".html" if path_parts else "index.html"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # 处理重复文件名
        counter = 1
        while os.path.exists(filepath):
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(self.output_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Saved: {filepath}")
    
    def get_links(self, url, html):
        """从HTML中提取所有内部链接"""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        
        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(url, link['href'])
            parsed = urlparse(absolute_url)
            
            # 只处理同域名下的链接
            if parsed.netloc == self.domain:
                # 标准化URL（去除查询参数和片段）
                clean_url = parsed._replace(query="", fragment="").geturl()
                if clean_url not in self.visited:
                    links.add(clean_url)
        
        return links
    
    def fetch_page(self, url):
        """获取页面内容"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 检查内容类型是否为HTML
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                print(f"Skipping non-HTML content: {url}")
                return None
            
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def crawl(self, max_pages=float('inf')):
        """开始爬取"""
        self.create_output_dir()
        self.to_visit.add(self.base_url)
        pages_crawled = 0
        
        while self.to_visit and pages_crawled < max_pages:
            url = self.to_visit.pop()
            
            if url in self.visited:
                continue
                
            html = self.fetch_page(url)
            if not html:
                continue
                
            # 保存HTML
            self.save_html(url, html)
            
            # 提取新链接
            new_links = self.get_links(url, html)
            self.to_visit.update(new_links)
            
            self.visited.add(url)
            pages_crawled += 1
            
            # 礼貌性延迟
            time.sleep(1)
        
        print(f"Crawling completed. Total pages crawled: {pages_crawled}")

if __name__ == "__main__":
    crawler = RuanYiFengCrawler()
    crawler.crawl()  # 爬取所有页面
    # 如果只想爬取部分内容，可以设置max_pages参数
    # crawler.crawl(max_pages=50)