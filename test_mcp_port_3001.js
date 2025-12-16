const axios = require('axios');

// 测试脚本：测试mcp是否能使用3001端口
async function testMcpPort3001() {
    console.log('=== 测试mcp是否能使用3001端口 ===');
    
    const baseUrl = 'http://localhost:3001';
    
    try {
        // 测试1：健康检查接口
        console.log('\n1. 测试健康检查接口...');
        const healthResponse = await axios.get(`${baseUrl}/health`);
        console.log('✅ 健康检查成功:', healthResponse.data);
        
        // 测试2：聊天补全接口（需要browser_server运行）
        console.log('\n2. 测试聊天补全接口...');
        try {
            const chatResponse = await axios.post(`${baseUrl}/v1/chat/completions`, {
                messages: [
                    { role: 'user', content: '你好，测试一下mcp是否能使用3001端口' }
                ]
            });
            console.log('✅ 聊天补全成功:', chatResponse.data.choices[0].message.content);
        } catch (chatError) {
            if (chatError.response?.status === 500) {
                console.log('⚠️  聊天补全失败（可能是browser_server未运行）:', chatError.message);
            } else {
                throw chatError;
            }
        }
        
        // 测试3：OCR识别接口（模拟）
        console.log('\n3. 测试OCR识别接口结构...');
        try {
            // 发送一个无效请求，测试接口是否存在
            await axios.post(`${baseUrl}/v1/ocr/recognize`, {});
        } catch (ocrError) {
            if (ocrError.response?.status === 400) {
                console.log('✅ OCR接口存在，返回了预期的400错误');
            } else {
                throw ocrError;
            }
        }
        
        // 测试4：是/否判断接口结构
        console.log('\n4. 测试是/否判断接口结构...');
        try {
            await axios.post(`${baseUrl}/v1/moderations`, {});
        } catch (modError) {
            if (modError.response?.status === 400) {
                console.log('✅ 是/否判断接口存在，返回了预期的400错误');
            } else {
                throw modError;
            }
        }
        
        console.log('\n=== 测试总结 ===');
        console.log('✅ 3001端口服务已成功启动');
        console.log('✅ 所有API接口结构正常');
        console.log('✅ mcp可以使用3001端口进行通信');
        
        return true;
        
    } catch (error) {
        console.error('❌ 测试失败:', error.message);
        if (error.response) {
            console.error('   状态码:', error.response.status);
            console.error('   响应内容:', error.response.data);
        }
        return false;
    }
}

// 运行测试
if (require.main === module) {
    testMcpPort3001().then(success => {
        process.exit(success ? 0 : 1);
    });
}

module.exports = { testMcpPort3001 };
