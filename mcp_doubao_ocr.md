# 豆包OCR识别工具MCP文档

**当前文件绝对路径**：/Volumes/600g/app1/doubao获取/mcp_doubao_ocr.md

## 1. 接口列表

| 接口名称 | 功能描述 | 命令路径 |
|---------|---------|---------|
| doubao.image.ocr | 识别指定图片的内容 | /Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr.py |
| doubao.screen.ocr | 截取当前屏幕并识别内容 | /Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/screenshot_ocr.py |
| doubao.judge.yesno | 调用豆包判断问题，解析结果仅输出是或否 | /Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_yes_no.py |

## 2. 接口详细说明

### 2.1 doubao.image.ocr - 图片OCR识别

**功能**：识别指定图片的内容，支持自定义提问。

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr.py <图片绝对路径> [--question <提问内容>] [--server_url <服务器地址>]
```

**参数说明**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `<图片绝对路径>` | 字符串 | 是 | - | 需要识别的图片的绝对路径 |
| `--question` | 字符串 | 否 | "图里有什么内容？" | 向豆包提问的内容，用于引导识别方向 |
| `--server_url` | 字符串 | 否 | http://localhost:3000 | 浏览器服务器地址 |

**返回值**：
- 成功：返回识别结果的JSON字符串
- 失败：返回错误信息

**示例**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_ocr.py /Volumes/600g/app1/doubao获取/image.png --question "图里有什么？"
```

### 2.2 doubao.screen.ocr - 屏幕截图OCR识别

**功能**：截取当前屏幕并识别内容，支持将结果输出到文件。

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/screenshot_ocr.py [--output <输出文件绝对路径>] [--question <提问内容>] [--server_url <服务器地址>]
```

**参数说明**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `--output` | 字符串 | 否 | - | 识别结果输出文件的绝对路径，不指定则只在控制台输出 |
| `--question` | 字符串 | 否 | "图里有什么内容？" | 向豆包提问的内容，用于引导识别方向 |
| `--server_url` | 字符串 | 否 | http://localhost:3000 | 浏览器服务器地址 |

**返回值**：
- 成功：返回识别结果的JSON字符串，并根据参数决定是否输出到文件
- 失败：返回错误信息

**示例**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/screenshot_ocr.py --output /Volumes/600g/app1/doubao获取/result.txt
```

### 2.3 doubao.judge.yesno - 是/否判断工具

**功能**：调用豆包判断问题，解析结果仅输出是或否。

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/python/doubao_yes_no.py --question <问题> [--file <文件路径>] [--image <图片路径>] [--server_url <服务器地址>] [--debug]
```

**参数说明**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `--question` | 字符串 | 是 | - | 需要判断的问题 |
| `--file` | 字符串 | 否 | - | 文件路径，与图片参数二选一 |
| `--image` | 字符串 | 否 | - | 图片路径，与文件参数二选一 |
| `--server_url` | 字符串 | 否 | http://localhost:3000 | 浏览器服务器地址 |
| `--debug` | 布尔值 | 否 | False | 是否输出调试信息 |

**返回值**：
- 成功：返回"是"或"否"，不包含其他内容
- 失败：返回错误信息

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

## 3. 环境要求

- Python 3.x
- Node.js
- 浏览器服务器正在运行（启动命令：`node /Volumes/600g/app1/doubao获取/js/browser_server.js`）

## 4. 注意事项

1. 所有命令均使用绝对路径，确保在任何目录下都能正常执行
2. 使用前请确保浏览器服务器已启动
3. 图片识别功能需要网络连接，因为需要调用豆包API
4. 屏幕截图功能仅支持Mac系统

## 5. 错误处理

- 如果浏览器服务器未运行，会提示："浏览器服务器未运行，请先启动服务器"
- 如果图片路径不存在，会提示："图片路径不存在：<路径>"
- 如果文件路径不存在，会提示："文件路径不存在：<路径>"

## 6. 版本信息

- **版本**：v1.0.1
- **更新日期**：2025-12-12
- **作者**：TraeAI