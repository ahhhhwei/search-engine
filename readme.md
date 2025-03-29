# 站内搜索引擎

1. python 新建虚拟环境并进入
2. 进入 Crawler/ 目录下，运行 crawler.py 文件
3. 安装 boost 开发库
   
   ```bash
   yum install -y boost-devel
   ```
4. 安装 jsoncpp 库
   ```bash
   yum -y install epel-release
   yum install jsoncpp.x86_64
   yum install jsoncpp-doc.noarch
   yum install jsoncpp-devel.x86_64
   ```
5. 安装 jieba 分词库
   ```bash
   git clone https://gitee.com/mohatarem/cppjieba.git

   ```

6. 安装 httplib 库
   选择 0.7.15 版本下载并上传至虚拟机，然后解压缩

7. 创建软链接
   ```bash
   ln -s ~/Desktop/third_lib/cppjieba/dict dict
   ln -s ~/Desktop/third_lib/cppjieba/include/cppjieba cppjieba
   ln -s ~/Desktop/third_lib/cpp-httplib-v0.7.15 cpp-httplib
   ```