/**
 * Speedtest RT.RU Card - Compact Version (Bubble Style)
 * Minimalist pill-shaped card inspired by Bubble Card design
 *
 * Version: 1.0.0
 *
 * Supports English and Russian UI (language: "en" | "ru")
 */

const RTRU_COMPACT_TRANSLATIONS = {
  en: { download: "Download", upload: "Upload", ping: "Ping", go: "GO", testing: "...", mbps: "Mbps", ms: "ms" },
  ru: { download: "Загрузка", upload: "Отдача", ping: "Пинг", go: "GO", testing: "...", mbps: "Мбит/с", ms: "мс" }
};

class SpeedtestRtRuCompact extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  static getConfigElement() {
    return document.createElement("speedtest-rt-ru-compact-editor");
  }

  static getStubConfig() {
    return {
      type: "custom:speedtest-rt-ru-compact",
      language: "en",
      entities: {
        download: "sensor.speedtest_rt_ru_download",
        upload: "sensor.speedtest_rt_ru_upload",
        ping: "sensor.speedtest_rt_ru_ping"
      },
      labels: {}
    };
  }

  setConfig(config) {
    this._config = { ...SpeedtestRtRuCompact.getStubConfig(), ...config };
  }

  _t(key) {
    const lang = this._config.language || 'en';
    const tr = RTRU_COMPACT_TRANSLATIONS[lang] || RTRU_COMPACT_TRANSLATIONS.en;
    if (this._config.labels && this._config.labels[key] !== undefined) return this._config.labels[key];
    return tr[key] || RTRU_COMPACT_TRANSLATIONS.en[key] || key;
  }

  set hass(hass) {
    this._hass = hass;
    this.updateCard();
  }

  connectedCallback() {
    this.render();
  }

  getCardSize() {
    return 2;
  }

  static getLayoutOptions() {
    return { grid_columns: null, grid_rows: null };
  }

  getLayoutOptions() {
    return { grid_columns: null, grid_rows: null };
  }

  updateCard() {
    if (!this._hass) return;

    const e = this._config.entities;
    const dl = this._getState(e.download);
    const ul = this._getState(e.upload);
    const ping = this._getState(e.ping);

    const dlEl = this.shadowRoot.querySelector('.dl-value');
    const ulEl = this.shadowRoot.querySelector('.ul-value');
    const pingEl = this.shadowRoot.querySelector('.ping-value');

    if (dlEl) dlEl.textContent = dl ? Math.round(dl) : '--';
    if (ulEl) ulEl.textContent = ul ? Math.round(ul) : '--';
    if (pingEl) pingEl.textContent = ping ? Math.round(ping) : '--';
  }

  _getState(entityId) {
    if (!this._hass || !entityId) return null;
    const state = this._hass.states[entityId];
    return state ? parseFloat(state.state) || null : null;
  }

  _showMoreInfo(entityId) {
    if (!entityId) return;
    const event = new CustomEvent('hass-more-info', { bubbles: true, composed: true, detail: { entityId } });
    this.dispatchEvent(event);
  }

  _runTest() {
    if (!this._hass) return;

    this._hass.callService('speedtest_rt_ru', 'perform_test');
    const btn = this.shadowRoot.querySelector('.action-button');
    if (btn) {
      btn.classList.add('running');
      btn.textContent = this._t('testing');
      setTimeout(() => {
        btn.classList.remove('running');
        btn.textContent = this._t('go');
      }, 5000);
    }
  }

  render() {
    if (this.shadowRoot.innerHTML !== '') return;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
          height: 100%;
          box-sizing: border-box;
          container-type: inline-size;
        }
        * { box-sizing: border-box; }
        .card {
          background: var(--bubble-main-background-color, var(--ha-card-background, var(--card-background-color, rgba(255, 255, 255, 0.04))));
          backdrop-filter: blur(50px);
          -webkit-backdrop-filter: blur(50px);
          border-radius: var(--bubble-border-radius, 12px);
          padding: 4px 8px 4px 4px;
          color: var(--primary-text-color, #f8fafc);
          font-family: var(--primary-font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
          display: flex;
          flex-direction: row;
          flex-wrap: nowrap;
          align-items: center;
          justify-content: flex-start;
          border: none;
          box-shadow: var(--bubble-box-shadow, 0 2px 8px 0 rgba(0, 0, 0, 0.16));
          width: 100%;
          height: 100%;
          min-height: 50px;
          max-height: 80px;
          gap: 8px;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
          overflow: hidden;
          flex: 1;
          direction: ltr;
        }
        .card:hover { box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.24); transform: translateY(-1px); }
        .card:active { transform: scale(0.98); }
        .stats-container { display: flex; flex-direction: row; align-items: center; flex: 1; min-width: 0; overflow: hidden; }
        .stats { display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 4px; min-width: 0; overflow: hidden; }
        .stat { display: flex; flex-direction: row; align-items: baseline; justify-content: center; gap: 2px; white-space: nowrap; flex: 1; min-width: 0; overflow: hidden; cursor: pointer; transition: opacity 0.2s; }
        .stat:hover { opacity: 0.8; }
        .stat-icon { font-size: 10px; opacity: 0.6; margin: 0; }
        .stat-value { font-size: 13px; font-weight: 700; letter-spacing: -0.02em; }
        .stat-unit { font-size: 9px; font-weight: 500; opacity: 0.5; margin: 0; }
        .stat-dl .stat-value { color: #38bdf8; }
        .stat-ul .stat-value { color: #a78bfa; }
        .stat-ping .stat-value { color: #fbbf24; }
        .action-button {
          width: 38px; height: 38px; border-radius: 50%;
          background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
          color: white; display: flex; align-items: center; justify-content: center;
          font-size: 10px; font-weight: 800; cursor: pointer;
          box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          flex: 0 0 auto; border: none; letter-spacing: 0.5px; white-space: nowrap; padding: 0;
        }
        .action-button:hover { transform: scale(1.05); box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4); }
        .action-button:active { transform: scale(0.95); }
        .action-button.running {
          animation: pulse-glow 1.5s cubic-bezier(0.4, 0, 0.2, 1) infinite;
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
        }
        @keyframes pulse-glow { 0%, 100% { opacity: 1; } 50% { opacity: 0.8; } }
        @container (max-width: 320px) {
          .stat-icon { display: none; }
          .stats { gap: 4px; }
          .stat-value { font-size: 11px; }
          .stat-unit { font-size: 8px; }
          .card { padding: 4px 8px; }
        }
      </style>

      <div class="card">
        <button class="action-button">${this._t('go')}</button>
        <div class="stats-container">
          <div class="stats">
            <div class="stat stat-dl" title="${this._t('download')}">
              <span class="stat-icon">⬇</span>
              <span class="stat-value dl-value">--</span>
              <span class="stat-unit">${this._t('mbps')}</span>
            </div>
            <div class="stat stat-ul" title="${this._t('upload')}">
              <span class="stat-icon">⬆</span>
              <span class="stat-value ul-value">--</span>
              <span class="stat-unit">${this._t('mbps')}</span>
            </div>
            <div class="stat stat-ping" title="${this._t('ping')}">
              <span class="stat-icon">⏱</span>
              <span class="stat-value ping-value">--</span>
              <span class="stat-unit">${this._t('ms')}</span>
            </div>
          </div>
        </div>
      </div>
    `;

    this.shadowRoot.querySelector('.action-button')?.addEventListener('click', (e) => {
      e.stopPropagation();
      this._runTest();
    });

    const e = this._config.entities;
    this.shadowRoot.querySelector('.stat-dl')?.addEventListener('click', (ev) => { ev.stopPropagation(); this._showMoreInfo(e.download); });
    this.shadowRoot.querySelector('.stat-ul')?.addEventListener('click', (ev) => { ev.stopPropagation(); this._showMoreInfo(e.upload); });
    this.shadowRoot.querySelector('.stat-ping')?.addEventListener('click', (ev) => { ev.stopPropagation(); this._showMoreInfo(e.ping); });
  }
}

customElements.define("speedtest-rt-ru-compact", SpeedtestRtRuCompact);

class SpeedtestRtRuCompactEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._elements) {
      this._elements.forEach(el => el.hass = hass);
    }
  }

  configChanged(newConfig) {
    const event = new CustomEvent("config-changed", { detail: { config: newConfig }, bubbles: true, composed: true });
    this.dispatchEvent(event);
  }

  render() {
    if (this._elements) return;

    this.innerHTML = '';
    this._elements = [];

    const container = document.createElement('div');
    container.style.cssText = "display: flex; flex-direction: column; gap: 12px; padding: 10px;";

    // Language selector
    const langDiv = document.createElement('div');
    langDiv.style.cssText = "border: 1px solid var(--divider-color, #e0e0e0); border-radius: 8px; padding: 10px; background: var(--card-background-color, rgba(0,0,0,0.2));";
    langDiv.innerHTML = `<div style="font-weight: 500; margin-bottom: 10px; color: var(--primary-text-color); font-size: 14px;">Language / Язык</div>`;

    const langRow = document.createElement('div');
    langRow.style.cssText = "display: flex; align-items: center; justify-content: space-between;";
    langRow.innerHTML = `<label style="font-size: 13px; color: var(--primary-text-color);">Language</label>`;
    const langSelect = document.createElement('select');
    langSelect.style.cssText = "padding: 6px; border-radius: 4px; border: 1px solid var(--divider-color, #888); background: var(--card-background-color, #fff); color: var(--primary-text-color, #000);";
    langSelect.innerHTML = `<option value="en">English</option><option value="ru">Русский</option>`;
    langSelect.value = this._config.language || 'en';
    langSelect.addEventListener('change', (e) => this.configChanged({ ...this._config, language: e.target.value }));
    langRow.appendChild(langSelect);
    langDiv.appendChild(langRow);
    container.appendChild(langDiv);

    const entitiesDiv = document.createElement('div');
    entitiesDiv.style.cssText = "border: 1px solid var(--divider-color, #e0e0e0); border-radius: 8px; padding: 10px; background: var(--card-background-color, rgba(0,0,0,0.2));";
    entitiesDiv.innerHTML = `<div style="font-weight: 500; margin-bottom: 10px; color: var(--primary-text-color); font-size: 14px;">Entities / Объекты</div>`;

    const createPicker = (key, label) => {
      const div = document.createElement('div');
      div.style.marginBottom = "12px";

      const lbl = document.createElement('label');
      lbl.innerText = label;
      lbl.style.cssText = "font-size: 12px; color: var(--secondary-text-color); margin-bottom: 4px; display: block;";
      div.appendChild(lbl);

      const picker = document.createElement('ha-entity-picker');
      picker.hass = this._hass;
      picker.value = (this._config.entities && this._config.entities[key]) || '';
      picker.includeDomains = ['sensor'];
      picker.allowCustomEntity = true;
      picker.addEventListener('value-changed', (e) => {
        const entities = { ...(this._config.entities || {}) };
        entities[key] = e.detail.value;
        this.configChanged({ ...this._config, entities });
      });

      this._elements.push(picker);
      div.appendChild(picker);
      return div;
    };

    entitiesDiv.appendChild(createPicker('download', 'Download / Загрузка'));
    entitiesDiv.appendChild(createPicker('upload', 'Upload / Отдача'));
    entitiesDiv.appendChild(createPicker('ping', 'Ping / Пинг'));

    container.appendChild(entitiesDiv);
    this.appendChild(container);
  }
}

customElements.define("speedtest-rt-ru-compact-editor", SpeedtestRtRuCompactEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "speedtest-rt-ru-compact",
  name: "Speedtest RT.RU - Compact",
  description: "Minimalist pill-shaped card / Компактная карточка",
  preview: true
});

console.info("%c SPEEDTEST RT.RU COMPACT %c v1.0.0 ", "background: #0ea5e9; color: #fff; font-weight: bold;", "background: #1e293b; color: #fff;");
