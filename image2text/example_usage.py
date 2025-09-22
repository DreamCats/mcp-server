#!/usr/bin/env python3
"""
使用示例
演示如何调用image2text MCP服务器的功能

本示例展示了多种使用方式：
1. 基本使用 - 使用默认配置
2. 自定义API参数 - 指定API基础地址、密钥和模型ID
3. 不同的分析类型 - general, text, objects, scene
4. 环境变量配置 - 通过HTTP headers传递配置（需要服务器支持）

API参数说明：
- api_base_url: API服务器地址，如 "https://api.openai.com/v1"
- api_key: API密钥，用于身份验证
- model_id: 模型ID，如 "gpt-4-vision-preview"
- prompt: 自定义提示词，用于指导图片分析
- analysis_type: 分析类型 (general, text, objects, scene)
"""

import base64
import requests
import uuid


def create_test_image():
    """创建一个测试用的base64图片数据"""
    # 这是一个1x1像素的PNG图片的base64编码
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd4c\x00\x00\x00\x00IEND\xaeB`\x82'
    return base64.b64encode(png_data).decode('utf-8')


def create_jsonrpc_request(method, params):
    """创建JSONRPC请求"""
    return {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params
    }


def test_extract_text(server_url="http://localhost:8201"):
    """测试图片文本提取"""
    print("测试图片文本提取...")

    image_data = create_test_image()

    # 使用正确的MCP JSONRPC格式
    payload = create_jsonrpc_request(
        "tools/call",
        {
            "name": "extract_text_from_image",
            "arguments": {
                "image_data": image_data,
                "prompt": "请描述这张图片的内容"
            }
        }
    )

    try:
        response = requests.post(
            f"{server_url}/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print(f"成功: {result['result']}")
            elif "error" in result:
                print(f"错误: {result['error']}")
            else:
                print(f"响应: {result}")
        else:
            print(f"失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"连接失败: 请确保服务器在 {server_url} 运行")
    except Exception as e:
        print(f"错误: {str(e)}")


def test_extract_text_with_custom_api(server_url="http://localhost:8201"):
    """测试使用自定义API参数的图片文本提取"""
    print("\n测试使用自定义API参数的图片文本提取...")

    image_data = create_test_image()

    payload = create_jsonrpc_request(
        "tools/call",
        {
            "name": "extract_text_from_image",
            "arguments": {
                "image_data": image_data,
                "api_base_url": "https://api.openai.com/v1",
                "api_key": "your-api-key-here",
                "model_id": "gpt-4-vision-preview",
                "prompt": "请详细描述这张图片的内容"
            }
        }
    )

    try:
        response = requests.post(
            f"{server_url}/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print(f"成功: {result['result']}")
            elif "error" in result:
                print(f"错误: {result['error']}")
            else:
                print(f"响应: {result}")
        else:
            print(f"失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"连接失败: 请确保服务器在 {server_url} 运行")
    except Exception as e:
        print(f"错误: {str(e)}")


def test_analyze_image(server_url="http://localhost:8201"):
    """测试图片内容分析"""
    print("\n测试图片内容分析...")

    image_data = create_test_image()

    payload = create_jsonrpc_request(
        "tools/call",
        {
            "name": "analyze_image_content",
            "arguments": {
                "image_data": image_data,
                "analysis_type": "general"
            }
        }
    )

    try:
        response = requests.post(
            f"{server_url}/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print(f"成功: {result['result']}")
            elif "error" in result:
                print(f"错误: {result['error']}")
            else:
                print(f"响应: {result}")
        else:
            print(f"失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"连接失败: 请确保服务器在 {server_url} 运行")
    except Exception as e:
        print(f"错误: {str(e)}")


def test_analyze_image_with_custom_api(server_url="http://localhost:8201"):
    """测试使用自定义API参数的图片内容分析"""
    print("\n测试使用自定义API参数的图片内容分析...")

    image_data = create_test_image()

    # 测试不同的分析类型
    analysis_types = ["general", "text", "objects", "scene"]

    for analysis_type in analysis_types:
        print(f"\n  分析类型: {analysis_type}")

        payload = create_jsonrpc_request(
            "tools/call",
            {
                "name": "analyze_image_content",
                "arguments": {
                    "image_data": image_data,
                    "analysis_type": analysis_type,
                    "api_base_url": "https://api.openai.com/v1",
                    "api_key": "your-api-key-here",
                    "model_id": "gpt-4-vision-preview"
                }
            }
        )

        try:
            response = requests.post(
                f"{server_url}/mcp",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    print(f"  成功: {result['result'][:100]}...")  # 只显示前100个字符
                elif "error" in result:
                    print(f"  错误: {result['error']}")
                else:
                    print(f"  响应: {result}")
            else:
                print(f"  失败: HTTP {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(f"  连接失败: 请确保服务器在 {server_url} 运行")
            break
        except Exception as e:
            print(f"  错误: {str(e)}")


def test_get_formats(server_url="http://localhost:8201"):
    """测试获取支持的格式"""
    print("\n测试获取支持的格式...")

    payload = create_jsonrpc_request(
        "tools/call",
        {
            "name": "get_supported_formats",
            "arguments": {}
        }
    )

    try:
        response = requests.post(
            f"{server_url}/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print(f"支持的格式: {result['result']}")
            elif "error" in result:
                print(f"错误: {result['error']}")
            else:
                print(f"响应: {result}")
        else:
            print(f"失败: HTTP {response.status_code}")

    except requests.exceptions.ConnectionError:
        print(f"连接失败: 请确保服务器在 {server_url} 运行")
    except Exception as e:
        print(f"错误: {str(e)}")


def test_with_environment_variables(server_url="http://localhost:8201"):
    """测试通过HTTP headers传递API参数"""
    print("\n测试通过HTTP headers传递API参数...")
    print("注意: 这种方式需要在服务器端配置环境变量")

    image_data = create_test_image()

    payload = create_jsonrpc_request(
        "tools/call",
        {
            "name": "extract_text_from_image",
            "arguments": {
                "image_data": image_data,
                "prompt": "请描述这张图片的内容"
            }
        }
    )

    # 通过headers传递API配置（如果服务器支持）
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
        # 这些header需要在服务器端特殊处理
        # "X-API-Base-URL": "https://api.openai.com/v1",
        # "X-API-Key": "your-api-key-here",
        # "X-Model-ID": "gpt-4-vision-preview"
    }

    try:
        response = requests.post(
            f"{server_url}/mcp",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print(f"成功: {result['result']}")
            elif "error" in result:
                print(f"错误: {result['error']}")
            else:
                print(f"响应: {result}")
        else:
            print(f"失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"连接失败: 请确保服务器在 {server_url} 运行")
    except Exception as e:
        print(f"错误: {str(e)}")


def main():
    """主函数"""
    print("image2text MCP服务器使用示例")
    print("=" * 40)

    # 测试服务器地址
    server_url = "http://localhost:8201"

    # 检查服务器是否运行
    try:
        requests.get(f"{server_url}/health", timeout=5)
        print(f"服务器状态: 运行中")
    except:
        print(f"服务器状态: 未运行")
        print(f"请先启动服务器: python src/main.py")
        return

    # 运行测试
    test_extract_text(server_url)
    test_extract_text_with_custom_api(server_url)
    test_analyze_image(server_url)
    test_analyze_image_with_custom_api(server_url)
    test_get_formats(server_url)
    test_with_environment_variables(server_url)

    print("\n" + "=" * 40)
    print("测试完成!")


if __name__ == "__main__":
    main()