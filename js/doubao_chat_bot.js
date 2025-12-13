const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class DoubaoChatBot {
    constructor() {
        this.browser = null;
        this.page = null;
        this.chatHistory = [];
        this.baseUrl = 'https://www.doubao.com/chat/';
    }

    // 启动浏览器并导航到豆包聊天页面
    async init(headless = true) {
        console.log('正在启动浏览器...');
        
        // 使用固定的用户数据目录，共享登录状态
        const userDataDir = path.join(__dirname, 'user_data');
        if (!fs.existsSync(userDataDir)) {
            fs.mkdirSync(userDataDir);
            console.log('创建用户数据目录:', userDataDir);
        } else {
            console.log('使用已有的用户数据目录:', userDataDir);
        }
        
        this.browser = await puppeteer.launch({
            headless: headless, // 无头模式，后台运行
            defaultViewport: null,
            args: [
                '--start-maximized',
                '--disable-blink-features=AutomationControlled', // 隐藏自动化控制提示
                '--disable-extensions-except=', // 禁用扩展
                '--disable-plugins-except=', // 禁用插件
                '--disable-popup-blocking',
                '--disable-infobars',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--ignore-certificate-errors',
                '--ignore-certificate-errors-spki-list'
            ],
            userDataDir: userDataDir, // 持久化登录状态
            ignoreHTTPSErrors: true
        });

        this.page = await this.browser.newPage();
        
        // 添加反检测措施
        await this.page.evaluateOnNewDocument(() => {
            // 禁用 navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 移除自动化扩展
            delete navigator.__proto__.webdriver;
            
            // 修改浏览器指纹信息
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            
            // 修改 Canvas 指纹
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type) {
                const context = originalGetContext.apply(this, arguments);
                if (type === '2d') {
                    // 添加一些随机噪声
                    const originalFillText = context.fillText;
                    context.fillText = function() {
                        for (let i = 0; i < arguments.length; i++) {
                            if (typeof arguments[i] === 'string') {
                                arguments[i] += String.fromCharCode(Math.floor(Math.random() * 128));
                            }
                        }
                        return originalFillText.apply(this, arguments);
                    };
                }
                return context;
            };
        });
        
        // 设置真实的用户代理
        await this.page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        
        console.log('正在访问豆包聊天页面...');
        await this.page.goto(this.baseUrl, {
            waitUntil: 'networkidle2',
            timeout: 60000
        });

        // 等待页面加载完成
        await this.page.waitForSelector('textarea.semi-input-textarea', {
            timeout: 30000
        });

        console.log('页面加载完成！');
    }

    // 检查登录状态（可选）
    async checkLoginStatus() {
        console.log('检查登录状态...');
        try {
            // 检查登录按钮是否存在
            const loginBtn = await this.page.$('button.login-btn-header-CTKsn1');
            if (loginBtn) {
                console.log('当前未登录，尝试不登录使用...');
                // 不强制登录，继续执行
            } else {
                console.log('当前已登录！');
            }
        } catch (error) {
            console.log('登录状态检查出错:', error.message);
        }
    }

    // 发送文本消息
    async sendMessage(message) {
        try {
            // 读取question_addon.md文件内容
            let addonContent = '';
            try {
                addonContent = fs.readFileSync(path.join(__dirname, 'question_addon.md'), 'utf8').trim();
                if (addonContent) {
                    message += ` ${addonContent}`;
                }
            } catch (err) {
                console.log('读取question_addon.md文件失败:', err.message);
            }
            
            console.log(`发送消息: ${message}`);
            
            // 定位输入框
            const inputBox = await this.page.$('textarea.semi-input-textarea');
            if (!inputBox) {
                throw new Error('未找到输入框');
            }

            // 输入消息
            await inputBox.type(message, { delay: 50 });
            
            // 点击发送按钮
            const sendBtn = await this.page.$('button.send-btn-mNNnTf:not(.semi-button-disabled)');
            if (!sendBtn) {
                throw new Error('发送按钮不可用');
            }
            await sendBtn.click();

            // 等待消息发送完成
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // 添加到聊天历史
            this.chatHistory.push({
                type: 'user',
                content: message,
                timestamp: new Date().toISOString()
            });

            console.log('消息发送成功！');
            return true;
        } catch (error) {
            console.error('发送消息失败:', error.message);
            return false;
        }
    }

    // 等待并获取AI回复
    async getAIResponse() {
        try {
            console.log('等待AI回复...');
            
            // 等待回复完成，无头模式下需要更长时间
            await new Promise(resolve => setTimeout(resolve, 15000));
            
            // 先尝试提取聊天记录，然后从中获取AI回复
            console.log('尝试先提取聊天记录，再获取AI回复');
            const chatHistory = await this.extractChatHistory();
            
            // 从聊天记录中查找最新的AI回复
            if (chatHistory && chatHistory.length > 0) {
                // 1. 寻找包含编辑分享的完整回复（适用于图片OCR和复杂问题）
                for (let i = chatHistory.length - 1; i >= 0; i--) {
                    const msg = chatHistory[i];
                    if (msg.content && msg.content.includes('编辑')) {
                        const cleanResponse = msg.content.split('编辑')[0].trim();
                        if (cleanResponse.length > 20) {
                            console.log('从聊天记录中成功获取AI回复');
                            console.log(`AI回复: ${cleanResponse}`);
                            return cleanResponse;
                        }
                    }
                }
                
                // 2. 寻找包含"是"/"否"或"yes"/"no"的回复（适用于yes/no判断）
                for (let i = chatHistory.length - 1; i >= 0; i--) {
                    const msg = chatHistory[i];
                    const lowerContent = msg.content.toLowerCase();
                    if (msg.content && (lowerContent.includes('是') || lowerContent.includes('否') || 
                        lowerContent.includes('yes') || lowerContent.includes('no'))) {
                        // 只返回第一个出现的回复内容
                        const cleanResponse = msg.content.trim().split('\n')[0].trim();
                        console.log('从聊天记录中获取到AI回复');
                        console.log(`AI回复: ${cleanResponse}`);
                        return cleanResponse;
                    }
                }
                
                // 3. 寻找最长的回复内容（适用于纯文本聊天）
                let longestResponse = '';
                for (const msg of chatHistory) {
                    if (msg.content && msg.content.length > longestResponse.length) {
                        // 跳过建议问题和短回复
                        if (!msg.content.includes('你可以回答') &&
                            !msg.content.includes('你是如何') &&
                            !msg.content.includes('你能和我') &&
                            !msg.content.includes('是什么意思') &&
                            !msg.content.includes('如何退出')) {
                            longestResponse = msg.content;
                        }
                    }
                }
                
                if (longestResponse.length > 20) {
                    console.log('从聊天记录中获取到AI回复');
                    console.log(`AI回复: ${longestResponse}`);
                    return longestResponse;
                }
                
                // 3. 寻找包含问候语的回复（适用于纯文本聊天）
                for (const msg of chatHistory) {
                    if (msg.content && (msg.content.includes('你好') || 
                                        msg.content.includes('您好') ||
                                        msg.content.includes('有什么可以帮到你') ||
                                        msg.content.includes('可以随时找我'))) {
                        const cleanResponse = msg.content.split('编辑')[0].trim();
                        console.log('从聊天记录中获取到AI回复');
                        console.log(`AI回复: ${cleanResponse}`);
                        return cleanResponse;
                    }
                }
            }

            console.log('未获取到有效的AI回复');
            return null;
        } catch (error) {
            console.error('获取AI回复失败:', error.message);
            return null;
        }
    }

    // 文件上传功能
    async uploadFile(filePath) {
        try {
            console.log(`上传文件: ${filePath}`);
            
            // 检查文件是否存在
            if (!fs.existsSync(filePath)) {
                throw new Error('文件不存在');
            }

            // 检查文件类型是否支持
            const supportedTypes = [
                '.pdf', '.txt', '.csv', '.docx', '.doc',
                '.xlsx', '.xls', '.pptx', '.ppt', '.md',
                '.mobi', '.epub'
            ];
            const fileExt = path.extname(filePath).toLowerCase();
            if (!supportedTypes.includes(fileExt)) {
                throw new Error(`不支持的文件类型: ${fileExt}`);
            }

            // 查找文件输入元素
            let fileInput = await this.page.$('input[type="file"]');
            if (!fileInput) {
                // 如果直接找不到，尝试点击上传按钮来触发文件选择
                const uploadBtn = await this.page.$('[class*="upload"], [class*="file"]');
                if (uploadBtn) {
                    await uploadBtn.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    fileInput = await this.page.$('input[type="file"]');
                }
            }

            if (!fileInput) {
                throw new Error('未找到文件上传元素');
            }

            // 上传文件
            await fileInput.uploadFile(filePath);
            
            // 等待上传完成
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            console.log('文件上传成功！');
            return true;
        } catch (error) {
            console.error('文件上传失败:', error.message);
            return false;
        }
    }

    // 发送包含文件的消息
    async sendMessageWithFile(message, filePath) {
        try {
            // 先上传文件
            const uploadSuccess = await this.uploadFile(filePath);
            if (!uploadSuccess) {
                return false;
            }

            // 然后发送消息
            return await this.sendMessage(message);
        } catch (error) {
            console.error('发送带文件的消息失败:', error.message);
            return false;
        }
    }

    // 提取完整聊天记录
    async extractChatHistory() {
        try {
            console.log('提取聊天记录...');
            
            // 获取聊天记录容器
            const messageList = await this.page.$('[class*="message-list"]') || 
                              await this.page.$('[class*="chat-list"]') ||
                              await this.page.$('body');
            if (!messageList) {
                throw new Error('未找到聊天记录容器');
            }

            // 获取所有消息元素
            const messages = await messageList.$$('[class*="message-item"], [class*="message-box"], [class*="message"]');
            if (messages.length === 0) {
                throw new Error('未找到消息元素');
            }

            const history = [];
            
            for (const message of messages) {
                try {
                    const content = await message.evaluate(el => {
                        return el.textContent.trim();
                    });

                    // 跳过空消息
                    if (!content || content.length < 2) {
                        continue;
                    }

                    // 简单判断消息类型（用户/AI）
                    const className = await message.evaluate(el => el.className);
                    const roleAttr = await message.evaluate(el => el.getAttribute('role') || '');
                    const ariaLabel = await message.evaluate(el => el.getAttribute('aria-label') || '');
                    
                    let type = 'ai'; // 默认AI消息
                    if (className.includes('user') || 
                        className.includes('human') ||
                        className.includes('sender') ||
                        roleAttr.includes('user') ||
                        ariaLabel.includes('user') ||
                        ariaLabel.includes('human')) {
                        type = 'user';
                    }

                    history.push({
                        type,
                        content,
                        timestamp: new Date().toISOString()
                    });
                } catch (err) {
                    console.error('提取单条消息失败:', err.message);
                }
            }

            this.chatHistory = history;
            console.log(`提取到 ${history.length} 条消息，其中用户消息 ${history.filter(msg => msg.type === 'user').length} 条，AI消息 ${history.filter(msg => msg.type === 'ai').length} 条`);
            return history;
        } catch (error) {
            console.error('提取聊天记录失败:', error.message);
            return [];
        }
    }

    // 保存聊天历史到文件
    saveChatHistory(filename = 'chat_history.json') {
        try {
            const data = {
                timestamp: new Date().toISOString(),
                messages: this.chatHistory
            };
            
            fs.writeFileSync(filename, JSON.stringify(data, null, 2), 'utf8');
            console.log(`聊天历史已保存到: ${filename}`);
            return true;
        } catch (error) {
            console.error('保存聊天历史失败:', error.message);
            return false;
        }
    }

    // 关闭浏览器
    async close() {
        if (this.browser) {
            console.log('关闭浏览器...');
            await this.browser.close();
            console.log('浏览器已关闭');
        }
    }
}

// 命令行调用功能
async function runFromCommandLine() {
    const bot = new DoubaoChatBot();
    
    try {
        // 解析命令行参数
        const args = process.argv.slice(2);
        
        // 默认配置
        const options = {
            message: '你好，豆包！',
            headless: true, // 默认无头模式，不会打开浏览器
            output: 'json' // 默认输出JSON格式
        };
        
        // 解析参数
        for (let i = 0; i < args.length; i++) {
            if (args[i] === '--headless') {
                // 下一个参数是headless的值
                options.headless = args[i + 1] === 'true';
                i++; // 跳过值
            } else if (args[i] === '--output') {
                // 下一个参数是output的值
                options.output = args[i + 1] || 'json';
                i++; // 跳过值
            } else {
                // 默认第一个参数是message
                options.message = args[i];
            }
        }
        
        // 初始化浏览器（无头模式）
        await bot.init(options.headless);
        
        // 检查登录状态
        await bot.checkLoginStatus();
        
        // 发送消息并获取回复
        await bot.sendMessage(options.message);
        
        // 提取聊天记录（必须在getAIResponse之前调用）
        await bot.extractChatHistory();
        
        // 获取AI回复
        const response = await bot.getAIResponse();
        
        // 根据输出格式返回结果
        if (options.output === 'json') {
            // 输出JSON格式结果
            console.log(JSON.stringify({
                success: true,
                message: options.message,
                response: response,
                chatHistory: bot.chatHistory,
                timestamp: new Date().toISOString()
            }, null, 2));
        } else {
            // 输出文本格式结果
            console.log('=== 豆包聊天结果 ===');
            console.log(`用户: ${options.message}`);
            console.log(`豆包: ${response}`);
        }
        
        // 保存聊天历史
        bot.saveChatHistory();
        
    } catch (error) {
        // 输出错误信息
        console.error(JSON.stringify({
            success: false,
            error: error.message,
            timestamp: new Date().toISOString()
        }, null, 2));
    } finally {
        // 自动关闭浏览器，不需要手动干预
        await bot.close();
        process.exit(0);
    }
}

// 使用示例
async function main() {
    // 检查是否通过命令行调用
    if (process.argv.length > 2) {
        // 命令行模式
        await runFromCommandLine();
    } else {
        // 交互式模式
        const bot = new DoubaoChatBot();
        
        try {
            // 初始化浏览器（非无头模式）
            await bot.init(false);
            
            // 检查登录状态
            await bot.checkLoginStatus();
            
            // 示例1：发送文本消息并获取回复
            console.log('=== 示例1：发送文本消息 ===');
            await bot.sendMessage('你好，豆包！');
            const response1 = await bot.getAIResponse();
            console.log('AI回复:', response1);
            
            // 示例2：多轮对话
            console.log('\n=== 示例2：多轮对话 ===');
            await bot.sendMessage('你能介绍一下自己吗？');
            const response2 = await bot.getAIResponse();
            console.log('AI回复:', response2);
            
            // 示例3：提取聊天记录并保存
            console.log('\n=== 示例3：保存聊天记录 ===');
            await bot.extractChatHistory();
            bot.saveChatHistory();
            
            // 示例4：文件上传（需要替换为实际文件路径）
            // console.log('\n=== 示例4：文件上传 ===');
            // const testFile = '/path/to/test.txt';
            // await bot.sendMessageWithFile('请分析这个文件', testFile);
            // const response3 = await bot.getAIResponse();
            // console.log('AI回复:', response3);
            
            console.log('\n=== 自动化流程完成 ===');
            
        } catch (error) {
            console.error('程序出错:', error.message);
            console.error(error.stack);
        } finally {
            // 等待用户手动关闭浏览器，方便查看结果
            console.log('\n按任意键关闭浏览器...');
            process.stdin.resume();
            process.stdin.once('data', async () => {
                await bot.close();
                process.exit(0);
            });
        }
    }
}

// 运行主程序
main();