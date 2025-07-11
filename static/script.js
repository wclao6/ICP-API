// 将函数暴露到全局作用域 
window.queryAPI  = async function(type) {
    // 性能监控开始
    const performanceStart = performance.now(); 
    let fetchEndTime, renderEndTime;
 
    // 1. 获取所有需要的元素 
    const allQueryBtns = document.querySelectorAll('.query-btn'); 
    const currentBtn = document.querySelector(`.query-btn.${type}`); 
    const inputField = document.getElementById(`${type}-input`); 
    const responseContainer = document.getElementById('response'); 
 
    // 2. 验证输入
    let keyword = inputField.value.trim(); 
    if (!keyword) {
        showToast('请输入查询关键词！', 'warning');
        inputField.focus(); 
        return;
    }
 
    // 3. 禁用所有按钮并设置加载状态
    allQueryBtns.forEach(btn  => {
        btn.disabled  = true;
        btn.style.pointerEvents  = 'none';
    });
    currentBtn.innerHTML  = `<i class="fas fa-spinner fa-spin"></i> 查询中...`;
 
    try {
        // 4. 显示加载状态 
        responseContainer.innerHTML  = `
            <div class="loading-overlay">
                <div class="loading-content">
                    <div class="spinner"></div>
                    <div class="loading-text">正在查询 ${type.toUpperCase()}  备案信息...</div>
                </div>
            </div>
            <pre class="response-json">{"status": "loading", "type": "${escapeHtml(type)}", "keyword": "${escapeHtml(keyword)}"}</pre>
        `;
 
        // 5. 发起请求并记录耗时 
        const fetchStartTime = performance.now(); 
        const response = await fetch(`/query${type}/${encodeURIComponent(keyword)}`);
        fetchEndTime = performance.now(); 
 
        if (!response.ok)  {
            throw new Error(`请求失败: ${response.status}`); 
        }
 
        const data = await response.json(); 
        
        // 记录渲染前时间 
        const renderStartTime = performance.now(); 
        showResult(type, keyword, data);
        renderEndTime = performance.now(); 
 
        // 打印性能数据 
        console.log(`[ 性能监控] ${type.toUpperCase()} 查询结果：\n` +
                    `网络请求耗时: ${(fetchEndTime - fetchStartTime).toFixed(2)}ms\n` +
                    `DOM渲染耗时: ${(renderEndTime - renderStartTime).toFixed(2)}ms\n` +
                    `总耗时: ${(renderEndTime - performanceStart).toFixed(2)}ms`);
 
    } catch (error) {
        console.error(' 查询错误:', error);
        showError(type, error);
 
        // 打印错误时的性能数据 
        if (fetchEndTime) {
            console.log(`[ 性能监控] ${type.toUpperCase()} 查询失败：\n` +
                        `网络请求耗时: ${(fetchEndTime - performanceStart).toFixed(2)}ms`);
        }
 
        // 6. 错误时恢复按钮状态 
        resetButtons(allQueryBtns);
        return;
    }
 
    // 7. 最终恢复按钮状态 
    resetButtons(allQueryBtns);
 
    // 8. 滚动到结果区域
    responseContainer.scrollIntoView({behavior:  'smooth'});
}
 
// 按钮状态重置函数 
function resetButtons(buttons) {
    buttons.forEach(btn  => {
        btn.disabled  = false;
        btn.style.pointerEvents  = 'auto';
        const btnType = btn.classList.contains('web')  ? 'web' :
                        btn.classList.contains('app')  ? 'app' : 'wx';
        btn.innerHTML  = `<i class="fas fa-search"></i> 查询${
            btnType === 'web' ? '网站' :
            btnType === 'app' ? 'APP' : '小程序'
        }备案`;
    });
}
 
// 显示结果函数
function showResult(type, keyword, data) {
    const responseContainer = document.getElementById('response'); 
    const formattedJson = formatJSON(data);
 
    responseContainer.innerHTML  = `
        <span class="code-comment"># ${type.toUpperCase()}  备案查询结果 (关键词: ${escapeHtml(keyword)})</span><br>
        <pre class="response-json">${formattedJson}</pre>
    `;
}
 
// 显示错误函数 
function showError(type, error) {
    const responseContainer = document.getElementById('response'); 
    responseContainer.innerHTML  = `
        <span class="code-comment"># ${type.toUpperCase()}  查询失败</span><br>
        <pre class="response-json">{"status": "error", "message": "${escapeHtml(error.message)}"}</pre> 
    `;
}
 
// 清除响应内容 
window.clearResponse  = function() {
    const responseContainer = document.getElementById('response'); 
    responseContainer.innerHTML  = `
        <span class="code-comment"># 响应结果已清除</span><br>
        <pre class="response-json">{"status": "cleared", "message": "请使用查询功能获取新的备案信息"}</pre>
    `;
    showToast('响应内容已清除', 'info');
}
 
// 复制响应内容
window.copyResponse  = async function() {
    const responseContainer = document.getElementById('response'); 
    const jsonElement = responseContainer.querySelector('.response-json'); 
 
    if (!jsonElement || jsonElement.textContent.includes('"status":  "cleared"')) {
        showToast('没有可复制的内容！', 'warning');
        return;
    }
 
    const responseText = jsonElement.textContent; 
    let textarea;
 
    try {
        if (navigator.clipboard)  {
            await navigator.clipboard.writeText(responseText); 
            showToast('✔ 已复制到剪贴板', 'success');
            return;
        }
 
        textarea = document.createElement('textarea'); 
        textarea.value  = responseText;
        textarea.style.position  = 'fixed';
        document.body.appendChild(textarea); 
        textarea.select(); 
 
        if (document.execCommand('copy'))  {
            showToast('✔ 已复制到剪贴板', 'success');
        } else {
            throw new Error('复制命令执行失败');
        }
    } catch (err) {
        console.error(' 复制失败:', err);
        showToast('复制失败，请手动选择内容复制', 'error');
    } finally {
        if (textarea) {
            document.body.removeChild(textarea); 
        }
    }
}
 
// 辅助函数：格式化JSON 
function formatJSON(data) {
    try {
        return JSON.stringify(data,  null, 2)
            .replace(/("[\w]+":)/g, '<span class="code-key">$1</span>')
            .replace(/: ("[^"]+")/g, ': <span class="code-value">$1</span>')
            .replace(/: (\d+)/g, ': <span class="code-value">$1</span>');
    } catch (e) {
        console.error('JSON  格式化错误:', e);
        return JSON.stringify({error:  "数据格式化失败"}, null, 2);
    }
}
 
// 辅助函数：HTML转义
function escapeHtml(text) {
    const div = document.createElement('div'); 
    div.textContent  = text;
    return div.innerHTML; 
}
 
// 显示Toast通知
function showToast(message, type = 'info') {
    const toast = document.createElement('div'); 
    toast.className  = `toast-notification toast-${type}`;
    toast.innerHTML  = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' :
          type === 'error' ? 'fa-exclamation-circle' :
          type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'}"></i>
        ${message}
    `;
 
    document.body.appendChild(toast); 
 
    setTimeout(() => {
        toast.classList.add('fade-out'); 
        setTimeout(() => toast.remove(),  300);
    }, 3000);
}
 
// 更新时间显示
function updateTime() {
    const now = new Date();
    const timeElement = document.querySelector('.time'); 
    const dateElement = document.querySelector('.date'); 
 
    // 格式化时间
    const timeString = now.toLocaleTimeString('zh-CN',  {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false 
    });
 
    // 格式化日期 
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
    };
    const dateString = now.toLocaleDateString('zh-CN',  options);
 
    // 农历计算（简化版）
    const lunarYear = (now.getFullYear()  - 4) % 60 + 1;
    const lunarMonth = now.getMonth()  + 1;
    const lunarDay = now.getDate(); 
 
    timeElement.textContent  = timeString;
    dateElement.textContent  = `${dateString} · 农历${lunarYear}年${lunarMonth}月${lunarDay}日`;
}
 
// 初始化
document.addEventListener('DOMContentLoaded',  () => {
    // 每秒更新时间
    setInterval(updateTime, 1000);
 
    // 初始更新时间 
    updateTime();
});