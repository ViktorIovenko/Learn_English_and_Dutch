(() => {
  const params = new URLSearchParams(location.search);
  const input = document.getElementById('family-code');
  if (!input) return;
  const dialog = document.getElementById('family-code-dialog');
  const form = document.getElementById('family-code-form');
  const submit = document.getElementById('family-preview-submit');
  const closeButton = document.getElementById('family-close');
  const confirmation = document.getElementById('family-confirmation');
  const accept = document.getElementById('family-accept');
  const status = document.getElementById('family-status');
  const cancel = document.getElementById('family-cancel');
  let invitation = null;
  let busy = false;
  let retryAfterAuth = false;
  let accepting = false;
  let controller = null;
  let generation = 0;
  const tr = (key, args) => window.I18N.t(key, args);
  const remember = () => { if (!dialog) sessionStorage.setItem('family_pending_url', location.pathname + location.search); };
  function setBusy(value) {
    busy = value;
    input.disabled = value;
    submit.disabled = value;
    accept.disabled = value;
    cancel.disabled = accepting;
    closeButton.disabled = accepting;
  }
  function dismiss() {
    if (accepting) return;
    if (dialog) dialog.close();
    else { sessionStorage.removeItem('family_pending_url'); location.replace('/settings'); }
  }
  if (dialog) {
    window.FamilyInvitation = {open() {
      if (dialog.open) return;
      generation++;
      invitation = null;
      input.value = '';
      status.textContent = '';
      form.hidden = false;
      confirmation.hidden = true;
      accept.hidden = true;
      setBusy(false);
      dialog.showModal();
      document.body.classList.add('family-invite-open');
      input.focus();
    }};
    dialog.addEventListener('close', () => {
      document.body.classList.remove('family-invite-open');
      generation++;
      if (controller) controller.abort();
      invitation = null;
      setBusy(false);
    });
    dialog.addEventListener('cancel', event => { if (accepting) event.preventDefault(); });
    dialog.addEventListener('click', event => {
      const rect = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dismiss();
    });
  }
  if (!dialog && params.get('code')) {
    input.value = params.get('code');
    remember();
    // Opening the same URL in Telegram uses the same server invitation.
    const bot = document.getElementById('family-bot');
    if (window.FAMILY_BOT_USERNAME) {
      bot.href = `https://t.me/${window.FAMILY_BOT_USERNAME}?start=${params.get('kind') === 'invite' ? 'invite' : 'family'}_${encodeURIComponent(input.value)}`;
      bot.hidden = false;
    }
  }
  function errorText(error) {
    return tr(error === 'parent_limit_reached' ? 'family.parent_limit' :
      error === 'too_many_attempts' ? 'family.too_many_attempts' :
      ['parent_account_required', 'child_account_required', 'parent_cannot_be_child', 'child_cannot_be_parent'].includes(error) ? 'family.wrong_account' : 'family.invalid');
  }
  async function preview(event) {
    if (event) event.preventDefault();
    if (!input.value.trim() || busy) return;
    const currentGeneration = generation;
    controller = new AbortController();
    setBusy(true);
    invitation = null;
    accept.hidden = true;
    document.getElementById('family-permissions').hidden = true;
    try {
      const response = await window.apiFetch('/api/family/invitation/preview', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code: input.value.trim(), kind: dialog ? '' : params.get('kind') || ''}),
        signal: controller.signal
      });
      const data = await response.json();
      if (currentGeneration !== generation) return;
      if (response.status === 401) return;
      if (!response.ok || !data.ok) throw new Error(data.error);
      invitation = {code: data.code, kind: data.kind};
      if (!dialog) history.replaceState(null, '', '/family/connect?' + new URLSearchParams(invitation));
      remember();
      document.getElementById('family-preview').textContent = tr('family.confirm_accounts', {account: data.account_name, name: data.display_name});
      document.getElementById('family-permissions').hidden = false;
      confirmation.hidden = false;
      form.hidden = true;
      accept.hidden = false;
      cancel.hidden = false;
      status.textContent = '';
    } catch (error) {
      if (error.name !== 'AbortError' && currentGeneration === generation) status.textContent = errorText(error.message);
    }
    finally {
      if (currentGeneration !== generation) return;
      setBusy(false);
      if (retryAfterAuth) { retryAfterAuth = false; preview(); }
    }
  }
  input.addEventListener('input', () => { invitation = null; accept.hidden = true; confirmation.hidden = true; });
  form.addEventListener('submit', preview);
  accept.addEventListener('click', async () => {
    if (!invitation || busy) return;
    accepting = true;
    setBusy(true);
    try {
      const response = await window.apiFetch('/api/family/invitation/accept', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(invitation)
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error);
      if (dialog) {
        accepting = false;
        dialog.close();
        document.dispatchEvent(new CustomEvent('family-connected'));
      } else {
        sessionStorage.removeItem('family_pending_url');
        location.replace('/settings');
      }
    } catch (error) { status.textContent = errorText(error.message); }
    finally { accepting = false; setBusy(false); }
  });
  cancel.addEventListener('click', dismiss);
  closeButton.addEventListener('click', dismiss);
  document.addEventListener('hello-name-ready', () => {
    if (dialog || invitation) return;
    if (busy) retryAfterAuth = true;
    else preview();
  });
  if (!dialog) preview();
})();
