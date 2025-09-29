// Minimal script extracted for Manage Model Groups modal
// This file contains the functions that directly manipulate the modal DOM
// and wire the buttons. It calls into existing global helpers like
// `listModelGroups`, `callJsonApi`, `fetchApi`, and dispatches
// `model-groups-changed` where appropriate.

(function () {
  // Define logDebug function if not available
  function logDebug(message, error) {
    if (window.DEBUG || window.console) {
      console.log('[Model Groups Debug]', message, error || '');
    }
  }
  // NOTE: legacy hook wiring removed. Previously there was a helper to wire legacy
  // open/close hooks when the template was injected; that logic has been removed
  // to centralize all open/close behavior in this module.

  // Expose refresh helper so other modules can trigger a reload and event
  window.refreshAndDispatchModelGroups = async function () {
    try {
      const latest = await listModelGroups();
      document.dispatchEvent(new CustomEvent('model-groups-changed', { detail: latest }));
    } catch (e) {
      try { logDebug('Failed to listModelGroups during refreshAndDispatchModelGroups', e); } catch (err) { /* ignore */ }
    }
  };

  // Insert template into DOM when script loads if placeholder exists
  function insertTemplateIfNeeded() {
    try {
      const placeholder = document.querySelector('[data-mg-placeholder]');
      if (!placeholder) return;
      // avoid double-insert
      if (document.getElementById('modelGroupsModal')) return;

      const tpl = document.getElementById('tmpl-model-groups');
      if (!tpl) {
        // Try to fetch the component file and inject it
        fetch('components/settings/model-groups/model-groups.html', {credentials: 'same-origin'})
          .then(r => {
            if (!r.ok) throw new Error('Failed to fetch model-groups template');
            return r.text();
          })
          .then(html => {
            // create a temporary container to parse
            const tmp = document.createElement('div');
            tmp.innerHTML = html;
            // If the fetched html contains a <template id="tmpl-model-groups">, use it
            const fetchedTpl = tmp.querySelector('#tmpl-model-groups');
            if (fetchedTpl) {
              const clone = fetchedTpl.content.cloneNode(true);
              placeholder.parentNode.insertBefore(clone, placeholder.nextSibling);
            } else {
              // fallback: insert raw html
              placeholder.parentNode.insertAdjacentHTML('afterend', html);
            }
          })
          .catch(e => {
            console.error('Failed to load model-groups component', e);
          });
        return;
      }
      const clone = tpl.content.cloneNode(true);
      // Insert directly before placeholder to keep DOM order predictable
      placeholder.parentNode.insertBefore(clone, placeholder.nextSibling);

      // If Alpine is present and `settingsModalProxy` exposes modelGroupsOpen, ensure
      // the inserted overlay is not displayed until Alpine sets it.
  // Let Alpine control visibility (x-show/x-cloak) — do not force display here
  const overlay = document.getElementById('modelGroupsModal');

    } catch (e) {
      console.error('Failed to insert Model Groups template', e);
    }
  }

  // Provide an initialization function that resolves when the template is present.
  // Uses MutationObserver to avoid polling and to be robust across insertion timing.
  window.initModelGroupsComponent = function () {
    return new Promise((resolve) => {
      try {
        insertTemplateIfNeeded();
      } catch (e) {
        console.error('initModelGroupsComponent: insertTemplateIfNeeded failed', e);
      }

      // If already present, resolve immediately
      let overlay = document.getElementById('modelGroupsModal');
      if (overlay) {
        return resolve();
      }

      // Observe the document body for additions of the template element
      const observer = new MutationObserver((mutations, obs) => {
        for (const m of mutations) {
          for (const node of Array.from(m.addedNodes || [])) {
            try {
              if (node && node.querySelector && node.querySelector('#modelGroupsModal')) {
                obs.disconnect();
                return resolve();
              }
              // If the added node itself is the overlay
              if (node && node.id === 'modelGroupsModal') {
                obs.disconnect();
                return resolve();
              }
            } catch (e) {
              // ignore individual node errors
            }
          }
        }
      });

      try {
        observer.observe(document.documentElement || document.body, { childList: true, subtree: true });
        // As a non-polling fallback, resolve after a timeout to avoid leaving the
        // promise pending indefinitely in environments where MutationObserver may fail.
        // This is a single timeout (not polling).
        setTimeout(() => {
          try { observer.disconnect(); } catch (e) { /* ignore */ }
          return resolve();
        }, 10000);
      } catch (e) {
        // If observe itself throws, fall back to resolving after a short timeout.
        setTimeout(() => { return resolve(); }, 10000);
      }
    });
  };

  // Implement open/close here so other modules can simply call the globals.
  // These functions will control Alpine state if present, and ensure population occurs.
  window.openModelGroupsModal = async function () {
  try { if (window.DEBUG && console && typeof console.debug === 'function') console.debug('openModelGroupsModal invoked'); } catch (e) {}
    try {
      await window.initModelGroupsComponent();
    } catch (e) {
      logDebug('openModelGroupsModal: init failed', e);
    }

    // Use Alpine store to control modal visibility
    try {
      if (window.Alpine && window.Alpine.store) {
        const modelGroupsStore = window.Alpine.store('modelGroups');
        if (modelGroupsStore) {
          modelGroupsStore.open();
        }
      } else {
        // Fallback for when Alpine is not available
        const overlay = document.getElementById('modelGroupsModal');
        if (overlay) {
          overlay.style.display = 'block';
          overlay.setAttribute('x-show', 'true');
        } else {
          logDebug('openModelGroupsModal: no Alpine store or overlay found');
        }
      }
    } catch (e) {
      logDebug('openModelGroupsModal: error toggling Alpine state', e);
    }

    // populate the modal content
    try {
      if (typeof window.populateModelGroupsModal === 'function') await window.populateModelGroupsModal();
    } catch (e) { logDebug('populateModelGroupsModal failed on open', e); }
  };

  window.closeModelGroupsModal = function () {
  try { if (window.DEBUG && console && typeof console.debug === 'function') console.debug('closeModelGroupsModal invoked'); } catch (e) {}
    try {
      if (window.Alpine && window.Alpine.store) {
        const modelGroupsStore = window.Alpine.store('modelGroups');
        if (modelGroupsStore) {
          modelGroupsStore.close();
        }
      } else {
        // Fallback for when Alpine is not available
        const overlay = document.getElementById('modelGroupsModal');
        if (overlay) {
          overlay.style.display = 'none';
          overlay.setAttribute('x-show', 'false');
        }
      }
    } catch (e) {
      logDebug('closeModelGroupsModal: error toggling state', e);
    }
    // No extra cleanup required here; UI will hide via Alpine. If needed, dispatch an event.
  };

  // Populate the modal: fetch providers and groups, render lists and wire buttons
  window.populateModelGroupsModal = async function () {
    // Ensure template is injected
    try {
      if (typeof window.initModelGroupsComponent === 'function') await window.initModelGroupsComponent();
      else insertTemplateIfNeeded();
    } catch (e) {
      // fallback short-wait
      insertTemplateIfNeeded();
    }

    let overlay = document.getElementById('modelGroupsModal');
    for (let i = 0; i < 10 && !overlay; i++) {
      // small wait
      // eslint-disable-next-line no-await-in-loop
      await new Promise(r => setTimeout(r, 40));
      overlay = document.getElementById('modelGroupsModal');
    }
    if (!overlay) {
      console.error('populateModelGroupsModal: modelGroupsModal not found');
      return;
    }

    // fetch provider list
    let providerData = null;
    try {
      const resp = await fetchApi(`/model_providers_list`, { method: 'GET', credentials: 'same-origin' });
      if (resp.ok) providerData = await resp.json();
    } catch (e) {
      logDebug('Failed to load provider list', e);
      providerData = null;
    }

    // fetch groups and pools
    try {
      const data = await listModelGroups();
      const el = document.getElementById('model-groups-list');
      if (!el) {
        console.error('populateModelGroupsModal: model-groups-list element missing');
        return;
      }
      el.innerHTML = '';

      function formatRef(r) {
        if (!r) return '(empty)';
        if (typeof r === 'string') {
          const s = r.trim();
          if (s.startsWith('{') || s.startsWith('[')) {
            try { return formatRef(JSON.parse(s)); } catch (e) { /* fallthrough */ }
          }
          return s;
        }
        try {
          const provider = r.provider || '';
          const name = r.name || '';
          if (!provider && !name) return '(empty)';
          return provider + ':' + name;
        } catch (e) { return String(r); }
      }

      if (data) {
        // populate chat/util selects
        const chatSelect = document.getElementById('mg-chat-ref');
        const utilSelect = document.getElementById('mg-util-ref');
        if (chatSelect) {
          chatSelect.innerHTML = '<option value="">(none)</option>';
          for (const m of (data.chat_models || [])) {
            const opt = document.createElement('option');
            opt.value = (m.provider || '') + ':' + (m.name || '');
            opt.textContent = (m.provider || '') + ':' + (m.name || '') + (m.api_base ? ' @ ' + m.api_base : '');
            chatSelect.appendChild(opt);
          }
        }
        if (utilSelect) {
          utilSelect.innerHTML = '<option value="">(none)</option>';
          for (const m of (data.utility_models || [])) {
            const opt = document.createElement('option');
            opt.value = (m.provider || '') + ':' + (m.name || '');
            opt.textContent = (m.provider || '') + ':' + (m.name || '') + (m.api_base ? ' @ ' + m.api_base : '');
            utilSelect.appendChild(opt);
          }
        }

        // provider select
        const providerSelect = document.getElementById('mg-pool-provider');
        const providerFallbackInput = document.getElementById('mg-pool-provider-fallback');
        if (providerData && providerSelect) {
          providerSelect.style.display = '';
          if (providerFallbackInput) providerFallbackInput.style.display = 'none';
          providerSelect.innerHTML = '<option value="">(select provider)</option>';
          const seen = new Set();
          const addOpts = (list) => {
            if (!list) return;
            for (const p of list) {
              const val = (p.value || p.id || '').toLowerCase();
              const label = p.label || p.name || val;
              if (!val || seen.has(val)) continue; seen.add(val);
              const opt = document.createElement('option'); opt.value = val; opt.textContent = label; providerSelect.appendChild(opt);
            }
          };
          addOpts(providerData.chat || []);
          addOpts(providerData.embedding || []);
        } else {
          if (providerSelect) providerSelect.style.display = 'none';
          if (providerFallbackInput) providerFallbackInput.style.display = '';
        }

        // render pool lists
        const poolEl = document.getElementById('model-groups-pool');
        if (poolEl) {
          poolEl.innerHTML = '';
          const chatModels = data.chat_models || [];
          const utilModels = data.utility_models || [];

          function makePoolTable(title, list, type) {
            if (!list || list.length === 0) return;
            const h = document.createElement('div'); h.textContent = title; h.style.marginBottom = '6px'; poolEl.appendChild(h);
            const table = document.createElement('table'); table.className = 'mg-pool-table';
            const thead = document.createElement('thead'); const headRow = document.createElement('tr');
            ['Provider', 'Name', 'API Base', 'Actions'].forEach(htext => { const th = document.createElement('th'); th.textContent = htext; headRow.appendChild(th); });
            thead.appendChild(headRow); table.appendChild(thead);
            const tbody = document.createElement('tbody');
            for (const m of list) {
              const tr = document.createElement('tr'); const provTd = document.createElement('td'); provTd.textContent = m.provider || '';
              const nameTd = document.createElement('td'); nameTd.textContent = m.name || '';
              const apiTd = document.createElement('td'); apiTd.textContent = m.api_base || '';
              const actionsTd = document.createElement('td'); actionsTd.style.whiteSpace = 'nowrap';

              const edit = document.createElement('button'); edit.className = 'btn btn-secondary'; edit.textContent = 'Edit'; edit.style.marginRight = '6px';
              edit.onclick = () => {
                document.getElementById('mg-pool-type').value = (type === 'chat' ? 'chat' : 'util');
                const providerSelectEl = document.getElementById('mg-pool-provider');
                const providerFallbackEl = document.getElementById('mg-pool-provider-fallback');
                if (providerSelectEl && providerSelectEl.style.display !== 'none') providerSelectEl.value = (m.provider || '').toLowerCase();
                else if (providerFallbackEl) providerFallbackEl.value = m.provider || '';
                document.getElementById('mg-pool-name').value = m.name || '';
                document.getElementById('mg-pool-api').value = m.api_base || '';
                const poolAddBtn = document.getElementById('mg-pool-add-btn'); poolAddBtn.textContent = 'Update Pool';
                poolAddBtn.onclick = async () => {
                  let t = document.getElementById('mg-pool-type').value.trim();
                  let provider = '';
                  const providerSelectEl2 = document.getElementById('mg-pool-provider');
                  const providerFallbackEl2 = document.getElementById('mg-pool-provider-fallback');
                  if (providerSelectEl2 && providerSelectEl2.style.display !== 'none') provider = providerSelectEl2.value.trim();
                  else if (providerFallbackEl2) provider = providerFallbackEl2.value.trim();
                  const name = document.getElementById('mg-pool-name').value.trim();
                  const api_base = document.getElementById('mg-pool-api').value.trim();
                  if (!t || !provider || !name) return alert('type/provider/name required');
                  if (t.toLowerCase() === 'util') t = 'utility';
                  await callJsonApi('/model_pool_remove', { type: (type === 'chat' ? 'chat' : 'utility'), provider: m.provider, name: m.name });
                  await callJsonApi('/model_pool_add', { type: t, provider, name, api_base, kwargs: {} });
                  showToast('Updated pool entry', 'success');
                  poolAddBtn.textContent = 'Add to Pool'; poolAddBtn.onclick = null;
                  refreshAndDispatchModelGroups(); window.openModelGroupsModal();
                };
              };

              const del = document.createElement('button'); del.className = 'btn btn-danger'; del.textContent = 'Delete';
              del.onclick = async () => { if (!confirm('Remove ' + (m.provider || '') + ':' + (m.name || '') + ' from pool?')) return; await callJsonApi('/model_pool_remove', { type: (type === 'chat' ? 'chat' : 'utility'), provider: m.provider, name: m.name }); showToast('Removed from pool', 'success'); refreshAndDispatchModelGroups(); window.openModelGroupsModal(); };

              actionsTd.appendChild(edit); actionsTd.appendChild(del);
              tr.appendChild(provTd); tr.appendChild(nameTd); tr.appendChild(apiTd); tr.appendChild(actionsTd);
              tbody.appendChild(tr);
            }
            table.appendChild(tbody); poolEl.appendChild(table);
          }

          makePoolTable('Chat models:', chatModels, 'chat');
          makePoolTable('Utility models:', utilModels, 'util');
        }

        // helper findModelInPool
        function findModelInPool(list, provider, name) {
          if (!list || !provider || !name) return null;
          const providerLower = (provider || '').toLowerCase();
          const nameLower = (name || '').toLowerCase();
          return list.find(m => (m.provider || '').toLowerCase() === providerLower && ((m.name || '').toLowerCase() === nameLower));
        }

        // render groups table
        if (data.groups) {
          const table = document.createElement('table'); table.className = 'mg-groups-table';
          const thead = document.createElement('thead'); const headRow = document.createElement('tr');
          ['Name', 'Chat', 'Utility', 'Actions'].forEach(h => { const th = document.createElement('th'); th.textContent = h; headRow.appendChild(th); });
          thead.appendChild(headRow); table.appendChild(thead);
          const tbody = document.createElement('tbody');

          for (const [name, g] of Object.entries(data.groups)) {
            const tr = document.createElement('tr'); tr.dataset.groupName = name;
            const nameTd = document.createElement('td'); nameTd.textContent = name;
            const chatTd = document.createElement('td'); chatTd.textContent = formatRef(g.chat);
            const utilTd = document.createElement('td'); utilTd.textContent = formatRef(g.util);
            const actionsTd = document.createElement('td'); actionsTd.className = 'mg-actions'; actionsTd.style.whiteSpace = 'nowrap';

            const selBtn = document.createElement('button'); selBtn.className = 'btn btn-ok'; selBtn.textContent = 'Select';
            selBtn.onclick = async () => {
              const resp = await selectModelGroup(name);
              showToast('Selected model group: ' + name, 'success');
              try {
                const settingsComp = document.getElementById('settingsModal');
                if (settingsComp && window.Alpine && typeof Alpine.$data === 'function') {
                  const sdata = Alpine.$data(settingsComp);

                  // Support both older proxy shape (`settings`) and newer component shape (`settingsData`)
                  const settingsObj = (sdata && (sdata.settingsData || sdata.settings)) ? (sdata.settingsData || sdata.settings) : null;
                  if (sdata && settingsObj) {
                    function findField(id) { for (const sec of settingsObj.sections || []) { for (const f of sec.fields || []) { if (f.id === id) return f; } } return null; }
                    const mgPayload = await listModelGroups(); const groupsObj = mgPayload.groups || {}; const chatModelsPool = mgPayload.chat_models || []; const utilModelsPool = mgPayload.utility_models || [];
                    const grpObj = groupsObj[name] || {}; const chat = Object.assign({}, grpObj.chat || {}); const util = Object.assign({}, grpObj.util || {});
                    if ((!chat.api_base || chat.api_base === '') && chat.provider && chat.name) { const found = findModelInPool(chatModelsPool, chat.provider, chat.name); if (found && found.api_base) chat.api_base = found.api_base; }
                    if ((!util.api_base || util.api_base === '') && util.provider && util.name) { const found = findModelInPool(utilModelsPool, util.provider, util.name); if (found && found.api_base) util.api_base = found.api_base; }
                    const chatIds = ['chat_model_provider', 'chat_model_name', 'chat_model_api_base', 'chat_model_kwargs'];
                    const utilIds = ['util_model_provider', 'util_model_name', 'util_model_api_base', 'util_model_kwargs'];
                    function fieldDomValue(id) { const el = document.querySelector(`[name="${id}"]`) || document.getElementById(id); if (!el) return null; return el.value; }
                    let modified = false;
                    for (const id of [...chatIds, ...utilIds]) { const f = findField(id); if (!f) continue; const baseline = f.value ?? ''; const domv = fieldDomValue(id); if (domv !== null && String(domv) !== String(baseline)) { modified = true; break; } }
                    if (modified) { if (!confirm('Settings 页面中 Chat/Utility 有未保存更改，是否用选定的模型组覆盖这些字段？')) { window.openModelGroupsModal(); return; } }
                    function setField(id, val) {
                      const f = findField(id);
                      if (f) f.value = val ?? '';
                      // keep both shapes in sync if present on proxy
                      try { if (sdata.settingsData) sdata.settingsData = sdata.settingsData; if (sdata.settings) sdata.settings = sdata.settings; } catch (e) { /* ignore */ }
                      const el = document.querySelector(`[name="${id}"]`) || document.getElementById(id);
                      if (el) { el.value = val ?? ''; try { el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); } catch (e) { } }
                      try {
                        const modalEl = document.getElementById('settingsModal');
                        if (modalEl) {
                          const modalData = Alpine.$data(modalEl);
                          if (modalData) {
                            if (typeof modalData.$nextTick === 'function') {
                              modalData.$nextTick(() => { if (typeof modalData.updateFilteredSections === 'function') { modalData.updateFilteredSections(); } });
                            } else {
                              if (typeof modalData.updateFilteredSections === 'function') modalData.updateFilteredSections();
                            }
                          }
                        }
                      } catch (e) { logDebug('Failed to trigger Alpine refresh after setField', e); }
                    }
                    setField('chat_model_provider', chat.provider || ''); setField('chat_model_name', chat.name || ''); setField('chat_model_api_base', chat.api_base || ''); setField('chat_model_kwargs', JSON.stringify(chat.kwargs || {}));
                    setField('util_model_provider', util.provider || ''); setField('util_model_name', util.name || ''); setField('util_model_api_base', util.api_base || ''); setField('util_model_kwargs', JSON.stringify(util.kwargs || {}));

                    // Attempt to refresh via component API if available, otherwise try backend fetch fallback
                    try {
                      const modalEl = document.getElementById('settingsModal');
                      if (modalEl && !modified) {
                        const modalData = Alpine.$data(modalEl);
                        if (modalData && typeof modalData.fetchSettings === 'function') {
                          await modalData.fetchSettings();
                          if (typeof modalData.updateFilteredSections === 'function') modalData.updateFilteredSections();
                        } else {
                          // fallback: try to fetch settings from server and update the proxy object
                          try {
                            let resp = null;
                            try {
                              resp = await fetchApi('/api/settings_get', { method: 'GET' });
                            } catch (e) { resp = null; }
                            if (!resp || !resp.ok) {
                              try { resp = await fetchApi('/settings_get', { method: 'GET' }); } catch (e) { resp = null; }
                            }
                            if (resp && resp.ok) {
                              const data = await resp.json();
                              if (data && data.settings) {
                                // Merge server settings into the existing proxy object instead
                                // of replacing it completely. This preserves UI-only
                                // properties (like the modal's buttons) that are added
                                // locally and would otherwise disappear.
                                const serverSettings = data.settings || {};
                                try {
                                  if (sdata.settingsData) {
                                    const preservedButtons = sdata.settingsData.buttons;
                                    sdata.settingsData = Object.assign({}, serverSettings);
                                    if (preservedButtons && !sdata.settingsData.buttons) sdata.settingsData.buttons = preservedButtons;
                                  }
                                  if (sdata.settings) {
                                    const preservedButtons2 = sdata.settings.buttons;
                                    sdata.settings = Object.assign({}, serverSettings);
                                    if (preservedButtons2 && !sdata.settings.buttons) sdata.settings.buttons = preservedButtons2;
                                  }
                                } catch (e) {
                                  // If merge fails for any reason, fall back to assignment
                                  try { if (sdata.settingsData) sdata.settingsData = serverSettings; if (sdata.settings) sdata.settings = serverSettings; } catch (ee) { /* ignore */ }
                                }
                                if (typeof sdata.updateFilteredSections === 'function') sdata.updateFilteredSections();
                              }
                            }
                          } catch (e) { logDebug('Failed to refresh settings modal after select via fallback fetch', e); }
                        }
                      }
                    } catch (e) { logDebug('Failed to refresh settings modal after group select', e); }
                  }
                }
              } catch (e) { logDebug('Failed to sync settings modal fields after select', e); }
              // Notify other components by fetching latest settings and dispatching event
              try {
                let respSettings = null;
                try { respSettings = await fetchApi('/api/settings_get', { method: 'GET' }); } catch (e) { respSettings = null; }
                if (!respSettings || !respSettings.ok) {
                  try { respSettings = await fetchApi('/settings_get', { method: 'GET' }); } catch (e) { respSettings = null; }
                }
                if (respSettings && respSettings.ok) {
                  const data = await respSettings.json();
                  try { document.dispatchEvent(new CustomEvent('settings-updated', { detail: data.settings })); } catch (e) { logDebug('Failed to dispatch settings-updated', e); }
                }
              } catch (e) { logDebug('Failed to fetch/dispatch settings after model group select', e); }
              refreshAndDispatchModelGroups(); window.openModelGroupsModal();
            };

            const delBtn = document.createElement('button'); delBtn.className = 'btn btn-danger'; delBtn.textContent = 'Delete'; delBtn.onclick = async () => { if (!confirm('Delete group ' + name + '?')) return; await callJsonApi('/model_group_delete', { name }); showToast('Deleted group: ' + name, 'success'); refreshAndDispatchModelGroups(); window.openModelGroupsModal(); };

            const editBtn = document.createElement('button'); editBtn.className = 'btn btn-secondary'; editBtn.textContent = 'Edit'; editBtn.style.marginRight = '6px';
            editBtn.onclick = () => {
              document.getElementById('mg-new-name').value = name;
              document.getElementById('mg-chat-ref').value = formatRef(g.chat) === '(empty)' ? '' : formatRef(g.chat);
              document.getElementById('mg-util-ref').value = formatRef(g.util) === '(empty)' ? '' : formatRef(g.util);
              const createBtn = document.getElementById('mg-create-btn'); createBtn.textContent = 'Update';
              createBtn.onclick = async () => {
                const chatRef = document.getElementById('mg-chat-ref').value.trim(); const utilRef = document.getElementById('mg-util-ref').value.trim(); const newName = document.getElementById('mg-new-name').value.trim();
                function parseRef(ref) { if (!ref) return {}; if (typeof ref === 'string' && ref.includes(':')) { const parts = ref.split(':'); return { provider: parts[0] || '', name: parts[1] || '', api_base: parts[2] || '', kwargs: {} }; } return { provider: '', name: ref, api_base: '', kwargs: {} }; }
                const chat = parseRef(chatRef); const util = parseRef(utilRef);
                try { await callJsonApi('/model_group_update', { name, new_name: newName, chat, util }); showToast('Updated group ' + name, 'success'); } catch (err) { console.error('Failed to update group', err); showToast('Failed to update group: ' + err.message, 'error'); return; }
                refreshAndDispatchModelGroups(); createBtn.textContent = 'Create'; createBtn.onclick = null; window.openModelGroupsModal();
              };
            };

            const activeName = data.active || data.active_group || null; if (activeName && activeName === name) tr.classList.add('selected');
            actionsTd.appendChild(selBtn); actionsTd.appendChild(editBtn); actionsTd.appendChild(delBtn);
            tr.appendChild(nameTd); tr.appendChild(chatTd); tr.appendChild(utilTd); tr.appendChild(actionsTd); tbody.appendChild(tr);
          }

          table.appendChild(tbody); el.appendChild(table);
        } else {
          el.innerHTML = '<i>No groups found</i>';
        }
      }
    } catch (e) {
      console.error('Failed to list model groups', e);
      showToast('Failed to list model groups: ' + e.message, 'error');
    }

    // wire create button
    const createBtn = document.getElementById('mg-create-btn');
    if (createBtn) {
      createBtn.onclick = async () => {
        const name = document.getElementById('mg-new-name').value.trim();
        const chatRef = document.getElementById('mg-chat-ref').value.trim();
        const utilRef = document.getElementById('mg-util-ref').value.trim();
        if (!name) return alert('Name required');
        function parseRef(ref) { if (!ref) return {}; if (typeof ref === 'string' && ref.includes(':')) { const parts = ref.split(':'); return { provider: parts[0] || '', name: parts[1] || '', api_base: parts[2] || '', kwargs: {} }; } return { provider: '', name: ref, api_base: '', kwargs: {} }; }
        const chat = parseRef(chatRef); const util = parseRef(utilRef);
        try { await callJsonApi('/model_group_create', { name, chat, util }); showToast('Created group ' + name, 'success'); } catch (err) { console.error('Failed to create group', err); showToast('Failed to create group: ' + err.message, 'error'); return; }
        refreshAndDispatchModelGroups(); window.openModelGroupsModal();
      };
    }

    // wire pool add button
    const poolAddBtn = document.getElementById('mg-pool-add-btn');
    if (poolAddBtn) {
      poolAddBtn.onclick = async () => {
        let type = document.getElementById('mg-pool-type').value.trim();
        const provider = document.getElementById('mg-pool-provider').value.trim();
        const name = document.getElementById('mg-pool-name').value.trim();
        const api_base = document.getElementById('mg-pool-api').value.trim();
        if (!type || !provider || !name) return alert('type/provider/name required');
        type = type.toLowerCase(); if (type === 'util') type = 'utility'; if (type !== 'chat' && type !== 'utility') return alert('type must be chat or utility');
        await callJsonApi('/model_pool_add', { type, provider, name, api_base, kwargs: {} }); showToast('Added model to pool', 'success'); window.openModelGroupsModal();
      };
    }

  };

  // Auto init on load
  document.addEventListener('DOMContentLoaded', () => {
    insertTemplateIfNeeded();
    try {
      if (typeof window.initQuickModelGroupSelector === 'function') window.initQuickModelGroupSelector();
    } catch (e) { /* ignore */ }
  });
})();

// Quick Model Groups selector logic (migrated here from settings.js)
window.initQuickModelGroupSelector = function () {
  const toggle = document.getElementById('quick-mg-toggle');
  const panel = document.getElementById('quick-mg-panel');
  const listEl = document.getElementById('quick-mg-list');
  const search = document.getElementById('quick-mg-search');
  if (!toggle || !panel || !listEl || !search) return;

  let cached = null;
  let focusedIndex = -1;

  async function fetchAndRender() {
    try {
      const data = await listModelGroups();
      cached = data;
      renderList(data);
      try {
        if (panel && panel.style.display === 'block') {
          requestAnimationFrame(() => {
            try { positionPanel(); } catch (e) { /* ignore */ }
          });
        }
      } catch (e) { /* ignore */ }
    } catch (e) {
      logDebug('Failed to load model groups for quick selector', e);
      listEl.innerHTML = '<li><i>Failed to load</i></li>';
    }
  }

  function formatRef(r) {
    if (!r) return '(empty)';
    if (typeof r === 'string') return r;
    try { return (r.provider || '') + ':' + (r.name || ''); } catch (e) { return String(r); }
  }

  function renderList(data) {
    listEl.innerHTML = '';
    if (!data || !data.groups) return listEl.innerHTML = '<li><i>No groups</i></li>';
    const q = (search.value || '').trim().toLowerCase();
    const activeName = data.active || data.active_group || null;
    let idx = 0;
    for (const [name, g] of Object.entries(data.groups)) {
      if (q && !name.toLowerCase().includes(q)) continue;
      const li = document.createElement('li');
      li.dataset.index = String(idx);
      const title = document.createElement('span');
      title.className = 'mg-name';
      title.textContent = name;
      li.appendChild(title);

      if (activeName && activeName === name) {
        li.classList.add('selected');
      }

      li.onclick = async () => {
        try {
          await selectModelGroup(name);
          showToast('Selected ' + name, 'success');
          try { if (cached) cached.active = name; } catch (e) { /* ignore */ }
        } catch (err) { logDebug(err); }
        hidePanel();
      };
      li.onmouseover = () => {
        try {
          const prev = listEl.querySelector('li.focused');
          if (prev) prev.classList.remove('focused');
        } catch (e) {}
        li.classList.add('focused');
        focusedIndex = parseInt(li.dataset.index || '-1');
      };
      li.onmouseleave = () => { try { li.classList.remove('focused'); } catch (e) {} };
      idx += 1;
      listEl.appendChild(li);
    }
  }

  function positionPanel() {
    if (!panel || !toggle) return;
    const rect = toggle.getBoundingClientRect();
    const prevDisplay = panel.style.display;
    if (panel.style.display === 'none' || !panel.style.display) panel.style.display = 'block';
    const pr = panel.getBoundingClientRect();
    let left = rect.left;
    let top = rect.bottom + 6;
    if (left + pr.width > window.innerWidth - 8) {
      left = Math.max(8, window.innerWidth - pr.width - 8);
    }
    if (top + pr.height > window.innerHeight - 8) {
      top = rect.top - pr.height - 6;
      if (top < 8) top = 8;
    }
    panel.style.left = left + 'px';
    panel.style.top = top + 'px';
    if (prevDisplay === 'none') panel.style.display = 'none';
  }

  function onModelGroupsChanged(e) {
    try {
      const payload = (e && e.detail) ? e.detail : null;
      if (payload) {
        cached = payload;
      } else {
        fetchAndRender();
        return;
      }
      try { renderList(cached); } catch (err) { /* ignore */ }
      try { if (panel && panel.style.display === 'block') positionPanel(); } catch (err) { /* ignore */ }
    } catch (err) { logDebug('onModelGroupsChanged handler failed', err); }
  }
  document.addEventListener('model-groups-changed', onModelGroupsChanged);

  function showPanel() {
    if (panel.style.display === 'block') return;
    if (!cached) fetchAndRender(); else renderList(cached);
    if (panel.parentElement !== document.body) {
      panel._mg_orig_parent = panel.parentElement;
      panel._mg_next_sibling = panel.nextElementSibling;
      document.body.appendChild(panel);
      panel.style.position = 'fixed';
    }
    panel.style.display = 'block'; panel.setAttribute('aria-hidden', 'false');
    try { const s = panel.querySelector('#quick-mg-search'); if (s) s.focus(); } catch (e) {}
    positionPanel(); window.addEventListener('resize', positionPanel); window.addEventListener('scroll', positionPanel, true);
    try {
      if (cached && cached.groups) {
        const active = cached.active || cached.active_group || null;
        if (active) {
          const items = Array.from(listEl.querySelectorAll('li'));
          for (let i = 0; i < items.length; i++) {
            const txt = (items[i].textContent || '').trim();
            if (txt === active) { focusedIndex = i; items[i].classList.add('focused'); items[i].scrollIntoView({ block: 'nearest' }); break; }
          }
        } else { focusedIndex = -1; }
      }
    } catch (e) { focusedIndex = -1; }

    panel._mg_keydown = function (e) {
      const items = Array.from(listEl.querySelectorAll('li'));
      if (!items || items.length === 0) return;
      if (e.key === 'ArrowDown') { e.preventDefault(); if (focusedIndex < items.length - 1) focusedIndex += 1; else focusedIndex = 0; items.forEach(it => it.classList.remove('focused')); const cur = items[focusedIndex]; if (cur) { cur.classList.add('focused'); cur.scrollIntoView({ block: 'nearest' }); } }
      else if (e.key === 'ArrowUp') { e.preventDefault(); if (focusedIndex > 0) focusedIndex -= 1; else focusedIndex = items.length - 1; items.forEach(it => it.classList.remove('focused')); const cur = items[focusedIndex]; if (cur) { cur.classList.add('focused'); cur.scrollIntoView({ block: 'nearest' }); } }
      else if (e.key === 'Enter') { e.preventDefault(); if (focusedIndex >= 0 && focusedIndex < items.length) { const name = (items[focusedIndex].textContent || '').trim(); if (name) items[focusedIndex].click(); } }
    };
    window.addEventListener('keydown', panel._mg_keydown);
    document.addEventListener('click', outsideClick); window.addEventListener('keydown', escHandler);
  }

  function hidePanel() {
    if (panel.style.display === 'none') return;
    panel.style.display = 'none'; panel.setAttribute('aria-hidden', 'true'); document.removeEventListener('click', outsideClick); window.removeEventListener('keydown', escHandler);
    try { window.removeEventListener('resize', positionPanel); window.removeEventListener('scroll', positionPanel, true); } catch (e) {}
    try { if (panel._mg_keydown) { window.removeEventListener('keydown', panel._mg_keydown); delete panel._mg_keydown; } } catch (e) { logDebug('Failed to cleanup quick panel keydown handler', e); }
    if (panel._mg_orig_parent) {
      try { if (panel._mg_next_sibling) panel._mg_orig_parent.insertBefore(panel, panel._mg_next_sibling); else panel._mg_orig_parent.appendChild(panel); } catch (e) { console.warn('Could not restore quick panel to original parent', e); }
      delete panel._mg_orig_parent; delete panel._mg_next_sibling; panel.style.position = ''; panel.style.left = ''; panel.style.top = ''; }
  }

  function togglePanel() { if (panel.style.display === 'block') hidePanel(); else showPanel(); }
  function outsideClick(e) { const p = panel; if (!p) return; if (!p.contains(e.target) && e.target !== toggle) hidePanel(); }
  function escHandler(e) { if (e.key === 'Escape' || e.key === 'Esc') hidePanel(); }
  toggle.onclick = (e) => { e.stopPropagation(); togglePanel(); };
  search.oninput = () => { if (cached) renderList(cached); };
};


// Signal for runtime debugging that the model-groups module initialized
try { console.debug && console.debug('model-groups.js initialized: open/close functions registered'); } catch (e) {}

