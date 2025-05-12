/**
 * 小红书发文助手 - 内容脚本
 * 负责在小红书网站上实现自动填充和发布功能
 */

// 全局变量
let isToolbarAdded = false;
let toolbarElement = null;
let isContentPage = false;
let isPublishPage = false;

// 页面加载完成后初始化
window.addEventListener('load', initialize);

// 初始化函数
function initialize() {
  // 检查当前页面类型
  checkPageType();
  
  // 如果是相关页面，添加工具栏
  if (isContentPage || isPublishPage) {
    // 延迟添加工具栏，确保页面元素已完全加载
    setTimeout(addToolbar, 1500);
    
    // 监听来自扩展popup的消息
    chrome.runtime.onMessage.addListener(handleMessage);
  }
}

// 检查页面类型
function checkPageType() {
  const url = window.location.href;
  
  // 检查是否是小红书内容页面
  isContentPage = url.includes('xiaohongshu.com/explore') || 
                 url.includes('xiaohongshu.com/discovery');
                 
  // 检查是否是发布页面
  isPublishPage = url.includes('xiaohongshu.com/publish');
}

// 添加工具栏
function addToolbar() {
  if (isToolbarAdded) return;
  
  // 创建工具栏
  toolbarElement = document.createElement('div');
  toolbarElement.className = 'xhs-ai-toolbar';
  
  let buttons = [];
  
  // 根据页面类型添加不同按钮
  if (isPublishPage) {
    // 发布页面的按钮
    buttons = [
      createButton('ai-fill-btn', '🪄 AI填充', fillWithAI),
      createButton('ai-format-btn', '✨ 格式优化', formatContent),
      createButton('ai-tags-btn', '🏷️ 生成标签', generateTags)
    ];
  } else if (isContentPage) {
    // 内容页面的按钮
    buttons = [
      createButton('ai-analyze-btn', '🔍 笔记分析', analyzeNote),
      createButton('ai-save-btn', '💾 保存灵感', saveIdea)
    ];
  }
  
  // 添加按钮到工具栏
  buttons.forEach(button => toolbarElement.appendChild(button));
  
  // 添加工具栏到页面
  document.body.appendChild(toolbarElement);
  isToolbarAdded = true;
  
  // 识别页面编辑区
  if (isPublishPage) {
    identifyEditorElements();
  }
}

// 创建按钮
function createButton(id, text, clickHandler) {
  const button = document.createElement('button');
  button.id = id;
  button.className = 'xhs-ai-toolbar-button';
  button.innerHTML = text;
  button.addEventListener('click', clickHandler);
  return button;
}

// 处理来自扩展popup的消息
function handleMessage(message, sender, sendResponse) {
  // 根据消息类型执行不同操作
  switch (message.action) {
    case 'fillContent':
      fillContent(message.title, message.content);
      sendResponse({ success: true });
      break;
      
    case 'formatContent':
      formatContent();
      sendResponse({ success: true });
      break;
      
    case 'analyzeCurrentPage':
      analyzeNote();
      sendResponse({ success: true });
      break;
      
    default:
      sendResponse({ success: false, error: '未知操作' });
  }
  
  // 返回true以保持通信通道开放，允许异步响应
  return true;
}

// 识别编辑器元素
function identifyEditorElements() {
  // 寻找标题输入框
  const titleInputs = document.querySelectorAll('input[placeholder*="标题"], input[placeholder*="title"], .title-input');
  
  // 寻找内容编辑区域
  const contentEditors = document.querySelectorAll('.content-editable, [contenteditable=true], textarea.content');
  
  // 为编辑区域添加高亮效果
  titleInputs.forEach(el => {
    el.classList.add('xhs-ai-highlight');
    el.dataset.xhsRole = 'title';
  });
  
  contentEditors.forEach(el => {
    el.classList.add('xhs-ai-highlight');
    el.dataset.xhsRole = 'content';
  });
}

// 填充内容
function fillContent(title, content) {
  try {
    // 查找标题输入框
    const titleInput = document.querySelector('[data-xhs-role="title"]') || 
                      document.querySelector('input[placeholder*="标题"], input[placeholder*="title"], .title-input');
    
    // 查找内容编辑区域
    const contentEditor = document.querySelector('[data-xhs-role="content"]') || 
                         document.querySelector('.content-editable, [contenteditable=true], textarea.content');
    
    // 填充标题
    if (titleInput) {
      titleInput.value = title;
      titleInput.dispatchEvent(new Event('input', { bubbles: true }));
      titleInput.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    // 填充内容
    if (contentEditor) {
      // 检查是否是textarea
      if (contentEditor.tagName.toLowerCase() === 'textarea') {
        contentEditor.value = content.replace(/<br>/g, '\n');
      } else {
        // 假设是div或其他HTML元素
        contentEditor.innerHTML = content;
      }
      
      contentEditor.dispatchEvent(new Event('input', { bubbles: true }));
      contentEditor.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    // 显示成功消息
    showTooltip('内容已填充，请检查并添加图片后发布');
    
  } catch (error) {
    console.error('填充内容失败:', error);
    showTooltip('填充内容失败: ' + error.message, true);
  }
}

// AI填充功能
function fillWithAI() {
  // 获取之前生成的内容
  chrome.storage.local.get(['lastGeneratedContent', 'lastGeneratedTitle'], (result) => {
    if (result.lastGeneratedContent) {
      fillContent(result.lastGeneratedTitle || '', result.lastGeneratedContent);
    } else {
      showTooltip('没有可用的AI生成内容，请先在扩展中生成内容', true);
    }
  });
}

// 格式优化功能
function formatContent() {
  try {
    // 获取当前内容
    const contentEditor = document.querySelector('[data-xhs-role="content"]') || 
                         document.querySelector('.content-editable, [contenteditable=true], textarea.content');
    
    if (!contentEditor) {
      showTooltip('未找到内容编辑区域', true);
      return;
    }
    
    let content = '';
    
    // 获取当前内容
    if (contentEditor.tagName.toLowerCase() === 'textarea') {
      content = contentEditor.value;
    } else {
      content = contentEditor.innerText;
    }
    
    if (!content.trim()) {
      showTooltip('内容为空，无法优化格式', true);
      return;
    }
    
    // 优化排版
    let formattedContent = formatText(content);
    
    // 应用格式化后的内容
    if (contentEditor.tagName.toLowerCase() === 'textarea') {
      contentEditor.value = formattedContent;
    } else {
      contentEditor.innerHTML = formattedContent.replace(/\n/g, '<br>');
    }
    
    contentEditor.dispatchEvent(new Event('input', { bubbles: true }));
    contentEditor.dispatchEvent(new Event('change', { bubbles: true }));
    
    showTooltip('格式已优化');
    
  } catch (error) {
    console.error('格式优化失败:', error);
    showTooltip('格式优化失败: ' + error.message, true);
  }
}

// 生成标签功能
function generateTags() {
  try {
    // 获取当前内容
    const contentEditor = document.querySelector('[data-xhs-role="content"]') || 
                         document.querySelector('.content-editable, [contenteditable=true], textarea.content');
    
    if (!contentEditor) {
      showTooltip('未找到内容编辑区域', true);
      return;
    }
    
    let content = '';
    
    // 获取当前内容
    if (contentEditor.tagName.toLowerCase() === 'textarea') {
      content = contentEditor.value;
    } else {
      content = contentEditor.innerText;
    }
    
    if (!content.trim()) {
      showTooltip('内容为空，无法生成标签', true);
      return;
    }
    
    // 模拟标签生成
    const tags = ['#小红书干货', '#经验分享', '#生活技巧', '#达人分享', '#好物推荐'];
    
    // 找到添加标签的区域
    const tagArea = document.querySelector('.tag-input, .hashtag-input, [placeholder*="添加标签"]');
    
    if (tagArea) {
      // 模拟点击标签区域
      tagArea.click();
      
      // 等待标签输入框出现
      setTimeout(() => {
        // 模拟填入标签
        const tagInput = document.querySelector('.tag-input-active, .hashtag-input-active, input[placeholder*="标签"]');
        
        if (tagInput) {
          // 依次添加标签
          addTagsSequentially(tagInput, tags, 0);
        } else {
          showTooltip('未找到标签输入框', true);
        }
      }, 500);
    } else {
      // 如果找不到标签区域，直接在内容末尾添加标签
      let newContent = content;
      if (!newContent.endsWith('\n')) {
        newContent += '\n\n';
      } else {
        newContent += '\n';
      }
      
      newContent += tags.join(' ');
      
      // 应用新内容
      if (contentEditor.tagName.toLowerCase() === 'textarea') {
        contentEditor.value = newContent;
      } else {
        contentEditor.innerHTML = newContent.replace(/\n/g, '<br>');
      }
      
      contentEditor.dispatchEvent(new Event('input', { bubbles: true }));
      contentEditor.dispatchEvent(new Event('change', { bubbles: true }));
      
      showTooltip('标签已添加到内容末尾');
    }
    
  } catch (error) {
    console.error('生成标签失败:', error);
    showTooltip('生成标签失败: ' + error.message, true);
  }
}

// 递归添加标签
function addTagsSequentially(tagInput, tags, index) {
  if (index >= tags.length) {
    showTooltip('标签已添加完成');
    return;
  }
  
  // 输入当前标签
  tagInput.value = tags[index].replace('#', '');
  tagInput.dispatchEvent(new Event('input', { bubbles: true }));
  tagInput.dispatchEvent(new Event('change', { bubbles: true }));
  
  // 模拟按回车确认
  setTimeout(() => {
    const enterEvent = new KeyboardEvent('keydown', {
      key: 'Enter',
      code: 'Enter',
      keyCode: 13,
      which: 13,
      bubbles: true
    });
    tagInput.dispatchEvent(enterEvent);
    
    // 添加下一个标签
    setTimeout(() => {
      addTagsSequentially(tagInput, tags, index + 1);
    }, 300);
  }, 300);
}

// 笔记分析功能
function analyzeNote() {
  // 获取当前页面内容
  try {
    const titleElement = document.querySelector('.title, .note-title, h1');
    const contentElement = document.querySelector('.content, .note-content, article');
    
    if (!titleElement || !contentElement) {
      showTooltip('无法识别当前笔记内容', true);
      return;
    }
    
    const title = titleElement.textContent.trim();
    const content = contentElement.textContent.trim();
    
    // 保存内容到存储，供扩展分析
    chrome.storage.local.set({
      'analyzeData': {
        title: title,
        content: content,
        url: window.location.href,
        timestamp: new Date().toISOString()
      }
    }, () => {
      showTooltip('已保存笔记数据，请在扩展中查看分析结果');
    });
    
  } catch (error) {
    console.error('分析笔记失败:', error);
    showTooltip('分析笔记失败: ' + error.message, true);
  }
}

// 保存灵感功能
function saveIdea() {
  try {
    const titleElement = document.querySelector('.title, .note-title, h1');
    const contentElement = document.querySelector('.content, .note-content, article');
    
    if (!titleElement || !contentElement) {
      showTooltip('无法识别当前笔记内容', true);
      return;
    }
    
    const title = titleElement.textContent.trim();
    const content = contentElement.textContent.trim();
    
    // 获取已保存的灵感列表
    chrome.storage.local.get(['savedIdeas'], (result) => {
      const savedIdeas = result.savedIdeas || [];
      
      // 添加新灵感
      savedIdeas.push({
        title: title,
        excerpt: content.substring(0, 100) + '...',
        url: window.location.href,
        timestamp: new Date().toISOString()
      });
      
      // 保存回存储
      chrome.storage.local.set({ 'savedIdeas': savedIdeas }, () => {
        showTooltip('灵感已保存，可在扩展中查看');
      });
    });
    
  } catch (error) {
    console.error('保存灵感失败:', error);
    showTooltip('保存灵感失败: ' + error.message, true);
  }
}

// 文本格式化
function formatText(text) {
  // 基本格式化
  let formatted = text.trim();
  
  // 确保段落之间有足够空行
  formatted = formatted.replace(/([。！？】\)）])\s*\n/g, '$1\n\n');
  
  // 确保每行开头有适当缩进
  formatted = formatted.replace(/\n\s*([^\n])/g, '\n$1');
  
  // 添加随机emoji
  const emojis = ['✨', '🌟', '💫', '⭐', '🔥', '❤️', '💕', '🥰', '😊', '🙌', '👏', '🎉', '🎊', '🎁', '🎀'];
  
  // 在句子末尾随机添加emoji
  formatted = formatted.replace(/([。！？])\s*(?=\S)/g, (match, p1) => {
    // 30%概率添加emoji
    if (Math.random() < 0.3) {
      const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)];
      return p1 + ' ' + randomEmoji + ' ';
    }
    return match;
  });
  
  return formatted;
}

// 显示提示框
function showTooltip(message, isError = false) {
  // 移除之前的提示框
  const oldTooltip = document.querySelector('.xhs-ai-tooltip');
  if (oldTooltip) {
    oldTooltip.remove();
  }
  
  // 创建新提示框
  const tooltip = document.createElement('div');
  tooltip.className = 'xhs-ai-tooltip';
  tooltip.textContent = message;
  
  if (isError) {
    tooltip.style.backgroundColor = '#e74c3c';
  }
  
  // 添加到页面
  document.body.appendChild(tooltip);
  
  // 定位在工具栏上方
  if (toolbarElement) {
    const rect = toolbarElement.getBoundingClientRect();
    tooltip.style.bottom = (window.innerHeight - rect.top + 10) + 'px';
    tooltip.style.right = (window.innerWidth - rect.right + rect.width / 2) + 'px';
  } else {
    tooltip.style.bottom = '70px';
    tooltip.style.right = '20px';
  }
  
  // 自动消失
  setTimeout(() => {
    tooltip.style.opacity = '0';
    tooltip.style.transition = 'opacity 0.5s ease';
    
    setTimeout(() => {
      if (tooltip.parentNode) {
        tooltip.parentNode.removeChild(tooltip);
      }
    }, 500);
  }, 3000);
} 