// Clicking the toolbar icon opens the Wisdrop Studio side panel (and grants activeTab for insert-into-chat).
chrome.runtime.onInstalled.addListener(() => chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {}));
chrome.runtime.onStartup.addListener(() => chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {}));
// Keys live in storage.local: keep it away from any injected/content script (default exposes it) - Chrome 102+.
chrome.storage.local.setAccessLevel?.({ accessLevel: 'TRUSTED_CONTEXTS' }).catch(() => {});
