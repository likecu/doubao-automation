# 用户规则更新

## 环境信息
- 请保持为中文，同时使用虚拟环境的python,安装pip时也要使用虚拟环境
- 系统为 Mac
- 虚拟环境的python的路径为： /Volumes/600g/app1/okx-py/bin

## 可用工具

### 4.1.1 图片OCR

**功能**：识别指定图片的内容

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_ocr.py <图片绝对路径> [--question <提问内容>] [--node_script /Volumes/600g/app1/doubao获取/test_upload_image.js]
```

**参数说明**：
- `<图片绝对路径>`：必填，图片的绝对路径
- `--question`：可选，向豆包提问的内容，默认值："图里有什么内容？"
**示例**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_ocr.py /Volumes/600g/app1/doubao获取/image.png --question "图里有什么？"
```

### 4.1.2 屏幕截图OCR

**功能**：截取当前屏幕并识别内容，支持将结果输出到文件

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/screenshot_ocr.py [--output <输出文件绝对路径>] [--question <提问内容>] 
```

**参数说明**：
- `--output`：可选，结果输出文件的绝对路径
- `--question`：可选，向豆包提问的内容，默认值："图里有什么内容？"

**示例**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/screenshot_ocr.py --output /Volumes/600g/app1/doubao获取/result.txt
```

### 4.1.3 Yes/No 图片OCR

**功能**：识别指定图片内容并回答是/否问题

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_yes_no.py --question <提问内容> --image <图片绝对路径>
```

**参数说明**：
- `--question`：必填，向豆包提问的是/否问题
- `--image`：必填，图片的绝对路径

**示例**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_yes_no.py --question "地球是圆的吗？" --image /Volumes/600g