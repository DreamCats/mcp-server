"""
API客户端模块
封装OpenAI兼容API调用
"""

import httpx
import base64
from typing import Dict, Any, Optional
from config import config


class APIClient:
    """OpenAI兼容API客户端"""

    def __init__(self, base_url: str, api_key: str, model_id: str):
        """
        初始化API客户端

        Args:
            base_url: API基础地址
            api_key: API密钥
            model_id: 模型ID
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_id = model_id
        self.client = httpx.AsyncClient(
            timeout=config.REQUEST_TIMEOUT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "image2text-mcp/1.0"
            }
        )

    async def vision_completion(self, image_data: str, prompt: str = "描述这张图片的内容") -> str:
        """
        调用视觉模型API进行图片理解

        Args:
            image_data: base64编码的图片数据
            prompt: 提示词

        Returns:
            模型返回的文本内容
        """
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception("API返回格式无效")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("API密钥无效，请检查配置")
            elif e.response.status_code == 429:
                raise Exception("API调用频率超限，请稍后重试")
            elif e.response.status_code == 400:
                error_msg = e.response.json().get("error", {}).get("message", "请求参数错误")
                raise Exception(f"API请求错误: {error_msg}")
            else:
                raise Exception(f"API调用失败: HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"处理失败: {str(e)}")

    async def close(self):
        """关闭HTTP客户端连接"""
        await self.client.aclose()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()