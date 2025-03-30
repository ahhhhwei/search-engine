# 站内搜索引擎
1. 克隆项目
   ```bash
   git clone https://github.com/ahhhhwei/search-engine.git
   ```

2. python 新建虚拟环境并进入
   ```bash
   cd search-engine
   python3 -m venv search-engine
   source search-engine/bin/activate
   pip install -r Crawler/requirements.txt
   ```

3. 安装 boost 库
   ```bash
   sudo apt install libboost-all-dev
   dpkg -s libboost-dev | grep Version # 检查是否安装成功，我的系统输出 Version: 1.71.0.0ubuntu2
   ```

4. 安装 jsoncpp 库
   ```bash
   sudo apt install libjsoncpp-dev
   ls /usr/include/jsoncpp/json/ # 检查是否安装成功
   ```

5. 安装 jieba 分词库
   在其他地方新建一个目录 third_lib
   ```bash
   cd ~/Desktop 
   mkdir third_lib
   cd third_lib
   git clone https://gitee.com/mohatarem/cppjieba.git
   cd cppjieba
   cp deps/limonp/ include/cppjieba/ -rf
   ```

6. 安装 httplib 库
   ```bash
   git clone https://gitee.com/yuanfeng1897/cpp-httplib.git
   ```

7. 创建软链接
   ```bash
   cd ~/Desktop/search-engine/src/
   ln -s ~/Desktop/third_lib/cppjieba/dict dict
   ln -s ~/Desktop/third_lib/cppjieba/include/cppjieba cppjieba
   ln -s ~/Desktop/third_lib/cpp-httplib cpp-httplib
   ```

8. 爬取网页
   ```bash
   cd ~/Desktop/search-engine/Crawler/
   python3 crawler.py
   ```

9. 数据预处理
   ```bash
   ./parser
   ```

10. 数据预处理
    ```bash
    ./http_server
    ```