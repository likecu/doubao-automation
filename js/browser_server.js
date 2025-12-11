const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const http = require('http');
const url = require('url');
const querystring = require('querystring');

class DoubaoBrowserServer {
    constructor() {
        this.browser = null;
        this.pages = new Map(); // 页面ID到页面实例的映射
        this.pageCounter = 0;
        this.server = null;
        this.port = 3000;
        this.isRunning = false;
        this.baseUrl = 'https://www.doubao.com/chat/';
        this.userDataDir = path.join(__dirname, 'user_data');
        this.loginStatusFile = path.join(__dirname, 'login_status.json');
        this.loginStatus = null;
        this.loginExpireTime = 24 * 60 * 60 * 1000; // 登录状态有效期：24小时
    }

    // 初始化浏览器
    async init(headless = false) {
        console.log('正在启动浏览器...');
        
        // 创建用户数据目录
        if (!fs.existsSync(this.userDataDir)) {
            fs.mkdirSync(this.userDataDir);
            console.log('创建用户数据目录:', this.userDataDir);
        } else {
            console.log('使用已有的用户数据目录:', this.userDataDir);
        }
        
        this.browser = await puppeteer.launch({
            headless: headless,
            defaultViewport: null,
            slowMo: 100, // 放慢操作速度，方便调试
            devtools: true, // 打开开发者工具，方便调试
            args: [
                '--start-maximized',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions-except=',
                '--disable-plugins-except=',
                '--disable-popup-blocking',
                '--disable-infobars',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--ignore-certificate-errors',
                '--ignore-certificate-errors-spki-list'
            ],
            userDataDir: this.userDataDir,
            ignoreHTTPSErrors: true,
            dumpio: true // 输出浏览器进程的控制台日志
        });

        console.log('浏览器启动成功！');
        console.log('浏览器模式:', headless ? '无头模式' : '有头模式');
        this.isRunning = true;
        this.headless = headless;
        
        // 加载登录状态
        this.loadLoginStatus();
    }
    
    // 加载登录状态
    loadLoginStatus() {
        try {
            if (fs.existsSync(this.loginStatusFile)) {
                const statusData = fs.readFileSync(this.loginStatusFile, 'utf8');
                this.loginStatus = JSON.parse(statusData);
                console.log('已加载登录状态:', this.loginStatus);
                
                // 检查登录状态是否过期
                if (this.checkLoginStatusExpired()) {
                    console.log('登录状态已过期');
                    this.clearLoginStatus();
                } else {
                    console.log('登录状态有效，有效期至:', new Date(this.loginStatus.expireTime).toLocaleString());
                }
            } else {
                console.log('未找到登录状态文件');
                this.loginStatus = null;
            }
        } catch (error) {
            console.error('加载登录状态失败:', error.message);
            this.loginStatus = null;
        }
    }
    
    // 保存登录状态
    saveLoginStatus() {
        try {
            const now = Date.now();
            this.loginStatus = {
                loginTime: now,
                expireTime: now + this.loginExpireTime,
                lastCheckTime: now,
                status: 'logged_in'
            };
            
            fs.writeFileSync(this.loginStatusFile, JSON.stringify(this.loginStatus, null, 2), 'utf8');
            console.log('已保存登录状态，有效期至:', new Date(this.loginStatus.expireTime).toLocaleString());
        } catch (error) {
            console.error('保存登录状态失败:', error.message);
        }
    }
    
    // 检查登录状态是否过期
    checkLoginStatusExpired() {
        if (!this.loginStatus) {
            return true;
        }
        
        const now = Date.now();
        return now > this.loginStatus.expireTime;
    }
    
    // 更新登录状态
    updateLoginStatus() {
        if (this.loginStatus) {
            this.loginStatus.lastCheckTime = Date.now();
            // 可以选择延长登录状态有效期
            // this.loginStatus.expireTime = Date.now() + this.loginExpireTime;
            this.saveLoginStatus();
        }
    }
    
    // 清除登录状态
    clearLoginStatus() {
        try {
            if (fs.existsSync(this.loginStatusFile)) {
                fs.unlinkSync(this.loginStatusFile);
                console.log('已清除登录状态');
            }
        } catch (error) {
            console.error('清除登录状态失败:', error.message);
        }
        this.loginStatus = null;
    }
    
    // 检查是否需要登录或处理验证码
    async checkLoginOrCaptcha(page) {
        try {
            console.log('检查登录状态和验证码...');
            
            // 获取页面文本内容，修复trim()错误
            const pageText = await page.evaluate(() => {
                try {
                    return document.body.textContent.trim();
                } catch (error) {
                    return document.body.textContent || '';
                }
            });
            
            console.log('页面文本预览:', pageText.substring(0, 150) + '...');
            
            // 检查是否需要登录（更精确的检测）
            const needLogin = 
                pageText.includes('登录') || 
                pageText.includes('Login') || 
                pageText.includes('sign in') ||
                pageText.includes('请登录') ||
                pageText.includes('登录后使用') ||
                pageText.includes('登录账号') ||
                pageText.includes('登录才能') ||
                pageText.includes('登录查看') ||
                pageText.includes('登录使用') ||
                pageText.includes('登录以');
            
            // 检查是否有验证码
            const hasCaptcha = 
                pageText.includes('验证码') || 
                pageText.includes('captcha') || 
                pageText.includes('verification') ||
                pageText.includes('验证') ||
                pageText.includes('verify');
            
            // 检查是否有滑块验证
            const hasSlider = 
                await page.$('[class*="slider"]') !== null || 
                await page.$('[class*="captcha"]') !== null ||
                await page.$('[class*="verify"]') !== null ||
                await page.$('[class*="slide"]') !== null ||
                await page.$('[class*="validate"]') !== null;
            
            // 检查登录按钮是否存在（更全面的检测，包括右上角登录按钮）
            const loginButtonExists = await page.evaluate(() => {
                // 检测多种可能的登录按钮
                const loginSelectors = [
                    // 按优先级排序，更可能的登录按钮在前
                    'button[class*="login-btn"]',
                    'a[class*="login-btn"]',
                    'button[class*="login-button"]',
                    'a[class*="login-button"]',
                    '.header-login-btn', // 右上角登录按钮
                    '.top-login-btn', // 顶部登录按钮
                    '.nav-login-btn', // 导航栏登录按钮
                    '.right-login-btn', // 右侧登录按钮
                    '[class*="login"]',
                    '[href*="login"]',
                    '[href*="Login"]',
                    '[id*="login"]',
                    '[id*="Login"]',
                    '[aria-label*="login"]',
                    '[aria-label*="Login"]',
                    '.login',
                    '.login-btn',
                    '#login',
                    '#Login'
                ];
                
                // 检查是否有任何登录按钮存在
                for (const selector of loginSelectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        
                        // 过滤掉不可见的元素
                        const visibleElements = Array.from(elements).filter(el => {
                            const style = window.getComputedStyle(el);
                            // 检查元素是否可见
                            const isVisible = style.display !== 'none' && 
                                           style.visibility !== 'hidden' &&
                                           style.opacity !== '0' &&
                                           el.offsetWidth > 0 &&
                                           el.offsetHeight > 0;
                            
                            // 检查元素是否在视口内
                            const rect = el.getBoundingClientRect();
                            const isInViewport = rect.top < window.innerHeight && 
                                             rect.bottom > 0 &&
                                             rect.left < window.innerWidth &&
                                             rect.right > 0;
                            
                            return isVisible && isInViewport;
                        });
                        
                        if (visibleElements.length > 0) {
                            console.log('找到登录按钮:', selector, '数量:', visibleElements.length);
                            return true;
                        }
                    } catch (error) {
                        // 忽略无效的选择器
                        continue;
                    }
                }
                
                // 使用JavaScript文本内容检测，替换:contains()选择器
                const allButtonsAndLinks = Array.from(document.querySelectorAll('button, a'));
                const hasLoginText = allButtonsAndLinks.some(el => {
                    try {
                        const text = el.textContent.toLowerCase();
                        return text.includes('登录') || text.includes('login') || text.includes('sign in');
                    } catch (error) {
                        return false;
                    }
                });
                
                if (hasLoginText) {
                    console.log('找到包含登录文本的按钮或链接');
                }
                
                return hasLoginText;
            });
            
            // 检查页面中是否有登录相关的元素
            const hasLoginElements = 
                await page.$('button[class*="login"]') !== null ||
                await page.$('a[href*="login"]') !== null ||
                await page.$('[class*="login"]') !== null ||
                await page.$('input[type="text"]') !== null && 
                await page.$('input[type="password"]') !== null ||
                await page.$('form[action*="login"]') !== null ||
                await page.$('form[method="post"]') !== null && 
                (await page.$('[name*="username"]') !== null || 
                 await page.$('[name*="email"]') !== null || 
                 await page.$('[name*="password"]') !== null);
            
            // 检查是否为登录页面（通过URL）
            const currentUrl = page.url();
            const isLoginUrl = 
                currentUrl.includes('login') || 
                currentUrl.includes('Login') ||
                currentUrl.includes('signin') ||
                currentUrl.includes('SignIn');
            
            // 检查是否有用户信息元素（已登录的特征）
            const hasUserInfo = await page.evaluate(() => {
                const userInfoSelectors = [
                    '[class*="avatar"]',
                    '[class*="username"]',
                    '[id*="user"]',
                    '[aria-label*="user"]',
                    '[class*="profile"]',
                    '[id*="profile"]',
                    '[href*="profile"]',
                    '[class*="account"]',
                    '[id*="account"]',
                    '[href*="account"]'
                ];
                
                for (const selector of userInfoSelectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        const visibleElements = Array.from(elements).filter(el => {
                            const style = window.getComputedStyle(el);
                            return style.display !== 'none' && style.visibility !== 'hidden';
                        });
                        if (visibleElements.length > 0) {
                            return true;
                        }
                    } catch (error) {
                        continue;
                    }
                }
                return false;
            });
            
            // 综合判断：需要满足多个条件才能确定登录状态
            let finalNeedLogin = false;
            
            // 如果是登录URL，肯定需要登录
            if (isLoginUrl) {
                finalNeedLogin = true;
            } 
            // 如果有登录按钮且没有用户信息，需要登录
            else if (loginButtonExists && !hasUserInfo) {
                finalNeedLogin = true;
            }
            // 如果页面包含登录相关文本且没有用户信息，需要登录
            else if (needLogin && !hasUserInfo) {
                finalNeedLogin = true;
            }
            // 如果有登录表单元素，需要登录
            else if (hasLoginElements && !hasUserInfo) {
                finalNeedLogin = true;
            }
            // 如果没有用户信息，且页面文本包含登录相关内容，需要登录
            else if (!hasUserInfo && (needLogin || loginButtonExists || hasLoginElements)) {
                finalNeedLogin = true;
            }
            // 其他情况，不需要登录
            else {
                finalNeedLogin = false;
            }
            
            // 更新登录状态：如果不需要登录且有用户信息，说明登录状态有效
            if (!finalNeedLogin && hasUserInfo) {
                this.updateLoginStatus();
                console.log('登录状态有效，已更新最后检查时间');
            } 
            // 如果需要登录，说明登录状态无效，清除登录状态
            else if (finalNeedLogin) {
                this.clearLoginStatus();
                console.log('登录状态无效，已清除登录状态');
            }
            
            // 添加调试信息
            console.log('登录检测结果:', { 
                needLogin: finalNeedLogin, 
                hasCaptcha, 
                hasSlider, 
                loginButtonExists, 
                hasLoginElements,
                isLoginUrl,
                hasUserInfo,
                originalNeedLogin: needLogin,
                loginStatus: this.loginStatus ? '有效' : '无效'
            });
            
            return { needLogin: finalNeedLogin, hasCaptcha, hasSlider };
            
        } catch (error) {
            console.error('检查登录和验证码失败:', error.message);
            // 失败时，默认需要登录，确保安全
            return { needLogin: true, hasCaptcha: false, hasSlider: false };
        }
    }
    
    // 处理登录和验证码
    async handleLoginAndCaptcha(page) {
        try {
            // 检查是否需要登录或验证码
            const { needLogin } = await this.checkLoginOrCaptcha(page);
            
            // 如果不需要登录，直接返回
            if (!needLogin) {
                console.log('不需要登录，直接使用');
                return true;
            }
            
            console.log('需要登录，正在处理...');
            
            // 如果是无头模式，需要重启浏览器为有头模式
            if (this.headless) {
                console.log('切换到有头模式，显示登录二维码...');
                
                // 关闭当前浏览器
                await this.browser.close();
                this.browser = null;
                
                // 重新启动为有头模式
                await this.init(false);
                
                // 创建新页面，替换原页面
                const newPage = await this.browser.newPage();
                
                // 复制原页面的反检测措施
                await this.addAntiDetection(newPage);
                
                // 导航到豆包页面
                await newPage.goto(this.baseUrl, {
                    waitUntil: 'networkidle2',
                    timeout: 60000
                });
                
                // 返回新页面，让后续逻辑处理
                return newPage;
            }
            
            // 已经是有头模式，尝试自动点击登录按钮
            console.log('=== 正在自动处理登录流程 ===');
            console.log('1. 尝试查找并点击登录按钮');
            
            // 查找并点击登录按钮
            const loginButtonSelectors = [
                'button[class*="login"]',
                'a[href*="login"]',
                '[class*="login"]',
                'button:contains("登录")',
                'a:contains("登录")'
            ];
            
            let loginButtonFound = false;
            for (const selector of loginButtonSelectors) {
                try {
                    const button = await page.$(selector);
                    if (button) {
                        console.log(`找到登录按钮: ${selector}`);
                        await button.click();
                        loginButtonFound = true;
                        break;
                    }
                } catch (error) {
                    console.log(`尝试选择器 ${selector} 失败: ${error.message}`);
                    continue;
                }
            }
            
            // 如果没有找到登录按钮，尝试通过文本内容查找
            if (!loginButtonFound) {
                console.log('尝试通过文本内容查找登录按钮...');
                const loginButtons = await page.evaluate(() => {
                    const buttons = Array.from(document.querySelectorAll('button, a'));
                    return buttons.filter(btn => {
                        const text = btn.textContent.toLowerCase();
                        return text.includes('登录') || text.includes('login');
                    });
                });
                
                if (loginButtons.length > 0) {
                    console.log('找到登录按钮，尝试点击...');
                    // 找到第一个登录按钮并点击
                    const buttonElement = await page.$$('button, a');
                    for (const btn of buttonElement) {
                        const text = await page.evaluate(el => el.textContent.toLowerCase(), btn);
                        if (text.includes('登录') || text.includes('login')) {
                            await btn.click();
                            loginButtonFound = true;
                            break;
                        }
                    }
                }
            }
            
            if (loginButtonFound) {
                console.log('已点击登录按钮，等待登录界面出现...');
                // 等待可能出现的弹出框
                await new Promise(resolve => setTimeout(resolve, 3000));
            } else {
                console.log('未找到登录按钮，请手动点击登录');
            }
            
            // 显示登录提示
            console.log('=== 请在浏览器中完成以下操作 ===');
            console.log('1. 如有登录弹出框，点击右上角获取二维码');
            console.log('2. 请扫描二维码登录');
            console.log('3. 扫描成功后，程序将自动继续');
            console.log('=== 操作完成后，程序将自动继续 ===');
            
            // 等待用户完成登录，改进检测逻辑
            let loginCompleted = false;
            const maxAttempts = 60; // 最多尝试60次，每次5秒，总共5分钟
            let attempt = 0;
            
            while (!loginCompleted && attempt < maxAttempts) {
                attempt++;
                console.log(`登录状态检查，第 ${attempt} 次尝试...`);
                
                try {
                    // 1. 检查是否存在用户信息（头像、用户名等）- 最可靠的登录标志
                    const hasUserInfo = await page.evaluate(() => {
                        const userSelectors = [
                            '[class*="avatar"]',
                            '[class*="username"]',
                            '[class*="user-info"]',
                            '[class*="profile"]',
                            '[class*="account"]',
                            '[class*="user-avatar"]',
                            '[class*="user-profile"]'
                        ];
                        return userSelectors.some(selector => {
                            const element = document.querySelector(selector);
                            return element && window.getComputedStyle(element).display !== 'none';
                        });
                    });
                    
                    if (hasUserInfo) {
                        console.log('检测到用户信息，登录成功！');
                        loginCompleted = true;
                        break;
                    }
                    
                    // 2. 检查页面是否还有登录相关元素
                    const hasLoginElements = await page.evaluate(() => {
                        const loginKeywords = ['登录', 'Login', 'sign in', '请登录'];
                        const pageText = document.body.textContent.toLowerCase();
                        return loginKeywords.some(keyword => pageText.includes(keyword.toLowerCase()));
                    });
                    
                    if (!hasLoginElements) {
                        console.log('页面中没有登录相关元素，登录成功！');
                        loginCompleted = true;
                        break;
                    }
                    
                    // 3. 检查是否有聊天历史或已加载的对话内容
                    const hasChatHistory = await page.evaluate(() => {
                        const chatSelectors = [
                            '[class*="message-list"]',
                            '[class*="chat-list"]',
                            '[class*="conversation"]',
                            '[class*="history"]'
                        ];
                        return chatSelectors.some(selector => {
                            const element = document.querySelector(selector);
                            return element && element.children.length > 0;
                        });
                    });
                    
                    if (hasChatHistory) {
                        console.log('检测到聊天历史，登录成功！');
                        loginCompleted = true;
                        break;
                    }
                    
                    // 4. 检查是否能够正常输入消息
                    const canInputMessage = await page.$('textarea.semi-input-textarea:not([disabled])') !== null &&
                                         await page.$('button[class*="send"]:not([disabled])') !== null;
                    
                    if (canInputMessage) {
                        console.log('检测到可输入的消息框和发送按钮，登录成功！');
                        loginCompleted = true;
                        break;
                    }
                    
                    console.log('等待用户扫码登录...');
                    // 截取当前页面状态用于调试
                    await page.screenshot({ path: `login_check_${attempt}.png` });
                    // 等待5秒后重试，给用户足够时间扫码
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    
                } catch (error) {
                    console.error('登录状态检查出错:', error.message);
                    console.log('5秒后重试...');
                    await new Promise(resolve => setTimeout(resolve, 5000));
                }
            }
            
            if (loginCompleted) {
                console.log('用户已完成登录，继续执行...');
                // 保存登录状态
                this.saveLoginStatus();
                return true;
            } else {
                console.error('登录超时，已尝试60次，每次5秒，总共5分钟');
                console.error('请检查浏览器中是否已完成登录');
                return false;
            }
            
        } catch (error) {
            console.error('处理登录和验证码失败:', error.message);
            return false;
        }
    }

    // 创建新页面
    async createPage() {
        if (!this.browser) {
            throw new Error('浏览器未初始化');
        }

        const pageId = ++this.pageCounter;
        let page = await this.browser.newPage();
        
        // 添加反检测措施
        await this.addAntiDetection(page);
        
        // 设置真实的用户代理
        await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        
        // 导航到豆包聊天页面
        console.log(`页面 ${pageId} 导航到豆包聊天页面...`);
        await page.goto(this.baseUrl, {
            waitUntil: 'networkidle2',
            timeout: 60000
        });

        // 检查并处理登录和验证码
        const result = await this.handleLoginAndCaptcha(page);
        
        // 如果返回的是新页面（无头模式切换到有头模式），使用新页面
        if (result !== true && result !== false) {
            // 关闭旧页面
            await page.close();
            // 使用新页面
            page = result;
        } else if (result === false) {
            // 处理失败，关闭页面
            await page.close();
            console.error(`页面 ${pageId} 创建失败，处理登录和验证码失败`);
            return null;
        }

        try {
            // 等待页面加载完成
            await page.waitForSelector('textarea.semi-input-textarea', {
                timeout: 30000
            });

            this.pages.set(pageId, page);
            console.log(`页面 ${pageId} 创建成功！`);
            return pageId;
        } catch (error) {
            console.error(`页面 ${pageId} 等待输入框失败:`, error.message);
            await page.close();
            return null;
        }
    }

    // 添加反检测措施
    async addAntiDetection(page) {
        await page.evaluateOnNewDocument(() => {
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
    }

    // 关闭指定页面
    async closePage(pageId) {
        const page = this.pages.get(pageId);
        if (page) {
            await page.close();
            this.pages.delete(pageId);
            console.log(`页面 ${pageId} 已关闭`);
            return true;
        }
        return false;
    }

    // 关闭所有页面
    async closeAllPages() {
        for (const [pageId, page] of this.pages) {
            await page.close();
        }
        this.pages.clear();
        this.pageCounter = 0;
        console.log('所有页面已关闭');
    }

    // 发送文本消息
    async sendMessage(pageId, message) {
        const page = this.pages.get(pageId);
        if (!page) {
            throw new Error(`页面 ${pageId} 不存在`);
        }

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
            
            console.log(`页面 ${pageId} 发送消息: ${message}`);
            
            // 定位输入框
            const inputBox = await page.$('textarea.semi-input-textarea');
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
                console.log(`页面 ${pageId} 尝试发送消息，第 ${attempt} 次尝试`);
                
                // 方式1：使用包含选择器等待按钮可见并点击
                try {
                    await page.waitForSelector('button[class*="send-btn"], button[class*="send-button"], button[type="submit"]', {
                        visible: true,
                        timeout: 5000
                    });
                    const sendBtn = await page.$('button[class*="send-btn"]:not([class*="disabled"], [disabled]), button[class*="send-button"]:not([class*="disabled"], [disabled]), button[type="submit"]:not([class*="disabled"], [disabled])');
                    if (sendBtn) {
                        await sendBtn.click();
                        sendSuccess = true;
                        console.log(`页面 ${pageId} 方式1：成功点击发送按钮`);
                        break;
                    }
                } catch (err) {
                    console.log(`页面 ${pageId} 方式1点击发送按钮失败（第${attempt}次）:`, err.message);
                }
                
                // 方式2：如果方式1失败，尝试使用Enter键发送
                if (!sendSuccess) {
                    try {
                        await page.keyboard.press('Enter');
                        sendSuccess = true;
                        console.log(`页面 ${pageId} 方式2：成功使用Enter键发送`);
                        break;
                    } catch (err) {
                        console.log(`页面 ${pageId} 方式2使用Enter键发送失败（第${attempt}次）:`, err.message);
                    }
                }
                
                // 增加尝试次数，等待后重试
                attempt++;
                if (attempt <= maxAttempts) {
                    console.log(`页面 ${pageId} 等待1秒后重试...`);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
            
            if (!sendSuccess) {
                throw new Error(`所有发送方式均失败，共尝试了 ${maxAttempts} 次`);
            }

            // 等待消息发送完成
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            console.log(`页面 ${pageId} 消息发送成功！`);
            return true;
        } catch (error) {
            console.error(`页面 ${pageId} 发送消息失败:`, error.message);
            throw error;
        }
    }

    // 文件上传功能
    async uploadFile(pageId, filePath) {
        const page = this.pages.get(pageId);
        if (!page) {
            throw new Error(`页面 ${pageId} 不存在`);
        }

        try {
            console.log(`页面 ${pageId} 上传文件: ${filePath}`);
            
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
            let fileInput = await page.$('input[type="file"]');
            if (!fileInput) {
                // 如果直接找不到，尝试点击上传按钮来触发文件选择
                // 先尝试查找上传按钮
                const uploadBtn = await page.$('[class*="upload"], [class*="file"], [class*="image"]');
                if (uploadBtn) {
                    await uploadBtn.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    fileInput = await page.$('input[type="file"]');
                }
                
                // 如果还是找不到，尝试点击输入框附近的元素
                if (!fileInput) {
                    const inputBox = await page.$('textarea.semi-input-textarea');
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
            
            console.log(`页面 ${pageId} 文件上传成功！`);
            return true;
        } catch (error) {
            console.error(`页面 ${pageId} 上传文件失败:`, error.message);
            throw error;
        }
    }

    // 发送包含文件的消息
    async sendMessageWithFile(pageId, message, filePath) {
        const page = this.pages.get(pageId);
        if (!page) {
            throw new Error(`页面 ${pageId} 不存在`);
        }

        try {
            // 先上传文件
            const uploadSuccess = await this.uploadFile(pageId, filePath);
            if (!uploadSuccess) {
                throw new Error('文件上传失败');
            }
            console.log(`页面 ${pageId} 文件上传成功，等待2秒后发送消息...`);
            await new Promise(resolve => setTimeout(resolve, 2000));

            // 然后发送消息
            const sendSuccess = await this.sendMessage(pageId, message);
            if (!sendSuccess) {
                throw new Error('消息发送失败');
            }
            console.log(`页面 ${pageId} 消息发送成功，等待5秒获取回复...`);
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            return true;
        } catch (error) {
            console.error(`页面 ${pageId} 发送带文件的消息失败:`, error.message);
            throw error;
        }
    }

    // 等待并获取AI回复
    async getAIResponse(pageId) {
        const page = this.pages.get(pageId);
        if (!page) {
            throw new Error(`页面 ${pageId} 不存在`);
        }

        try {
            console.log(`页面 ${pageId} 等待AI回复...`);
            
            // 等待回复完成，最多等待60秒
            await new Promise(resolve => setTimeout(resolve, 8000));
            
            // 截取当前页面状态，用于调试
            await page.screenshot({ path: `page_${pageId}_debug.png` });
            console.log(`页面 ${pageId} 已截图，保存为 page_${pageId}_debug.png`);
            
            // 先尝试提取聊天记录，然后从中获取AI回复
            console.log(`页面 ${pageId} 尝试先提取聊天记录，再获取AI回复`);
            const chatHistory = await this.extractChatHistory(pageId);
            
            // 从聊天记录中查找最新的AI回复
            if (chatHistory && chatHistory.length > 0) {
                // 1. 寻找包含编辑分享的完整回复（适用于图片OCR和复杂问题）
                for (let i = chatHistory.length - 1; i >= 0; i--) {
                    const msg = chatHistory[i];
                    if (msg.content && msg.content.includes('编辑分享')) {
                        const cleanResponse = msg.content.split('编辑分享')[0].trim();
                        if (cleanResponse.length > 20) {
                            console.log(`页面 ${pageId} 从聊天记录中成功获取AI回复`);
                            console.log(`页面 ${pageId} AI回复: ${cleanResponse}`);
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
                    console.log(`页面 ${pageId} 从聊天记录中获取到AI回复`);
                    console.log(`页面 ${pageId} AI回复: ${longestResponse}`);
                    return longestResponse;
                }
                
                // 3. 寻找包含问候语的回复（适用于纯文本聊天）
                for (const msg of chatHistory) {
                    if (msg.content && (msg.content.includes('你好') || 
                                        msg.content.includes('您好') ||
                                        msg.content.includes('有什么可以帮到你') ||
                                        msg.content.includes('可以随时找我'))) {
                        const cleanResponse = msg.content.split('编辑分享')[0].trim();
                        console.log(`页面 ${pageId} 从聊天记录中获取到AI回复`);
                        console.log(`页面 ${pageId} AI回复: ${cleanResponse}`);
                        return cleanResponse;
                    }
                }
            }

            console.log(`页面 ${pageId} 未获取到有效的AI回复`);
            return null;
        } catch (error) {
            console.error(`页面 ${pageId} 获取AI回复失败:`, error.message);
            throw error;
        }
    }

    // 提取完整聊天记录
    async extractChatHistory(pageId) {
        const page = this.pages.get(pageId);
        if (!page) {
            throw new Error(`页面 ${pageId} 不存在`);
        }

        try {
            console.log(`页面 ${pageId} 提取聊天记录...`);
            
            // 获取聊天记录容器，增加更多选择器
            const messageList = await page.$('[class*="message-list"]') || 
                              await page.$('[class*="chat-list"]') ||
                              await page.$('[role="list"]') ||
                              await page.$('[class*="ant-list"]') ||
                              await page.$('body');
            if (!messageList) {
                throw new Error('未找到聊天记录容器');
            }

            // 获取所有消息元素，增加更多选择器
            const messages = await messageList.$$('[class*="message-item"], [class*="message-box"], [class*="message"], [class*="ant-list-item"], [role="listitem"]');
            
            // 如果没有找到消息元素，尝试获取整个页面的文本内容作为备选
            if (messages.length === 0) {
                console.log(`页面 ${pageId} 未找到消息元素，尝试获取页面文本`);
                const pageText = await page.evaluate(el => el.textContent.trim(), messageList);
                
                // 检查是否需要登录
                if (pageText.includes('登录') || pageText.includes('Login') || pageText.includes('sign in')) {
                    console.log(`页面 ${pageId} 需要登录`);
                    return [{ 
                        type: 'system', 
                        content: '需要登录才能使用豆包功能，请在浏览器中手动登录', 
                        timestamp: new Date().toISOString() 
                    }];
                }
                
                // 检查是否有错误提示
                if (pageText.includes('错误') || pageText.includes('Error')) {
                    console.log(`页面 ${pageId} 显示错误信息: ${pageText}`);
                    return [{ 
                        type: 'error', 
                        content: pageText, 
                        timestamp: new Date().toISOString() 
                    }];
                }
                
                // 其他情况，返回页面文本
                return [{ 
                    type: 'page_text', 
                    content: pageText, 
                    timestamp: new Date().toISOString() 
                }];
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
                        className.includes('self') ||
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
                    console.error(`页面 ${pageId} 提取单条消息失败:`, err.message);
                }
            }

            console.log(`页面 ${pageId} 提取到 ${history.length} 条消息`);
            return history;
        } catch (error) {
            console.error(`页面 ${pageId} 提取聊天记录失败:`, error.message);
            // 失败时返回更友好的错误信息
            return [{ 
                type: 'error', 
                content: `提取聊天记录失败: ${error.message}`, 
                timestamp: new Date().toISOString() 
            }];
        }
    }

    // 处理HTTP请求
    async handleRequest(req, res) {
        // 设置CORS头
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

        // 处理OPTIONS请求
        if (req.method === 'OPTIONS') {
            res.writeHead(200);
            res.end();
            return;
        }

        // 解析请求URL和参数
        const parsedUrl = url.parse(req.url);
        const pathname = parsedUrl.pathname;
        
        // 处理GET请求
        if (req.method === 'GET') {
            const query = querystring.parse(parsedUrl.query);
            await this.handleGetRequest(pathname, query, res);
        }
        // 处理POST请求
        else if (req.method === 'POST') {
            let body = '';
            req.on('data', chunk => {
                body += chunk.toString();
            });
            req.on('end', async () => {
                const postData = JSON.parse(body);
                await this.handlePostRequest(pathname, postData, res);
            });
        }
        else {
            res.writeHead(405, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: false, error: 'Method Not Allowed' }));
        }
    }

    // 处理GET请求
    async handleGetRequest(pathname, query, res) {
        try {
            switch (pathname) {
                case '/status':
                    // 返回服务状态
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: true,
                        running: this.isRunning,
                        browserOpen: !!this.browser,
                        pageCount: this.pages.size,
                        pages: Array.from(this.pages.keys())
                    }));
                    break;

                case '/createPage':
                    // 创建新页面
                    const pageId = await this.createPage();
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: true,
                        pageId: pageId
                    }));
                    break;

                case '/closePage':
                    // 关闭指定页面
                    const pageIdToClose = parseInt(query.pageId);
                    const closed = await this.closePage(pageIdToClose);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: closed
                    }));
                    break;

                case '/closeAllPages':
                    // 关闭所有页面
                    await this.closeAllPages();
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: true
                    }));
                    break;

                default:
                    res.writeHead(404, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: false, error: 'Not Found' }));
            }
        } catch (error) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: false, error: error.message }));
        }
    }

    // 处理POST请求
    async handlePostRequest(pathname, postData, res) {
        try {
            switch (pathname) {
                case '/sendMessage':
                    // 发送文本消息
                    const { pageId: msgPageId, message } = postData;
                    const sendSuccess = await this.sendMessage(msgPageId, message);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: sendSuccess
                    }));
                    break;

                case '/uploadFile':
                    // 上传文件
                    const { pageId: uploadPageId, filePath } = postData;
                    const uploadSuccess = await this.uploadFile(uploadPageId, filePath);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: uploadSuccess
                    }));
                    break;

                case '/sendMessageWithFile':
                    // 发送包含文件的消息
                    const { pageId: fileMsgPageId, message: fileMsg, filePath: fileMsgPath } = postData;
                    const fileSendSuccess = await this.sendMessageWithFile(fileMsgPageId, fileMsg, fileMsgPath);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: fileSendSuccess
                    }));
                    break;

                case '/getAIResponse':
                    // 获取AI回复
                    const { pageId: responsePageId } = postData;
                    const response = await this.getAIResponse(responsePageId);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: true,
                        response: response
                    }));
                    break;

                case '/extractChatHistory':
                    // 提取聊天记录
                    const { pageId: historyPageId } = postData;
                    const history = await this.extractChatHistory(historyPageId);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: true,
                        chatHistory: history
                    }));
                    break;

                case '/ocr':
                    // 执行OCR识别
                    const { pageId: ocrPageId, imagePath, question } = postData;
                    
                    // 发送包含图片的消息
                    const ocrSendSuccess = await this.sendMessageWithFile(ocrPageId, question, imagePath);
                    let ocrResponse = null;
                    let chatHistory = [];
                    
                    if (ocrSendSuccess) {
                        // 获取AI回复
                        ocrResponse = await this.getAIResponse(ocrPageId);
                        
                        // 提取聊天记录
                        chatHistory = await this.extractChatHistory(ocrPageId);
                    }
                    
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: ocrSendSuccess,
                        message: question,
                        response: ocrResponse,
                        chatHistory: chatHistory,
                        timestamp: new Date().toISOString()
                    }));
                    break;

                case '/textChat':
                    // 纯文本聊天
                    const { pageId: textChatPageId, message: textMsg } = postData;
                    
                    // 发送文本消息
                    const textSendSuccess = await this.sendMessage(textChatPageId, textMsg);
                    let textResponse = null;
                    let textChatHistory = [];
                    
                    if (textSendSuccess) {
                        // 获取AI回复
                        textResponse = await this.getAIResponse(textChatPageId);
                        
                        // 提取聊天记录
                        textChatHistory = await this.extractChatHistory(textChatPageId);
                    }
                    
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: textSendSuccess,
                        message: textMsg,
                        response: textResponse,
                        chatHistory: textChatHistory,
                        timestamp: new Date().toISOString()
                    }));
                    break;

                default:
                    res.writeHead(404, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: false, error: 'Not Found' }));
            }
        } catch (error) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: false, error: error.message }));
        }
    }

    // 启动HTTP服务器
    async startServer(port = 3000) {
        this.port = port;
        
        // 初始化浏览器
        await this.init(false); // 默认使用有头模式，方便用户扫码登录
        
        // 创建HTTP服务器
        this.server = http.createServer((req, res) => {
            this.handleRequest(req, res);
        });
        
        // 启动服务器
        this.server.listen(this.port, () => {
            this.isRunning = true;
            console.log(`\n=== 豆包浏览器服务已启动 ===`);
            console.log(`服务地址: http://localhost:${this.port}`);
            console.log(`\n可用API:`);
            console.log(`GET  /status            - 获取服务状态`);
            console.log(`GET  /createPage        - 创建新页面`);
            console.log(`GET  /closePage?pageId=1 - 关闭指定页面`);
            console.log(`GET  /closeAllPages     - 关闭所有页面`);
            console.log(`POST /sendMessage       - 发送文本消息`);
            console.log(`POST /uploadFile        - 上传文件`);
            console.log(`POST /sendMessageWithFile - 发送包含文件的消息`);
            console.log(`POST /getAIResponse     - 获取AI回复`);
            console.log(`POST /extractChatHistory - 提取聊天记录`);
            console.log(`POST /ocr               - 执行OCR识别`);
            console.log(`POST /textChat          - 纯文本聊天`);
            console.log(`\n按 Ctrl+C 停止服务`);
        });
        
        // 处理服务器错误
        this.server.on('error', (error) => {
            console.error('服务器错误:', error.message);
            this.isRunning = false;
        });
        
        // 处理SIGINT信号（Ctrl+C）
        process.on('SIGINT', async () => {
            console.log('\n接收到停止信号，正在关闭服务...');
            await this.stop();
        });
    }

    // 停止服务
    async stop() {
        console.log('正在停止服务...');
        
        // 关闭所有页面
        await this.closeAllPages();
        
        // 关闭浏览器
        if (this.browser) {
            await this.browser.close();
            this.browser = null;
            console.log('浏览器已关闭');
        }
        
        // 关闭HTTP服务器
        if (this.server) {
            this.server.close();
            this.server = null;
            console.log('HTTP服务器已关闭');
        }
        
        this.isRunning = false;
        console.log('服务已停止');
        process.exit(0);
    }
}

// 启动服务
async function main() {
    const server = new DoubaoBrowserServer();
    await server.startServer(3000);
}

main();
