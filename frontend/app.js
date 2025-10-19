// ========================================
// Конфигурация и состояние приложения
// ========================================

const API_BASE_URL = 'http://localhost:5000/api';

const state = {
    keystrokeEvents: [],
    startTime: null,
    isTyping: false,
    currentText: '',
    referenceText: '',
    features: null
};

// ========================================
// DOM элементы
// ========================================

const elements = {
    typingInput: document.getElementById('typingInput'),
    referenceText: document.getElementById('referenceText'),
    keyBubbles: document.getElementById('keyBubbles'),
    usernameInput: document.getElementById('usernameInput'),
    existingUserSelect: document.getElementById('existingUserSelect'),
    newUserBtn: document.getElementById('newUserBtn'),
    existingUserBtn: document.getElementById('existingUserBtn'),
    registerBtn: document.getElementById('registerBtn'),
    identifyBtn: document.getElementById('identifyBtn'),
    resetBtn: document.getElementById('resetBtn'),
    matchesList: document.getElementById('matchesList'),
    usersList: document.getElementById('usersList'),
    typingSpeed: document.getElementById('typingSpeed'),
    avgLatency: document.getElementById('avgLatency'),
    accuracy: document.getElementById('accuracy'),
    totalUsers: document.getElementById('totalUsers'),
    systemTotalUsers: document.getElementById('systemTotalUsers'),
    systemTotalSamples: document.getElementById('systemTotalSamples'),
    systemAvgSamples: document.getElementById('systemAvgSamples'),
    apiStatus: document.getElementById('apiStatus'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    toastContainer: document.getElementById('toastContainer'),
    featuresGrid: document.getElementById('featuresGrid'),
    userDetailsModal: document.getElementById('userDetailsModal'),
    closeModal: document.getElementById('closeModal'),
    modalBody: document.getElementById('modalBody')
};

let isExistingUser = false;

// ========================================
// Инициализация
// ========================================

function init() {
    state.referenceText = elements.referenceText.textContent.trim();
    setupEventListeners();
    checkAPIHealth();
    loadSystemStats();
    loadExistingUsers();
    loadRegisteredUsers(); // Load registered users list
    updateFeaturesVisualizationRealtime(); // Initialize features panel
    updateUI();
}

// ========================================
// Event Listeners
// ========================================

function setupEventListeners() {
    // Захват нажатий клавиш
    elements.typingInput.addEventListener('keydown', handleKeyDown);
    elements.typingInput.addEventListener('keyup', handleKeyUp);
    elements.typingInput.addEventListener('input', handleInput);
    
    // Кнопки действий
    elements.registerBtn.addEventListener('click', handleRegister);
    elements.identifyBtn.addEventListener('click', handleIdentify);
    elements.resetBtn.addEventListener('click', handleReset);
    
    // Проверка имени пользователя
    elements.usernameInput.addEventListener('input', updateButtonStates);
    elements.existingUserSelect.addEventListener('change', updateButtonStates);
    
    // Переключение между новым и существующим пользователем
    elements.newUserBtn.addEventListener('click', () => toggleUserMode(false));
    elements.existingUserBtn.addEventListener('click', () => toggleUserMode(true));
    
    // Модальное окно
    elements.closeModal.addEventListener('click', closeUserDetailsModal);
    elements.userDetailsModal.addEventListener('click', (e) => {
        if (e.target === elements.userDetailsModal) {
            closeUserDetailsModal();
        }
    });
}

// ========================================
// Обработка нажатий клавиш
// ========================================

function handleKeyDown(event) {
    const timestamp = Date.now();
    
    // Начало набора
    if (!state.isTyping) {
        state.isTyping = true;
        state.startTime = timestamp;
    }
    
    // Игнорируем специальные клавиши для отображения
    const ignoreKeys = ['Shift', 'Control', 'Alt', 'Meta', 'CapsLock', 'Tab'];
    if (!ignoreKeys.includes(event.key)) {
        addKeyBubble(event.key);
    }
    
    // Записываем событие
    state.keystrokeEvents.push({
        type: 'keydown',
        key: event.key,
        code: event.code,
        timestamp: timestamp,
        keyCode: event.keyCode
    });
    
    updateRealtimeStats();
}

function handleKeyUp(event) {
    const timestamp = Date.now();
    
    state.keystrokeEvents.push({
        type: 'keyup',
        key: event.key,
        code: event.code,
        timestamp: timestamp,
        keyCode: event.keyCode
    });
}

function handleInput(event) {
    state.currentText = event.target.value;
    updateAccuracy();
    updateButtonStates();
    updateFeaturesVisualizationRealtime();
}

// ========================================
// UI Updates
// ========================================

function addKeyBubble(key) {
    const bubble = document.createElement('div');
    bubble.className = 'key-bubble';
    
    // Отображение специальных символов
    const displayKey = {
        ' ': 'Space',
        'Enter': '↵',
        'Backspace': '⌫',
        'Delete': 'Del',
        'ArrowUp': '↑',
        'ArrowDown': '↓',
        'ArrowLeft': '←',
        'ArrowRight': '→'
    }[key] || key;
    
    bubble.textContent = displayKey.length > 1 ? displayKey.substring(0, 3) : displayKey;
    
    elements.keyBubbles.appendChild(bubble);
    
    // Ограничиваем количество пузырьков
    const bubbles = elements.keyBubbles.querySelectorAll('.key-bubble');
    if (bubbles.length > 20) {
        bubbles[0].remove();
    }
}

function updateRealtimeStats() {
    // Скорость печати (символов в минуту)
    if (state.startTime && state.currentText.length > 0) {
        const elapsedMinutes = (Date.now() - state.startTime) / 60000;
        const cpm = Math.round(state.currentText.length / elapsedMinutes);
        elements.typingSpeed.textContent = cpm;
    }
    
    // Средняя задержка между нажатиями
    const keydownEvents = state.keystrokeEvents.filter(e => e.type === 'keydown');
    if (keydownEvents.length > 1) {
        const latencies = [];
        for (let i = 1; i < keydownEvents.length; i++) {
            latencies.push(keydownEvents[i].timestamp - keydownEvents[i-1].timestamp);
        }
        const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
        elements.avgLatency.textContent = Math.round(avgLatency);
    }
}

function updateAccuracy() {
    if (state.currentText.length === 0) {
        elements.accuracy.textContent = '0%';
        return;
    }
    
    let correct = 0;
    const minLength = Math.min(state.currentText.length, state.referenceText.length);
    
    for (let i = 0; i < minLength; i++) {
        if (state.currentText[i] === state.referenceText[i]) {
            correct++;
        }
    }
    
    const accuracy = Math.round((correct / minLength) * 100);
    elements.accuracy.textContent = `${accuracy}%`;
}

function updateButtonStates() {
    const hasText = state.currentText.trim().length > 0;
    const hasUsername = isExistingUser 
        ? elements.existingUserSelect.value.trim().length > 0
        : elements.usernameInput.value.trim().length > 0;
    const hasMinimalData = state.keystrokeEvents.length > 10;
    
    elements.registerBtn.disabled = !(hasText && hasUsername && hasMinimalData);
    elements.identifyBtn.disabled = !(hasText && hasMinimalData);
}

function updateUI() {
    updateButtonStates();
    updateRealtimeStats();
    updateAccuracy();
}

// ========================================
// API взаимодействие
// ========================================

async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            elements.apiStatus.innerHTML = '<span class="status-dot"></span>Online';
            return true;
        }
    } catch (error) {
        elements.apiStatus.innerHTML = '<span class="status-dot error"></span>Offline';
        showToast('Failed to connect to API. Make sure backend is running.', 'error');
    }
    return false;
}

async function loadSystemStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        if (!response.ok) return;
        
        const data = await response.json();
        if (data.success) {
            elements.totalUsers.textContent = data.stats.total_users;
            elements.systemTotalUsers.textContent = data.stats.total_users;
            elements.systemTotalSamples.textContent = data.stats.total_samples;
            elements.systemAvgSamples.textContent = data.stats.avg_samples_per_user.toFixed(1);
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function handleRegister() {
    const username = isExistingUser 
        ? elements.existingUserSelect.value.trim()
        : elements.usernameInput.value.trim();
    
    if (!username) {
        showToast('Please enter or select a username', 'error');
        return;
    }
    
    if (state.keystrokeEvents.length < 10) {
        showToast('Insufficient data. Continue typing.', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                text: state.currentText,
                keystroke_events: state.keystrokeEvents
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(
                `✓ Pattern registered! Samples: ${data.samples_count}`,
                'success'
            );
            loadSystemStats();
            loadExistingUsers();
            loadRegisteredUsers(); // Update users list
        } else {
            showToast(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showToast(`Network error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

async function handleIdentify() {
    if (state.keystrokeEvents.length < 10) {
        showToast('Insufficient data. Continue typing.', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/identify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: state.currentText,
                keystroke_events: state.keystrokeEvents
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayMatches(data.matches);
            if (data.matches.length > 0) {
                showToast('🔍 Identification complete!', 'success');
            } else {
                showToast('No matches found. Register your pattern.', 'info');
            }
        } else {
            showToast(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showToast(`Network error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

function handleReset() {
    state.keystrokeEvents = [];
    state.startTime = null;
    state.isTyping = false;
    state.currentText = '';
    
    elements.typingInput.value = '';
    elements.keyBubbles.innerHTML = '';
    elements.typingSpeed.textContent = '0';
    elements.avgLatency.textContent = '0';
    elements.accuracy.textContent = '0%';
    
    // Очищаем панель признаков
    updateFeaturesVisualizationRealtime();
    
    // Не очищаем имя пользователя, чтобы было удобнее
    
    updateUI();
    showToast('Data cleared', 'info');
}

// ========================================
// Отображение результатов
// ========================================

function displayMatches(matches) {
    if (!matches || matches.length === 0) {
        elements.matchesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">👤</div>
                <p>No matches found</p>
                <p class="empty-hint">Try registering your pattern</p>
            </div>
        `;
        return;
    }
    
    elements.matchesList.innerHTML = '';
    
    matches.forEach((match, index) => {
        const matchItem = document.createElement('div');
        matchItem.className = 'match-item';
        
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : 'default';
        
        matchItem.innerHTML = `
            <div class="match-header">
                <div class="match-rank">
                    <div class="rank-badge ${rankClass}">${index + 1}</div>
                    <span class="match-username">${escapeHtml(match.username)}</span>
                </div>
                <div class="similarity-badge">${Math.round(match.similarity)}%</div>
            </div>
            <div class="match-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${match.similarity}%"></div>
                </div>
            </div>
            <div class="match-info">
                <span>Samples: ${match.samples_count}</span>
                <span>Confidence: ${Math.round(match.confidence)}%</span>
            </div>
        `;
        
        // Добавляем обработчик клика для просмотра деталей
        matchItem.addEventListener('click', () => showUserDetails(match.username));
        
        elements.matchesList.appendChild(matchItem);
    });
}

// ========================================
// Toast уведомления
// ========================================

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========================================
// Loading overlay
// ========================================

function showLoading(show) {
    if (show) {
        elements.loadingOverlay.classList.add('active');
    } else {
        elements.loadingOverlay.classList.remove('active');
    }
}

// ========================================
// Утилиты
// ========================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========================================
// Периодические обновления
// ========================================

// Обновляем статистику системы каждые 10 секунд
setInterval(loadSystemStats, 10000);

// Обновляем список пользователей каждые 15 секунд
setInterval(loadRegisteredUsers, 15000);

// Проверяем API каждые 30 секунд
setInterval(checkAPIHealth, 30000);

// ========================================
// Запуск приложения
// ========================================

document.addEventListener('DOMContentLoaded', init);

// ========================================
// Real-time Features Visualization
// ========================================

function calculateRealtimeFeatures() {
    const keydownEvents = state.keystrokeEvents.filter(e => e.type === 'keydown');
    const keyupEvents = state.keystrokeEvents.filter(e => e.type === 'keyup');
    
    if (keydownEvents.length < 2) {
        return null;
    }
    
    // Dwell times
    const dwellTimes = [];
    for (const kd of keydownEvents) {
        const matchingKu = keyupEvents.find(ku => 
            ku.key === kd.key && ku.timestamp > kd.timestamp
        );
        if (matchingKu) {
            dwellTimes.push(matchingKu.timestamp - kd.timestamp);
        }
    }
    
    // Inter-key latencies
    const latencies = [];
    for (let i = 1; i < keydownEvents.length; i++) {
        latencies.push(keydownEvents[i].timestamp - keydownEvents[i-1].timestamp);
    }
    
    // Flight times
    const flightTimes = [];
    for (let i = 0; i < keyupEvents.length - 1; i++) {
        if (i + 1 < keydownEvents.length) {
            const flight = keydownEvents[i + 1].timestamp - keyupEvents[i].timestamp;
            if (flight > 0) {
                flightTimes.push(flight);
            }
        }
    }
    
    // Rhythm consistency
    let rhythmConsistency = 0;
    if (latencies.length > 1) {
        const mean = latencies.reduce((a, b) => a + b, 0) / latencies.length;
        const variance = latencies.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / latencies.length;
        const std = Math.sqrt(variance);
        const cv = mean > 0 ? std / mean : 0;
        rhythmConsistency = 1 / (1 + cv);
    }
    
    return {
        dwell_mean: dwellTimes.length > 0 ? dwellTimes.reduce((a, b) => a + b, 0) / dwellTimes.length : 0,
        latency_mean: latencies.length > 0 ? latencies.reduce((a, b) => a + b, 0) / latencies.length : 0,
        flight_mean: flightTimes.length > 0 ? flightTimes.reduce((a, b) => a + b, 0) / flightTimes.length : 0,
        rhythm_consistency: rhythmConsistency,
        typing_speed: elements.typingSpeed.textContent ? parseInt(elements.typingSpeed.textContent) : 0
    };
}

function updateFeaturesVisualizationRealtime() {
    const features = calculateRealtimeFeatures();
    
    if (!features) {
        // Показываем пустое состояние
        elements.featuresGrid.innerHTML = `
            <div class="feature-item">
                <span class="feature-label">Dwell Time</span>
                <div class="feature-bar">
                    <div class="feature-fill" style="width: 0%"></div>
                </div>
                <span class="feature-value">0 ms</span>
            </div>
            <div class="feature-item">
                <span class="feature-label">Flight Time</span>
                <div class="feature-bar">
                    <div class="feature-fill" style="width: 0%"></div>
                </div>
                <span class="feature-value">0 ms</span>
            </div>
            <div class="feature-item">
                <span class="feature-label">Rhythm Consistency</span>
                <div class="feature-bar">
                    <div class="feature-fill" style="width: 0%"></div>
                </div>
                <span class="feature-value">0%</span>
            </div>
        `;
        return;
    }
    
    const featureItems = [
        {
            label: 'Dwell Time',
            value: features.dwell_mean,
            max: 200,
            unit: 'ms',
            color: '#667eea'
        },
        {
            label: 'Inter-key Latency',
            value: features.latency_mean,
            max: 300,
            unit: 'ms',
            color: '#764ba2'
        },
        {
            label: 'Flight Time',
            value: features.flight_mean,
            max: 200,
            unit: 'ms',
            color: '#f093fb'
        },
        {
            label: 'Rhythm Consistency',
            value: features.rhythm_consistency * 100,
            max: 100,
            unit: '%',
            color: '#4ade80'
        },
        {
            label: 'Typing Speed',
            value: features.typing_speed,
            max: 500,
            unit: 'CPM',
            color: '#fbbf24'
        }
    ];
    
    let html = '';
    featureItems.forEach(item => {
        const percentage = Math.min((item.value / item.max) * 100, 100);
        html += `
            <div class="feature-item">
                <span class="feature-label">${item.label}</span>
                <div class="feature-bar">
                    <div class="feature-fill" style="width: ${percentage}%; background: ${item.color};"></div>
                </div>
                <span class="feature-value">${Math.round(item.value)} ${item.unit}</span>
            </div>
        `;
    });
    
    elements.featuresGrid.innerHTML = html;
}

// Дополнительная визуализация признаков (для статических данных)
function updateFeaturesVisualization(features) {
    if (!features) return;
    
    const featureItems = [
        {
            label: 'Dwell Time',
            value: features.dwell_mean || 0,
            max: 200,
            unit: 'ms'
        },
        {
            label: 'Flight Time',
            value: features.flight_mean || 0,
            max: 200,
            unit: 'ms'
        },
        {
            label: 'Rhythm Consistency',
            value: (features.rhythm_consistency || 0) * 100,
            max: 100,
            unit: '%'
        }
    ];
    
    let html = '';
    featureItems.forEach(item => {
        const percentage = Math.min((item.value / item.max) * 100, 100);
        html += `
            <div class="feature-item">
                <span class="feature-label">${item.label}</span>
                <div class="feature-bar">
                    <div class="feature-fill" style="width: ${percentage}%"></div>
                </div>
                <span class="feature-value">${Math.round(item.value)} ${item.unit}</span>
            </div>
        `;
    });
    
    elements.featuresGrid.innerHTML = html;
}

// ========================================
// User Mode Toggle
// ========================================

function toggleUserMode(existing) {
    isExistingUser = existing;
    
    if (existing) {
        elements.newUserBtn.classList.remove('active');
        elements.existingUserBtn.classList.add('active');
        elements.usernameInput.style.display = 'none';
        elements.existingUserSelect.style.display = 'block';
    } else {
        elements.newUserBtn.classList.add('active');
        elements.existingUserBtn.classList.remove('active');
        elements.usernameInput.style.display = 'block';
        elements.existingUserSelect.style.display = 'none';
    }
    
    updateButtonStates();
}

// ========================================
// Load Existing Users
// ========================================

async function loadExistingUsers() {
    try {
        const response = await fetch(`${API_BASE_URL}/users`);
        if (!response.ok) return;
        
        const data = await response.json();
        if (data.success) {
            const select = elements.existingUserSelect;
            
            // Сохраняем текущий выбор
            const currentValue = select.value;
            
            // Очищаем и добавляем опции
            select.innerHTML = '<option value="">Select a user...</option>';
            
            data.users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.username;
                option.textContent = `${user.username} (${user.samples_count} samples)`;
                select.appendChild(option);
            });
            
            // Восстанавливаем выбор если возможно
            if (currentValue && data.users.some(u => u.username === currentValue)) {
                select.value = currentValue;
            }
        }
    } catch (error) {
        console.error('Failed to load users:', error);
    }
}

// ========================================
// User Details Modal
// ========================================

async function showUserDetails(username) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/user/${encodeURIComponent(username)}`);
        if (!response.ok) {
            showToast('Failed to load user data', 'error');
            return;
        }
        
        const data = await response.json();
        if (!data.success) {
            showToast(`Error: ${data.error}`, 'error');
            return;
        }
        
        const user = data.user;
        const features = user.averaged_features;
        const stats = user.variation_stats;
        
        // Формируем HTML для модального окна
        let html = `
            <div class="user-info-header">
                <h3>👤 ${escapeHtml(username)}</h3>
                <div class="user-badge">${user.samples_count} samples</div>
            </div>
            
            <h4 style="margin-bottom: 1rem; color: var(--text-secondary);">📊 Average Typing Parameters</h4>
            <div class="param-grid">
        `;
        
        // Основные параметры
        const mainParams = [
            { key: 'dwell_mean', label: 'Dwell Time', unit: 'ms', category: 'timing' },
            { key: 'latency_mean', label: 'Inter-key Latency', unit: 'ms', category: 'timing' },
            { key: 'flight_mean', label: 'Flight Time', unit: 'ms', category: 'timing' },
            { key: 'typing_speed', label: 'Typing Speed', unit: 'CPM', category: 'speed' },
            { key: 'rhythm_consistency', label: 'Rhythm Consistency', unit: '', category: 'pattern', multiplier: 100 },
            { key: 'digraph_mean', label: 'Average Digraph Time', unit: 'ms', category: 'timing' }
        ];
        
        mainParams.forEach(param => {
            let value = features[param.key] || 0;
            if (param.multiplier) value *= param.multiplier;
            
            const variation = stats[param.key];
            let variationText = '';
            
            if (variation && user.samples_count > 1) {
                const range = (variation.max - variation.min).toFixed(1);
                variationText = `<div class="param-variation">Range: ±${range} ${param.unit}</div>`;
            }
            
            html += `
                <div class="param-card">
                    <h4>${param.label}</h4>
                    <div class="param-value">${value.toFixed(1)} ${param.unit}</div>
                    ${variationText}
                </div>
            `;
        });
        
        html += `</div>`;
        
        // Дополнительная статистика
        html += `
            <h4 style="margin: 2rem 0 1rem 0; color: var(--text-secondary);">📈 Detailed Statistics</h4>
            <div class="param-grid">
                <div class="param-card">
                    <h4>Dwell Std Dev</h4>
                    <div class="param-value">${features.dwell_std.toFixed(2)} ms</div>
                </div>
                <div class="param-card">
                    <h4>Latency Std Dev</h4>
                    <div class="param-value">${features.latency_std.toFixed(2)} ms</div>
                </div>
                <div class="param-card">
                    <h4>Dwell Median</h4>
                    <div class="param-value">${features.dwell_median.toFixed(1)} ms</div>
                </div>
                <div class="param-card">
                    <h4>Latency Median</h4>
                    <div class="param-value">${features.latency_median.toFixed(1)} ms</div>
                </div>
                <div class="param-card">
                    <h4>Min Dwell Time</h4>
                    <div class="param-value">${features.dwell_min.toFixed(1)} ms</div>
                </div>
                <div class="param-card">
                    <h4>Max Dwell Time</h4>
                    <div class="param-value">${features.dwell_max.toFixed(1)} ms</div>
                </div>
            </div>
        `;
        
        // Информация о создании
        html += `
            <div style="margin-top: 2rem; padding: 1rem; background: var(--background); border-radius: var(--radius-md); font-size: 0.875rem; color: var(--text-muted);">
                <div>Created: ${new Date(user.created_at).toLocaleString('en-US')}</div>
                <div style="margin-top: 0.5rem;">Last updated: ${new Date(user.last_updated).toLocaleString('en-US')}</div>
            </div>
        `;
        
        elements.modalBody.innerHTML = html;
        elements.userDetailsModal.classList.add('active');
        
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

function closeUserDetailsModal() {
    elements.userDetailsModal.classList.remove('active');
}

// ========================================
// Registered Users List
// ========================================

async function loadRegisteredUsers() {
    try {
        const response = await fetch(`${API_BASE_URL}/users`);
        if (!response.ok) return;
        
        const data = await response.json();
        if (!data.success || !data.users || data.users.length === 0) {
            elements.usersList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">👤</div>
                    <p>No users yet</p>
                    <p class="empty-hint">Register your pattern</p>
                </div>
            `;
            return;
        }
        
        // Сортируем пользователей по последнему обновлению
        const users = data.users.sort((a, b) => {
            return new Date(b.last_updated || b.created_at) - new Date(a.last_updated || a.created_at);
        });
        
        // Формируем HTML для списка пользователей
        let html = '';
        users.forEach(user => {
            const initials = user.username.substring(0, 2).toUpperCase();
            const lastUpdate = user.last_updated || user.created_at;
            const updateDate = new Date(lastUpdate);
            const timeAgo = getTimeAgo(updateDate);
            
            html += `
                <div class="user-item" data-username="${escapeHtml(user.username)}">
                    <div class="user-item-info">
                        <div class="user-item-avatar">${initials}</div>
                        <div class="user-item-details">
                            <div class="user-item-name">${escapeHtml(user.username)}</div>
                            <div class="user-item-meta">${timeAgo}</div>
                        </div>
                    </div>
                    <div class="user-item-stats">
                        <span class="user-stat-badge">📊 ${user.samples_count} samples</span>
                    </div>
                </div>
            `;
        });
        
        elements.usersList.innerHTML = html;
        
        // Добавляем обработчики клика
        const userItems = elements.usersList.querySelectorAll('.user-item');
        userItems.forEach(item => {
            item.addEventListener('click', () => {
                const username = item.getAttribute('data-username');
                showUserDetails(username);
            });
        });
        
    } catch (error) {
        console.error('Failed to load registered users:', error);
    }
}

function getTimeAgo(date) {
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'just now';
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hr ago`;
    
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days} d ago`;
    
    if (days < 30) return `${Math.floor(days / 7)} wk ago`;
    
    return date.toLocaleDateString('en-US');
}

