/**
 * 小红书发文助手 - 后台脚本
 * 负责处理扩展的后台逻辑，包括消息传递、API请求等
 */

// 引入许可证管理模块 (需确保先加载license.js)
// 在实际项目中，您需要在manifest.json中按正确顺序加载这些脚本

// 监听扩展安装事件
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    // 首次安装时初始化配置
    initializeSettings();
    // 打开欢迎页面或选项页
    chrome.tabs.create({ url: chrome.runtime.getURL('options/options.html') });
  } else if (details.reason === 'update') {
    // 版本更新时的逻辑
    console.log('扩展已更新到版本：', chrome.runtime.getManifest().version);
  }
});

// 监听来自popup或content script的消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // 根据消息类型执行不同操作
  switch (message.action) {
    case 'generateContent':
      generateContent(message.title, message.content, message.apiKey, message.model)
        .then(result => sendResponse({ success: true, data: result }))
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true; // 保持消息通道开放，允许异步响应
      
    case 'saveSettings':
      saveSettings(message.settings)
        .then(() => sendResponse({ success: true }))
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true;
      
    case 'getSettings':
      getSettings()
        .then(settings => sendResponse({ success: true, data: settings }))
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true;
      
    case 'fillContent':
      // 将内容发送到content script填充到小红书编辑器
      fillContentInTab(message.tabId, message.title, message.content)
        .then(() => sendResponse({ success: true }))
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true;
    
    // 会员相关功能
    case 'getCurrentLicenseInfo':
      if (window.licenseManager) {
        window.licenseManager.getCurrentLicenseInfo()
          .then(info => sendResponse({ success: true, data: info }))
          .catch(error => sendResponse({ success: false, error: error.message }));
      } else {
        // 如果许可证管理器不可用，返回免费状态
        sendResponse({ 
          success: true, 
          data: { 
            status: 'free', 
            features: ['basic_content_generation', 'basic_format'] 
          } 
        });
      }
      return true;
      
    case 'activateLicense':
      if (window.licenseManager) {
        window.licenseManager.validateLicense(message.licenseKey)
          .then(result => {
            // 如果许可证有效，保存到设置中
            if (result.status === 'premium') {
              getSettings().then(settings => {
                settings.licenseKey = message.licenseKey;
                saveSettings(settings);
              });
            }
            sendResponse({ success: true, data: result });
          })
          .catch(error => sendResponse({ success: false, error: error.message }));
      } else {
        sendResponse({ success: false, error: '许可证管理模块未加载' });
      }
      return true;
      
    case 'getMembershipPlans':
      if (window.licenseManager) {
        window.licenseManager.getMembershipPlans()
          .then(plans => sendResponse({ success: true, data: plans }))
          .catch(error => sendResponse({ success: false, error: error.message }));
      } else {
        // 如果许可证管理器不可用，返回默认计划
        sendResponse({ 
          success: true, 
          data: [
            {
              id: 'monthly',
              name: '月度会员',
              price: '29.9',
              currency: 'CNY',
              interval: 'month',
              description: '解锁所有高级功能，每月付费'
            },
            {
              id: 'yearly',
              name: '年度会员',
              price: '299',
              currency: 'CNY',
              interval: 'year',
              description: '解锁所有高级功能，年付更优惠'
            }
          ]
        });
      }
      return true;
      
    case 'getMembershipPurchaseUrl':
      if (window.licenseManager) {
        const url = window.licenseManager.getMembershipPurchaseUrl(message.planId);
        sendResponse({ success: true, data: url });
      } else {
        sendResponse({ success: false, error: '许可证管理模块未加载' });
      }
      return true;
      
    case 'canAccessFeature':
      if (window.licenseManager) {
        window.licenseManager.canAccessFeature(message.feature)
          .then(canAccess => sendResponse({ success: true, data: canAccess }))
          .catch(error => sendResponse({ success: false, error: error.message }));
      } else {
        // 如果许可证管理器不可用，检查是否是基础功能
        const isBasicFeature = ['basic_content_generation', 'basic_format'].includes(message.feature);
        sendResponse({ success: true, data: isBasicFeature });
      }
      return true;
  }
});

// 初始化设置
function initializeSettings() {
  const defaultSettings = {
    apiKey: '',
    aiModel: 'gpt-3.5',
    autoLogin: false,
    saveDraft: false,
    lastUpdated: new Date().toISOString()
  };
  
  chrome.storage.sync.set({ settings: defaultSettings });
}

// 保存设置
function saveSettings(settings) {
  return new Promise((resolve, reject) => {
    try {
      settings.lastUpdated = new Date().toISOString();
      chrome.storage.sync.set({ settings }, resolve);
    } catch (error) {
      reject(error);
    }
  });
}

// 获取设置
function getSettings() {
  return new Promise((resolve, reject) => {
    try {
      chrome.storage.sync.get(['settings'], (result) => {
        if (result.settings) {
          resolve(result.settings);
        } else {
          // 如果没有找到设置，初始化并返回默认设置
          initializeSettings();
          chrome.storage.sync.get(['settings'], (result) => {
            resolve(result.settings);
          });
        }
      });
    } catch (error) {
      reject(error);
    }
  });
}

// 生成内容
async function generateContent(title, topic, apiKey, model) {
  if (!apiKey) {
    const settings = await getSettings();
    apiKey = settings.apiKey;
    model = settings.aiModel || model;
  }
  
  if (!apiKey) {
    throw new Error('未配置API密钥，请在设置中添加');
  }
  
  // 检查功能访问权限
  if (window.licenseManager) {
    // 基本功能检查
    const canAccessBasic = await window.licenseManager.canAccessFeature(
      window.licenseManager.FeatureAccess.BASIC_CONTENT_GENERATION
    );
    
    if (!canAccessBasic) {
      throw new Error('您的账户无权使用内容生成功能');
    }
    
    // 如果选择了高级模型，检查是否有权限
    if (model === 'gpt-4' || model === 'claude') {
      const canAccessAdvanced = await window.licenseManager.canAccessFeature(
        window.licenseManager.FeatureAccess.ADVANCED_AI_MODELS
      );
      
      if (!canAccessAdvanced) {
        throw new Error('高级AI模型仅限会员使用，请升级会员后使用');
      }
    }
  }
  
  // 构建提示词
  let prompt = `你是一名小红书内容创作专家，请根据以下主题创作一篇小红书风格的文章：\n\n`;
  prompt += `主题：${topic}\n`;
  
  if (title) {
    prompt += `标题：${title}\n`;
  } else {
    prompt += `并为文章创建一个吸引人的标题\n`;
  }
  
  prompt += `\n要求：\n1. 使用小红书流行的写作风格\n2. 增加emoji表情\n3. 分段清晰\n4. 内容真实有价值\n5. 字数适中(500-800字)`;
  
  try {
    // 调用OpenAI API
    const apiEndpoint = 'https://api.openai.com/v1/chat/completions';
    
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: model === 'gpt-3.5' ? 'gpt-3.5-turbo' : 'gpt-4',
        messages: [
          { role: 'system', content: '你是一名专业的小红书内容创作者，擅长创作吸引人的、有价值的内容。' },
          { role: 'user', content: prompt }
        ],
        temperature: 0.7
      })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error?.message || '调用AI服务失败');
    }
    
    const generatedContent = data.choices[0].message.content;
    
    // 提取标题和内容
    let extractedTitle = title;
    let extractedContent = generatedContent;
    
    // 如果没有提供标题，尝试从生成的内容中提取
    if (!title) {
      const titleMatch = generatedContent.match(/^(.*?)[：:]/);
      if (titleMatch) {
        extractedTitle = titleMatch[1].trim();
        extractedContent = generatedContent.substring(titleMatch[0].length).trim();
      }
    }
    
    // 保存到本地存储
    chrome.storage.local.set({
      'lastGeneratedTitle': extractedTitle,
      'lastGeneratedContent': extractedContent
    });
    
    return {
      title: extractedTitle,
      content: extractedContent
    };
    
  } catch (error) {
    console.error('AI服务调用失败:', error);
    throw error;
  }
}

// 在指定标签页中填充内容
function fillContentInTab(tabId, title, content) {
  return new Promise((resolve, reject) => {
    try {
      // 发送消息到content script
      chrome.tabs.sendMessage(tabId, {
        action: 'fillContent',
        title: title,
        content: content
      }, response => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else if (response && response.success) {
          resolve();
        } else {
          reject(new Error(response?.error || '内容填充失败'));
        }
      });
    } catch (error) {
      reject(error);
    }
  });
} 