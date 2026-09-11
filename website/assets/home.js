/* ParallelLingvo — homepage interactive widgets (phone demo, language builder, add-words, family dashboard)
   Vanilla JS port of the original design-tool demo logic. No frameworks. */
(function () {
  'use strict';

  var LANG = (document.documentElement.lang === 'ru') ? 'ru' : 'en';
  var T = {
    en: {
      spellReveal: 'Spell it to reveal the sentence',
      spellRevealShort: 'Spell the word to reveal this line',
      correct: '✓ Correct — every language on the card moved forward.',
      wrong: '✗ Not quite. Tap a filled box to take the letter back.',
      correctShort: '✓ Correct',
      wrongShort: '✗ Try again',
      dailyGoal: 'Daily goal',
      dailyGoalDone: 'Daily goal done',
      starAdd: '★ Added to difficult words',
      starRemove: 'Removed from difficult words',
      allLangHint: 'All languages — pick one to practise',
      allLangHintDemo: 'All languages — pick one above to practise',
      translating: 'Translating…',
      translateBtn: 'Translate & build sentences',
      generating: 'Generating…',
      generateBtn: 'Generate deck',
      example: 'Example: ',
      exampleTail: ' is used every day.',
      connect: 'connect',
      connected: 'connected',
      importBtn: 'Import deck',
      imported: function (n, from) { return 'Imported ' + n + ' words from ' + from; },
      chooseLesson: 'Choose a lesson…',
      lessonOptions: [['18.1', '18.1 At the market'], ['18.2', '18.2 Family weekend'], ['19.1', '19.1 Weather & seasons']],
      todayProgress: "Today's progress:",
      studyTime: 'Study time:',
      currentPriority: 'Current priority:'
    },
    ru: {
      spellReveal: 'Соберите слово, чтобы увидеть пример',
      spellRevealShort: 'Соберите слово, чтобы открыть строку',
      correct: '✓ Верно — все языки карточки продвинулись.',
      wrong: '✗ Почти. Нажмите на заполненную ячейку, чтобы вернуть букву.',
      correctShort: '✓ Верно',
      wrongShort: '✗ Попробуйте ещё',
      dailyGoal: 'Цель дня',
      dailyGoalDone: 'Цель дня выполнена',
      starAdd: '★ Добавлено в сложные слова',
      starRemove: 'Убрано из сложных слов',
      allLangHint: 'Все языки — выберите один для тренировки',
      allLangHintDemo: 'Все языки — выберите один сверху для тренировки',
      translating: 'Переводим…',
      translateBtn: 'Перевести и придумать предложения',
      generating: 'Генерируем…',
      generateBtn: 'Сгенерировать колоду',
      example: 'Пример: ',
      exampleTail: ' используется каждый день.',
      connect: 'подключить',
      connected: 'подключено',
      importBtn: 'Импортировать',
      imported: function (n, from) { return 'Импортировано ' + n + ' слов от ' + from; },
      chooseLesson: 'Выберите урок…',
      lessonOptions: [['18.1', '18.1 На рынке'], ['18.2', '18.2 Семейные выходные'], ['19.1', '19.1 Погода и сезоны']],
      todayProgress: 'Прогресс сегодня:',
      studyTime: 'Время занятий:',
      currentPriority: 'Текущий приоритет:'
    }
  }[LANG];

  var LANGS = [
    { code: 'en', name: 'English', voice: 'en-GB' },
    { code: 'es', name: 'Español', voice: 'es-ES' },
    { code: 'fr', name: 'Français', voice: 'fr-FR' }
  ];

  var CONCEPTS = [
    { label: { en: 'development', ru: 'развитие' }, w: {
      en: { t: 'development', s: 'The development of the city is moving quickly.' },
      es: { t: 'desarrollo', s: 'El desarrollo de la ciudad avanza rápido.' },
      fr: { t: 'développement', s: 'Le développement de la ville avance vite.' } } },
    { label: { en: 'to hire', ru: 'нанимать' }, w: {
      en: { t: 'hire', s: 'The company wants to hire two new employees.' },
      es: { t: 'contratar', s: 'La empresa quiere contratar a dos empleados.' },
      fr: { t: 'embaucher', s: "L'entreprise veut embaucher deux employés." } } },
    { label: { en: 'rain', ru: 'дождь' }, w: {
      en: { t: 'rain', s: 'The rain started right after lunch.' },
      es: { t: 'lluvia', s: 'La lluvia empezó justo después del almuerzo.' },
      fr: { t: 'pluie', s: 'La pluie a commencé juste après le déjeuner.' } } }
  ];

  var SITE_LANGS = [
    ['EN', 'English', ''], ['RU', 'Русский', 'ru'], ['ES', 'Español', 'es'], ['FR', 'Français', 'fr'],
    ['DE', 'Deutsch', 'de'], ['IT', 'Italiano', 'it'], ['PT', 'Português', 'pt'], ['NL', 'Nederlands', 'nl'],
    ['PL', 'Polski', 'pl'], ['UK', 'Українська', 'uk'], ['CS', 'Čeština', 'cs'], ['SK', 'Slovenčina', 'sk'],
    ['SV', 'Svenska', 'sv'], ['NO', 'Norsk', 'no'], ['DA', 'Dansk', 'da'], ['FI', 'Suomi', 'fi'],
    ['IS', 'Íslenska', 'is'], ['ET', 'Eesti', 'et'], ['LV', 'Latviešu', 'lv'], ['LT', 'Lietuvių', 'lt'],
    ['HU', 'Magyar', 'hu'], ['RO', 'Română', 'ro'], ['BG', 'Български', 'bg'], ['EL', 'Ελληνικά', 'el'],
    ['HR', 'Hrvatski', 'hr'], ['SR', 'Српски', 'sr'], ['SL', 'Slovenščina', 'sl'], ['TR', 'Türkçe', 'tr'],
    ['BE', 'Беларуская', 'be'], ['KK', 'Қазақша', 'kk'], ['KA', 'ქართული', 'ka'], ['HY', 'Հայերեն', 'hy'],
    ['HE', 'עברית', 'he'], ['AR', 'العربية', 'ar'], ['FA', 'فارسی', 'fa'], ['HI', 'हिन्दी', 'hi'],
    ['BN', 'বাংলা', 'bn'], ['UR', 'اردو', 'ur'], ['TH', 'ไทย', 'th'], ['VI', 'Tiếng Việt', 'vi'],
    ['ID', 'Indonesia', 'id'], ['MS', 'Melayu', 'ms'], ['ZH', '中文', 'zh'], ['JA', '日本語', 'ja'],
    ['KO', '한국어', 'ko'], ['CA', 'Català', 'ca'], ['SW', 'Kiswahili', 'sw'], ['TL', 'Filipino', 'tl']
  ];

  var RAIN = {"en":["rain","The rain started right after lunch."],"es":["lluvia","La lluvia empezó justo después del almuerzo."],"fr":["pluie","La pluie a commencé juste après le déjeuner."],"de":["Regen","Der Regen begann gleich nach dem Mittagessen."],"it":["pioggia","La pioggia è iniziata subito dopo pranzo."],"pt":["chuva","A chuva começou logo depois do almoço."],"nl":["regen","De regen begon vlak na de lunch."],"pl":["deszcz","Deszcz zaczął się zaraz po obiedzie."],"uk":["дощ","Дощ почався одразу після обіду."],"ru":["дождь","Дождь начался сразу после обеда."],"cs":["déšť","Déšť začal hned po obědě."],"sk":["dážď","Dážď začal hneď po obede."],"sv":["regn","Regnet började strax efter lunch."],"no":["regn","Regnet begynte rett etter lunsj."],"da":["regn","Regnen begyndte lige efter frokost."],"fi":["sade","Sade alkoi heti lounaan jälkeen."],"is":["rigning","Rigningin byrjaði rétt eftir hádegismat."],"et":["vihm","Vihm algas kohe pärast lõunat."],"lv":["lietus","Lietus sākās tūlīt pēc pusdienām."],"lt":["lietus","Lietus prasidėjo iškart po pietų."],"hu":["eső","Az eső mindjárt ebéd után kezdődött."],"ro":["ploaie","Ploaia a început imediat după prânz."],"bg":["дъжд","Дъждът започна веднага след обяда."],"el":["βροχή","Η βροχή άρχισε αμέσως μετά το μεσημεριανό."],"hr":["kiša","Kiša je počela odmah nakon ručka."],"sr":["киша","Киша је почела одмах после ручка."],"sl":["dež","Dež se je začel takoj po kosilu."],"tr":["yağmur","Yağmur öğle yemeğinden hemen sonra başladı."],"be":["дождж","Дождж пачаўся адразу пасля абеду."],"kk":["жаңбыр","Жаңбыр түскі астан кейін бірден басталды."],"ka":["წვიმა","წვიმა სადილის შემდეგ მაშინვე დაიწყო."],"hy":["անձրև","Անձրևը սկսվեց ճաշից անմիջապես հետո։"],"he":["גשם","הגשם התחיל מיד אחרי הצהריים."],"ar":["مطر","بدأ المطر بعد الغداء مباشرة."],"fa":["باران","باران بلافاصله بعد از ناهار شروع شد."],"hi":["बारिश","बारिश दोपहर के खाने के तुरंत बाद शुरू हुई।"],"bn":["বৃষ্টি","দুপুরের খাবারের পরপরই বৃষ্টি শুরু হলো।"],"ur":["بارش","بارش دوپہر کے کھانے کے فوراً بعد شروع ہوئی۔"],"th":["ฝน","ฝนเริ่มตกทันทีหลังอาหารกลางวัน"],"vi":["mưa","Mưa bắt đầu ngay sau bữa trưa."],"id":["hujan","Hujan mulai turun tepat setelah makan siang."],"ms":["hujan","Hujan mula turun sebaik selepas makan tengah hari."],"zh":["雨","午饭后马上就下雨了。"],"ja":["雨","昼食のすぐ後に雨が降り始めた。"],"ko":["비","점심 직후에 비가 내리기 시작했다."],"ca":["pluja","La pluja va començar just després de dinar."],"sw":["mvua","Mvua ilianza mara tu baada ya chakula cha mchana."],"tl":["ulan","Nagsimula ang ulan matapos ang tanghalian."]};
  var VOICE = {"en":"en-GB","es":"es-ES","fr":"fr-FR","de":"de-DE","it":"it-IT","pt":"pt-PT","nl":"nl-NL","pl":"pl-PL","uk":"uk-UA","ru":"ru-RU","cs":"cs-CZ","sk":"sk-SK","sv":"sv-SE","no":"nb-NO","da":"da-DK","fi":"fi-FI","is":"is-IS","et":"et-EE","lv":"lv-LV","lt":"lt-LT","hu":"hu-HU","ro":"ro-RO","bg":"bg-BG","el":"el-GR","hr":"hr-HR","sr":"sr-RS","sl":"sl-SI","tr":"tr-TR","be":"be-BY","kk":"kk-KZ","ka":"ka-GE","hy":"hy-AM","he":"he-IL","ar":"ar-SA","fa":"fa-IR","hi":"hi-IN","bn":"bn-BD","ur":"ur-PK","th":"th-TH","vi":"vi-VN","id":"id-ID","ms":"ms-MY","zh":"zh-CN","ja":"ja-JP","ko":"ko-KR","ca":"ca-ES","sw":"sw-KE","tl":"fil-PH"};

  function speak(text, voice) {
    try {
      var s = window.speechSynthesis;
      if (!s) return;
      s.cancel();
      var u = new SpeechSynthesisUtterance(text);
      u.lang = voice || 'en-GB';
      u.rate = 0.9;
      s.speak(u);
    } catch (e) {}
  }

  function shuffledPool(word) {
    var chars = word.split('');
    var pool = chars.map(function (ch, i) { return { ch: ch, id: i }; });
    for (var i = pool.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = pool[i]; pool[i] = pool[j]; pool[j] = tmp;
    }
    return { pool: pool, placed: chars.map(function () { return null; }) };
  }

  /* ---------- Puzzle widget (shared behavior for phone demo + language builder demo) ---------- */
  function Puzzle(root, opts) {
    this.root = root;
    this.opts = opts; // { slotsEl, poolEl, statusEl, checkBtn }
    this.pool = [];
    this.placed = [];
    this.answer = '';
    this.checked = false;
  }
  Puzzle.prototype.build = function (answer) {
    this.answer = answer;
    var made = shuffledPool(answer.toLowerCase());
    this.pool = made.pool;
    this.placed = made.placed;
    this.checked = false;
    this.render();
  };
  Puzzle.prototype.isFull = function () { return this.placed.length > 0 && this.placed.indexOf(null) === -1; };
  Puzzle.prototype.isCorrect = function () {
    var self = this;
    if (!this.isFull()) return false;
    var typed = this.placed.map(function (id) { return self.chOf(id); }).join('');
    return typed === this.answer;
  };
  Puzzle.prototype.chOf = function (id) {
    var t = this.pool.filter(function (p) { return p.id === id; })[0];
    return t ? t.ch : '';
  };
  Puzzle.prototype.place = function (index, id) {
    var prev = this.placed.indexOf(id);
    if (prev !== -1) this.placed[prev] = null;
    this.placed[index] = id;
    this.checked = this.opts.autoCheck ? this.isFull() : false;
    this.render();
  };
  Puzzle.prototype.pickFirstEmpty = function (id) {
    var i = this.placed.indexOf(null);
    if (i === -1) return;
    this.place(i, id);
  };
  Puzzle.prototype.undo = function (index) {
    if (this.placed[index] === null) return;
    this.placed[index] = null;
    this.checked = false;
    this.render();
  };
  Puzzle.prototype.check = function () { this.checked = true; this.render(); };
  Puzzle.prototype.render = function () {
    var self = this;
    var correct = this.checked && this.isCorrect();
    var wrong = this.checked && this.isFull() && !this.isCorrect();

    this.opts.slotsEl.innerHTML = '';
    this.placed.forEach(function (id, i) {
      var span = document.createElement('span');
      span.className = 'slot' + (id !== null ? ' filled' : '') + (correct ? ' correct' : '') + (wrong ? ' wrong' : '');
      span.textContent = id === null ? '' : self.chOf(id).toUpperCase();
      span.addEventListener('click', function () { self.undo(i); });
      span.addEventListener('dragover', function (e) { e.preventDefault(); });
      span.addEventListener('drop', function (e) {
        e.preventDefault();
        var raw = e.dataTransfer && e.dataTransfer.getData('text/plain');
        var id2 = parseInt(raw, 10);
        if (!isNaN(id2)) self.place(i, id2);
      });
      self.opts.slotsEl.appendChild(span);
    });

    this.opts.poolEl.innerHTML = '';
    this.pool.forEach(function (p) {
      var used = self.placed.indexOf(p.id) !== -1;
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pool-tile' + (used ? ' used' : '');
      btn.textContent = p.ch.toUpperCase();
      btn.draggable = true;
      btn.addEventListener('dragstart', function (e) {
        if (e.dataTransfer) { e.dataTransfer.setData('text/plain', String(p.id)); e.dataTransfer.effectAllowed = 'move'; }
      });
      btn.addEventListener('click', function () { if (!used) self.pickFirstEmpty(p.id); });
      self.opts.poolEl.appendChild(btn);
    });

    if (this.opts.statusEl) {
      if (correct) { this.opts.statusEl.textContent = this.opts.correctMsg; this.opts.statusEl.style.color = '#16a34a'; }
      else if (wrong) { this.opts.statusEl.textContent = this.opts.wrongMsg; this.opts.statusEl.style.color = '#e11d48'; }
      else { this.opts.statusEl.textContent = ''; }
    }
    if (this.opts.onRender) this.opts.onRender(correct, wrong);
  };

  /* ---------- Phone demo (Unit 4) ---------- */
  function initPhoneDemo() {
    var root = document.getElementById('phone-demo');
    if (!root) return;
    var ci = 0, target = 'fr', star = false;
    var slotsEl = root.querySelector('.js-ph-slots');
    var poolEl = root.querySelector('.js-ph-pool');
    var statusEl = root.querySelector('.js-ph-status');
    var rowsEl = root.querySelector('.js-ph-rows');
    var chipsEl = root.querySelectorAll('.js-ph-chip');
    var starBtn = root.querySelector('.js-ph-star');
    var checkBtn = root.querySelector('.js-ph-check');
    var prevBtn = root.querySelector('.js-ph-prev');
    var nextBtn = root.querySelector('.js-ph-next');
    var toastEl = root.querySelector('.js-ph-toast');
    var progressFill = root.querySelector('.js-ph-progress');
    var allHint = root.querySelector('.js-ph-all-hint');
    var practiceArea = root.querySelector('.js-ph-practice');

    var puzzle = new Puzzle(root, {
      slotsEl: slotsEl, poolEl: poolEl, statusEl: statusEl,
      correctMsg: T.correctShort, wrongMsg: T.wrongShort,
      autoCheck: true,
      onRender: renderRows
    });

    function renderRows() {
      var practicing = target !== 'all';
      practiceArea.hidden = !practicing;
      allHint.hidden = practicing;
      var langs = ['en', 'es', 'fr'];
      rowsEl.innerHTML = '';
      langs.forEach(function (code) {
        var isT = code === target;
        var correct = puzzle.checked && puzzle.isCorrect();
        if (isT && !correct) return;
        var entry = CONCEPTS[ci].w[code];
        var hidden = isT && !correct;
        var row = document.createElement('div');
        row.className = 'word-row' + (isT ? ' target' : '');
        var top = document.createElement('div');
        top.className = 'word-row-top';
        var codeSpan = document.createElement('span');
        codeSpan.className = 'word-code';
        codeSpan.textContent = code.toUpperCase();
        var wordSpan = document.createElement('span');
        wordSpan.className = 'word-text';
        wordSpan.textContent = hidden ? entry.t.split('').map(function () { return '_'; }).join(' ') : entry.t;
        if (hidden) wordSpan.style.color = '#3B4CB8';
        var speakBtn = document.createElement('button');
        speakBtn.type = 'button';
        speakBtn.className = 'word-speak';
        speakBtn.textContent = '🔊';
        speakBtn.addEventListener('click', function () { if (!hidden) speak(entry.t, VOICE[code]); });
        top.appendChild(codeSpan); top.appendChild(wordSpan); top.appendChild(speakBtn);
        var sentence = document.createElement('div');
        sentence.className = 'word-sentence';
        sentence.textContent = hidden ? T.spellRevealShort : entry.s;
        row.appendChild(top); row.appendChild(sentence);
        rowsEl.appendChild(row);
      });
    }

    function setTarget(code) {
      target = code;
      chipsEl.forEach(function (c) { c.classList.toggle('active', c.dataset.target === code); });
      if (code === 'all') { puzzle.placed = []; puzzle.pool = []; puzzle.checked = false; renderRows(); slotsEl.innerHTML = ''; poolEl.innerHTML = ''; }
      else puzzle.build(CONCEPTS[ci].w[code].t.toLowerCase());
    }

    chipsEl.forEach(function (chip) {
      chip.addEventListener('click', function () { setTarget(chip.dataset.target); });
    });
    if (checkBtn) checkBtn.addEventListener('click', function () { puzzle.check(); });
    if (prevBtn) prevBtn.addEventListener('click', function () { ci = (ci + CONCEPTS.length - 1) % CONCEPTS.length; progressFill.style.width = Math.round(((ci + 1) / CONCEPTS.length) * 100) + '%'; setTarget(target === 'all' ? 'all' : target); });
    if (nextBtn) nextBtn.addEventListener('click', function () { ci = (ci + 1) % CONCEPTS.length; progressFill.style.width = Math.round(((ci + 1) / CONCEPTS.length) * 100) + '%'; setTarget(target === 'all' ? 'all' : target); });
    starBtn.addEventListener('click', function () {
      star = !star;
      starBtn.style.color = star ? '#F9A80B' : '#C6CBD8';
      toastEl.textContent = star ? T.starAdd : T.starRemove;
      toastEl.hidden = false;
      clearTimeout(root._toastTimer);
      root._toastTimer = setTimeout(function () { toastEl.hidden = true; }, 2200);
    });

    // timer
    var timerValueEl = root.querySelector('.js-ph-timer-value');
    var timerLabelEl = root.querySelector('.js-ph-timer-label');
    var timerToggleBtn = root.querySelector('.js-ph-timer-toggle');
    var timerRestartBtn = root.querySelector('.js-ph-timer-restart');
    var remaining = 600, running = true;
    function renderTimer() {
      var m = Math.floor(remaining / 60), s = remaining % 60;
      timerValueEl.textContent = m + ':' + String(s).padStart(2, '0');
      var done = remaining <= 0;
      timerValueEl.style.color = done ? '#16a34a' : '#3B4CB8';
      timerLabelEl.textContent = done ? T.dailyGoalDone : T.dailyGoal;
      timerToggleBtn.textContent = running ? '❚❚' : '▶';
    }
    timerToggleBtn.addEventListener('click', function () { running = !running; renderTimer(); });
    timerRestartBtn.addEventListener('click', function () { remaining = 600; running = true; renderTimer(); });
    setInterval(function () { if (running && remaining > 0) { remaining -= 1; renderTimer(); } }, 1000);
    renderTimer();

    setTarget('fr');
  }

  /* ---------- Language builder demo ---------- */
  function initBuilderDemo() {
    var root = document.getElementById('lang-builder');
    if (!root) return;
    var active = ['en', 'es', 'fr'];
    var target = 'fr';
    var langGrid = root.querySelector('.js-dm-langs');
    var countEl = root.querySelector('.js-dm-count');
    var chipsEl = root.querySelector('.js-dm-chips');
    var rowsEl = root.querySelector('.js-dm-rows');
    var slotsEl = root.querySelector('.js-dm-slots');
    var poolEl = root.querySelector('.js-dm-pool');
    var statusEl = root.querySelector('.js-dm-status');
    var checkBtn = root.querySelector('.js-dm-check');
    var resetBtn = root.querySelector('.js-dm-reset');
    var practiceArea = root.querySelector('.js-dm-practice');
    var allHint = root.querySelector('.js-dm-all-hint');

    var puzzle = new Puzzle(root, {
      slotsEl: slotsEl, poolEl: poolEl, statusEl: statusEl,
      correctMsg: T.correct, wrongMsg: T.wrong,
      onRender: renderRows
    });

    function renderLangGrid() {
      langGrid.innerHTML = '';
      SITE_LANGS.forEach(function (l) {
        var code = l[2] || 'en';
        var on = active.indexOf(code) !== -1;
        var disabled = !on && active.length >= 6;
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.title = l[1];
        btn.className = 'demo-lang-btn' + (on ? ' on' : '') + (disabled ? ' disabled' : '');
        btn.textContent = l[1];
        btn.addEventListener('click', function () {
          if (on) {
            if (active.length <= 2) return;
            var next = active.filter(function (c) { return c !== code; });
            active = next;
            if (code === target) setTarget(next[0], false); else renderAll();
          } else {
            if (active.length >= 6) return;
            active = active.concat([code]);
            renderAll();
          }
        });
        langGrid.appendChild(btn);
      });
      countEl.textContent = active.length + ' / 6';
    }

    function renderRows() {
      var practicing = target !== 'all' && active.indexOf(target) !== -1;
      practiceArea.hidden = !practicing;
      allHint.hidden = practicing;
      rowsEl.innerHTML = '';
      var correct = puzzle.checked && puzzle.isCorrect();
      active.filter(function (c) { return c !== target || correct || !practicing; }).forEach(function (code) {
        var e = RAIN[code] || ['', ''];
        var row = document.createElement('div');
        row.className = 'word-row';
        row.style.padding = '6px 0';
        var top = document.createElement('div');
        top.className = 'word-row-top';
        var codeSpan = document.createElement('span'); codeSpan.className = 'word-code'; codeSpan.textContent = code.toUpperCase();
        var wordSpan = document.createElement('span'); wordSpan.className = 'word-text'; wordSpan.style.color = 'var(--app-fg)'; wordSpan.textContent = e[0];
        var speakBtn = document.createElement('button'); speakBtn.type = 'button'; speakBtn.className = 'word-speak'; speakBtn.textContent = '🔊';
        speakBtn.addEventListener('click', function () { speak(e[0], VOICE[code]); });
        top.appendChild(codeSpan); top.appendChild(wordSpan); top.appendChild(speakBtn);
        var sentence = document.createElement('div'); sentence.className = 'word-sentence'; sentence.style.paddingLeft = '0'; sentence.textContent = e[1];
        row.appendChild(top); row.appendChild(sentence);
        rowsEl.appendChild(row);
      });
    }

    function renderChips() {
      chipsEl.innerHTML = '';
      active.concat(['all']).forEach(function (code) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'chip' + (target === code ? ' active' : '');
        btn.textContent = code.toUpperCase();
        btn.addEventListener('click', function () { setTarget(code, true); });
        chipsEl.appendChild(btn);
      });
    }

    function setTarget(code, keepActive) {
      target = code;
      if (code === 'all') {
        puzzle.placed = []; puzzle.pool = []; puzzle.checked = false;
        slotsEl.innerHTML = ''; poolEl.innerHTML = '';
        renderRows();
      } else {
        puzzle.build((RAIN[code] ? RAIN[code][0] : '').toLowerCase());
      }
      renderChips();
      renderLangGrid();
    }

    function renderAll() { renderLangGrid(); renderChips(); setTarget(target, true); }

    checkBtn.addEventListener('click', function () { puzzle.check(); });
    resetBtn.addEventListener('click', function () { setTarget(target, true); });

    renderAll();
  }

  /* ---------- Add-words method switcher ---------- */
  function initAddWords() {
    var root = document.getElementById('add-words');
    if (!root) return;
    var methods = root.querySelectorAll('.js-aw-method');
    var panels = root.querySelectorAll('.js-aw-panel');
    var current = 1;
    var autoTimer = null;
    var userSelected = false;

    function show(n) {
      current = n;
      methods.forEach(function (m) { m.classList.toggle('active', Number(m.dataset.method) === n); });
      panels.forEach(function (p) { p.hidden = Number(p.dataset.method) !== n; });
    }
    methods.forEach(function (m) {
      m.addEventListener('click', function () {
        userSelected = true;
        clearInterval(autoTimer);
        show(Number(m.dataset.method));
      });
    });
    show(1);

    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (userSelected) return;
        if (e.isIntersecting) {
          clearInterval(autoTimer);
          autoTimer = setInterval(function () { show((current % 4) + 1); }, 1700);
        } else {
          clearInterval(autoTimer);
        }
      });
    }, { threshold: 0.5 });
    obs.observe(root);

    // upload panel
    var upTextarea = root.querySelector('.js-aw-up-words');
    var upBtn = root.querySelector('.js-aw-up-run');
    var upBtnLabel = root.querySelector('.js-aw-up-run-label');
    var upResultEl = root.querySelector('.js-aw-up-result');
    if (upTextarea) {
      upTextarea.addEventListener('input', function () { upBtn.disabled = !upTextarea.value.trim(); });
      upBtn.addEventListener('click', function () {
        var words = upTextarea.value.split(/[\n,]+/).map(function (w) { return w.trim(); }).filter(Boolean).slice(0, 4);
        if (!words.length) return;
        upBtnLabel.textContent = T.translating;
        upBtn.disabled = true;
        setTimeout(function () {
          upResultEl.innerHTML = '';
          words.forEach(function (w) {
            var fr = w.length % 2 ? 'le ' + w.toLowerCase() : w.toLowerCase() + 'age';
            var ru = w.toLowerCase() + 'ность';
            var div = document.createElement('div');
            div.className = 'aw-result-item';
            div.innerHTML = '<div style="color:#fff;font-weight:600;font-size:14.5px;">' + w + ' → <span style="color:#F9A80B;">' + fr + '</span> · <span style="color:#F9A80B;">' + ru + '</span></div>' +
              '<div style="color:#C4B4D8;font-size:13px;margin-top:4px;">' + T.example + w + T.exampleTail + '</div>';
            upResultEl.appendChild(div);
          });
          upBtnLabel.textContent = T.translateBtn;
          upBtn.disabled = false;
        }, 900);
      });
    }

    // generate panel
    var topicBtns = root.querySelectorAll('.js-aw-topic');
    var levelBtns = root.querySelectorAll('.js-aw-level');
    var genBtn = root.querySelector('.js-aw-gen-run');
    var genBtnLabel = root.querySelector('.js-aw-gen-run-label');
    var genResultEl = root.querySelector('.js-aw-gen-result');
    var genTopic = 'travel', genLevel = 'B1';
    var bank = { travel: ['airport', 'ticket', 'luggage', 'passport'], food: ['recipe', 'flavor', 'kitchen', 'grocery'], work: ['deadline', 'meeting', 'colleague', 'report'] };
    topicBtns.forEach(function (b) { b.addEventListener('click', function () { genTopic = b.dataset.topic; topicBtns.forEach(function (x) { x.classList.toggle('active', x === b); }); genResultEl.innerHTML = ''; }); });
    levelBtns.forEach(function (b) { b.addEventListener('click', function () { genLevel = b.dataset.level; levelBtns.forEach(function (x) { x.classList.toggle('active', x === b); }); genResultEl.innerHTML = ''; }); });
    if (genBtn) {
      genBtn.addEventListener('click', function () {
        genBtnLabel.textContent = T.generating;
        setTimeout(function () {
          var words = bank[genTopic] || bank.travel;
          genResultEl.innerHTML = '<div style="color:#C4B4D8;font-size:13px;margin-bottom:8px;font-family:\'IBM Plex Mono\',monospace;">Level ' + genLevel + '</div>';
          words.forEach(function (w) {
            var div = document.createElement('div');
            div.className = 'aw-result-item';
            div.style.color = '#fff'; div.style.fontSize = '14.5px';
            div.textContent = w;
            genResultEl.appendChild(div);
          });
          genBtnLabel.textContent = T.generateBtn;
        }, 900);
      });
    }

    // mcp panel
    root.querySelectorAll('.js-aw-mcp').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var on = btn.classList.toggle('connected');
        btn.querySelector('.aw-mcp-status').textContent = on ? T.connected : T.connect;
      });
    });

    // share panel
    var shareInput = root.querySelector('.js-aw-share-input');
    var shareBtn = root.querySelector('.js-aw-share-run');
    var shareResultEl = root.querySelector('.js-aw-share-result');
    if (shareBtn) {
      shareBtn.addEventListener('click', function () {
        var code = shareInput.value.trim();
        if (!code) return;
        shareResultEl.hidden = false;
        shareResultEl.textContent = T.imported(24, code);
      });
    }
  }

  /* ---------- Family dashboard ---------- */
  function initFamily() {
    var root = document.getElementById('family');
    if (!root) return;
    var children = [
      { name: 'Child 1', progress: '4 / 10', study: '12 min', langs: 'Nederlands, English, Русский, Italiano',
        stats: ['262', '9', '21', '🔥 6', '527', '91%'],
        chart: { correct: [9, 14, 11, 10, 8, 12, 13, 9, 7, 10, 12, 8], wrong: [2, 3, 1, 2, 3, 1, 2, 1, 2, 1, 1, 2] } },
      { name: 'Child 2', progress: '0 / 10', study: '0 min', langs: 'Nederlands, English, Русский, Français',
        stats: ['148', '5', '12', '🔥 0', '203', '76%'],
        chart: { correct: [4, 5, 3, 6, 2, 5, 4, 3, 5, 4, 2, 3], wrong: [3, 2, 4, 2, 3, 2, 3, 4, 2, 3, 2, 3] } }
    ];
    var statLabels = LANG === 'ru'
      ? ['Слов в уроках', 'Всего уроков', 'Дней обучения', 'Серия дней', 'Правильных ответов', 'Успешность']
      : ['Words in lessons', 'Total lessons', 'Learning days', 'Learning streak', 'Correct answers', 'Success rate'];

    var childCards = root.querySelectorAll('.js-child-card');
    var statGrid = root.querySelector('.js-stat-grid');
    var chartBars = root.querySelector('.js-chart-bars');
    var prioritySelect = root.querySelector('.js-priority-select');
    var currentPriorityEl = root.querySelector('.js-current-priority');
    var saveBtn = root.querySelector('.js-priority-save');
    var current = 0;
    var savedPriority = {};

    function fillSelect() {
      prioritySelect.innerHTML = '<option value="">' + T.chooseLesson + '</option>' +
        T.lessonOptions.map(function (o) { return '<option value="' + o[0] + '">' + o[1] + '</option>'; }).join('');
    }

    function render() {
      childCards.forEach(function (c, i) { c.classList.toggle('active', i === current); });
      var c = children[current];
      statGrid.innerHTML = '';
      c.stats.forEach(function (v, i) {
        var div = document.createElement('div');
        div.className = 'stat-card';
        div.innerHTML = '<div class="stat-label">' + statLabels[i] + '</div><div class="stat-value">' + v + '</div>';
        statGrid.appendChild(div);
      });
      chartBars.innerHTML = '';
      c.chart.correct.forEach(function (correct, i) {
        var wrong = c.chart.wrong[i];
        var total = 14 + 3;
        var bar = document.createElement('div');
        bar.className = 'chart-bar';
        bar.title = String(correct + wrong);
        bar.innerHTML = '<div class="wrong" style="height:' + Math.round((wrong / total) * 100) + '%"></div><div class="correct" style="height:' + Math.round((correct / total) * 100) + '%"></div>';
        chartBars.appendChild(bar);
      });
      var sel = savedPriority[current];
      var found = T.lessonOptions.filter(function (o) { return o[0] === sel; })[0];
      currentPriorityEl.textContent = found ? found[1] : (LANG === 'ru' ? '17.1 Ik ben heel handig' : '17.1 Ik ben heel handig');
      prioritySelect.value = '';
    }

    childCards.forEach(function (c, i) {
      c.addEventListener('click', function () { current = i; render(); });
    });
    saveBtn.addEventListener('click', function () {
      if (!prioritySelect.value) return;
      savedPriority[current] = prioritySelect.value;
      render();
    });

    fillSelect();
    render();
  }

  document.addEventListener('DOMContentLoaded', function () {
    initPhoneDemo();
    initBuilderDemo();
    initAddWords();
    initFamily();
  });
})();
