const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const app = express();
const PORT = 3001;

// 中间件
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true }));

// 基础路径
const PYTHON_PATH = '/Volumes/600g/app1/okx-py/bin/python3';
const OCR_SCRIPT = '/Volumes/600g/app1/doubao获取/python/doubao_ocr_all.py';
const BROWSER_SERVER_URL = 'http://localhost:3000';

// 健康检查
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        service: 'doubao-ai-api'
    });
});

// 标准AI接口：聊天补全
app.post('/v1/chat/completions', (req, res) => {
    try {
        const { messages, model, max_tokens, temperature } = req.body;
        
        // 验证请求
        if (!messages || !Array.isArray(messages) || messages.length === 0) {
            return res.status(400).json({
                error: {
                    message: "Messages array is required",
                    type: "invalid_request_error",
                    param: "messages"
                }
            });
        }
        
        // 获取最后一条用户消息
        const lastMessage = messages[messages.length - 1];
        if (lastMessage.role !== 'user') {
            return res.status(400).json({
                error: {
                    message: "Last message must be from user",
                    type: "invalid_request_error",
                    param: "messages"
                }
            });
        }
        
        const userMessage = lastMessage.content;
        
        // 使用curl调用现有的browser_server
        let cmd = `curl -X GET ${BROWSER_SERVER_URL}/createPage`;
        const pageIdResult = execSync(cmd).toString();
        const pageIdData = JSON.parse(pageIdResult);
        
        if (!pageIdData.success) {
            throw new Error('Failed to create page');
        }
        
        const pageId = pageIdData.pageId;
        
        try {
            // 发送消息
            cmd = `curl -X POST ${BROWSER_SERVER_URL}/textChat -H "Content-Type: application/json" -d '{"pageId": ${pageId}, "message": "${userMessage}"}'`;
            const chatResult = execSync(cmd).toString();
            const chatData = JSON.parse(chatResult);
            
            if (!chatData.success) {
                throw new Error('Chat failed');
            }
            
            // 返回标准格式
            res.json({
                id: `chatcmpl-${Date.now()}`,
                object: "chat.completion",
                created: Math.floor(Date.now() / 1000),
                model: model || "doubao-1.0",
                choices: [{
                    index: 0,
                    message: {
                        role: "assistant",
                        content: chatData.response
                    },
                    finish_reason: "stop"
                }],
                usage: {
                    prompt_tokens: userMessage.length,
                    completion_tokens: chatData.response.length,
                    total_tokens: userMessage.length + chatData.response.length
                }
            });
        } finally {
            // 关闭页面
            cmd = `curl -X GET ${BROWSER_SERVER_URL}/closePage?pageId=${pageId}`;
            execSync(cmd, { stdio: 'ignore' });
        }
        
    } catch (error) {
        console.error('Chat completion error:', error);
        res.status(500).json({
            error: {
                message: error.message,
                type: "server_error"
            }
        });
    }
});

// 标准AI接口：OCR识别
app.post('/v1/ocr/recognize', (req, res) => {
    try {
        const { image_url, image_base64, question, type } = req.body;
        
        // 验证请求
        if (!image_url && !image_base64 && type !== 'screenshot') {
            return res.status(400).json({
                error: {
                    message: "Either image_url, image_base64, or type=screenshot is required",
                    type: "invalid_request_error"
                }
            });
        }
        
        let imagePath = '';
        let cmd = '';
        
        if (type === 'screenshot') {
            // 屏幕截图OCR
            cmd = `${PYTHON_PATH} ${OCR_SCRIPT} screenshot`;
            if (question) {
                cmd += ` --question "${question}"`;
            }
        } else if (image_url) {
            // 图片URL（需要先下载）
            const tempPath = `/tmp/${Date.now()}_ocr_image`;
            execSync(`curl -o ${tempPath} ${image_url}`);
            imagePath = tempPath;
            
            cmd = `${PYTHON_PATH} ${OCR_SCRIPT} ocr ${imagePath}`;
            if (question) {
                cmd += ` --question "${question}"`;
            }
        } else if (image_base64) {
            // 图片base64
            const tempPath = `/tmp/${Date.now()}_ocr_image.png`;
            const base64Data = image_base64.replace(/^data:image\/\w+;base64,/, '');
            fs.writeFileSync(tempPath, base64Data, { encoding: 'base64' });
            imagePath = tempPath;
            
            cmd = `${PYTHON_PATH} ${OCR_SCRIPT} ocr ${imagePath}`;
            if (question) {
                cmd += ` --question "${question}"`;
            }
        }
        
        // 执行命令
        const result = execSync(cmd).toString();
        
        // 清理临时文件
        if (imagePath && fs.existsSync(imagePath)) {
            fs.unlinkSync(imagePath);
        }
        
        // 解析结果
        const jsonMatch = result.match(/\{[\s\S]*\}/);
        if (!jsonMatch) {
            throw new Error('Failed to parse OCR result');
        }
        
        const ocrData = JSON.parse(jsonMatch[0]);
        
        // 返回标准格式
        res.json({
            id: `ocr-${Date.now()}`,
            object: "ocr.recognize",
            created: Math.floor(Date.now() / 1000),
            model: "doubao-ocr-1.0",
            result: {
                text: ocrData.response,
                success: ocrData.success,
                original_result: ocrData
            }
        });
        
    } catch (error) {
        console.error('OCR error:', error);
        res.status(500).json({
            error: {
                message: error.message,
                type: "server_error"
            }
        });
    }
});

// 标准AI接口：是/否判断
app.post('/v1/moderations', (req, res) => {
    try {
        const { input, question } = req.body;
        
        // 验证请求
        if (!input && !question) {
            return res.status(400).json({
                error: {
                    message: "Either input or question is required",
                    type: "invalid_request_error"
                }
            });
        }
        
        let cmd = `${PYTHON_PATH} ${OCR_SCRIPT} yesno`;
        
        if (question) {
            cmd += ` --question "${question}"`;
        }
        
        if (typeof input === 'string') {
            // 文本输入，直接使用question
            if (!question) {
                cmd += ` --question "Is this content acceptable?"`;
            }
        } else if (input?.image) {
            // 图片输入
            cmd += ` --image "${input.image}"`;
        } else if (input?.file) {
            // 文件输入
            cmd += ` --file "${input.file}"`;
        }
        
        // 执行命令
        const result = execSync(cmd).toString().trim();
        
        // 转换为标准格式
        const isPositive = result.toLowerCase() === 'yes';
        
        res.json({
            id: `mod-${Date.now()}`,
            object: "moderation",
            created: Math.floor(Date.now() / 1000),
            model: "doubao-moderation-1.0",
            results: [{
                flagged: !isPositive,
                categories: {
                    positive: isPositive,
                    negative: !isPositive
                },
                category_scores: {
                    positive: isPositive ? 0.99 : 0.01,
                    negative: !isPositive ? 0.99 : 0.01
                },
                original_result: result
            }]
        });
        
    } catch (error) {
        console.error('Moderation error:', error);
        res.status(500).json({
            error: {
                message: error.message,
                type: "server_error"
            }
        });
    }
});

// 文件上传接口
app.post('/v1/files/upload', (req, res) => {
    try {
        const { file } = req.body;
        
        if (!file) {
            return res.status(400).json({
                error: {
                    message: "File is required",
                    type: "invalid_request_error",
                    param: "file"
                }
            });
        }
        
        // 保存文件
        const tempPath = `/tmp/${Date.now()}_upload`;
        fs.writeFileSync(tempPath, file, { encoding: 'base64' });
        
        res.json({
            id: `file-${Date.now()}`,
            object: "file",
            bytes: fs.statSync(tempPath).size,
            created_at: Math.floor(Date.now() / 1000),
            filename: `upload_${Date.now()}`,
            purpose: "fine-tune",
            status: "processed",
            status_details: null
        });
        
    } catch (error) {
        console.error('File upload error:', error);
        res.status(500).json({
            error: {
                message: error.message,
                type: "server_error"
            }
        });
    }
});

// 启动服务器
app.listen(PORT, () => {
    console.log(`=== 豆包AI标准接口服务已启动 ===`);
    console.log(`服务地址: http://localhost:${PORT}`);
    console.log(`\n可用API:`);
    console.log(`GET  /health                     - 健康检查`);
    console.log(`POST /v1/chat/completions        - 聊天补全`);
    console.log(`POST /v1/ocr/recognize           - OCR识别`);
    console.log(`POST /v1/moderations             - 是/否判断`);
    console.log(`POST /v1/files/upload            - 文件上传`);
    console.log(`\n按 Ctrl+C 停止服务`);
});

// 优雅关闭
process.on('SIGINT', () => {
    console.log('\n正在关闭服务器...');
    process.exit(0);
});
