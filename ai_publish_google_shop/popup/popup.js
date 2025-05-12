// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', () => {
  // 获取DOM元素
  const homeTab = document.getElementById('home-tab');
  const toolsTab = document.getElementById('tools-tab');
  const settingsTab = document.getElementById('settings-tab');
  
  const homePage = document.getElementById('home-page');
  const toolsPage = document.getElementById('tools-page');
  const settingsPage = document.getElementById('settings-page');
  
  const generateBtn = document.getElementById('generate-btn');
  const previewBtn = document.getElementById('preview-btn');
  const saveSettingsBtn = document.getElementById('save-settings');
  
  const titleInput = document.getElementById('title');
  const contentInput = document.getElementById('content');
  const resultDiv = document.getElementById('result');
  const resultContent = document.getElementById('result-content');
  
  // 加载保存的设置
  loadSettings();
  
  // 标签切换事件
  homeTab.addEventListener('click', () => switchTab('home'));
  toolsTab.addEventListener('click', () => switchTab('tools'));
  settingsTab.addEventListener('click', () => switchTab('settings'));
  
  // 生成内容事件
  generateBtn.addEventListener('click', generateContent);
  
  // 预览发布事件
  previewBtn.addEventListener('click', previewContent);
  
  // 保存设置事件
  saveSettingsBtn.addEventListener('click', saveSettings);
  
  // 标签切换函数
  function switchTab(tabName) {
    // 隐藏所有页面
    homePage.classList.remove('active');
    toolsPage.classList.remove('active');
    settingsPage.classList.remove('active');
    
    // 取消所有标签选中状态
    homeTab.classList.remove('active');
    toolsTab.classList.remove('active');
    settingsTab.classList.remove('active');
    
    // 根据选择的标签显示对应页面
    switch(tabName) {
      case 'home':
        homePage.classList.add('active');
        homeTab.classList.add('active');
        break;
      case 'tools':
        toolsPage.classList.add('active');
        toolsTab.classList.add('active');
        break;
      case 'settings':
        settingsPage.classList.add('active');
        settingsTab.classList.add('active');
        break;
    }
  }
  
  // 生成内容函数
  async function generateContent() {
    const title = titleInput.value.trim();
    const content = contentInput.value.trim();
    
    if (!content) {
      alert('请输入内容主题或关键词');
      return;
    }
    
    // 更改按钮状态为加载中
    generateBtn.disabled = true;
    generateBtn.innerText = '生成中...';
    
    try {
      // 获取API密钥和模型设置
      const apiKey = await getSetting('apiKey');
      const aiModel = await getSetting('aiModel') || 'gpt-3.5';
      
      if (!apiKey) {
        alert('请先在设置中配置API密钥');
        switchTab('settings');
        generateBtn.disabled = false;
        generateBtn.innerText = '生成内容';
        return;
      }
      
      // 调用AI生成内容
      const generatedContent = await callAIService(title, content, aiModel, apiKey);
      
      // 显示生成结果
      resultContent.innerHTML = generatedContent;
      resultDiv.classList.remove('hidden');
      
      // 将生成的内容保存到本地存储
      chrome.storage.local.set({ 'lastGeneratedContent': generatedContent });
      
    } catch (error) {
      console.error('生成内容出错:', error);
      alert('生成内容失败: ' + error.message);
    } finally {
      // 恢复按钮状态
      generateBtn.disabled = false;
      generateBtn.innerText = '生成内容';
    }
  }
  
  // 调用AI服务生成内容
  async function callAIService(title, topic, model, apiKey) {
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
      // 这里使用OpenAI API作为示例，实际使用时可以根据需要更换为其他AI服务
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
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
      
      return data.choices[0].message.content.replace(/\n/g, '<br>');
      
    } catch (error) {
      console.error('AI服务调用失败:', error);
      throw error;
    }
  }
  
  // 预览发布函数
  async function previewContent() {
    // 获取生成的内容
    const content = await chrome.storage.local.get(['lastGeneratedContent']);
    
    if (!content.lastGeneratedContent) {
      alert('请先生成内容');
      return;
    }
    
    previewBtn.disabled = true;
    previewBtn.innerText = '准备中...';
    
    try {
      // 检查当前是否在小红书网站
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab.url.includes('xiaohongshu.com')) {
        // 如果不在小红书网站，则打开小红书
        const newTab = await chrome.tabs.create({
          url: 'https://www.xiaohongshu.com/publish/publish'
        });
        
        // 等待新标签页加载完成
        chrome.tabs.onUpdated.addListener(function listener(tabId, changeInfo) {
          if (tabId === newTab.id && changeInfo.status === 'complete') {
            chrome.tabs.onUpdated.removeListener(listener);
            // 页面加载完成后填充内容
            fillContent(newTab.id, titleInput.value, content.lastGeneratedContent);
          }
        });
      } else {
        // 已经在小红书网站，直接填充内容
        fillContent(tab.id, titleInput.value, content.lastGeneratedContent);
      }
    } catch (error) {
      console.error('预览发布出错:', error);
      alert('预览发布失败: ' + error.message);
    } finally {
      previewBtn.disabled = false;
      previewBtn.innerText = '预览发布';
    }
  }
  
  // 填充内容到小红书编辑器
  function fillContent(tabId, title, content) {
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: (title, content) => {
        // 这里编写操作小红书编辑器的代码
        // 注意：以下代码是假设性的，实际实现需要根据小红书网站的DOM结构进行调整
        try {
          // 等待编辑器加载
          setTimeout(() => {
            // 填充标题
            const titleInput = document.querySelector('.title-input');
            if (titleInput) {
              titleInput.value = title;
              titleInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            
            // 填充内容
            const contentDiv = document.querySelector('.content-editable');
            if (contentDiv) {
              // 移除HTML标签，保留换行
              const processedContent = content.replace(/<br>/g, '\n');
              contentDiv.innerText = processedContent;
              contentDiv.dispatchEvent(new Event('input', { bubbles: true }));
            }
            
            // 通知用户
            alert('内容已填充到编辑器，请检查并手动上传图片后发布');
          }, 2000);
        } catch (error) {
          console.error('填充内容失败:', error);
          alert('填充内容失败: ' + error.message);
        }
      },
      args: [title, content]
    });
  }
  
  // 保存设置函数
  function saveSettings() {
    const apiKey = document.getElementById('api-key').value.trim();
    const aiModel = document.getElementById('ai-model').value;
    const autoLogin = document.getElementById('auto-login').checked;
    const saveDraft = document.getElementById('save-draft').checked;
    
    chrome.storage.sync.set({
      'apiKey': apiKey,
      'aiModel': aiModel,
      'autoLogin': autoLogin,
      'saveDraft': saveDraft
    }, () => {
      alert('设置已保存');
    });
  }
  
  // 加载设置函数
  function loadSettings() {
    chrome.storage.sync.get(['apiKey', 'aiModel', 'autoLogin', 'saveDraft'], (result) => {
      if (result.apiKey) {
        document.getElementById('api-key').value = result.apiKey;
      }
      
      if (result.aiModel) {
        document.getElementById('ai-model').value = result.aiModel;
      }
      
      document.getElementById('auto-login').checked = result.autoLogin || false;
      document.getElementById('save-draft').checked = result.saveDraft || false;
    });
  }
  
  // 获取设置项
  function getSetting(key) {
    return new Promise((resolve) => {
      chrome.storage.sync.get([key], (result) => {
        resolve(result[key]);
      });
    });
  }
}); 