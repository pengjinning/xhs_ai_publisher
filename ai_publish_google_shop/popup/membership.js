/**
 * 小红书发文助手 - 会员中心脚本
 */

document.addEventListener('DOMContentLoaded', () => {
  const licenseKeyInput = document.getElementById('license-key');
  const activateButton = document.getElementById('activate-btn');
  const currentLicenseElement = document.getElementById('current-license');
  const membershipPlansElement = document.getElementById('membership-plans');
  
  // 初始化
  initMembershipPage();
  
  // 绑定事件
  activateButton.addEventListener('click', activateLicense);
  
  /**
   * 初始化会员页面
   */
  async function initMembershipPage() {
    try {
      // 加载当前许可证信息
      loadCurrentLicenseInfo();
      
      // 加载会员计划
      loadMembershipPlans();
    } catch (error) {
      console.error('初始化会员页面失败:', error);
      showError('会员信息加载失败，请刷新重试');
    }
  }
  
  /**
   * 加载当前许可证信息
   */
  async function loadCurrentLicenseInfo() {
    try {
      // 获取当前许可证信息
      const licenseInfo = await new Promise((resolve) => {
        chrome.runtime.sendMessage(
          { action: 'getCurrentLicenseInfo' },
          (response) => {
            if (!response || !response.success) {
              throw new Error('获取许可证信息失败');
            }
            resolve(response.data);
          }
        );
      });
      
      // 更新UI
      renderLicenseInfo(licenseInfo);
    } catch (error) {
      console.error('加载许可证信息失败:', error);
      currentLicenseElement.innerHTML = `
        <div class="license-error">
          加载会员信息失败，请刷新重试
        </div>
      `;
    }
  }
  
  /**
   * 渲染许可证信息
   * @param {Object} licenseInfo 许可证信息
   */
  function renderLicenseInfo(licenseInfo) {
    // 如果未找到许可证信息，显示免费版
    if (!licenseInfo) {
      licenseInfo = {
        status: 'free',
        features: []
      };
    }
    
    let licenseHtml = '';
    const { status, expiryDate, licenseKey } = licenseInfo;
    
    // 根据状态显示不同内容
    if (status === 'premium') {
      // 高级会员
      const expiry = new Date(expiryDate);
      const formattedDate = expiry.toLocaleDateString('zh-CN', {
        year: 'numeric', 
        month: 'long', 
        day: 'numeric'
      });
      
      licenseHtml = `
        <div class="license-type premium">✨ 高级会员</div>
        <div class="license-info">您的会员有效期至 <span class="license-expiry">${formattedDate}</span></div>
        ${licenseKey ? `<div class="license-key-display">${formatLicenseKey(licenseKey)}</div>` : ''}
      `;
    } else if (status === 'expired') {
      // 已过期会员
      licenseHtml = `
        <div class="license-type expired">⚠️ 会员已过期</div>
        <div class="license-info">您的会员已过期，请续费以继续使用高级功能</div>
        ${licenseKey ? `<div class="license-key-display">${formatLicenseKey(licenseKey)}</div>` : ''}
        <button class="plan-button" onclick="renewMembership()">立即续费</button>
      `;
    } else {
      // 免费版
      licenseHtml = `
        <div class="license-type free">🆓 免费版</div>
        <div class="license-info">升级会员以解锁全部高级功能</div>
      `;
    }
    
    currentLicenseElement.innerHTML = licenseHtml;
  }
  
  /**
   * 格式化许可证密钥显示
   * @param {string} key 许可证密钥
   * @returns {string} 格式化后的密钥
   */
  function formatLicenseKey(key) {
    // 将密钥格式化为 XXXX-XXXX-XXXX-XXXX 格式
    if (!key) return '';
    
    // 如果已经是格式化的，直接返回
    if (key.includes('-')) return key;
    
    // 每4个字符加一个分隔符
    return key.replace(/(.{4})/g, '$1-').slice(0, -1);
  }
  
  /**
   * 加载会员计划
   */
  async function loadMembershipPlans() {
    try {
      // 获取会员计划
      const plans = await new Promise((resolve) => {
        chrome.runtime.sendMessage(
          { action: 'getMembershipPlans' },
          (response) => {
            if (!response || !response.success) {
              throw new Error('获取会员计划失败');
            }
            resolve(response.data);
          }
        );
      });
      
      // 更新UI
      renderMembershipPlans(plans);
    } catch (error) {
      console.error('加载会员计划失败:', error);
      membershipPlansElement.innerHTML = `
        <div class="plan-error">
          加载会员计划失败，请刷新重试
        </div>
      `;
    }
  }
  
  /**
   * 渲染会员计划
   * @param {Array} plans 会员计划列表
   */
  function renderMembershipPlans(plans) {
    if (!plans || plans.length === 0) {
      membershipPlansElement.innerHTML = `
        <div class="plan-error">
          暂无可用的会员计划
        </div>
      `;
      return;
    }
    
    let plansHtml = '';
    
    plans.forEach((plan, index) => {
      const isPopular = plan.id === 'yearly'; // 年度计划标记为推荐
      
      plansHtml += `
        <div class="plan-card ${isPopular ? 'popular' : ''}" data-plan-id="${plan.id}">
          <div class="plan-name">${plan.name}</div>
          <div class="plan-price">
            ${plan.price}<span class="plan-currency">${plan.currency}</span>
            <span class="plan-interval">/${plan.interval === 'month' ? '月' : '年'}</span>
          </div>
          <div class="plan-description">${plan.description}</div>
          <button class="plan-button" onclick="purchasePlan('${plan.id}')">立即购买</button>
        </div>
      `;
    });
    
    membershipPlansElement.innerHTML = plansHtml;
    
    // 给所有计划卡片添加点击事件
    document.querySelectorAll('.plan-card .plan-button').forEach(button => {
      button.addEventListener('click', (e) => {
        e.stopPropagation(); // 防止冒泡到卡片
        const planId = e.target.closest('.plan-card').dataset.planId;
        purchasePlan(planId);
      });
    });
  }
  
  /**
   * 购买会员计划
   * @param {string} planId 计划ID
   */
  function purchasePlan(planId) {
    // 获取购买URL并打开新标签页
    chrome.runtime.sendMessage(
      { action: 'getMembershipPurchaseUrl', planId },
      (response) => {
        if (!response || !response.success) {
          showError('获取购买链接失败');
          return;
        }
        
        // 打开购买页面
        chrome.tabs.create({ url: response.data });
      }
    );
  }
  
  /**
   * 激活许可证
   */
  function activateLicense() {
    const licenseKey = licenseKeyInput.value.trim();
    
    if (!licenseKey) {
      showError('请输入有效的激活码');
      return;
    }
    
    // 禁用按钮
    activateButton.disabled = true;
    activateButton.textContent = '激活中...';
    
    // 发送激活请求
    chrome.runtime.sendMessage(
      { action: 'activateLicense', licenseKey },
      (response) => {
        // 恢复按钮状态
        activateButton.disabled = false;
        activateButton.textContent = '激活';
        
        if (!response || !response.success) {
          showError(response?.error || '激活失败，请检查激活码是否正确');
          return;
        }
        
        // 激活成功，刷新许可证信息
        showSuccess('激活成功！');
        licenseKeyInput.value = '';
        loadCurrentLicenseInfo();
      }
    );
  }
  
  /**
   * 显示错误消息
   * @param {string} message 错误消息
   */
  function showError(message) {
    alert('错误: ' + message);
  }
  
  /**
   * 显示成功消息
   * @param {string} message 成功消息
   */
  function showSuccess(message) {
    alert(message);
  }
  
  /**
   * 续费会员
   */
  window.renewMembership = function() {
    // 滚动到会员计划部分
    document.querySelector('.plans-section').scrollIntoView({
      behavior: 'smooth'
    });
  };
  
  /**
   * 购买计划方法 (全局暴露给HTML使用)
   */
  window.purchasePlan = purchasePlan;
}); 