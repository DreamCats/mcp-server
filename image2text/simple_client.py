#!/usr/bin/env python3
"""
简化版MCP客户端示例
直接调用底层工具函数，避免复杂的session管理
"""

import asyncio
import base64
import tempfile
import os
from src.main import extract_text_from_image, analyze_image_content, get_supported_formats


def create_test_image():
    """创建一个测试用的base64图片数据"""
    # 这是一个1x1像素的PNG图片的base64编码
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd4c\x00\x00\x00\x00IEND\xaeB`\x82'
    return base64.b64encode(png_data).decode('utf-8')


def create_temp_image_file():
    """创建临时图片文件用于测试"""
    # 创建一个1x1像素的PNG图片数据
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd4c\x00\x00\x00\x00IEND\xaeB`\x82'

    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        tmp_file.write(png_data)
        return tmp_file.name


async def test_basic_functions():
    """测试基本功能"""
    print("image2text MCP服务器简化测试")
    print("=" * 40)

    image_data = create_test_image()
    temp_image_path = create_temp_image_file()

    # 测试1: 获取支持的格式
    print("1. 测试获取支持的格式...")
    try:
        formats = await get_supported_formats()
        print(f"支持的格式: {formats}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n2. 测试图片文本提取（使用base64数据）...")
    try:
        result = await extract_text_from_image(
            image_data=image_data,
            prompt="请描述这张图片的内容"
        )
        print(f"结果: {result}")
    except Exception as e:
        print(f"错误: {e}")

    print(f"\n3. 测试图片文本提取（使用文件路径: {temp_image_path}）...")
    try:
        result = await extract_text_from_image(
            image_data=temp_image_path,
            prompt="请描述这张图片的内容"
        )
        print(f"结果: {result}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n4. 测试图片文本提取（使用自定义API参数）...")
    try:
        result = await extract_text_from_image(
            image_data=image_data,
            api_base_url="https://api.openai.com/v1",
            api_key="your-api-key-here",
            model_id="gpt-4-vision-preview",
            prompt="请详细描述这张图片的内容"
        )
        print(f"结果: {result}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n5. 测试图片内容分析（使用文件路径）...")
    analysis_types = ["general", "text", "objects", "scene"]

    for analysis_type in analysis_types:
        print(f"\n  分析类型: {analysis_type}")
        try:
            result = await analyze_image_content(
                image_data=temp_image_path,
                analysis_type=analysis_type,
                api_base_url="https://api.openai.com/v1",
                api_key="your-api-key-here",
                model_id="gpt-4-vision-preview"
            )
            print(f"  结果: {result[:100]}...")  # 只显示前100个字符
        except Exception as e:
            print(f"  错误: {e}")

    print("\n6. 测试错误处理（不存在的文件）...")
    try:
        result = await extract_text_from_image(
            image_data="/nonexistent/image.png",
            prompt="请描述这张图片的内容"
        )
        print(f"结果: {result}")
    except Exception as e:
        print(f"错误: {e}")

    # 清理临时文件
    try:
        os.unlink(temp_image_path)
    except:
        pass

    print("\n" + "=" * 40)
    print("测试完成!")


if __name__ == "__main__":
    asyncio.run(test_basic_functions())