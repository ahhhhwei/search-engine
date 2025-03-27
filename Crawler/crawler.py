import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import urllib3

# 禁用SSL警告（可选）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RuanYiFengCrawler:
    def __init__(self, base_url="https://www.ruanyifeng.com/blog"):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited = set()
        self.to_visit = set([base_url])
        self.session = requests.Session()
        
        # 更新请求头配置
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Connection': 'keep-alive'
        })
        
        # SSL相关配置
        self.session.verify = False  # 禁用SSL验证（简单方案）
        # 或者使用以下配置（需要安装certifi）：
        # import certifi
        # self.session.verify = certifi.where()
        
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
            soup = BeautifulSoup(html, 'html.parser')
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else path_parts[-1]
            title = self.sanitize_filename(title)
            
            date_str = path_parts[2] if len(path_parts) > 2 else "unknown_date"
            try:
                datetime.strptime(date_str, "%Y/%m")
                filename = f"{date_str.replace('/', '-')}_{title}.html"
            except ValueError:
                filename = f"{title}.html"
        else:
            filename = "_".join(path_parts) + ".html" if path_parts else "index.html"
        
        filepath = os.path.join(self.output_dir, filename)
        
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
            
            if parsed.netloc == self.domain:
                clean_url = parsed._replace(query="", fragment="").geturl()
                if clean_url not in self.visited:
                    links.add(clean_url)
        
        return links
    
    def fetch_page(self, url):
        """获取页面内容（修复SSL问题）"""
        try:
            print(f"Fetching: {url}")
            # 增加超时时间和重试机制
            response = self.session.get(
                url,
                timeout=(10, 30),  # 连接超时10秒，读取超时30秒
                allow_redirects=True,
                verify=False  # 禁用SSL验证
            )
            response.raise_for_status()
            
            # 确保使用UTF-8编码
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding or 'utf-8'
            response.encoding = 'utf-8'
            
            return response.text
        except requests.exceptions.SSLError:
            # SSL错误时重试一次
            try:
                print(f"Retrying {url} due to SSL error")
                response = self.session.get(url, timeout=(10, 30), verify=False)
                response.encoding = 'utf-8'
                return response.text
            except Exception as e:
                print(f"Error fetching {url} after retry: {e}")
                return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def crawl(self, max_pages=float('inf')):
        """开始爬取"""
        self.create_output_dir()
        pages_crawled = 0
        
        while self.to_visit and pages_crawled < max_pages:
            url = self.to_visit.pop()
            
            if url in self.visited:
                continue
                
            html = self.fetch_page(url)
            if not html:
                continue
                
            self.save_html(url, html)
            new_links = self.get_links(url, html)
            self.to_visit.update(new_links)
            
            self.visited.add(url)
            pages_crawled += 1
            
            # 增加随机延迟（1-3秒）
            time.sleep(1 + 2 * random.random())
        
        print(f"Crawling completed. Total pages crawled: {pages_crawled}")

if __name__ == "__main__":
    import random
    crawler = RuanYiFengCrawler()
    crawler.crawl()