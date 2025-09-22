"""
MCP服务器主模块
负责初始化FastMCP服务器并注册图片处理工具
"""

import argparse
import base64
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

from config import config
from image_processor import ImageProcessor


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化FastMCP服务器
mcp = FastMCP(
    name="image2text",
    json_response=False,      # 使用SSE流式响应
    stateless_http=False      # 保持连接状态
)


@mcp.tool()
async def extract_text_from_image(
    image_data: str,
    api_base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model_id: Optional[str] = None,
    prompt: Optional[str] = None
) -> str:
    """
    从图片中提取文本内容

    Args:
        image_data: 图片的base64编码数据或图片文件路径（如 /Users/bytedance/Demo/doc/assets/test.png）
        api_base_url: API基础地址（可选，通过header传递）
        api_key: API密钥（可选，通过header传递）
        model_id: 模型ID（可选，通过header传递）
        prompt: 自定义提示词（可选）

    Returns:
        提取的文本内容
    """
    logger.info("收到图片文本提取请求")

    try:
        # 创建图片处理器
        processor = ImageProcessor(
            base_url=api_base_url or config.DEFAULT_API_BASE,
            api_key=api_key or config.DEFAULT_API_KEY or "",
            model_id=model_id or config.DEFAULT_MODEL_ID
        )

        # 提取文本内容
        # 如果没有提供提示词，使用默认提示词
        if prompt is None:
            prompt = "请详细描述这张图片的内容，包括文字和视觉元素"
        result = await processor.extract_text(image_data, prompt)

        logger.info("图片文本提取成功")
        return result

    except ValueError as e:
        error_msg = f"参数错误: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"处理失败: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
async def analyze_image_content(
    image_data: str,
    analysis_type: str = "general",
    api_base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model_id: Optional[str] = None
) -> str:
    """
    分析图片内容

    Args:
        image_data: 图片的base64编码数据或图片文件路径（如 /Users/bytedance/Demo/doc/assets/test.png）
        analysis_type: 分析类型 (general, text, objects, scene)
        api_base_url: API基础地址
        api_key: API密钥
        model_id: 模型ID

    Returns:
        分析结果
    """
    logger.info(f"收到图片分析请求，类型: {analysis_type}")

    # 根据分析类型设置不同的提示词
    prompts = {
        "general": "请详细描述这张图片的内容，包括主要元素、场景和氛围",
        "text": "请提取图片中的所有文字内容，保持原有格式",
        "objects": "请识别并列出图片中的所有物体及其位置",
        "scene": "请描述图片中的场景、环境和背景信息"
    }

    prompt = prompts.get(analysis_type, prompts["general"])

    return await extract_text_from_image(
        image_data=image_data,
        api_base_url=api_base_url,
        api_key=api_key,
        model_id=model_id,
        prompt=prompt
    )


@mcp.tool()
async def get_supported_formats() -> dict:
    """
    获取支持的图片格式

    Returns:
        支持的格式列表和配置信息
    """
    return {
        "supported_formats": config.SUPPORTED_FORMATS,
        "max_image_size": config.MAX_IMAGE_SIZE,
        "max_image_size_mb": config.MAX_IMAGE_SIZE / (1024 * 1024)
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="image2text MCP服务器 - 图片转文本MCP工具"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.SERVER_PORT,
        help=f"监听端口 (默认: {config.SERVER_PORT})"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=config.SERVER_HOST,
        help=f"监听主机地址 (默认: {config.SERVER_HOST})"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: INFO)"
    )

    args = parser.parse_args()

    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info(f"启动image2text MCP服务器，监听地址: {args.host}:{args.port}")
    logger.info(f"默认API基础地址: {config.DEFAULT_API_BASE}")
    logger.info(f"默认模型ID: {config.DEFAULT_MODEL_ID}")

    try:
        # 启动HTTP服务器
        import uvicorn
        uvicorn.run(
            mcp.streamable_http_app,
            host=args.host,
            port=args.port,
            log_level=args.log_level.lower()
        )
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        raise


if __name__ == "__main__":
    main()