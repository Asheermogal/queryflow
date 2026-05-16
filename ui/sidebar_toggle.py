"""
JavaScript-injected sidebar toggle.

Streamlit's built-in sidebar collapse toggle is fragile across versions and
can be hidden by browser state. This component injects a custom ☰ button
into the page that always works.
"""
from __future__ import annotations

import streamlit.components.v1 as components


_SIDEBAR_TOGGLE_JS = """
<script>
(function() {
  const ID = 'queryflow-sidebar-toggle';

  function ensureToggle() {
    try {
      const doc = window.parent.document;
      let btn = doc.getElementById(ID);
      if (!btn) {
        btn = doc.createElement('button');
        btn.id = ID;
        btn.innerHTML = '☰';
        btn.title = 'Toggle sidebar';
        btn.style.cssText = [
          'position: fixed',
          'top: 14px',
          'left: 14px',
          'z-index: 999999',
          'background: #ffffff',
          'border: 1px solid #e7e5e0',
          'border-radius: 4px',
          'padding: 6px 12px',
          'cursor: pointer',
          'font-size: 18px',
          'line-height: 1',
          'color: #0c0a09',
          'box-shadow: 0 2px 8px rgba(0,0,0,0.08)',
          'font-family: system-ui, sans-serif',
        ].join(';');
        btn.onmouseover = () => { btn.style.background = '#f5f3ee'; };
        btn.onmouseout = () => { btn.style.background = '#ffffff'; };
        btn.onclick = () => {
          const expand = doc.querySelector('[data-testid="stSidebarCollapsedControl"] button')
                       || doc.querySelector('[aria-label="Open sidebar"]');
          if (expand) { expand.click(); return; }
          const collapse = doc.querySelector('[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button')
                         || doc.querySelector('[data-testid="stSidebar"] button[kind="headerNoPadding"]')
                         || doc.querySelector('[aria-label="Close sidebar"]');
          if (collapse) { collapse.click(); return; }
        };
        doc.body.appendChild(btn);
      }
    } catch (e) {}
  }

  ensureToggle();
  setInterval(ensureToggle, 800);
})();
</script>
"""


def inject_sidebar_toggle() -> None:
    components.html(_SIDEBAR_TOGGLE_JS, height=0)
