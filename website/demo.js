/* =========================================================
   [ДОБАВЛЕНО 2026-09-09]
   Интерактивная демонстрация на главной странице ParallelLingvo.
   - English показывается первым.
   - Кнопка + открывает выбор языка.
   - Можно добавить до 6 языков одновременно.
   - Кнопка динамика реально произносит слово через Web Speech API.
   ========================================================= */

(() => {
  'use strict';

  const MAX_LANGUAGES = 6;

  const LANGUAGE_DATA = [
    {
      code: 'nl',
      name: 'Nederlands',
      flag: '🇳🇱',
      voice: 'nl-NL',
      word: 'ontwikkeling',
      example: 'De ontwikkeling van de stad gaat snel.'
    },
    {
      code: 'ru',
      name: 'Русский',
      flag: '🇷🇺',
      voice: 'ru-RU',
      word: 'развитие',
      example: 'Развитие города идёт быстро.'
    },
    {
      code: 'de',
      name: 'Deutsch',
      flag: '🇩🇪',
      voice: 'de-DE',
      word: 'Entwicklung',
      example: 'Die Entwicklung der Stadt geht schnell voran.'
    },
    {
      code: 'fr',
      name: 'Français',
      flag: '🇫🇷',
      voice: 'fr-FR',
      word: 'développement',
      example: 'Le développement de la ville avance rapidement.'
    },
    {
      code: 'es',
      name: 'Español',
      flag: '🇪🇸',
      voice: 'es-ES',
      word: 'desarrollo',
      example: 'El desarrollo de la ciudad avanza rápidamente.'
    },
    {
      code: 'it',
      name: 'Italiano',
      flag: '🇮🇹',
      voice: 'it-IT',
      word: 'sviluppo',
      example: 'Lo sviluppo della città procede rapidamente.'
    },
    {
      code: 'pt',
      name: 'Português',
      flag: '🇵🇹',
      voice: 'pt-PT',
      word: 'desenvolvimento',
      example: 'O desenvolvimento da cidade avança rapidamente.'
    },
    {
      code: 'pl',
      name: 'Polski',
      flag: '🇵🇱',
      voice: 'pl-PL',
      word: 'rozwój',
      example: 'Rozwój miasta postępuje szybko.'
    },
    {
      code: 'uk',
      name: 'Українська',
      flag: '🇺🇦',
      voice: 'uk-UA',
      word: 'розвиток',
      example: 'Розвиток міста відбувається швидко.'
    },
    {
      code: 'zh',
      name: '中文（普通话）',
      flag: '🇨🇳',
      voice: 'zh-CN',
      word: '发展',
      example: '这座城市的发展很快。'
    },
    {
      code: 'ja',
      name: '日本語',
      flag: '🇯🇵',
      voice: 'ja-JP',
      word: '発展',
      example: 'この街の発展はとても速いです。'
    },
    {
      code: 'ko',
      name: '한국어',
      flag: '🇰🇷',
      voice: 'ko-KR',
      word: '발전',
      example: '도시의 발전이 빠르게 진행되고 있습니다.'
    },
    {
      code: 'tr',
      name: 'Türkçe',
      flag: '🇹🇷',
      voice: 'tr-TR',
      word: 'gelişim',
      example: 'Şehrin gelişimi hızla ilerliyor.'
    },
    {
      code: 'ar',
      name: 'العربية',
      flag: '🇸🇦',
      voice: 'ar-SA',
      word: 'تطور',
      example: 'يتقدم تطور المدينة بسرعة.'
    }
  ];

  const BASE_LANGUAGE = {
    code: 'en',
    name: 'English',
    flag: '🇬🇧',
    voice: 'en-GB',
    word: 'development',
    example: 'The development of the city is moving quickly.'
  };

  function initDemo() {
    const demo = document.getElementById('conceptDemo');
    const stack = document.getElementById('demoStack');
    const addButton = document.getElementById('demoAddLanguage');
    const picker = document.getElementById('demoLanguagePicker');
    const pickerGrid = document.getElementById('demoLanguageGrid');
    const pickerClose = document.getElementById('demoPickerClose');
    const count = document.getElementById('demoLanguageCount');

    if (!demo || !stack || !addButton || !picker || !pickerGrid || !pickerClose || !count) {
      return;
    }

    const selected = new Set([BASE_LANGUAGE.code]);

    function updateCounter() {
      count.textContent = `${selected.size} / ${MAX_LANGUAGES} languages`;

      if (selected.size >= MAX_LANGUAGES) {
        addButton.disabled = true;
        addButton.setAttribute('aria-disabled', 'true');
        addButton.querySelector('.demo-add-text').textContent = 'Maximum 6 languages';
        closePicker();
      } else {
        addButton.disabled = false;
        addButton.removeAttribute('aria-disabled');
        addButton.querySelector('.demo-add-text').textContent = 'Add another language';
      }
    }

    function closePicker() {
      picker.hidden = true;
      addButton.setAttribute('aria-expanded', 'false');
    }

    function openPicker() {
      if (selected.size >= MAX_LANGUAGES) {
        return;
      }

      renderPicker();
      picker.hidden = false;
      addButton.setAttribute('aria-expanded', 'true');

      const firstOption = pickerGrid.querySelector('.demo-language-option');
      if (firstOption) {
        requestAnimationFrame(() => firstOption.focus({ preventScroll: true }));
      }
    }

    function renderPicker() {
      pickerGrid.replaceChildren();

      LANGUAGE_DATA
        .filter((language) => !selected.has(language.code))
        .forEach((language) => {
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'demo-language-option';
          button.dataset.language = language.code;
          button.setAttribute('role', 'option');
          button.setAttribute('aria-label', `Add ${language.name}`);

          const flag = document.createElement('span');
          flag.className = 'demo-option-flag';
          flag.textContent = language.flag;

          const name = document.createElement('span');
          name.className = 'demo-option-name';
          name.textContent = language.name;

          const code = document.createElement('span');
          code.className = 'demo-option-code';
          code.textContent = language.code.toUpperCase();

          button.append(flag, name, code);
          pickerGrid.append(button);
        });
    }

    function createLanguageRow(language) {
      const row = document.createElement('article');
      row.className = 'concept-language-row is-entering';
      row.dataset.language = language.code;

      const identity = document.createElement('div');
      identity.className = 'demo-language-id';

      const flag = document.createElement('span');
      flag.className = 'demo-language-flag';
      flag.textContent = language.flag;
      flag.setAttribute('aria-hidden', 'true');

      const identityText = document.createElement('span');
      const languageName = document.createElement('strong');
      languageName.textContent = language.name;
      const languageCode = document.createElement('small');
      languageCode.textContent = language.code.toUpperCase();
      identityText.append(languageName, languageCode);
      identity.append(flag, identityText);

      const copy = document.createElement('div');
      copy.className = 'demo-language-copy';

      const wordLine = document.createElement('div');
      wordLine.className = 'demo-word-line';
      const word = document.createElement('strong');
      word.textContent = language.word;

      const speak = document.createElement('button');
      speak.type = 'button';
      speak.className = 'demo-speak';
      speak.dataset.speakWord = language.word;
      speak.dataset.speakLang = language.voice;
      speak.setAttribute('aria-label', `Pronounce ${language.word}`);
      speak.title = `Pronounce ${language.word}`;
      speak.textContent = '🔊';

      wordLine.append(word, speak);

      const example = document.createElement('p');
      example.className = 'demo-example';
      example.lang = language.code;
      example.textContent = language.example;

      copy.append(wordLine, example);
      row.append(identity, copy);

      row.addEventListener('animationend', () => {
        row.classList.remove('is-entering');
      }, { once: true });

      return row;
    }

    function addLanguage(code) {
      const language = LANGUAGE_DATA.find((item) => item.code === code);
      if (!language || selected.has(code) || selected.size >= MAX_LANGUAGES) {
        return;
      }

      selected.add(code);
      stack.append(createLanguageRow(language));
      updateCounter();
      closePicker();
    }

    function speakWord(button) {
      const word = button.dataset.speakWord || '';
      const lang = button.dataset.speakLang || 'en-US';

      if (!word || !('speechSynthesis' in window) || typeof SpeechSynthesisUtterance === 'undefined') {
        button.title = 'Speech synthesis is not available in this browser';
        return;
      }

      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(word);
      utterance.lang = lang;
      utterance.rate = 0.88;
      utterance.pitch = 1;

      button.classList.add('is-speaking');
      button.textContent = '◖))';

      const stopVisual = () => {
        button.classList.remove('is-speaking');
        button.textContent = '🔊';
      };

      utterance.onend = stopVisual;
      utterance.onerror = stopVisual;

      window.speechSynthesis.speak(utterance);
    }

    addButton.addEventListener('click', () => {
      if (picker.hidden) {
        openPicker();
      } else {
        closePicker();
      }
    });

    pickerClose.addEventListener('click', () => {
      closePicker();
      addButton.focus({ preventScroll: true });
    });

    pickerGrid.addEventListener('click', (event) => {
      const option = event.target.closest('.demo-language-option');
      if (!option) {
        return;
      }
      addLanguage(option.dataset.language);
    });

    demo.addEventListener('click', (event) => {
      const speakButton = event.target.closest('.demo-speak');
      if (speakButton) {
        speakWord(speakButton);
      }
    });

    document.addEventListener('click', (event) => {
      if (!picker.hidden && !demo.contains(event.target)) {
        closePicker();
      }
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !picker.hidden) {
        closePicker();
        addButton.focus({ preventScroll: true });
      }
    });

    const baseRow = stack.querySelector('.concept-language-row');
    if (baseRow) {
      baseRow.classList.add('is-entering');
      baseRow.addEventListener('animationend', () => {
        baseRow.classList.remove('is-entering');
      }, { once: true });
    }

    updateCounter();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDemo, { once: true });
  } else {
    initDemo();
  }
})();
