#include <iostream>
#include <vector>
#include <string>
#include <boost/filesystem.hpp>
#include "util.hpp"

const std::string src_path = "../Crawler/ruanyifeng_blog";
const std::string desc_path = "../Crawler/raw.txt";

typedef struct DocInfo
{
    std::string title;
    std::string content;
    std::string url;
} DocInfo_t;

bool EnumFile(const std::string &src_path, std::vector<std::string> *files_list);
bool ParseHtml(const std::vector<std::string> &files_list, std::vector<DocInfo_t> *results);
bool SaveHtml(const std::vector<DocInfo_t> &results, const std::string &desc_path);

int main()
{
    // 1. 解析网页名称
    std::vector<std::string> files_lists;
    if (!EnumFile(src_path, &files_lists))
    {
        std::cerr << "解析网页文件名称失败！" << std::endl;
        return 1;
    }

    // 2. 从 files_list 读取每个文件的内容，并对其内容进行解析
    std::vector<DocInfo_t> results;
    if (!ParseHtml(files_lists, &results))
    {
        std::cerr << "解析 Html 失败！" << std::endl;
        return 2;
    }

    // 3. 解析后的文件内容，写入 desc_path
    if (!SaveHtml(results, desc_path))
    {
        std::cerr << "保存文件失败！" << std::endl;
        return 3;
    }
    return 0;
}

bool EnumFile(const std::string &src_path, std::vector<std::string> *files_list)
{
    boost::filesystem::path root_path(src_path);

    if (!boost::filesystem::exists(root_path))
    {
        std::cerr << "文件" << src_path << " 不存在！" << std::endl;
        return false;
    }

    // 定义一个空的迭代器，用来进行判断递归结束
    boost::filesystem::recursive_directory_iterator end;
    for (boost::filesystem::recursive_directory_iterator iter(root_path); iter != end; iter++)
    {
        // 判断文件是否是普通文件，html都是普通文件
        if (!boost::filesystem::is_regular_file(*iter))
        {
            continue;
        }
        if (iter->path().extension() != ".html")
        { // 判断文件路径名的后缀是否符合要求
            continue;
        }
        std::cout << "debug: " << iter->path().string() << std::endl;
        // 当前的路径一定是一个合法的，以.html结束的普通网页文件
        files_list->push_back(iter->path().string()); // 将所有带路径的html保存在files_list,方便后续进行文本分析
    }

    return true;
}

static bool ParseTitle(const std::string &file, std::string *title)
{
    std::size_t begin = file.find("<title>");
    if (begin == std::string::npos)
    {
        return false;
    }
    std::size_t end = file.find("</title>");
    if (end == std::string::npos)
    {
        return false;
    }

    begin += std::string("<title>").size();

    if (begin > end)
    {
        return false;
    }
    *title = file.substr(begin, end - begin);
    return true;
}

static bool ParseContent(const std::string &file, std::string *content)
{
    enum status
    {
        LABLE,
        CONTENT,
        SCRIPT,
        STYLE,
        COMMENT
    };

    enum status s = LABLE;
    std::string tag;
    bool lastWasSpace = true; // 避免多余空格

    for (size_t i = 0; i < file.size(); i++)
    {
        char c = file[i];

        switch (s)
        {
        case LABLE:
            if (c == '>')
            {
                // 转换为小写并去除属性部分
                std::string cleanTag;
                for (char tc : tag) {
                    if (isspace(tc)) break; // 遇到空格停止，忽略属性
                    cleanTag.push_back(tolower(tc));
                }
                
                if (cleanTag == "script")
                    s = SCRIPT;
                else if (cleanTag == "style")
                    s = STYLE;
                else
                {
                    s = CONTENT;
                    if (!content->empty() && !lastWasSpace)
                    {
                        content->push_back(' '); // 标签切换时插入空格
                        lastWasSpace = true;
                    }
                }
                tag.clear();
            }
            else if (c == '<')
            {
                tag.clear();
                // 处理 HTML 注释 <!--
                if (file.substr(i, 4) == "<!--")
                {
                    s = COMMENT;
                    i += 3; // 跳过 <!--
                }
            }
            else
            {
                tag.push_back(c); // 不再转换为小写，后面统一处理
            }
            break;

        case SCRIPT:
            if (c == '<' && file.substr(i, 9) == "</script>")
            {
                s = LABLE;
                i += 8;
            }
            break;

        case STYLE:
            if (c == '<' && file.substr(i, 8) == "</style>")
            {
                s = LABLE;
                i += 7;
            }
            break;

        case COMMENT:
            if (c == '-' && file.substr(i, 3) == "-->")
            {
                s = LABLE;
                i += 2; // 跳过 -->
            }
            break;

        case CONTENT:
            if (c == '<')
            {
                s = LABLE;
                tag.clear();
            }
            else
            {
                if (c == '\n' || c == '\t')
                    c = ' ';

                if (c == ' ' && lastWasSpace)
                    continue; // 避免多个空格

                content->push_back(c);
                lastWasSpace = (c == ' '); // 更新空格状态
            }
            break;

        default:
            break;
        }
    }

    return true;
}

static bool ParseUrl(const std::string &file_path, std::string *url)
{
    std::string url_head = "https://www.ruanyifeng.com/blog";
    std::string url_tail = file_path.substr(src_path.size());

    *url = url_head + url_tail;
    return true;
}

bool ParseHtml(const std::vector<std::string> &files_list, std::vector<DocInfo_t> *results)
{
    for (const std::string &file : files_list)
    {
        // 1. 读取文件
        std::string result;
        if (!ns_util::FileUtil::ReadFile(file, &result))
        {
            continue;
        }
        // 2. 解析文件
        DocInfo_t doc;
        if (!ParseTitle(result, &doc.title))
        {
            continue;
        }
        if (!ParseContent(result, &doc.content))
        {
            continue;
        }
        if (!ParseUrl(file, &doc.url))
        {
            continue;
        }

        // 3. 保存至 results
        results->push_back(std::move(doc));
    }
    return true;
}

bool SaveHtml(const std::vector<DocInfo_t> &results, const std::string &output)
{
#define SEP '\3'
    // 按照二进制方式进行写入
    std::ofstream out(output, std::ios::out | std::ios::binary);
    if (!out.is_open())
    {
        std::cerr << "open " << output << " failed!" << std::endl;
        return false;
    }

    // 就可以进行文件内容的写入了
    for (auto &item : results)
    {
        std::string out_string;
        out_string = item.title;
        out_string += SEP;
        out_string += item.content;
        out_string += SEP;
        out_string += item.url;
        out_string += '\n';

        out.write(out_string.c_str(), out_string.size());
    }

    out.close();

    return true;
}