# 豆包API调用工具集 - 架构设计

## 1. 项目概述

豆包API调用工具集是一个用于调用豆包API的Python工具集，提供图片OCR识别、屏幕截图OCR、纯文字聊天以及是/否判断等功能。该工具集通过Python调用Node.js脚本，利用Puppeteer自动化浏览器来实现与豆包API的交互。

## 2. 系统架构

### 2.1 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       应用层 (Python)                           │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│  DoubaoOCR  │ScreenshotOCR│DoubaoTextChat│    DoubaoYesNo       │
├─────────────┴─────────────┴─────────────┴───────────────────────┤
│                         桥接层 (Subprocess)                       │
├─────────────────────────────────────────────────────────────────┤
│                       执行层 (Node.js)                           │
├─────────────────────┬───────────────────────────────────────────┤
│test_upload_image.js │           doubao_chat_bot.js              │
├─────────────────────┴───────────────────────────────────────────┤
│                         自动化层 (Puppeteer)                     │
├─────────────────────────────────────────────────────────────────┤
│                       服务层 (豆包API)                            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 分层设计

1. **应用层**：提供Python API接口，供用户直接调用或通过命令行使用
2. **桥接层**：通过Python的`subprocess`模块调用Node.js脚本
3. **执行层**：Node.js脚本，实现与豆包API的交互逻辑
4. **自动化层**：使用Puppeteer库自动化浏览器操作
5. **服务层**：豆包API服务，处理用户请求并返回结果

## 3. 核心组件

### 3.1 DoubaoOCR类

**功能**：提供图片OCR识别功能

**主要方法**：
- `__init__(node_script_path)`：初始化OCR类，参数为Node.js脚本路径
- `recognize_image(image_path, question="图里有什么内容？")`：识别图片内容并回答问题
- `get_ocr_result(image_path, question="图里有什么内容？")`：获取OCR识别结果文本

**实现原理**：
1. 接收图片路径和问题
2. 调用Node.js脚本`test_upload_image.js`
3. Node.js脚本使用Puppeteer打开豆包聊天页面
4. 上传图片并发送问题
5. 提取并返回豆包的回答

### 3.2 ScreenshotOCR类

**功能**：提供屏幕截图OCR功能

**主要方法**：
- `__init__(node_script_path)`：初始化截图OCR类，参数为Node.js脚本路径
- `capture_screen(output_path=None)`：截取当前屏幕，参数为截图保存路径（可选）
- `recognize_screen(output_file=None, question="图里有什么内容？")`：截取屏幕并识别内容

**实现原理**：
1. 使用PIL库的`ImageGrab.grab()`方法截取当前屏幕
2. 将截图保存为临时文件
3. 调用`DoubaoOCR.recognize_image()`方法识别截图内容
4. 可选：将识别结果保存到指定文件
5. 清理临时文件

### 3.3 DoubaoTextChat类

**功能**：提供纯文字聊天功能

**主要方法**：
- `__init__(node_script_path)`：初始化纯文字聊天类，参数为Node.js脚本路径
- `send_message(message)`：发送消息并获取原始响应
- `get_response(message)`：获取消息的回复文本

**实现原理**：
1. 接收用户消息
2. 调用Node.js脚本`doubao_chat_bot.js`
3. Node.js脚本使用Puppeteer打开豆包聊天页面
4. 发送消息并等待回复
5. 提取并返回豆包的回答

### 3.4 DoubaoYesNo类

**功能**：提供是/否判断功能

**主要方法**：
- `__init__(node_script_path)`：初始化是/否判断类，参数为Node.js脚本路径
- `judge_text(question, debug=False)`：判断纯文字问题
- `judge_file(question, file_path, debug=False)`：判断文件内容相关问题
- `judge_image(question, image_path, debug=False)`：判断图片内容相关问题
- `judge(question=None, file_path=None, image_path=None, debug=False)`：统一的判断方法

**实现原理**：
1. 根据输入类型（文字、文件、图片）调用不同的处理方法
2. 构建包含"Please answer with only 'yes' or 'no'"的完整问题
3. 调用相应的底层API（`DoubaoTextChat`或`DoubaoOCR`）获取豆包回答
4. 解析回答，提取yes/no信息
5. 返回判断结果

### 3.5 Node.js脚本组件

#### 3.5.1 test_upload_image.js

**功能**：上传图片并询问内容

**主要流程**：
1. 解析命令行参数
2. 初始化Puppeteer浏览器
3. 打开豆包聊天页面
4. 上传指定图片
5. 发送问题
6. 等待并获取AI回复
7. 提取聊天记录
8. 输出JSON格式结果

#### 3.5.2 doubao_chat_bot.js

**功能**：纯文字聊天

**主要流程**：
1. 解析命令行参数
2. 初始化Puppeteer浏览器
3. 打开豆包聊天页面
4. 发送文本消息
5. 等待并获取AI回复
6. 提取聊天记录
7. 输出JSON格式结果

## 4. 数据流程

### 4.1 图片OCR识别流程

```
用户调用 → DoubaoOCR.recognize_image() → subprocess.run() → test_upload_image.js →
Puppeteer自动化浏览器 → 豆包API → 解析响应 → 返回JSON结果 → Python解析 → 返回结果给用户
```

### 4.2 屏幕截图OCR流程

```
用户调用 → ScreenshotOCR.recognize_screen() → ImageGrab.grab() → 保存临时图片 →
DoubaoOCR.recognize_image() → subprocess.run() → test_upload_image.js →
Puppeteer自动化浏览器 → 豆包API → 解析响应 → 返回JSON结果 → Python解析 → 返回结果给用户 → 清理临时文件
```

### 4.3 纯文字聊天流程

```
用户调用 → DoubaoTextChat.send_message() → subprocess.run() → doubao_chat_bot.js →
Puppeteer自动化浏览器 → 豆包API → 解析响应 → 返回JSON结果 → Python解析 → 返回结果给用户
```

### 4.4 是/否判断流程

```
用户调用 → DoubaoYesNo.judge() → 根据类型调用相应方法 →
（文字：DoubaoTextChat | 文件：读取文件+DoubaoTextChat | 图片：DoubaoOCR）→
获取豆包回答 → 解析yes/no → 返回结果给用户
```

## 5. 关键技术点

### 5.1 跨语言调用

通过Python的`subprocess`模块调用Node.js脚本，实现跨语言交互。参数传递通过命令行参数实现，结果返回通过标准输出的JSON格式实现。

### 5.2 Puppeteer自动化

使用Puppeteer库自动化浏览器操作，包括：
- 启动/关闭浏览器
- 导航到豆包聊天页面
- 输入消息
- 点击发送按钮
- 上传文件/图片
- 提取聊天记录

### 5.3 反检测措施

为了避免被豆包API检测到是自动化程序，实现了多种反检测措施：
- 禁用`navigator.webdriver`
- 修改浏览器指纹信息
- 修改Canvas指纹
- 设置真实的用户代理
- 使用持久化的用户数据目录

### 5.4 异步处理

由于浏览器操作和网络请求需要时间，代码中使用了适当的延迟和等待机制，确保操作完成后再进行下一步。

## 6. 代码结构

```
doubao获取/
├── doubao_ocr.py          # 图片OCR识别模块
├── screenshot_ocr.py      # 屏幕截图OCR模块
├── doubao_text_chat.py    # 纯文字聊天模块
├── doubao_yes_no.py       # 是/否判断模块
├── doubao_chat_bot.js     # 纯文字聊天Node.js脚本
├── test_upload_image.js   # 图片上传Node.js脚本
├── package.json           # Node.js依赖配置
├── README.md              # 项目文档
├── ARCHITECTURE.md        # 架构设计文档
├── test_doubao_api.py     # 单元测试
└── image.png              # 测试图片
```

## 7. 扩展性设计

### 7.1 模块化设计

各个功能模块相互独立，通过明确的接口进行交互，便于扩展和维护。新功能可以通过添加新的Python类和对应的Node.js脚本来实现。

### 7.2 配置灵活性

支持通过命令行参数配置各种选项，如Node.js脚本路径、无头模式开关、问题内容等，便于用户根据需要进行调整。

### 7.3 可测试性

设计了完整的单元测试套件，便于测试各个模块的功能和修复bug。测试使用了mock技术，避免了对外部服务的依赖。

## 8. 部署与运行

### 8.1 环境要求

- Python 3.6+
- Node.js
- PIL/Pillow

### 8.2 安装依赖

```bash
# Python依赖
/Volumes/600g/app1/okx-py/bin/pip install Pillow

# Node.js依赖
cd /Volumes/600g/app1/doubao获取
npm install
```

### 8.3 运行方式

#### 命令行运行

```bash
# 图片OCR识别
/Volumes/600g/app1/okx-py/bin/python3 doubao_ocr.py <图片路径> --question <问题>

# 屏幕截图OCR
/Volumes/600g/app1/okx-py/bin/python3 screenshot_ocr.py --output <输出文件> --question <问题>

# 纯文字聊天
/Volumes/600g/app1/okx-py/bin/python3 doubao_text_chat.py "<聊天内容>"

# 是/否判断
/Volumes/600g/app1/okx-py/bin/python3 doubao_yes_no.py --question "<问题>" [--file <文件路径>] [--image <图片路径>]
```

#### 作为库使用

```python
from doubao_ocr import DoubaoOCR
from screenshot_ocr import ScreenshotOCR
from doubao_text_chat import DoubaoTextChat
from doubao_yes_no import DoubaoYesNo

# 图片OCR
ocr = DoubaoOCR("test_upload_image.js")
result = ocr.recognize_image("image.png", question="图里有什么？")

# 屏幕截图OCR
screenshot_ocr = ScreenshotOCR("test_upload_image.js")
result = screenshot_ocr.recognize_screen(question="图里有什么？")

# 纯文字聊天
chat = DoubaoTextChat("doubao_chat_bot.js")
result = chat.send_message("你好，豆包！")

# 是/否判断
yes_no = DoubaoYesNo("doubao_chat_bot.js")
result = yes_no.judge(question="地球是圆的吗？")
```

## 9. 监控与维护

### 9.1 日志记录

各个模块都有适当的日志输出，便于调试和监控运行状态。关键操作如图片识别、消息发送、API调用等都会输出日志信息。

### 9.2 错误处理

实现了完善的错误处理机制，包括：
- 文件不存在检查
- 脚本执行失败处理
- 超时处理
- JSON解析错误处理
- 异常捕获和友好提示

### 9.3 测试策略

使用unittest框架编写了完整的单元测试，覆盖了主要功能和边界情况。测试使用了mock技术，确保测试的独立性和可靠性。

## 10. 未来改进方向

1. **使用官方API**：考虑使用豆包官方API，替代目前的Puppeteer自动化方式，提高稳定性和效率
2. **异步调用**：实现异步调用机制，提高并发处理能力
3. **缓存机制**：添加结果缓存，避免重复请求
4. **多语言支持**：支持更多语言的OCR识别和聊天
5. **更完善的错误处理**：增强错误处理和恢复机制
6. **配置文件支持**：添加配置文件，便于集中管理配置选项
7. **Web界面**：添加Web界面，提高用户体验
8. **Docker部署**：支持Docker部署，简化环境配置

## 11. 总结

豆包API调用工具集采用了模块化、分层设计，通过Python调用Node.js脚本实现与豆包API的交互。该架构具有良好的扩展性、灵活性和可测试性，便于维护和扩展。未来可以考虑使用官方API替代自动化方式，进一步提高稳定性和效率。