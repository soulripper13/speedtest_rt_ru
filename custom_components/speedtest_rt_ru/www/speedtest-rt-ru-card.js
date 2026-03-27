/**
 * Speedtest RT.RU Card for Home Assistant
 * A custom Lovelace card that recreates the iconic Ookla Speedtest interface
 *
 * Version: 1.1.0
 *
 * Layout Compatibility:
 * - Masonry: Returns card size for proper column distribution
 * - Sections: Automatic width/height
 * - Both layouts fully supported with proper height handling
 *
 * Supports English and Russian UI (language: "en" | "ru")
 */

const RTRU_TRANSLATIONS = {
  en: {
    download: "Download",
    upload: "Upload",
    ping: "Ping",
    jitter: "Jitter",
    run_test: "Run Speed Test",
    go: "GO",
    testing: "Testing...",
    unknown_isp: "Unknown ISP",
    unknown_server: "Unknown Server",
    internet_speed: "Internet Speed",
    rt_ru_speedtest: "RT.RU Speedtest",
    mbps: "Mbps",
    ms: "ms",
    result: "View Result",
    last_test: "Last test",
    ip: "IP",
  },
  ru: {
    download: "Загрузка",
    upload: "Отдача",
    ping: "Пинг",
    jitter: "Джиттер",
    run_test: "Запустить тест",
    go: "GO",
    testing: "Тест...",
    unknown_isp: "Неизвестный провайдер",
    unknown_server: "Неизвестный сервер",
    internet_speed: "Скорость интернета",
    rt_ru_speedtest: "Спидтест RT.RU",
    mbps: "Мбит/с",
    ms: "мс",
    result: "Результат",
    last_test: "Последний тест",
    ip: "IP",
  }
};

class SpeedtestRtRuCard extends HTMLElement {
  constructor() {
    super();
    this._config = {};
    this._hass = null;
    this._isRunning = false;
  }

  static getConfigElement() {
    return document.createElement("speedtest-rt-ru-card-editor");
  }

  static getStubConfig() {
    return {
      type: "custom:speedtest-rt-ru-card",
      entities: {
        download: "sensor.speedtest_rt_ru_download",
        upload: "sensor.speedtest_rt_ru_upload",
        ping: "sensor.speedtest_rt_ru_ping",
        jitter: "sensor.speedtest_rt_ru_jitter",
        isp: "sensor.speedtest_rt_ru_isp",
        server: "sensor.speedtest_rt_ru_server",
        result_url: "sensor.speedtest_rt_ru_result_url",
        last_test: "sensor.speedtest_rt_ru_last_test",
        ip: "sensor.speedtest_rt_ru_ip",
      },
      language: "en",
      labels: {},
      max_download: 1000,
      max_upload: 500,
      show_gauges: true,
      theme: "dark"
    };
  }

  _t(key) {
    const lang = this._config.language || 'en';
    const tr = RTRU_TRANSLATIONS[lang] || RTRU_TRANSLATIONS.en;
    if (this._config.labels && this._config.labels[key] !== undefined) {
      return this._config.labels[key];
    }
    return tr[key] || RTRU_TRANSLATIONS.en[key] || key;
  }

  setConfig(config) {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    this._config = {
      ...SpeedtestRtRuCard.getStubConfig(),
      ...config,
      entities: {
        ...SpeedtestRtRuCard.getStubConfig().entities,
        ...(config.entities || {}),
      }
    };
  }

  set hass(hass) {
    this._hass = hass;
    this.updateCard();
  }

  get hass() {
    return this._hass;
  }

  connectedCallback() {
    this.render();
  }

  getCardSize() {
    return 12;
  }

  static getLayoutOptions() {
    return { grid_columns: null, grid_rows: null };
  }

  getLayoutOptions() {
    return { grid_columns: null, grid_rows: null };
  }

  updateCard() {
    if (!this._hass || !this.isConnected) return;

    const entities = this._config.entities;
    const download = this._getState(entities.download);
    const upload = this._getState(entities.upload);
    const ping = this._getState(entities.ping);
    const jitter = this._getState(entities.jitter);
    const isp = this._getState(entities.isp);
    const server = this._getState(entities.server);
    const resultUrl = this._getState(entities.result_url);
    const lastTest = this._getState(entities.last_test);
    const ip = this._getState(entities.ip);

    this._updateGauge('download', download, this._config.max_download);
    this._updateGauge('upload', upload, this._config.max_upload);

    this._updateMetric('ping', ping, this._t('ms'));
    this._updateMetric('jitter', jitter, this._t('ms'));

    const ispEl = this.querySelector('.isp-name');
    const serverEl = this.querySelector('.server-name span');
    const ipEl = this.querySelector('.ip-address');
    if (ispEl) ispEl.textContent = isp || this._t('unknown_isp');
    if (serverEl) serverEl.textContent = server || this._t('unknown_server');
    if (ipEl) ipEl.textContent = ip ? `${this._t('ip')}: ${ip}` : '';

    // Result URL link
    const resultLink = this.querySelector('.result-link');
    if (resultLink) {
      if (resultUrl && resultUrl !== 'unknown' && resultUrl.startsWith('http')) {
        resultLink.href = resultUrl;
        resultLink.style.display = 'inline-flex';
        resultLink.textContent = this._t('result');
      } else {
        resultLink.style.display = 'none';
      }
    }

    // Last test time
    const lastTestEl = this.querySelector('.last-test');
    if (lastTestEl) {
      if (lastTest && lastTest !== 'unknown') {
        try {
          const date = new Date(lastTest);
          lastTestEl.textContent = `${this._t('last_test')}: ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ${date.toLocaleDateString()}`;
          lastTestEl.style.display = 'block';
        } catch {
          lastTestEl.style.display = 'none';
        }
      } else {
        lastTestEl.style.display = 'none';
      }
    }
  }

  _getState(entityId) {
    if (!this._hass || !entityId) return null;
    const state = this._hass.states[entityId];
    return state ? state.state : null;
  }

  _showMoreInfo(entityId) {
    if (!entityId) return;
    const event = new CustomEvent('hass-more-info', {
      bubbles: true,
      composed: true,
      detail: { entityId }
    });
    this.dispatchEvent(event);
  }

  _updateGauge(type, value, max) {
    const gauge = this.querySelector(`.gauge-${type} .gauge-fill`);
    const valueEl = this.querySelector(`.gauge-${type} .gauge-value`);

    if (!gauge || !valueEl) return;

    const numValue = parseFloat(value) || 0;
    const percentage = Math.min((numValue / max) * 100, 100);

    const maxArc = 424;
    const offset = maxArc * (1 - percentage / 100);

    gauge.style.strokeDashoffset = offset;

    let color = '#ef4444';
    if (percentage >= 50) color = '#22d3ee';
    if (percentage >= 80) color = '#22c55e';

    gauge.style.stroke = color;
    valueEl.textContent = Math.round(numValue);
    valueEl.style.color = color;
  }

  _updateMetric(type, value, unit) {
    const el = this.querySelector(`.metric-${type} .metric-value`);
    if (el) {
      let displayValue = value || '-';
      el.textContent = displayValue + (unit ? ` ${unit}` : '');
    }
  }

  _runSpeedtest() {
    if (this._isRunning) return;

    this._isRunning = true;
    const btn = this.querySelector('.go-button');
    if (btn) {
      btn.classList.add('running');
      btn.textContent = this._t('testing');
    }

    this._hass.callService('speedtest_rt_ru', 'perform_test').then(() => {
      setTimeout(() => {
        this._isRunning = false;
        if (btn) {
          btn.classList.remove('running');
          btn.textContent = this._t('go');
        }
      }, 3000);
    });
  }

  render() {
    this.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          width: 100%;
          height: 100%;
          box-sizing: border-box;
          container-type: inline-size;
        }

        * {
          box-sizing: border-box;
        }

        .card {
          background: rgba(15, 23, 42, 0.6);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-radius: 24px;
          padding: 20px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
          border: 1px solid rgba(255, 255, 255, 0.08);
          color: #f8fafc;
          position: relative;
          overflow: hidden;
          width: 100%;
          height: 100%;
          min-height: 0;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          flex: 1;
          direction: ltr;
        }

        .card::before {
          content: '';
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: radial-gradient(circle at 50% 50%, rgba(34, 211, 238, 0.05), transparent 60%);
          pointer-events: none;
          z-index: 0;
        }

        .content-wrapper {
          position: relative;
          z-index: 1;
        }

        .header {
          text-align: center;
          margin-bottom: 16px;
          display: flex;
          flex-direction: column;
          align-items: center;
          flex-shrink: 0;
        }

        .header-icon {
          font-size: 28px;
          margin-bottom: 12px;
          background: rgba(255,255,255,0.05);
          width: 50px;
          height: 50px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        .isp-name {
          font-size: 20px;
          font-weight: 700;
          color: #f8fafc;
          margin-bottom: 4px;
          text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .server-name {
          font-size: 13px;
          color: #94a3b8;
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 4px;
        }

        .ip-address {
          font-size: 11px;
          color: #64748b;
        }

        .gauges-container {
          display: flex;
          justify-content: center;
          gap: 16px;
          margin: 16px 0;
          position: relative;
          flex: 1;
          align-items: center;
        }

        .gauge {
          position: relative;
          width: 140px;
          height: 140px;
          flex-shrink: 0;
          cursor: pointer;
          transition: transform 0.2s;
        }

        .gauge:hover {
          transform: scale(1.05);
        }

        .gauge-svg {
          transform: rotate(135deg);
          width: 100%;
          height: 100%;
        }

        .gauge-bg {
          fill: none;
          stroke: rgba(255,255,255,0.05);
          stroke-width: 12;
          stroke-linecap: round;
          stroke-dasharray: 424 566;
          stroke-dashoffset: 0;
        }

        .gauge-fill {
          fill: none;
          stroke-width: 12;
          stroke-linecap: round;
          stroke-dasharray: 424 566;
          stroke-dashoffset: 424;
          transition: stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.3s ease;
          filter: drop-shadow(0 0 4px currentColor);
        }

        .gauge-content {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .gauge-label {
          font-size: 11px;
          color: #94a3b8;
          text-transform: uppercase;
          letter-spacing: 1.5px;
          margin-bottom: 8px;
          font-weight: 600;
        }

        .gauge-value {
          font-size: 32px;
          font-weight: 800;
          color: #fff;
          line-height: 1;
          letter-spacing: -0.5px;
          text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }

        .gauge-unit {
          font-size: 12px;
          color: #64748b;
          margin-top: 4px;
          font-weight: 500;
        }

        .go-button-container {
          display: flex;
          justify-content: center;
          margin: -30px 0 20px;
          position: relative;
          z-index: 10;
        }

        .go-button {
          width: 80px;
          height: 80px;
          border-radius: 50%;
          border: 4px solid rgba(255,255,255,0.1);
          background: radial-gradient(circle at 30% 30%, #0ea5e9, #0284c7);
          color: white;
          font-size: 20px;
          font-weight: 900;
          letter-spacing: 1px;
          cursor: pointer;
          box-shadow:
            0 0 20px rgba(14, 165, 233, 0.4),
            inset 0 0 20px rgba(255,255,255,0.2),
            0 10px 20px rgba(0,0,0,0.3);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          text-shadow: 0 2px 4px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .go-button:hover {
          transform: scale(1.05) translateY(-2px);
          box-shadow:
            0 0 30px rgba(14, 165, 233, 0.6),
            inset 0 0 20px rgba(255,255,255,0.3),
            0 15px 25px rgba(0,0,0,0.4);
          background: radial-gradient(circle at 30% 30%, #38bdf8, #0ea5e9);
        }

        .go-button:active {
          transform: scale(0.95) translateY(0);
          box-shadow: 0 0 10px rgba(14, 165, 233, 0.4);
        }

        .go-button.running {
          animation: pulse 1.5s infinite;
          background: radial-gradient(circle at 30% 30%, #10b981, #059669);
          box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
        }

        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
          70% { box-shadow: 0 0 0 20px rgba(16, 185, 129, 0); }
          100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        .metrics {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
          margin-bottom: 16px;
        }

        .metric {
          background: rgba(255,255,255,0.03);
          border-radius: 16px;
          padding: 16px 12px;
          text-align: center;
          border: 1px solid rgba(255,255,255,0.02);
          transition: transform 0.2s, background 0.2s;
          cursor: pointer;
        }

        .metric:hover {
          background: rgba(255,255,255,0.05);
          transform: translateY(-2px);
        }

        .metric-icon {
          font-size: 20px;
          margin-bottom: 8px;
          opacity: 0.8;
        }

        .metric-label {
          font-size: 10px;
          color: #94a3b8;
          text-transform: uppercase;
          letter-spacing: 1px;
          margin-bottom: 4px;
          font-weight: 600;
        }

        .metric-value {
          font-size: 16px;
          font-weight: 700;
          color: #f8fafc;
        }

        .metric-ping .metric-value { color: #fbbf24; text-shadow: 0 0 10px rgba(251, 191, 36, 0.3); }
        .metric-jitter .metric-value { color: #a78bfa; text-shadow: 0 0 10px rgba(167, 139, 250, 0.3); }

        .footer {
          padding-top: 12px;
          border-top: 1px solid rgba(255,255,255,0.05);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          flex-shrink: 0;
        }

        .footer-row {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 12px;
          width: 100%;
        }

        .result-link {
          display: none;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: #22d3ee;
          text-decoration: none;
          padding: 4px 10px;
          border-radius: 20px;
          border: 1px solid rgba(34, 211, 238, 0.3);
          background: rgba(34, 211, 238, 0.05);
          transition: background 0.2s, border-color 0.2s;
        }

        .result-link:hover {
          background: rgba(34, 211, 238, 0.12);
          border-color: rgba(34, 211, 238, 0.5);
        }

        .last-test {
          display: none;
          font-size: 10px;
          color: #475569;
        }

        .branding {
          font-size: 11px;
          color: #64748b;
        }

        @container (max-width: 450px) {
          .card { padding: 16px; }
          .gauges-container { gap: 12px; }
          .gauge { width: 120px; height: 120px; }
          .gauge-value { font-size: 28px; }
          .go-button { width: 70px; height: 70px; font-size: 18px; }
          .metrics { gap: 8px; }
          .metric { padding: 12px 8px; }
        }

        @container (max-width: 350px) {
          .gauges-container { flex-direction: column; gap: 8px; }
          .gauge { width: 100px; height: 100px; }
          .gauge-value { font-size: 24px; }
          .go-button { width: 60px; height: 60px; font-size: 16px; }
          .go-button-container { margin: -20px 0 16px; }
        }
</style>

      <div class="card">
        <div class="content-wrapper">
          <div class="header">
            <div class="header-icon">🌐</div>
            <div class="isp-name">Loading...</div>
            <div class="server-name">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
              <span>-</span>
            </div>
            <div class="ip-address"></div>
          </div>

          <div class="gauges-container">
            <div class="gauge gauge-download">
              <svg class="gauge-svg" viewBox="0 0 200 200">
                <defs>
                  <linearGradient id="grad-rtru-download" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#0ea5e9;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#22d3ee;stop-opacity:1" />
                  </linearGradient>
                  <linearGradient id="grad-rtru-upload" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#7c3aed;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#a78bfa;stop-opacity:1" />
                  </linearGradient>
                </defs>
                <circle class="gauge-bg" cx="100" cy="100" r="90"></circle>
                <circle class="gauge-fill" cx="100" cy="100" r="90" stroke="url(#grad-rtru-download)"></circle>
              </svg>
              <div class="gauge-content">
                <div class="gauge-label">${this._t('download')}</div>
                <div class="gauge-value">0</div>
                <div class="gauge-unit">${this._t('mbps')}</div>
              </div>
            </div>

            <div class="gauge gauge-upload">
              <svg class="gauge-svg" viewBox="0 0 200 200">
                <circle class="gauge-bg" cx="100" cy="100" r="90"></circle>
                <circle class="gauge-fill" cx="100" cy="100" r="90" stroke="url(#grad-rtru-upload)"></circle>
              </svg>
              <div class="gauge-content">
                <div class="gauge-label">${this._t('upload')}</div>
                <div class="gauge-value">0</div>
                <div class="gauge-unit">${this._t('mbps')}</div>
              </div>
            </div>
          </div>

          <div class="go-button-container">
            <button class="go-button">${this._t('go')}</button>
          </div>

          <div class="metrics">
            <div class="metric metric-ping">
              <div class="metric-icon">⚡</div>
              <div class="metric-label">${this._t('ping')}</div>
              <div class="metric-value">- ${this._t('ms')}</div>
            </div>
            <div class="metric metric-jitter">
              <div class="metric-icon">📶</div>
              <div class="metric-label">${this._t('jitter')}</div>
              <div class="metric-value">- ${this._t('ms')}</div>
            </div>
          </div>

          <div class="footer">
            <div class="footer-row">
              <span class="branding">${this._t('rt_ru_speedtest')}</span>
              <a class="result-link" target="_blank" rel="noopener noreferrer">
                🔗 ${this._t('result')}
              </a>
            </div>
            <div class="last-test"></div>
          </div>
        </div>
      </div>
    `;

    const goBtn = this.querySelector('.go-button');
    if (goBtn) {
      goBtn.addEventListener('click', () => this._runSpeedtest());
    }

    const entities = this._config.entities;
    this.querySelector('.gauge-download')?.addEventListener('click', () => this._showMoreInfo(entities.download));
    this.querySelector('.gauge-upload')?.addEventListener('click', () => this._showMoreInfo(entities.upload));
    this.querySelector('.metric-ping')?.addEventListener('click', () => this._showMoreInfo(entities.ping));
    this.querySelector('.metric-jitter')?.addEventListener('click', () => this._showMoreInfo(entities.jitter));
  }
}

customElements.define("speedtest-rt-ru-card", SpeedtestRtRuCard);

class SpeedtestRtRuCardEditor extends HTMLElement {
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
    const event = new CustomEvent("config-changed", {
      detail: { config: newConfig },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }

  render() {
    if (this._elements) return;

    this.innerHTML = '';
    this._elements = [];

    const container = document.createElement('div');
    container.style.cssText = "display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px;";

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

    const gaugeDiv = document.createElement('div');
    gaugeDiv.style.cssText = "border: 1px solid var(--divider-color, #e0e0e0); border-radius: 8px; padding: 10px; background: var(--card-background-color, rgba(0,0,0,0.2));";
    gaugeDiv.innerHTML = `<div style="font-weight: 500; margin-bottom: 10px; color: var(--primary-text-color); font-size: 14px;">Gauge Scale Settings</div>`;

    const createInput = (key, label, defaultValue) => {
      const div = document.createElement('div');
      div.style.cssText = "display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;";

      const lbl = document.createElement('label');
      lbl.innerText = label;
      lbl.style.cssText = "font-size: 13px; color: var(--primary-text-color);";
      div.appendChild(lbl);

      const input = document.createElement('input');
      input.type = "number";
      input.value = this._config[key] || defaultValue;
      input.style.cssText = "padding: 6px; border-radius: 4px; border: 1px solid var(--divider-color, #888); background: var(--card-background-color, #fff); color: var(--primary-text-color, #000); width: 80px;";
      input.addEventListener('change', (e) => {
        this.configChanged({ ...this._config, [key]: Number(e.target.value) });
      });

      div.appendChild(input);
      return div;
    };

    gaugeDiv.appendChild(createInput('max_download', 'Max Download (Mbps)', 1000));
    gaugeDiv.appendChild(createInput('max_upload', 'Max Upload (Mbps)', 500));
    container.appendChild(gaugeDiv);

    const entitiesDiv = document.createElement('div');
    entitiesDiv.style.cssText = "border: 1px solid var(--divider-color, #e0e0e0); border-radius: 8px; padding: 10px; background: var(--card-background-color, rgba(0,0,0,0.2));";
    entitiesDiv.innerHTML = `<div style="font-weight: 500; margin-bottom: 10px; color: var(--primary-text-color); font-size: 14px;">Entities</div>`;

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

    const entityFields = [
      { key: 'download', label: 'Download Speed' },
      { key: 'upload', label: 'Upload Speed' },
      { key: 'ping', label: 'Ping Latency' },
      { key: 'jitter', label: 'Jitter' },
      { key: 'isp', label: 'ISP Name' },
      { key: 'server', label: 'Server Name' },
      { key: 'result_url', label: 'Result URL' },
      { key: 'last_test', label: 'Last Test' },
      { key: 'ip', label: 'IP Address' },
    ];

    entityFields.forEach(f => entitiesDiv.appendChild(createPicker(f.key, f.label)));
    container.appendChild(entitiesDiv);

    this.appendChild(container);
  }
}

customElements.define("speedtest-rt-ru-card-editor", SpeedtestRtRuCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "speedtest-rt-ru-card",
  name: "Speedtest RT.RU",
  description: "Beautiful RT.RU speedtest interface with radial gauges",
  preview: true,
  documentationURL: "https://github.com/katoaroosultan/speedtest_rt_ru"
});

console.info("%c SPEEDTEST RT.RU CARD %c v1.1.0 ", "background: #0ea5e9; color: #fff; font-weight: bold;", "background: #1e293b; color: #fff;");
