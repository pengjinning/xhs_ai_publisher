/**
 * 小红书发文助手 - 许可证验证模块
 * 负责处理会员验证、许可证检查等功能
 */

// 许可证状态
const LicenseStatus = {
  FREE: 'free',         // 免费用户
  PREMIUM: 'premium',   // 高级会员
  EXPIRED: 'expired',   // 已过期会员
  INVALID: 'invalid'    // 无效许可证
};

// 功能权限
const FeatureAccess = {
  // 免费功能
  BASIC_CONTENT_GENERATION: 'basic_content_generation',  // 基础内容生成
  BASIC_FORMAT: 'basic_format',                         // 基础格式优化
  
  // 高级功能(会员专享)
  ADVANCED_AI_MODELS: 'advanced_ai_models',             // 高级AI模型
  BULK_GENERATION: 'bulk_generation',                   // 批量生成
  TEMPLATES: 'templates',                               // 模板功能
  AUTO_TAGS: 'auto_tags',                               // 自动标签生成
  ANALYTICS: 'analytics'                                // 数据分析功能
};

// 许可证API端点 (示例)
const LICENSE_API_ENDPOINT = 'https://yourdomain.com/api/license';

// 本地缓存许可证信息的键
const LICENSE_CACHE_KEY = 'xhs_license_info';
// 许可证缓存有效期 (24小时)
const LICENSE_CACHE_TTL = 24 * 60 * 60 * 1000;

/**
 * 验证许可证
 * @param {string} licenseKey 许可证密钥
 * @returns {Promise<Object>} 许可证信息
 */
async function validateLicense(licenseKey) {
  try {
    // 检查缓存
    const cachedLicense = await getLicenseCacheInfo();
    if (cachedLicense && 
        cachedLicense.licenseKey === licenseKey && 
        cachedLicense.timestamp > Date.now() - LICENSE_CACHE_TTL) {
      return cachedLicense;
    }
    
    // 调用API验证许可证
    const response = await fetch(`${LICENSE_API_ENDPOINT}/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ licenseKey })
    });
    
    if (!response.ok) {
      throw new Error('许可证验证服务请求失败');
    }
    
    const licenseInfo = await response.json();
    
    // 缓存许可证信息
    await cacheLicenseInfo({
      ...licenseInfo,
      licenseKey,
      timestamp: Date.now()
    });
    
    return licenseInfo;
  } catch (error) {
    console.error('许可证验证失败:', error);
    // 如果API调用失败，返回缓存的信息(如果有)
    const cachedLicense = await getLicenseCacheInfo();
    if (cachedLicense && cachedLicense.licenseKey === licenseKey) {
      return {
        ...cachedLicense,
        fromCache: true
      };
    }
    
    // 如果没有缓存或缓存不匹配，返回免费状态
    return {
      status: LicenseStatus.FREE,
      features: getFreeFeaturesAccess(),
      expiryDate: null,
      error: error.message
    };
  }
}

/**
 * 缓存许可证信息
 * @param {Object} licenseInfo 许可证信息
 */
function cacheLicenseInfo(licenseInfo) {
  return new Promise((resolve) => {
    chrome.storage.local.set({ [LICENSE_CACHE_KEY]: licenseInfo }, resolve);
  });
}

/**
 * 获取缓存的许可证信息
 * @returns {Promise<Object|null>} 许可证信息或null
 */
function getLicenseCacheInfo() {
  return new Promise((resolve) => {
    chrome.storage.local.get([LICENSE_CACHE_KEY], (result) => {
      resolve(result[LICENSE_CACHE_KEY] || null);
    });
  });
}

/**
 * 清除许可证信息
 * @returns {Promise<void>}
 */
function clearLicenseInfo() {
  return new Promise((resolve) => {
    chrome.storage.local.remove([LICENSE_CACHE_KEY], resolve);
  });
}

/**
 * 检查用户是否有权访问特定功能
 * @param {string} feature 功能标识符
 * @returns {Promise<boolean>} 是否可以访问
 */
async function canAccessFeature(feature) {
  const licenseInfo = await getCurrentLicenseInfo();
  
  // 检查功能访问权限
  return licenseInfo && 
         licenseInfo.features && 
         licenseInfo.features.includes(feature);
}

/**
 * 获取当前许可证信息
 * @returns {Promise<Object>} 许可证信息
 */
async function getCurrentLicenseInfo() {
  // 从存储中获取许可证密钥
  const settings = await new Promise((resolve) => {
    chrome.storage.sync.get(['settings'], (result) => {
      resolve(result.settings || {});
    });
  });
  
  const licenseKey = settings.licenseKey;
  
  // 如果没有许可证密钥，返回免费状态
  if (!licenseKey) {
    return {
      status: LicenseStatus.FREE,
      features: getFreeFeaturesAccess(),
      expiryDate: null
    };
  }
  
  // 验证许可证
  return validateLicense(licenseKey);
}

/**
 * 获取免费用户可访问的功能列表
 * @returns {Array<string>} 可访问的功能列表
 */
function getFreeFeaturesAccess() {
  return [
    FeatureAccess.BASIC_CONTENT_GENERATION,
    FeatureAccess.BASIC_FORMAT
  ];
}

/**
 * 获取高级会员可访问的功能列表
 * @returns {Array<string>} 可访问的功能列表
 */
function getPremiumFeaturesAccess() {
  return [
    // 免费功能
    ...getFreeFeaturesAccess(),
    // 高级功能
    FeatureAccess.ADVANCED_AI_MODELS,
    FeatureAccess.BULK_GENERATION,
    FeatureAccess.TEMPLATES,
    FeatureAccess.AUTO_TAGS,
    FeatureAccess.ANALYTICS
  ];
}

/**
 * 获取会员计划信息
 * @returns {Promise<Array<Object>>} 会员计划列表
 */
async function getMembershipPlans() {
  try {
    const response = await fetch(`${LICENSE_API_ENDPOINT}/plans`);
    
    if (!response.ok) {
      throw new Error('获取会员计划失败');
    }
    
    return await response.json();
  } catch (error) {
    console.error('获取会员计划失败:', error);
    // 返回默认计划信息
    return [
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
    ];
  }
}

/**
 * 生成购买会员的URL
 * @param {string} planId 会员计划ID
 * @returns {string} 购买URL
 */
function getMembershipPurchaseUrl(planId) {
  // 这里可以生成一个带有用户标识和计划ID的URL，指向你的购买页面
  return `https://yourdomain.com/purchase?plan=${planId}&ref=${chrome.runtime.id}`;
}

// 导出模块
window.licenseManager = {
  validateLicense,
  canAccessFeature,
  getCurrentLicenseInfo,
  clearLicenseInfo,
  getLicenseCacheInfo,
  getMembershipPlans,
  getMembershipPurchaseUrl,
  LicenseStatus,
  FeatureAccess
}; 