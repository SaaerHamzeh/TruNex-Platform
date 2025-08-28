window.addEventListener('DOMContentLoaded', () => {
  /* ------------------------------------------------------------------ */
  /* 1) WebSocket                                                       */
  /* ------------------------------------------------------------------ */
  const socket = new WebSocket('ws://' + window.location.host + '/ws/fetch-logs/');
  socket.addEventListener('open', () => console.log('[WS] connected (combined script)'));

  /* ✅ دالة واحدة للإرسال */


  function sendBroadcast(data) {
    socket.send(JSON.stringify({
      type: 'broadcast',
      ...data
    }));
  }

  // ✅ كشفها للكونسول
  window.sendBroadcast = sendBroadcast;

  /* ✅ استقبال الرسائل وتوزيعها حسب subtype */
  socket.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    const subtype = data.subtype;

    switch (subtype) {
      case "log":
        const logBox = document.getElementById('log-output');
        if (logBox) {
          const line = document.createElement("div");
          line.textContent = data.message;
          logBox.prepend(line);
        }
        break;

      case "countdown":
        const countdownEl = document.getElementById("countdown");
        if (data.next_fetch_timestamp && countdownEl) {
          const targetTime = data.next_fetch_timestamp * 1000;
          const updateCountdown = () => {
            const secondsLeft = Math.max(0, Math.floor((targetTime - Date.now()) / 1000));
            const minutes = Math.floor(secondsLeft / 60);
            const seconds = secondsLeft % 60;
            countdownEl.textContent = `${minutes}m ${seconds}s`;
          };
          updateCountdown();
          clearInterval(window._fetchCountdownInterval);
          window._fetchCountdownInterval = setInterval(updateCountdown, 1000);
        }
        break;

      case "toggle_fetch":
        console.log('[WS] Toggle fetch state updated');
        break;

      case "update_settings":
        console.log('[WS] Settings updated via broadcast');
        break;

      default:
        console.log('[WS] Unknown message:', data);
    }
  });

  /* ------------------------------------------------------------------ */
  /* 2) Toggle Automatic Fetch                                          */
  /* ------------------------------------------------------------------ */
  const formToggle = document.getElementById('toggle-fetch-form');
  const btnToggle = document.getElementById('toggle-btn');
  const statusText = document.getElementById('fetch-status');

  formToggle?.addEventListener('submit', (e) => {
    e.preventDefault();
    const csrf = formToggle.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(formToggle.action, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf }
    })
      .then(res => {
        if (!res.ok) return;
        const wasEnabled = btnToggle.textContent.trim().includes('Stop');
        // flip UI
        btnToggle.textContent = wasEnabled ? '✅ Enable Automatic Fetching' : '⛔ Stop Automatic Fetching';
        statusText.textContent = wasEnabled ? '🔴 متوقف' : '🟢 مفعل';

        sendBroadcast({
          subtype: 'toggle_fetch',
          enabled: !wasEnabled
        });
      })
      .catch(console.error);
  });

  /* ------------------------------------------------------------------ */
  /* 3) Update Settings (interval + limit)                              */
  /* ------------------------------------------------------------------ */
  const updateForm = document.querySelector('form[action$="update_fetch_interval"]');
  updateForm?.addEventListener('submit', (e) => {
    e.preventDefault(); // ✅ ضروري

    const csrf = updateForm.querySelector('[name=csrfmiddlewaretoken]').value;
    const fetch_interval = updateForm.querySelector('[name=fetch_interval]').value;
    const fetch_limit = updateForm.querySelector('[name=fetch_limit]').value;

    fetch(updateForm.action, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrf
      },
      body: `fetch_interval=${fetch_interval}&fetch_limit=${fetch_limit}`
    })
      .then(res => {
        if (!res.ok) return;
        alert('✅ Settings updated (no reload)');
        sendBroadcast({
          subtype: 'update_settings',
          fetch_interval,
          fetch_limit
        });

        // ✅ بث Log واضح للمستخدم
        sendBroadcast({
          subtype: 'log',
          message: `✅ تم تعديل الإعدادات إلى ${fetch_interval} دقيقة، ${fetch_limit} مقالة.`
        });
      })
      .catch(console.error);
  });

  /* ------------------------------------------------------------------ */
  /* 4) Manual "Fetch Now"                                              */
  /* ------------------------------------------------------------------ */
  const fetchNowForm = document.querySelector('form[action$="run_fetch_now"]');
  fetchNowForm?.addEventListener('submit', (e) => {
    e.preventDefault(); // ✅ هذا مهم

    const csrf = fetchNowForm.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(fetchNowForm.action, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf }
    })
      .then(res => res.json())
      .then(data => {
        console.log('[FETCH NOW] response:', data);
        if (data.ok) {
          alert('✅ تم الجلب الآن بنجاح!');
          // ✅ بث log واضح
          sendBroadcast({
            subtype: 'log',
            message: 'تم الجلب اليدوي بنجاح!'
          });
        } else {
          alert('❌ فشل الجلب الآن.');
        }
      })
      .catch(err => {
        console.error('Fetch now error:', err);
        alert('⚠️ خطأ أثناء الجلب الآن.');
      });
  });

});
