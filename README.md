# 豆包OCR识别工具

豆包OCR识别工具是一套基于豆包API的图片识别工具集，提供图片OCR、屏幕截图OCR和是/否判断等功能。

## 功能特性

- 📸 **图片OCR**：识别指定图片的内容
- 🖥️ **屏幕截图OCR**：截取当前屏幕并识别内容，支持结果输出到文件
- ❓ **是/否判断工具**：调用豆包判断问题，解析结果仅输出是或否

## 环境要求

- Python 3.x
- Node.js
- 虚拟环境Python路径：`/Volumes/600g/app1/okx-py/bin/python3`

## 使用方法

### 启动浏览器服务器

在使用OCR功能前，需要先启动浏览器服务器：

**命令格式**：
```bash
node /Volumes/600g/app1/doubao获取/js/browser_server.js [--debug] [-d]
```

**参数说明**：
- `--debug` 或 `-d`：可选，启用调试模式，使用有头模式启动浏览器，默认使用无头模式

**示例**：
```bash
# 默认无头模式启动
node /Volumes/600g/app1/doubao获取/js/browser_server.js

# 调试模式启动（有头模式）
node /Volumes/600g/app1/doubao获取/js/browser_server.js --debug
```

### 关于路径的说明

文档中所有命令使用的Python解释器路径 `/Volumes/600g/app1/okx-py/bin/python3` 是一个绝对路径，脚本文件也使用绝对路径，这是为了确保命令在任何目录下都能正常执行。

**修改说明**：如果您的Python解释器安装在不同位置，请将命令中的Python路径替换为您实际的Python解释器路径。

### 命令行使用

#### 图片OCR

**功能**：识别指定图片的内容

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr.py <图片绝对路径> [--question <提问内容>] [--node_script /Volumes/600g/app1/doubao获取/test_upload_image.js]
```

**参数说明**：
- `<图片绝对路径>`：必填，图片的绝对路径
- `--question`：可选，向豆包提问的内容，默认值："图里有什么内容？"
- `--node_script`：可选，Node.js脚本的绝对路径，默认值：`/Volumes/600g/app1/doubao获取/test_upload_image.js`

**示例**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr.py /Volumes/600g/app1/doubao获取/image.png --question "图里有什么？"
```

#### 屏幕截图OCR

**功能**：截取当前屏幕并识别内容，支持将结果输出到文件

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/screenshot_ocr.py [--output <输出文件绝对路径>] [--question <提问内容>] 
```

**参数说明**：
- `--output`：可选，结果输出文件的绝对路径
- `--question`：可选，向豆包提问的内容，默认值："图里有什么内容？"

**示例**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/screenshot_ocr.py --output /Volumes/600g/app1/doubao获取/result.txt
```

#### 是/否判断工具

**功能**：调用豆包判断问题，解析结果仅输出是或否

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_yes_no.py --question <问题> [--file <文件路径>] [--image <图片路径>] [--node_script /Volumes/600g/app1/doubao获取/test_upload_image.js] [--debug]
```

**参数说明**：
- `--question`：必填，判断的问题
- `--file`：可选，文件路径（与图片二选一）
- `--image`：可选，图片路径（与文件二选一）
- `--node_script`：可选，Node.js脚本的绝对路径，默认值：`/Volumes/600g/app1/doubao获取/test_upload_image.js`
- `--debug`：可选，输出调试信息

**示例**：

1. 纯文字问题判断：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_yes_no.py --question "地球是圆的吗？"
```

2. 文件内容判断：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_yes_no.py --question "文件中是否包含'测试'一词？" --file /Volumes/600g/app1/doubao获取/test.txt
```

3. 图片内容判断：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_yes_no.py --question "图片中是否有人物？" --image /Volumes/600g/app1/doubao获取/image.png
```

4. 带调试信息：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_yes_no.py --question "地球是圆的吗？" 
```

## 版本信息

- **版本**：v1.0.1
- **更新日期**：2025-12-12
- **作者**：TraeAI