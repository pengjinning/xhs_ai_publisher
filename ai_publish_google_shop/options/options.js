// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  // DOM元素
  const apiKeyInput = document.getElementById('api-key');
  const aiModelSelect = document.getElementById('ai-model');
  const autoLoginCheckbox = document.getElementById('auto-login');
  const saveDraftCheckbox = document.getElementById('save-draft');
  const autoFormatCheckbox = document.getElementById('auto-format');
  const defaultTemplateTextarea = document.getElementById('default-template');
  const signatureInput = document.getElementById('signature');
  const saveButton = document.getElementById('save-btn');
  const resetButton = document.getElementById('reset-btn');
  
  // 默认设置
  const defaultSettings = {
    apiKey: '',
    aiModel: 'gpt-3.5',
    autoLogin: false,
    saveDraft: false,
    autoFormat: true,
    defaultTemplate: '✨ {{标题}} ✨\n\n大家好，今天想和大家分享一下关于"{{主题}}"的心得体会 💗\n\n',
    signature: '',
    lastUpdated: new Date().toISOString()
  };
  
  // 加载设置
  loadSettings();
  
  // 保存按钮点击事件
  saveButton.addEventListener('click', saveSettings);
  
  // 重置按钮点击事件
  resetButton.addEventListener('click', resetSettings);
  
  // 加载设置函数
  function loadSettings() {
    chrome.runtime.sendMessage({ action: 'getSettings' }, (response) => {
      if (response && response.success && response.data) {
        const settings = response.data;
        
        // 填充表单
        apiKeyInput.value = settings.apiKey || '';
        aiModelSelect.value = settings.aiModel || defaultSettings.aiModel;
        autoLoginCheckbox.checked = settings.autoLogin || false;
        saveDraftCheckbox.checked = settings.saveDraft || false;
        autoFormatCheckbox.checked = settings.autoFormat !== undefined ? settings.autoFormat : defaultSettings.autoFormat;
        defaultTemplateTextarea.value = settings.defaultTemplate || defaultSettings.defaultTemplate;
        signatureInput.value = settings.signature || '';
        
      } else {
        // 如果获取设置失败，使用默认设置
        resetSettings();
      }
    });
  }
  
  // 保存设置函数
  function saveSettings() {
    // 收集表单数据
    const settings = {
      apiKey: apiKeyInput.value.trim(),
      aiModel: aiModelSelect.value,
      autoLogin: autoLoginCheckbox.checked,
      saveDraft: saveDraftCheckbox.checked,
      autoFormat: autoFormatCheckbox.checked,
      defaultTemplate: defaultTemplateTextarea.value,
      signature: signatureInput.value.trim()
    };
    
    // 发送到后台保存
    chrome.runtime.sendMessage(
      { action: 'saveSettings', settings: settings },
      (response) => {
        if (response && response.success) {
          showMessage('设置已保存', 'success');
        } else {
          showMessage('保存设置失败: ' + (response?.error || '未知错误'), 'error');
        }
      }
    );
  }
  
  // 重置设置函数
  function resetSettings() {
    // 使用默认设置填充表单
    apiKeyInput.value = defaultSettings.apiKey;
    aiModelSelect.value = defaultSettings.aiModel;
    autoLoginCheckbox.checked = defaultSettings.autoLogin;
    saveDraftCheckbox.checked = defaultSettings.saveDraft;
    autoFormatCheckbox.checked = defaultSettings.autoFormat;
    defaultTemplateTextarea.value = defaultSettings.defaultTemplate;
    signatureInput.value = defaultSettings.signature;
    
    showMessage('已重置为默认设置', 'info');
  }
  
  // 显示消息函数
  function showMessage(message, type = 'info') {
    // 检查是否已有消息元素
    let messageElement = document.querySelector('.message');
    
    // 如果没有，创建新的消息元素
    if (!messageElement) {
      messageElement = document.createElement('div');
      messageElement.className = 'message';
      document.querySelector('.container').appendChild(messageElement);
    }
    
    // 设置消息类型和内容
    messageElement.className = `message ${type}`;
    messageElement.textContent = message;
    
    // 显示消息
    messageElement.style.display = 'block';
    messageElement.style.opacity = '1';
    
    // 3秒后隐藏消息
    setTimeout(() => {
      messageElement.style.opacity = '0';
      setTimeout(() => {
        messageElement.style.display = 'none';
      }, 500);
    }, 3000);
  }
  
  // 添加表单验证
  apiKeyInput.addEventListener('blur', () => {
    const apiKey = apiKeyInput.value.trim();
    if (apiKey && !apiKey.startsWith('sk-')) {
      showMessage('API密钥格式可能不正确，请检查', 'warning');
    }
  });
}); 