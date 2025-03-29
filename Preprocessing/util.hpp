#pragma once

#include <iostream>
#include <vector>
#include <string>
#include <fstream>

namespace ns_util{
    class FileUtil{
        public:
            static bool ReadFile(const std::string &file_path, std::string *out)
            {
                std::ifstream in(file_path, std::ios::in);
                if(!in.is_open()){
                    std::cerr << "open file " << file_path << " error" << std::endl;
                    return false;
                }

                std::string line;
                while(std::getline(in, line)){ //如何理解getline读取到文件结束呢？？getline的返回值是一个&，while(bool), 本质是因为重载了强制类型转化
                    *out += line;
                }

                in.close();
                return true;
            }
    };

}