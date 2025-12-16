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
        
        // 检查并创建用户数据目录（如果不存在）
        if (!fs.existsSync(this.userDataDir)) {
            fs.mkdirSync(this.userDataDir);
            console.log('创建用户数据目录:', this.userDataDir);
        } else {
            console.log('使用已有的用户数据目录:', this.userDataDir);
        }
        
        // 重写浏览器启动配置，避免窗口自动置顶
        this.browser = await puppeteer.launch({
            headless: headless,
            defaultViewport: null,
            // slowMo: 100, // 加快操作速度，移除调试延迟
            devtools: false, // 关闭开发者工具，加快速度
            // 完全自定义浏览器启动参数，避免任何可能导致窗口置顶的设置
            args: [
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
                '--ignore-certificate-errors-spki-list',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--window-size=1024,768', // 指定窗口大小
                '--window-position=100,100', // 明确指定窗口位置，避免自动置顶
                '--restore-last-session=false', // 不恢复上次会话
                '--disable-default-apps', // 禁用默认应用
                '--disable-component-extensions-with-background-pages', // 禁用带后台页面的组件扩展
                '--disable-hang-monitor', // 禁用挂起监控
                '--disable-prompt-on-repost', // 禁用重发提示
                '--disable-sync', // 禁用同步
                '--disable-translate' // 禁用翻译
            ],
            // 忽略更多可能导致窗口置顶的默认参数
            ignoreDefaultArgs: [
                '--enable-automation',
                '--start-maximized',
                '--app'
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
                pageText.includes('登录以') ||
                pageText.includes('请选择所有符合上文描述的图片') ||
                pageText.includes('拖拽到下方');
            
            // 增强的验证码检测
            // 1. 文本检测 - 只检测明确的验证码关键词
            const hasCaptchaText = 
                pageText.includes('验证码') || 
                pageText.includes('captcha') || 
                pageText.includes('安全验证') ||
                pageText.includes('人机验证') ||
                pageText.includes('滑块验证') ||
                pageText.includes('图形验证') ||
                pageText.includes('请选择所有符合上文描述的图片') ||
                pageText.includes('拖拽到下方');
            
            // 2. 元素检测 - 检查各种验证码相关元素
            const captchaElements = await page.evaluate(() => {
                // 检测多种可能的验证码元素，但更严格
                const captchaSelectors = [
                    '[class*="captcha"]',
                    '[id*="captcha"]',
                    'img[src*="captcha"]',
                    'canvas[id*="captcha"]',
                    'canvas[class*="captcha"]',
                    '[aria-label*="captcha"]',
                    '[role*="captcha"]',
                    // 滑块验证码相关元素
                    '[class*="slider-captcha"]',
                    '[class*="verify-slider"]',
                    '[class*="captcha-slider"]',
                    '[id*="slider-captcha"]',
                    '[id*="verify-slider"]',
                    '[id*="captcha-slider"]',
                    // 明确的验证码验证元素
                    '[class*="security-verify"]',
                    '[class*="human-verify"]',
                    '[id*="security-verify"]',
                    '[id*="human-verify"]',
                    // 图片选择验证相关元素
                    '[class*="image-verify"]',
                    '[class*="img-verify"]',
                    '[id*="image-verify"]',
                    '[id*="img-verify"]',
                    '[class*="select-image"]',
                    '[id*="select-image"]',
                    '[class*="drag-to-select"]',
                    '[id*="drag-to-select"]',
                    '[class*="drag-to-bottom"]',
                    '[id*="drag-to-bottom"]'
                ];
                
                // 检查是否有任何验证码元素存在
                for (const selector of captchaSelectors) {
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
                            console.log('找到验证码元素:', selector, '数量:', visibleElements.length);
                            return true;
                        }
                    } catch (error) {
                        // 忽略无效的选择器
                        continue;
                    }
                }
                
                // 检查是否有包含明确验证码文本的元素
                const allElements = Array.from(document.querySelectorAll('*'));
                const hasCaptchaContent = allElements.some(el => {
                    try {
                        const text = el.textContent.toLowerCase();
                        return text.includes('验证码') || 
                               text.includes('captcha') || 
                               text.includes('安全验证') ||
                               text.includes('人机验证') ||
                               text.includes('滑块验证');
                    } catch (error) {
                        return false;
                    }
                });
                
                return hasCaptchaContent;
            });
            
            // 3. 检查是否有明确的滑块验证
            const hasSlider = 
                await page.$('[class*="slider-captcha"]') !== null || 
                await page.$('[class*="verify-slider"]') !== null ||
                await page.$('[class*="captcha-slider"]') !== null ||
                await page.$('[id*="slider-captcha"]') !== null ||
                await page.$('[id*="verify-slider"]') !== null ||
                await page.$('[id*="captcha-slider"]') !== null ||
                await page.$('[class*="slider-verify"]') !== null;
            
            // 4. 检查是否有iframe可能包含验证码（但不单独作为验证码判断依据）
            const hasIframe = await page.$('iframe') !== null;
            
            // 5. 检查页面中是否有输入验证码的输入框
            const hasCaptchaInput = await page.$('input[type="text"][name*="captcha"], input[type="text"][id*="captcha"], input[type="text"][class*="captcha"]') !== null;
            
            // 综合判断是否有验证码 - 更严格的逻辑，需要多个条件同时满足
            // 只有当文本包含明确的验证码关键词，或者同时满足多个验证码相关条件时，才判断为有验证码
            let hasCaptcha = false;
            if (hasCaptchaText) {
                // 如果文本中明确提到验证码，直接判断为有验证码
                hasCaptcha = true;
            } else if (captchaElements && (hasSlider || hasCaptchaInput)) {
                // 如果有验证码元素，并且同时有滑块或验证码输入框，判断为有验证码
                hasCaptcha = true;
            } else if (hasSlider && hasCaptchaInput) {
                // 如果同时有滑块和验证码输入框，判断为有验证码
                hasCaptcha = true;
            } else {
                // 其他情况，判断为没有验证码
                hasCaptcha = false;
            }
            
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
            
            // 检查是否有用户信息元素（已登录的特征）- 更严格的检测
            const hasUserInfo = await page.evaluate(() => {
                const userInfoSelectors = [
                    '[class*="avatar"][class*="user"]',
                    '[class*="username"]:not([class*="login"])',
                    '[id*="user"][id*="avatar"]',
                    '[aria-label*="user"][aria-label*="avatar"]',
                    '[class*="profile"][class*="user"]',
                    '[id*="profile"][id*="user"]',
                    '[href*="profile"][href*="user"]',
                    '[class*="account"][class*="user"]',
                    '[id*="account"][id*="user"]',
                    '[href*="account"][href*="user"]'
                ];
                
                for (const selector of userInfoSelectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        const visibleElements = Array.from(elements).filter(el => {
                            const style = window.getComputedStyle(el);
                            return style.display !== 'none' && 
                                   style.visibility !== 'hidden' &&
                                   el.offsetWidth > 0 &&
                                   el.offsetHeight > 0;
                        });
                        if (visibleElements.length > 0) {
                            // 进一步检查元素是否真正包含用户信息
                            const hasRealUserInfo = visibleElements.some(el => {
                                const text = el.textContent || '';
                                return text.length > 0 && !text.includes('登录') && !text.includes('Login');
                            });
                            if (hasRealUserInfo) {
                                return true;
                            }
                        }
                    } catch (error) {
                        continue;
                    }
                }
                return false;
            });
            
            // 综合判断：需要满足多个条件才能确定登录状态
            let finalNeedLogin = false;
            
            // 核心逻辑：如果没有用户信息，默认需要登录
            if (!hasUserInfo) {
                // 检查是否有明确的登录标识
                if (isLoginUrl || loginButtonExists || needLogin || hasLoginElements) {
                    finalNeedLogin = true;
                } else {
                    // 即使没有明确的登录标识，如果没有用户信息，也认为需要登录
                    finalNeedLogin = true;
                }
            } else {
                // 如果有用户信息，检查是否有明确的需要登录的标识
                if (isLoginUrl || loginButtonExists || needLogin || hasLoginElements) {
                    finalNeedLogin = true;
                } else {
                    finalNeedLogin = false;
                }
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
                hasIframe, 
                hasCaptchaInput,
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
            // 调用登录和验证码检查
            const result = await this.checkLoginOrCaptcha(page);
            
            if (result.needLogin) {
                console.log('检测到需要登录');
                return false;
            } else if (result.hasCaptcha) {
                console.log('检测到验证码');
                return false;
            } else {
                console.log('登录状态有效，无验证码');
                return true;
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
        
        // 尝试获取浏览器窗口并调整其行为，避免自动置顶
        if (!this.headless) {
            try {
                // 获取当前页面的浏览器窗口
                const browserContext = page.browserContext();
                const pages = await browserContext.pages();
                if (pages.length > 0) {
                    // 尝试通过浏览器上下文来控制窗口行为
                    // 这里我们不使用任何可能导致窗口置顶的操作
                    console.log(`页面 ${pageId} 创建，已配置窗口行为`);
                }
            } catch (error) {
                console.log(`页面 ${pageId} 窗口行为配置失败:`, error.message);
            }
        }
        
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
            // 登录或验证码检测失败，但仍继续创建页面
            // 这样用户可以手动处理登录或验证码
            console.warn(`页面 ${pageId} 检测到需要登录或验证码，但仍继续创建页面`);
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
            // 在发送消息前检查验证码
            const captchaResult = await this.checkLoginOrCaptcha(page);
            if (captchaResult.hasCaptcha) {
                console.log(`页面 ${pageId} 检测到验证码，消息发送失败`);
                return false;
            }
            
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

            // 输入消息，加快速度
            await inputBox.type(message, { delay: 5 }); // 减少字符输入延迟
            
            // 优化：等待输入框内容更新，减少等待时间
            await new Promise(resolve => setTimeout(resolve, 100));
            
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
            // 在上传文件前检查验证码
            const captchaResult = await this.checkLoginOrCaptcha(page);
            if (captchaResult.hasCaptcha) {
                throw new Error('检测到验证码，请手动处理后重试');
            }
            
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
            // 在发送带文件的消息前检查验证码
            const captchaResult = await this.checkLoginOrCaptcha(page);
            if (captchaResult.hasCaptcha) {
                throw new Error('检测到验证码，请手动处理后重试');
            }
            
            // 先上传文件
            const uploadSuccess = await this.uploadFile(pageId, filePath);
            if (!uploadSuccess) {
                throw new Error('文件上传失败');
            }
            console.log(`页面 ${pageId} 文件上传成功，等待2秒后发送消息...`);
            await new Promise(resolve => setTimeout(resolve, 500));

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
            // 在获取AI回复前检查验证码
            const captchaResult = await this.checkLoginOrCaptcha(page);
            if (captchaResult.hasCaptcha) {
                console.log(`页面 ${pageId} 检测到验证码，返回验证码信息`);
                // 截取当前页面状态，用于调试
                await page.screenshot({ path: `page_${pageId}_captcha.png` });
                console.log(`页面 ${pageId} 已截图，保存为 page_${pageId}_captcha.png`);
                // 返回特殊标记，表示检测到验证码
                return '[CAPTCHA_DETECTED]';
            }
            
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
                console.log(`页面 ${pageId} 提取到 ${chatHistory.length} 条消息`);
                
                // 1. 先过滤掉明显无效的消息
                const validMessages = chatHistory.filter(msg => {
                    return msg.content && 
                           msg.content.length > 15 && // 跳过非常短的消息
                           !msg.content.includes('Please answer') && // 跳过英文指令
                           !msg.content.includes('请回答'); // 跳过中文指令
                    // 注意：不再过滤包含"编辑分享"的消息，因为这些通常是完整的AI回复，只是末尾包含了编辑选项
                });
                
                console.log(`页面 ${pageId} 过滤后剩余 ${validMessages.length} 条有效消息`);
                
                // 2. 找到包含实际回答的消息
                // 寻找包含有意义回答的消息，通常是最长的那条
                let bestResponse = null;
                let maxLength = 0;
                
                for (const msg of validMessages) {
                    console.log(`检查消息: ${msg.content.substring(0, 60)}... (长度: ${msg.content.length})`);
                    
                    // 改进的问题列表过滤：只跳过以问题列表开头或主要内容是问题列表的消息
                    // 真正的AI回复通常先回答问题，然后才会列出相关问题
                    const chineseQuestionCount = msg.content.split('？').length - 1;
                    const englishQuestionCount = msg.content.split('?').length - 1;
                    const totalQuestionCount = chineseQuestionCount + englishQuestionCount;
                    
                    // 检查消息是否主要由问题组成
                    // 1. 如果问题数量超过3个，但消息长度很长，可能是包含相关问题的正常回复
                    // 2. 如果消息开头就是问题列表，跳过
                    // 3. 否则，保留消息
                    const isMainlyQuestions = 
                        (totalQuestionCount > 3 && msg.content.length < 200) || 
                        (msg.content.startsWith('如何') && totalQuestionCount > 2) ||
                        (msg.content.startsWith('什么') && totalQuestionCount > 2) ||
                        (msg.content.startsWith('为什么') && totalQuestionCount > 2) ||
                        (msg.content.startsWith('怎么') && totalQuestionCount > 2);
                    
                    if (isMainlyQuestions) {
                        console.log('跳过主要由问题组成的消息');
                        continue;
                    }
                    
                    // 寻找最长的消息，因为AI的实际回答通常是最长的
                    if (msg.content.length > maxLength) {
                        maxLength = msg.content.length;
                        bestResponse = msg;
                        console.log('找到更长的消息，更新最佳回复');
                    }
                }
                
                // 3. 如果找到了最佳回复，返回它
                if (bestResponse) {
                    // 清理AI回复，移除可能的干扰内容
                    let cleanResponse = bestResponse.content;
                    
                    // 移除"编辑"相关内容
                    if (cleanResponse.includes('编辑')) {
                        cleanResponse = cleanResponse.split('编辑')[0].trim();
                    }
                    
                    // 移除末尾的问题列表
                    if (cleanResponse.includes('～')) {
                        cleanResponse = cleanResponse.split('～')[0] + '～';
                    }
                    
                    console.log(`页面 ${pageId} 从聊天记录中成功获取AI回复`);
                    console.log(`页面 ${pageId} AI回复: ${cleanResponse}`);
                    return cleanResponse;
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
            // 在提取聊天记录前检查验证码
            const captchaResult = await this.checkLoginOrCaptcha(page);
            if (captchaResult.hasCaptcha) {
                console.log(`页面 ${pageId} 检测到验证码`);
                return [{ 
                    type: 'error', 
                    content: '检测到验证码，请手动处理后重试', 
                    timestamp: new Date().toISOString() 
                }];
            }
            
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

                    // 改进消息类型识别（用户/AI）
                    const className = await message.evaluate(el => el.className);
                    const roleAttr = await message.evaluate(el => el.getAttribute('role') || '');
                    const ariaLabel = await message.evaluate(el => el.getAttribute('aria-label') || '');
                    const innerHTML = await message.evaluate(el => el.innerHTML);
                    
                    // 更准确的类型判断：先检查是否包含编辑分享，这通常是AI回复的特征
                    // 然后根据消息内容和位置判断类型
                    let type = 'ai'; // 默认AI消息
                    
                    // 用户消息特征：包含user/human/sender/self等关键词，或包含输入相关的类
                    if (
                        className.includes('user') || 
                        className.includes('human') ||
                        className.includes('sender') ||
                        className.includes('self') ||
                        className.includes('input') ||
                        className.includes('textarea') ||
                        className.includes('message-sender') ||
                        className.includes('self-message') ||
                        roleAttr.includes('user') ||
                        ariaLabel.includes('user') ||
                        ariaLabel.includes('human')
                    ) {
                        type = 'user';
                    }
                    
                    // 特别处理：如果消息包含"编辑分享"，则更可能是AI回复
                    if (content.includes('编辑分享') || content.includes('编辑')) {
                        type = 'ai';
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
                    const aiResponseData = {
                        success: true,
                        response: response
                    };
                    // 记录完整API响应日志
                    console.log('=== API响应日志 - /getAIResponse ===');
                    console.log('请求数据:', postData);
                    console.log('响应数据:', JSON.stringify(aiResponseData, null, 2));
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify(aiResponseData));
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
                    
                    const ocrResponseData = {
                        success: ocrSendSuccess,
                        message: question,
                        response: ocrResponse,
                        chatHistory: chatHistory,
                        timestamp: new Date().toISOString()
                    };
                    
                    // 记录完整API响应日志
                    console.log('=== API响应日志 - /ocr ===');
                    console.log('请求数据:', JSON.stringify(postData, null, 2));
                    console.log('响应数据:', JSON.stringify(ocrResponseData, null, 2));
                    
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify(ocrResponseData));
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
                    
                    const textChatResponseData = {
                        success: textSendSuccess,
                        message: textMsg,
                        response: textResponse,
                        chatHistory: textChatHistory,
                        timestamp: new Date().toISOString()
                    };
                    
                    // 记录完整API响应日志
                    console.log('=== API响应日志 - /textChat ===');
                    console.log('请求数据:', JSON.stringify(postData, null, 2));
                    console.log('响应数据:', JSON.stringify(textChatResponseData, null, 2));
                    
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify(textChatResponseData));
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
    async startServer(port = 3000, headless = true) {
        this.port = port;
        
        // 初始化浏览器
        await this.init(headless); // 根据参数决定是否使用无头模式
        
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
    // 解析命令行参数
    const args = process.argv.slice(2);
    const debug = args.includes('--debug') || args.includes('-d');
    
    // 检查是否有明确指定无头模式
    let headless = true; // 默认使用无头模式
    
    if (debug) {
        headless = false;
    } else if (args.includes('--no-headless') || args.includes('-nh')) {
        headless = false;
    } else if (args.includes('--headless') || args.includes('-h')) {
        headless = true;
    }
    
    console.log(`浏览器模式: ${headless ? '无头模式' : '有头模式'}`);
    
    const server = new DoubaoBrowserServer();
    await server.startServer(3000, headless);
}

main();
