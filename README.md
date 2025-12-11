# 豆包API调用工具集

这是一个用于调用豆包API的Python工具集，提供图片OCR识别、屏幕截图OCR、纯文字聊天以及是/否判断等功能。

## 功能列表

1. **图片OCR识别** - 识别指定图片的内容并回答相关问题
2. **屏幕截图OCR** - 截取当前屏幕并识别内容
3. **纯文字聊天** - 与豆包进行纯文字对话
4. **是/否判断** - 针对文字、文件内容或图片内容进行是/否判断

## 环境要求

- Python 3.6+
- Node.js（用于调用豆包API）
- PIL/Pillow（用于屏幕截图）

## 安装依赖

```bash
/Volumes/600g/app1/okx-py/bin/pip install Pillow
```

## 文件结构

```
doubao获取/
├── doubao_ocr.py          # 图片OCR识别模块
├── screenshot_ocr.py      # 屏幕截图OCR模块
├── doubao_text_chat.py    # 纯文字聊天模块
├── doubao_yes_no.py       # 是/否判断模块
├── doubao_chat_bot.js     # 纯文字聊天Node.js脚本
├── test_upload_image.js   # 图片上传Node.js脚本
├── package.json           # Node.js依赖配置
└── README.md              # 项目文档
```

## 使用方法

### 1. 图片OCR识别

**功能**：识别指定图片的内容并回答相关问题

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_ocr.py <图片绝对路径> [--question <提问内容>] [--node_script /Volumes/600g/app1/doubao获取/test_upload_image.js]
```

**参数说明**：
- `<图片绝对路径>`：必填，图片的绝对路径
- `--question`：可选，向豆包提问的内容，默认值："图里有什么内容？"
- `--node_script`：可选，Node.js脚本路径，默认值："./test_upload_image.js"

**示例**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_ocr.py /Volumes/600g/app1/doubao获取/image.png --question "图里有什么？"
```

### 2. 屏幕截图OCR

**功能**：截取当前屏幕并识别内容，支持将结果输出到文件

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/screenshot_ocr.py [--output <输出文件绝对路径>] [--question <提问内容>] [--node_script /Volumes/600g/app1/doubao获取/test_upload_image.js]
```

**参数说明**：
- `--output`：可选，结果输出文件的绝对路径
- `--question`：可选，向豆包提问的内容，默认值："图里有什么内容？"
- `--node_script`：可选，Node.js脚本路径，默认值："./test_upload_image.js"

**示例**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/screenshot_ocr.py --output /Volumes/600g/app1/doubao获取/result.txt
```

### 3. 纯文字聊天

**功能**：与豆包进行纯文字对话

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_text_chat.py "<聊天内容>" [--node_script /Volumes/600g/app1/doubao获取/doubao_chat_bot.js]
```

**参数说明**：
- `<聊天内容>`：必填，要发送给豆包的消息
- `--node_script`：可选，Node.js脚本路径，默认值："./doubao_chat_bot.js"

**示例**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_text_chat.py "你好，豆包！"
```

### 4. 是/否判断

**功能**：针对文字、文件内容或图片内容进行是/否判断

**命令格式**：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_yes_no.py --question "<问题>" [--file <文件路径>] [--image <图片路径>] [--node_script /Volumes/600g/app1/doubao获取/doubao_chat_bot.js] [--debug]
```

**参数说明**：
- `--question`：必填，要判断的问题
- `--file`：可选，要分析的文件路径
- `--image`：可选，要分析的图片路径
- `--node_script`：可选，Node.js脚本路径，默认值："./doubao_chat_bot.js"
- `--debug`：可选，输出调试信息

**注意**：`--file`和`--image`参数不能同时使用。

**示例**：

1. 文字问题判断：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_yes_no.py --question "地球是圆的吗？"
```

2. 文件内容判断：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_yes_no.py --question "文件中是否提到地球是圆的？" --file /Volumes/600g/app1/doubao获取/test_file.txt
```

3. 图片内容判断：
```bash
/Volumes/600g/app1/okx-py/bin/python3 /Volumes/600g/app1/doubao获取/doubao_yes_no.py --question "这是不是微博界面？" --image /Volumes/600g/app1/doubao获取/image.png --debug
```

## API文档

### 1. DoubaoOCR类

**功能**：提供图片OCR识别功能

**主要方法**：

```python
__init__(node_script_path)  # 初始化OCR类，参数为Node.js脚本路径
recognize_image(image_path, question="图里有什么内容？")  # 识别图片内容并回答问题
get_ocr_result(image_path, question="图里有什么内容？")  # 获取OCR识别结果文本
```

### 2. ScreenshotOCR类

**功能**：提供屏幕截图OCR功能

**主要方法**：

```python
__init__(node_script_path)  # 初始化截图OCR类，参数为Node.js脚本路径
capture_screen(output_path=None)  # 截取当前屏幕，参数为截图保存路径（可选）
recognize_screen(output_file=None, question="图里有什么内容？")  # 截取屏幕并识别内容
```

### 3. DoubaoTextChat类

**功能**：提供纯文字聊天功能

**主要方法**：

```python
__init__(node_script_path)  # 初始化纯文字聊天类，参数为Node.js脚本路径
send_message(message)  # 发送消息并获取原始响应
get_response(message)  # 获取消息的回复文本
```

### 4. DoubaoYesNo类

**功能**：提供是/否判断功能

**主要方法**：

```python
__init__(node_script_path)  # 初始化是/否判断类，参数为Node.js脚本路径
judge_text(question, debug=False)  # 判断纯文字问题
judge_file(question, file_path, debug=False)  # 判断文件内容相关问题
judge_image(question, image_path, debug=False)  # 判断图片内容相关问题
judge(question=None, file_path=None, image_path=None, debug=False)  # 统一的判断方法
```

## 注意事项

1. 请确保Node.js环境已正确配置，并且已安装所需依赖：
   ```bash
   cd /Volumes/600g/app1/doubao获取
   npm install
   ```

2. 所有工具都支持`--node_script`参数，用于指定自定义的Node.js脚本路径。

3. 是/否判断工具（doubao_yes_no.py）默认使用doubao_chat_bot.js脚本进行纯文字和文件判断，使用test_upload_image.js脚本进行图片判断。

4. 屏幕截图功能仅在支持PIL/Pillow的平台上可用。

## 常见问题

### Q: 为什么图片OCR识别失败？
A: 可能的原因包括：
   - 图片路径不正确
   - Node.js脚本路径不正确
   - 网络连接问题
   - 图片格式不支持

### Q: 为什么是/否判断返回"无法判断"？
A: 可能的原因包括：
   - 豆包的回答没有包含明确的肯定或否定词汇
   - 问题表述不够清晰
   - 图片或文件内容不明确

### Q: 如何获取更详细的调试信息？
A: 在使用是/否判断工具时，可以添加`--debug`参数来获取详细的调试信息。

## 示例输出

### 图片OCR识别示例

```
开始识别图片: /Volumes/600g/app1/doubao获取/image.png
提问内容: 这是不是微博界面？
脚本输出: {...JSON数据...}
提取到的JSON: {...JSON数据...}

=== 识别结果 ===
{
  "success": true,
  "message": "这是不是微博界面？",
  "response": "这是微博界面。从截图中可以看到左上角有'微博'标识，顶部有微博的导航栏，包含'首页'、'消息'、'发现'等核心功能入口，还有用户头像和搜索框，这些都是微博的典型界面特征。",
  "chatHistory": [...]  
}

=== 关键信息 ===
提问: 这是不是微博界面？
回复: 这是微博界面。从截图中可以看到左上角有'微博'标识，顶部有微博的导航栏，包含'首页'、'消息'、'发现'等核心功能入口，还有用户头像和搜索框，这些都是微博的典型界面特征。

聊天记录数量: 2
```

### 是/否判断示例

```
向豆包提问: 文件中是否提到地球是圆的？ Please answer with only 'yes' or 'no'.
原始回答: 是的，文件中提到了地球是圆的。
yes
```

## 许可证

MIT License
