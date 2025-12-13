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
            
            // 优化：等待输入框内容更新
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // 优化：尝试多种方式点击发送按钮
            let sendSuccess = false;
            let attempt = 1;
            const maxAttempts = 3;
            
            while (!sendSuccess && attempt <= maxAttempts) {
                console.log(`尝试发送消息，第 ${attempt} 次尝试`);
                
                // 方式1：使用包含选择器等待按钮可见并点击
                try {
                    await this.page.waitForSelector('button[class*="send-btn"], button[class*="send-button"], button[type="submit"]', {
                        visible: true,
                        timeout: 5000
                    });
                    const sendBtn = await this.page.$('button[class*="send-btn"]:not([class*="disabled"], [disabled]), button[class*="send-button"]:not([class*="disabled"], [disabled]), button[type="submit"]:not([class*="disabled"], [disabled])');
                    if (sendBtn) {
                        await sendBtn.click();
                        sendSuccess = true;
                        console.log('方式1：成功点击发送按钮');
                        break;
                    }
                } catch (err) {
                    console.log(`方式1点击发送按钮失败（第${attempt}次）:`, err.message);
                }
                
                // 方式2：如果方式1失败，尝试使用Enter键发送
                if (!sendSuccess) {
                    try {
                        await this.page.keyboard.press('Enter');
                        sendSuccess = true;
                        console.log('方式2：成功使用Enter键发送');
                        break;
                    } catch (err) {
                        console.log(`方式2使用Enter键发送失败（第${attempt}次）:`, err.message);
                    }
                }
                
                // 方式3：如果方式2失败，尝试强制点击
                if (!sendSuccess) {
                    try {
                        const sendBtn = await this.page.$('button[class*="send-btn"], button[class*="send-button"], button[type="submit"]');
                        if (sendBtn) {
                            await sendBtn.click({ force: true });
                            sendSuccess = true;
                            console.log('方式3：成功强制点击发送按钮');
                            break;
                        }
                    } catch (err) {
                        console.log(`方式3强制点击发送按钮失败（第${attempt}次）:`, err.message);
                    }
                }
                
                // 方式4：如果方式3失败，尝试点击输入框附近的发送图标
                if (!sendSuccess) {
                    try {
                        const sendIcon = await this.page.$('[class*="send-icon"], [class*="send"]');
                        if (sendIcon) {
                            await sendIcon.click();
                            sendSuccess = true;
                            console.log('方式4：成功点击发送图标');
                            break;
                        }
                    } catch (err) {
                        console.log(`方式4点击发送图标失败（第${attempt}次）:`, err.message);
                    }
                }
                
                // 方式5：如果方式4失败，尝试模拟Ctrl+Enter发送（某些聊天应用支持）
                if (!sendSuccess) {
                    try {
                        await this.page.keyboard.down('Control');
                        await this.page.keyboard.press('Enter');
                        await this.page.keyboard.up('Control');
                        sendSuccess = true;
                        console.log('方式5：成功使用Ctrl+Enter发送');
                        break;
                    } catch (err) {
                        console.log(`方式5使用Ctrl+Enter发送失败（第${attempt}次）:`, err.message);
                    }
                }
                
                // 增加尝试次数，等待后重试
                attempt++;
                if (attempt <= maxAttempts) {
                    console.log(`等待1秒后重试...`);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
            
            if (!sendSuccess) {
                throw new Error(`所有发送方式均失败，共尝试了 ${maxAttempts} 次`);
            }

            // 等待消息发送完成
            await new Promise(resolve => setTimeout(resolve, 2000));
            
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
                '.mobi', '.epub', '.png', '.jpg', '.jpeg', '.gif', '.webp'
            ];
            const fileExt = path.extname(filePath).toLowerCase();
            if (!supportedTypes.includes(fileExt)) {
                throw new Error(`不支持的文件类型: ${fileExt}`);
            }

            // 查找文件输入元素
            let fileInput = await this.page.$('input[type="file"]');
            if (!fileInput) {
                // 如果直接找不到，尝试点击上传按钮来触发文件选择
                // 先尝试查找上传按钮
                const uploadBtn = await this.page.$('[class*="upload"], [class*="file"], [class*="image"]');
                if (uploadBtn) {
                    await uploadBtn.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    fileInput = await this.page.$('input[type="file"]');
                }
                
                // 如果还是找不到，尝试点击输入框附近的元素
                if (!fileInput) {
                    const inputBox = await this.page.$('textarea.semi-input-textarea');
                    if (inputBox) {
                        // 模拟拖拽文件到输入框
                        await inputBox.uploadFile(filePath);
                        await new Promise(resolve => setTimeout(resolve, 3000));
                        return true;
                    }
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
                console.error('文件上传失败');
                return false;
            }
            console.log('文件上传成功，等待2秒后发送消息...');
            await new Promise(resolve => setTimeout(resolve, 2000));

            // 然后发送消息
            const sendSuccess = await this.sendMessage(message);
            if (!sendSuccess) {
                console.error('消息发送失败');
                return false;
            }
            console.log('消息发送成功，等待5秒获取回复...');
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            return true;
        } catch (error) {
            console.error('发送带文件的消息失败:', error.message);
            return false;
        }
    }

    // 等待并获取AI回复
    async getAIResponse() {
        try {
            console.log('等待AI回复...');
            
            // 等待回复完成，最多等待60秒
            await new Promise(resolve => setTimeout(resolve, 8000));
            
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
                
                // 2. 寻找最长的回复内容（适用于纯文本聊天）
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

// 命令行参数解析
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        image: null,
        question: '图里有什么内容？',
        headless: true // 命令行调用时默认使用无头模式
    };
    
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--image' && i + 1 < args.length) {
            options.image = args[i + 1];
            i++;
        } else if (args[i] === '--question' && i + 1 < args.length) {
            options.question = args[i + 1];
            i++;
        } else if (args[i] === '--headless' && i + 1 < args.length) {
            options.headless = args[i + 1] === 'true';
            i++;
        }
    }
    
    return options;
}

// 测试脚本：上传图片并询问内容
async function main() {
    const bot = new DoubaoChatBot();
    
    try {
        // 解析命令行参数
        const options = parseArgs();
        
        // 检查必要参数
        if (!options.image) {
            console.error('错误：缺少 --image 参数');
            console.error('使用方法：node test_upload_image.js --image <图片路径> [--question <问题>]');
            process.exit(1);
        }
        
        // 确保图片路径存在
        if (!fs.existsSync(options.image)) {
            console.error(`错误：图片不存在: ${options.image}`);
            process.exit(1);
        }
        
        // 初始化浏览器（根据参数决定是否使用无头模式）
        await bot.init(options.headless);
        
        // 检查登录状态
        await bot.checkLoginStatus();
        
        // 上传图片并询问内容
        console.log(`\n=== 测试上传图片 ===`);
        const imagePath = options.image;
        const message = options.question;
        
        // 发送包含图片的消息
        const sendSuccess = await bot.sendMessageWithFile(message, imagePath);
        let response = null;
        let chatHistory = [];
        
        if (sendSuccess) {
            // 获取AI回复
            response = await bot.getAIResponse();
            
            // 提取聊天记录
            chatHistory = await bot.extractChatHistory();
            
            // 保存聊天历史
            const filename = `chat_history_${Date.now()}.json`;
            bot.saveChatHistory(filename);
            console.log(`聊天历史已保存到: ${filename}`);
        }
        
        // 构建输出结果
        const output = {
            success: sendSuccess,
            message: message,
            response: response,
            chatHistory: chatHistory,
            timestamp: new Date().toISOString()
        };
        
        // 直接输出JSON结果，便于Python脚本解析
        console.log(JSON.stringify(output, null, 2));
        
    } catch (error) {
        // 输出错误信息
        const errorOutput = {
            success: false,
            error: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        };
        console.error(JSON.stringify(errorOutput, null, 2));
        process.exit(1);
    } finally {
        // 自动关闭浏览器，不需要手动干预
        await bot.close();
    }
}

// 运行主程序
main();