// Standalone personal MCP connector.
function _esc(s) {
  if (s == null) return '';
  if (Array.isArray(s)) s = s[0] ?? '';
  if (typeof s !== 'string') s = String(s);
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function _jsArg(s) {
  if (s == null) return "''";
  if (Array.isArray(s)) s = s[0] ?? '';
  return JSON.stringify(String(s)).replace(/</g, '\\u003c');
}

// ── Personal MCP connector ─────────────────────────────────────
let _mcpLoaded = false;
let _mcpData = null;

function _mcpIsRussian() {
  return (window.I18N?.language || 'en') === 'ru';
}

function _mcpText(ru, en) {
  return window.I18N.legacy(ru);
}

function _mcpDate(timestamp) {
  if (!timestamp) return _mcpText('ещё не использовалось', 'not used yet');
  return new Date(Number(timestamp) * 1000).toLocaleString(window.I18N.language || 'en');
}

async function mcpCopy(value, button) {
  if (!value) return;
  try {
    await navigator.clipboard.writeText(value);
  } catch (_) {
    const input = document.createElement('textarea');
    input.value = value;
    input.style.position = 'fixed';
    input.style.opacity = '0';
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    input.remove();
  }
  if (button) {
    const previous = button.textContent;
    button.textContent = _mcpText('Скопировано', 'Copied');
    setTimeout(() => { button.textContent = previous; }, 1200);
  }
}

function _mcpDetail(label, value, wide) {
  return `<div class="mcp-detail${wide ? ' wide' : ''}">
    <span class="mcp-detail-label">${_esc(label)}</span>
    <div class="mcp-copy-row">
      <span class="mcp-copy-value" title="${_esc(value)}">${_esc(value)}</span>
      <button type="button" class="mcp-copy-btn">${_mcpText('Копировать', 'Copy')}</button>
    </div>
  </div>`;
}

function mcpRender(data) {
  _mcpData = data;
  const connector = data.connector || {};
  const content = document.getElementById('mcp-user-content');
  const toggle = document.getElementById('mcp-enabled-toggle');
  const toggleLabel = document.getElementById('mcp-toggle-label');
  const name = document.getElementById('mcp-user-name');
  const description = document.getElementById('mcp-user-description');
  const icon = document.getElementById('mcp-user-icon');
  const heroImage = document.getElementById('mcp-user-art');
  if (!content || !toggle) return;

  toggle.disabled = false;
  toggle.checked = data.enabled === true;
  toggleLabel.textContent = data.enabled
    ? _mcpText('Коннектор включён', 'Connector enabled')
    : _mcpText('Коннектор выключен', 'Connector disabled');
  name.textContent = connector.name || 'ParallelLingvo';
  description.textContent = window.I18N.t('mcp.note');
  if (connector.icon_url) icon.src = connector.icon_url;
  if (connector.hero_image_url && heroImage) heroImage.src = connector.hero_image_url;

  const states = {
    connected: _mcpText('Подключён и активен', 'Connected and active'),
    paused: _mcpText('Подключён, но приостановлен', 'Connected but paused'),
    ready: _mcpText('Включён — ожидает подключения', 'Enabled — waiting for connection'),
    disabled: _mcpText('Выключен', 'Disabled'),
  };
  const connections = Array.isArray(data.connections) ? data.connections : [];
  const googleAccount = data.google_account || {};
  const googleLinkResult = new URLSearchParams(window.location.search || '').get('google_link');
  const googleMessages = {
    linked: _mcpText('Google-аккаунт успешно привязан к вашему профилю.', 'Google account was linked to your profile.'),
    conflict: _mcpText('Этот Google-аккаунт уже привязан к другому профилю.', 'This Google account is already linked to another profile.'),
    auth_required: _mcpText('Сессия закончилась. Войдите через Telegram и повторите привязку.', 'Your session expired. Sign in with Telegram and try again.'),
    user_not_found: _mcpText('Профиль пользователя не найден.', 'User profile was not found.'),
    error: _mcpText('Не удалось привязать Google-аккаунт.', 'Could not link the Google account.'),
  };
  const googleMessage = googleMessages[googleLinkResult] || '';
  const googleMessageClass = googleLinkResult === 'linked' ? '' : ' error';
  const googleIcon = `<svg width="21" height="21" viewBox="0 0 48 48" aria-hidden="true"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.6 32.8 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 7.9 3l5.7-5.7C34.1 6.5 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.2-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.5 16.1 18.9 13 24 13c3.1 0 5.8 1.1 7.9 3l5.7-5.7C34.1 6.5 29.3 4 24 4c-7.5 0-14 4.1-17.7 10.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.3 26.7 36 24 36c-5.2 0-9.5-3.2-11.3-7.7l-6.6 5.1C9.8 40 16.4 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.4 4.3-4.4 5.6l6.2 5.2C36.9 37.2 44 32 44 24c0-1.2-.1-2.4-.4-3.5z"/></svg>`;
  const googleBlock = `<div class="mcp-google-card">
    <div class="mcp-google-info">
      <span class="mcp-google-icon">${googleIcon}</span>
      <div><div class="mcp-google-title">${_mcpText('Google-аккаунт', 'Google account')}</div>
      <div class="mcp-google-meta">${_esc(googleAccount.linked ? (googleAccount.email || _mcpText('Привязан к профилю ParallelLingvo', 'Linked to your ParallelLingvo profile')) : _mcpText('Используйте Google для входа в этот же профиль', 'Use Google to sign in to this same profile'))}</div></div>
    </div>
    ${googleAccount.linked
      ? `<span class="mcp-google-badge">${_mcpText('Привязан', 'Linked')}</span>`
      : `<a class="mcp-google-btn" href="/auth/google?mode=link&amp;next=%2Fsettings%2Fmcp">${googleIcon}${_mcpText('Привязать Google', 'Link Google')}</a>`}
  </div>`;
  const connectorDescription = window.I18N.t('mcp.note');
  const details = [
    [_mcpText('URL коннектора', 'Connector URL'), connector.mcp_url, true],
    [_mcpText('Название', 'Name'), connector.name, false],
    [_mcpText('Краткое описание', 'Description'), connectorDescription, true],
    [_mcpText('Версия', 'Version'), connector.version, false],
    [_mcpText('Издатель OAuth', 'OAuth issuer'), connector.issuer, true],
    [_mcpText('Транспорт', 'Transport'), connector.transport, false],
    [_mcpText('Авторизация', 'Authorization'), connector.authorization, false],
    [_mcpText('Метаданные OAuth', 'OAuth metadata'), connector.authorization_metadata, true],
    [_mcpText('Метаданные ресурса', 'Resource metadata'), connector.resource_metadata, true],
    [_mcpText('URL иконки', 'Icon URL'), connector.icon_url, true],
  ];
  const connectionItems = connections.map((item) => `<div class="mcp-connection-item">
    <div><div class="mcp-connection-name">${_esc(item.client_name)}</div><div>${_esc((item.scopes || []).join(', '))}</div></div>
    <div class="mcp-connection-meta">${_mcpText('Последнее использование', 'Last used')}:<br>${_esc(_mcpDate(item.last_used_at))}</div>
  </div>`).join('');

  content.innerHTML = `
    ${googleMessage ? `<div class="mcp-google-message${googleMessageClass}">${_esc(googleMessage)}</div>` : ''}
    ${googleBlock}
    <div class="mcp-status-row">
      <div class="mcp-status ${_esc(data.state)}">${_esc(states[data.state] || data.state)}</div>
      <div class="mcp-connection-count">${_mcpText('Активных подключений', 'Active connections')}: ${connections.length}</div>
    </div>
    <div class="mcp-details-grid">${details.map(item => _mcpDetail(item[0], item[1] || '—', item[2])).join('')}</div>
    <div class="mcp-help"><strong>${_mcpText('Как подключить:', 'How to connect:')}</strong> ${_mcpText(
      'скопируйте URL коннектора, добавьте его как пользовательский MCP-коннектор в настройках вашего ИИ-ассистента и войдите в свой аккаунт ParallelLingvo на странице авторизации.',
      'copy the connector URL, add it as a custom MCP connector in your AI assistant\'s settings, then sign in to your ParallelLingvo account on the authorization page.'
    )}</div>
    <div class="mcp-actions">
      <button type="button" class="mcp-primary-btn" id="mcp-copy-all">${_mcpText('Скопировать данные подключения', 'Copy connection details')}</button>
      <a class="mcp-secondary-btn" id="mcp-download-icon" href="${_esc(connector.icon_url || '')}" download="parallellingvo-mcp-icon.png">${_mcpText('Скачать значок коннектора', 'Download connector icon')}</a>
      <button type="button" class="mcp-danger-btn" id="mcp-revoke-all" ${connections.length ? '' : 'hidden'}>${_mcpText('Отозвать все подключения', 'Revoke all connections')}</button>
    </div>
    <div class="mcp-connections" ${connections.length ? '' : 'hidden'}>
      <h3 class="mcp-connections-title">${_mcpText('Подключённые клиенты', 'Connected clients')}</h3>
      ${connectionItems}
    </div>`;

  content.querySelectorAll('.mcp-detail').forEach((detail, index) => {
    const button = detail.querySelector('.mcp-copy-btn');
    button?.addEventListener('click', () => mcpCopy(details[index][1] || '', button));
  });
  document.getElementById('mcp-copy-all')?.addEventListener('click', (event) => {
    const text = details.map(item => `${item[0]}: ${item[1] || '—'}`).join('\n');
    mcpCopy(text, event.currentTarget);
  });
  document.getElementById('mcp-revoke-all')?.addEventListener('click', mcpRevokeAll);
}

async function mcpLoad(force) {
  if (_mcpLoaded && !force) return;
  const content = document.getElementById('mcp-user-content');
  try {
    const response = await apiFetch('/api/mcp/user');
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || 'MCP status failed');
    _mcpLoaded = true;
    mcpRender(data);
  } catch (error) {
    if (content) content.innerHTML = `<div class="mcp-loading">${_esc(_mcpText('Не удалось загрузить данные MCP.', 'Could not load MCP details.'))}</div>`;
  }
}

async function mcpToggle(enabled) {
  const toggle = document.getElementById('mcp-enabled-toggle');
  if (toggle) toggle.disabled = true;
  try {
    const response = await apiFetch('/api/mcp/user', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({enabled}),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || 'MCP update failed');
    _mcpLoaded = false;
    await mcpLoad(true);
  } catch (_) {
    if (toggle) toggle.checked = !enabled;
  } finally {
    if (toggle) toggle.disabled = false;
  }
}

async function mcpRevokeAll() {
  if (!confirm(_mcpText('Отозвать все подключения MCP? Для повторного подключения потребуется новая авторизация.', 'Revoke all MCP connections? A new authorization will be required to connect again.'))) return;
  const response = await apiFetch('/api/mcp/user/revoke-all', {method: 'POST'});
  const data = await response.json();
  if (!response.ok || !data.ok) {
    alert(_mcpText('Не удалось отозвать подключения.', 'Could not revoke connections.'));
    return;
  }
  _mcpLoaded = false;
  await mcpLoad(true);
}


document.addEventListener('DOMContentLoaded', () => mcpLoad());
document.addEventListener('hello-name-ready', () => mcpLoad());
