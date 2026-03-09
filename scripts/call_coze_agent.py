#!/usr/bin/env python3
"""
调用Coze智能体的脚本
用于收集testcase目录下模块的apis.yaml和path_scope_mapping.yaml文件信息
并传递给Coze智能体进行处理
"""
import os
import json
import requests
import argparse

def get_testcase_modules(testcase_dir):
    """获取testcase目录下的模块名称（排除_config）"""
    modules = set()
    for root, dirs, files in os.walk(testcase_dir):
        # 排除_config目录
        dirs[:] = [d for d in dirs if d != '_config']
        # 获取模块名称
        for dir_name in dirs:
            modules.add(dir_name)
    return sorted(modules)

def collect_module_info(testcase_dir, modules):
    """收集模块的apis.yaml和path_scope_mapping.yaml文件信息"""
    module_info = []
    for module in modules:
        module_path = os.path.join(testcase_dir, module)
        config_path = os.path.join(module_path, '_config')
        
        # 检查apis.yaml和path_scope_mapping.yaml是否存在
        apis_file = os.path.join(config_path, 'apis.yaml')
        mapping_file = os.path.join(config_path, 'path_scope_mapping.yaml')
        
        if os.path.exists(apis_file) and os.path.exists(mapping_file):
            # 读取文件内容
            with open(apis_file, 'r', encoding='utf-8') as f:
                apis_content = f.read()
            
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping_content = f.read()
            
            # 添加模块信息
            module_info.append({
                'module': module,
                'apis_path': apis_file,
                'apis_content': apis_content,
                'mapping_path': mapping_file,
                'mapping_content': mapping_content
            })
    return module_info

def build_prompt(module_info):
    """构建传递给Coze智能体的提示"""
    prompt = ""
    for info in module_info:
        prompt += f"模块: {info['module']}\n"
        prompt += f"apis.yaml路径: {info['apis_path']}\n"
        prompt += f"apis.yaml内容:\n{info['apis_content']}\n\n"
        prompt += f"path_scope_mapping.yaml路径: {info['mapping_path']}\n"
        prompt += f"path_scope_mapping.yaml内容:\n{info['mapping_content']}\n\n"
    return prompt

def call_coze_agent(token, prompt):
    """调用Coze智能体"""
    url = "https://956xc237sr.coze.site/stream_run"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "content": {
            "query": {
                "prompt": [
                    {
                        "type": "text",
                        "content": {
                            "text": prompt
                        }
                    }
                ]
            }
        },
        "type": "query",
        "session_id": "TUnB_7Bu7_h6zBgi_ntgJ",
        "project_id": 7614077849934413843
    }
    
    print("Calling Coze agent with testcase modules information...")
    response = requests.post(url, headers=headers, json=data)
    
    print("Coze agent response:")
    print(response.text)
    
    return response

def main():
    parser = argparse.ArgumentParser(description='调用Coze智能体处理testcase模块信息')
    parser.add_argument('--testcase-dir', default='testcase', help='testcase目录路径')
    parser.add_argument('--token', required=True, help='Coze API令牌')
    
    args = parser.parse_args()
    
    # 获取模块名称
    modules = get_testcase_modules(args.testcase_dir)
    print(f"Found modules: {modules}")
    
    # 收集模块信息
    module_info = collect_module_info(args.testcase_dir, modules)
    print(f"Collected info for {len(module_info)} modules")
    
    # 构建提示
    prompt = build_prompt(module_info)
    
    # 调用Coze智能体
    call_coze_agent(args.token, prompt)

if __name__ == '__main__':
    main()
