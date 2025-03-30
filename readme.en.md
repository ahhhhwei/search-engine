# Site Search Engine

<div align="center">
[简体中文](readme.md) | English
</div>

## Introduction
This is a simple search engine project.

## Environment
Based on C++11, STL, Boost library, Jsoncpp, cppjieba, cpp-httplib, etc.

## Build Instructions
1. Clone the project
    ```bash
    git clone https://github.com/ahhhhwei/search-engine.git
    ```
2. Create and activate a Python virtual environment
    ```bash
    cd search-engine
    python3 -m venv search-engine
    source search-engine/bin/activate
    pip install -r Crawler/requirements.txt
    ```
3. Install the Boost library
    ```bash
    sudo apt install libboost-all-dev
    dpkg -s libboost-dev | grep Version # Check if installed successfully. Example output: Version: 1.71.0.0ubuntu2
    ```
4. Install the Jsoncpp library
    ```bash
    sudo apt install libjsoncpp-dev
    ls /usr/include/jsoncpp/json/ # Check if installed successfully
    ```
5. Install the Jieba tokenizer library
    ```bash
    cd ~/Desktop 
    mkdir third_lib
    cd third_lib
    git clone https://gitee.com/mohatarem/cppjieba.git
    # Copy the directory to avoid make errors
    cd cppjieba
    cp deps/limonp/ include/cppjieba/ -rf
    ```
6. Install the httplib library
    ```bash
    git clone https://gitee.com/yuanfeng1897/cpp-httplib.git
    ```
7. Create symbolic links
    ```bash
    cd ~/Desktop/search-engine/src/
    ln -s ~/Desktop/third_lib/cppjieba/dict dict
    ln -s ~/Desktop/third_lib/cppjieba/include/cppjieba cppjieba
    ln -s ~/Desktop/third_lib/cpp-httplib cpp-httplib
    ```
8. Crawl web pages
    ```bash
    cd ~/Desktop/search-engine/Crawler/
    python3 crawler.py
    ```
9. Preprocess data
    ```bash
    ./parser
    ```
10. Run the server
    ```bash
    ./http_server
    ```