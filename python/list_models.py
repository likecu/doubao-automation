#!/Users/aaa/python-sdk/python3.13.2/bin/python
# -*- coding: utf-8 -*-
"""
列出当前Google Generative AI SDK支持的模型，并测试每个模型的能力
"""

import os
import google.genai as genai
from gemini_config import GEMINI_API_KEYS

# 创建客户端实例
client = genai.Client(api_key=GEMINI_API_KEYS[0])

def test_model_capabilities(model_name, image_path=None):
    """
    测试指定模型的能力
    
    :param model_name: 模型名称
    :param image_path: 图片路径，用于测试图像功能
    :return: 测试结果字典，包含模型名称、文本测试结果、图像测试结果
    """
    result = {
        "model_name": model_name,
        "text_test": "failed",
        "image_test": "not_supported"
    }
    
    try:
        # 测试文本生成能力
        print(f"\n=== 测试 {model_name} 文本生成能力 ===")
        response = client.models.generate_content(
            model=model_name,
            contents=["你好，简单介绍一下自己。"]
        )
        print(f"文本测试成功: {response.text[:100]}...")
        result["text_test"] = "success"
    except Exception as e:
        print(f"文本测试失败: {e}")
    
    # 测试图像功能（如果提供了图像路径）
    if image_path and os.path.exists(image_path):
        try:
            print(f"\n=== 测试 {model_name} 图像功能 ===")
            # 读取图片数据
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # 构建消息内容
            from google.genai import types
            contents = [
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/jpeg' if image_path.endswith('.jpg') or image_path.endswith('.jpeg') else 'image/png'
                ),
                "图里有什么内容？"
            ]
            
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            print(f"图像测试成功: {response.text[:100]}...")
            result["image_test"] = "success"
        except Exception as e:
            print(f"图像测试失败: {e}")
    
    return result

# 列出所有可用模型并测试
if __name__ == "__main__":
    # 测试图片路径
    test_image_path = "/Volumes/600g/app1/doubao获取/test_valid_image.png"
    
    # 验证测试图片是否存在
    if not os.path.exists(test_image_path):
        print(f"测试图片不存在: {test_image_path}")
        test_image_path = None
    
    print("可用的模型列表及测试结果：")
    print("=" * 80)
    print(f"{'模型名称':<30} {'文本测试':<15} {'图像测试':<15}")
    print("=" * 80)
    
    # 遍历所有模型并测试
    test_results = []
    for model in client.models.list():
        # 测试模型能力
        result = test_model_capabilities(model.name, test_image_path)
        test_results.append(result)
        
        # 输出简洁的测试结果
        print(f"{model.name:<30} {result['text_test']:<15} {result['image_test']:<15}")
    
    print("=" * 80)
    print("测试结果汇总：")
    
    # 统计测试结果
    text_success = sum(1 for r in test_results if r['text_test'] == 'success')
    image_success = sum(1 for r in test_results if r['image_test'] == 'success')
    total_models = len(test_results)
    
    print(f"总模型数: {total_models}")
    print(f"文本生成测试通过: {text_success}/{total_models}")
    print(f"图像功能测试通过: {image_success}/{total_models}")
    
    # 输出详细的模型信息
    print("\n\n=== 详细模型信息 ===")
    for model in client.models.list():
        print(f"模型名称: {model.name}")
        print(f"  显示名称: {model.display_name}")
        print(f"  描述: {model.description}")
        print(f"  支持的操作: {model.supported_actions}")
        print(f"  输入令牌限制: {model.input_token_limit}")
        print(f"  输出令牌限制: {model.output_token_limit}")
        print()
