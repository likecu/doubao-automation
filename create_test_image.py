#!/usr/bin/env /Volumes/600g/app1/okx-py/bin/python3

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    # 创建一个简单的测试图片
    width, height = 400, 200
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 使用默认字体
    try:
        # 尝试加载系统字体
        font = ImageFont.truetype('/Library/Fonts/Arial.ttf', 24)
    except IOError:
        # 如果没有Arial，使用默认字体
        font = ImageFont.load_default()
    
    # 绘制测试文本
    text = "测试OCR识别功能\n这是第二行文本\n1234567890"
    lines = text.split('\n')
    
    y = 50
    for line in lines:
        text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:4]
        x = (width - text_width) // 2
        draw.text((x, y), line, fill='black', font=font)
        y += text_height + 10
    
    # 保存图片
    image_path = "/Volumes/600g/app1/doubao获取/test_ocr_image.png"
    image.save(image_path)
    print(f"测试图片已创建: {image_path}")
    return image_path

if __name__ == "__main__":
    create_test_image()
