# 豆包OCR整合工具使用说明

## 功能介绍

豆包OCR整合工具是一个统一的命令行工具，包含所有OCR相关功能：

1. **图片OCR识别** - 识别指定图片的内容
2. **屏幕截图OCR识别** - 截取当前屏幕并识别内容
3. **是/否判断** - 支持纯文本、文件、图片内容的是/否判断

## 前提条件

1. 已安装 Node.js 环境
2. 已安装 Python 3.8+ 环境
3. 已启动浏览器服务器：
   ```bash
   node browser_server.js
   ```

## 安装依赖

```bash
# 安装 Python 依赖
/Volumes/600g/app1/okx-py/bin/python3 -m pip install -r requirements.txt

# 安装 Node.js 依赖
npm install
```

## 基本使用方法

### 命令格式

```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py [命令] [参数]
```

### 可用命令

| 命令 | 描述 |
|------|------|
| `ocr` | 图片OCR识别 |
| `screenshot` | 屏幕截图OCR识别 |
| `yesno` | 是/否判断 |

## 详细命令说明

### 1. 图片OCR识别 (`ocr`)

**功能**：识别指定图片的内容

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py ocr <图片绝对路径> [--question <提问内容>] [--server <服务器地址>]
```

**参数说明**：
- `<图片绝对路径>`：必填，图片的绝对路径
- `--question`：可选，向豆包提问的内容，默认值："图里有什么内容？"
- `--server`：可选，浏览器服务器地址，默认值："http://localhost:3000"

**示例**：
```bash
# 基本使用
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py ocr /Volumes/600g/app1/doubao获取/image.png

# 自定义问题
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py ocr /Volumes/600g/app1/doubao获取/image.png --question "图里有哪些文字？"

# 指定服务器地址
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py ocr /Volumes/600g/app1/doubao获取/image.png --server http://localhost:3001
```

### 2. 屏幕截图OCR识别 (`screenshot`)

**功能**：截取当前屏幕并识别内容，支持将结果输出到文件

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py screenshot [--output <输出文件绝对路径>] [--question <提问内容>] [--server <服务器地址>]
```

**参数说明**：
- `--output`：可选，结果输出文件的绝对路径
- `--question`：可选，向豆包提问的内容，默认值："图里有什么内容？"
- `--server`：可选，浏览器服务器地址，默认值："http://localhost:3000"

**示例**：
```bash
# 基本使用
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py screenshot

# 输出结果到文件
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py screenshot --output /Volumes/600g/app1/doubao获取/result.txt

# 自定义问题
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py screenshot --question "图里显示的是什么时间？" --output /Volumes/600g/app1/doubao获取/time.txt
```

### 3. 是/否判断 (`yesno`)

**功能**：支持纯文本、文件、图片内容的是/否判断

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py yesno --question <问题> [--file <文件路径>] [--image <图片路径>] [--server <服务器地址>] [--debug]
```

**参数说明**：
- `--question`：必填，判断的问题
- `--file`：可选，文件路径（与 `--image` 二选一）
- `--image`：可选，图片路径（与 `--file` 二选一）
- `--server`：可选，浏览器服务器地址，默认值："http://localhost:3000"
- `--debug`：可选，输出调试信息

**示例**：
```bash
# 纯文本判断
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py yesno --question "地球是圆的吗？"

# 文件内容判断
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py yesno --question "文件中包含'hello'吗？" --file /Volumes/600g/app1/doubao获取/test.txt

# 图片内容判断
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py yesno --question "图里有一只猫吗？" --image /Volumes/600g/app1/doubao获取/cat.png

# 调试模式
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py yesno --question "地球是圆的吗？" --debug
```

## 返回结果格式

### 图片OCR识别结果

```json
{
  "success": true,
  "message": "图里有什么内容？",
  "response": "图中显示了一个风景图片...",
  "chatHistory": [
    {
      "type": "user",
      "content": "图里有什么内容？",
      "timestamp": "2024-01-01 12:00:00"
    },
    {
      "type": "assistant",
      "content": "图中显示了一个风景图片...",
      "timestamp": "2024-01-01 12:00:05"
    }
  ]
}
```

### 是/否判断结果

- 成功：返回 `yes` 或 `no`
- 失败：返回 `无法判断`

## 常见问题

1. **浏览器服务器未运行**
   - 错误信息："浏览器服务器未运行，请先启动服务器"
   - 解决方法：先启动浏览器服务器 `node browser_server.js`

2. **创建页面失败**
   - 错误信息："创建页面失败"
   - 解决方法：检查浏览器服务器是否正常运行，或重启服务器

3. **识别失败**
   - 错误信息："识别失败"
   - 解决方法：检查图片格式是否支持，或网络连接是否正常

## 代码结构

```
doubao_ocr_all.py
├── 公共工具函数
│   └── validate_file_path, get_script_dir
├── 豆包浏览器客户端
│   └── DoubaoBrowserClient 类
├── 豆包OCR识别类
│   └── DoubaoOCR 类
├── 屏幕截图OCR类
│   └── ScreenshotOCR 类
├── 豆包是/否判断类
│   └── DoubaoYesNo 类
└── 命令行入口
    └── main 函数
```

## 高级用法

### 作为Python模块使用

```python
from doubao_ocr_all import DoubaoOCR, ScreenshotOCR, DoubaoYesNo

# 图片OCR识别
ocr = DoubaoOCR()
result = ocr.recognize_image("/path/to/image.png", question="图里有什么？")

# 屏幕截图OCR识别
screenshot_ocr = ScreenshotOCR()
screenshot_ocr.recognize_screen(output_file="/path/to/result.txt")

# 是/否判断
yes_no = DoubaoYesNo()
result = yes_no.judge(question="地球是圆的吗？")
```

## 更新日志

### v1.0.0
- 整合了图片OCR、屏幕截图OCR、是/否判断功能
- 统一了命令行接口
- 支持自定义服务器地址
- 优化了错误处理机制

## 联系方式

如有问题或建议，请联系开发团队。