import { createStore } from "/js/AlpineStore.js";

createStore("terminalView", {
    open: false,
    tabs: [],
    activeTabId: null,

    toggle() {
        this.open = !this.open;
        if (this.open && this.tabs.length === 0) this.addTab();
    },

    addTab() {
        const id = 'term_' + Date.now();
        const n = this.tabs.length + 1;
        const sessionId = localStorage.getItem('a0_term_session_' + id)
                       || this._newSid(id);
        this.tabs.push({ id, name: 'Shell ' + n, sessionId, renaming: false });
        this.activeTabId = id;
        this._save();
        localStorage.setItem('a0_term_active', id);
    },

    removeTab(id) {
        const idx = this.tabs.findIndex(t => t.id === id);
        if (idx === -1) return;
        this.tabs.splice(idx, 1);
        localStorage.removeItem('a0_term_session_' + id);
        if (this.activeTabId === id)
            this.activeTabId = this.tabs.length
                ? this.tabs[Math.max(0, idx - 1)].id
                : null;
        if (this.tabs.length === 0) this.open = false;
        this._save();
    },

    setActive(id) { this.activeTabId = id; localStorage.setItem('a0_term_active', id); this._save(); },

    commitRename(id, name) {
        const tab = this.tabs.find(t => t.id === id);
        if (tab) { tab.name = name.trim() || tab.name; tab.renaming = false; this._save(); }
    },

    getTab(id) { return this.tabs.find(t => t.id === id); },

    _newSid(tabId) {
        const s = 'sid_' + Math.random().toString(36).slice(2);
        localStorage.setItem('a0_term_session_' + tabId, s);
        return s;
    },

    _save() {
        localStorage.setItem('a0_term_tabs',
            JSON.stringify(this.tabs.map(({id, name, sessionId}) => ({id, name, sessionId}))));
        localStorage.setItem('a0_term_active', this.activeTabId || '');
    },

    _loadTabs() {
        try {
            const saved = JSON.parse(localStorage.getItem('a0_term_tabs') || '[]');
            if (saved.length) {
                this.tabs = saved.map(t => ({ ...t, renaming: false }));
                const savedActive = localStorage.getItem('a0_term_active');
                const validActive = savedActive && this.tabs.find(t => t.id === savedActive);
                this.activeTabId = validActive ? savedActive : this.tabs[0].id;
            }
        } catch(e) {}
    }
});

document.addEventListener('alpine:init', () => {
    Alpine.store('terminalView')._loadTabs();
});
