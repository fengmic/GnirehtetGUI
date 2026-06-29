"""
图片转 ICO 格式工具
用法：python demo.py <输入图片> [输出ICO路径]
示例：python demo.py icon.png
      python demo.py icon.png output.ico
"""

import sys
import os
from PIL import Image

# 支持的输入格式
SUPPORTED = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff"}

# ICO 标准尺寸
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def convert_to_ico(input_path: str, output_path: str = None) -> str:
    """
    将图片转换为 ICO 文件。

    :param input_path:  输入图片路径
    :param output_path: 输出 ICO 路径（可选，默认与输入同名）
    :return: 输出文件的绝对路径
    """
    input_path = os.path.abspath(input_path)

    # 检查输入文件
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到输入文件：{input_path}")

    ext = os.path.splitext(input_path)[1].lower()
    if ext not in SUPPORTED:
        raise ValueError(f"不支持的图片格式：{ext}，支持：{', '.join(SUPPORTED)}")

    # 确定输出路径
    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + ".ico"
    output_path = os.path.abspath(output_path)

    # 打开并转换
    img = Image.open(input_path).convert("RGBA")

    # 生成各尺寸缩略图，保持比例居中（方形填透明背景）
    frames = []
    for size in ICO_SIZES:
        thumb = img.copy()
        thumb.thumbnail(size, Image.LANCZOS)
        # 居中贴到透明画布
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        offset = ((size[0] - thumb.width) // 2, (size[1] - thumb.height) // 2)
        canvas.paste(thumb, offset)
        frames.append(canvas)

    # 保存 ICO
    frames[0].save(
        output_path,
        format="ICO",
        sizes=ICO_SIZES,
        append_images=frames[1:],
    )

    return output_path


def main():
    if len(sys.argv) < 2:
        print("用法：python demo.py <输入图片> [输出ICO路径]")
        print("示例：python demo.py icon.png")
        print("      python demo.py icon.png output.ico")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None

    try:
        result = convert_to_ico(input_file, output_file)
        print(f"转换成功：{result}")
        print(f"包含尺寸：{', '.join(f'{w}x{h}' for w, h in ICO_SIZES)}")
    except FileNotFoundError as e:
        print(f"错误：{e}")
        sys.exit(1)
    except ValueError as e:
        print(f"错误：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"未知错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
