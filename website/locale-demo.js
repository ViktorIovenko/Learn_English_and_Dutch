(() => {
  'use strict';

  const stage = document.querySelector('.product-stage:not(.interactive-demo-stage)');
  if (!stage) return;

  const italian = document.documentElement.lang === 'it';
  const text = italian ? {
    live: 'DEMO DAL VIVO · FINO A 6', label: 'Un concetto', title: 'Scopri come ParallelLingvo collega le lingue',
    add: 'Aggiungi un’altra lingua', choose: 'Scegli una lingua', hint: 'Premi +, scegli una lingua, poi usa 🔊 per ascoltare la parola.'
  } : {
    live: 'LIVE DEMO · UP TO 6', label: 'One concept', title: 'See how ParallelLingvo connects languages',
    add: 'Add another language', choose: 'Choose a language', hint: 'Press +, choose a language, then use 🔊 to hear the word.'
  };

  stage.className = 'product-stage interactive-demo-stage';
  stage.setAttribute('aria-label', 'Interactive ParallelLingvo demo');
  stage.innerHTML = `
    <div class="stage-orbit orbit-one" aria-hidden="true"></div><div class="stage-orbit orbit-two" aria-hidden="true"></div>
    <div class="floating-chip chip-top">${text.live}</div>
    <div class="concept-demo" id="conceptDemo"><div class="concept-demo-head"><div class="concept-demo-label"><small>${text.label}</small><strong>${text.title}</strong></div><span class="concept-demo-count" id="demoLanguageCount">1 / 6 languages</span></div>
    <div class="concept-stack" id="demoStack" aria-live="polite"><article class="concept-language-row is-base" data-language="en"><div class="demo-language-id"><span class="demo-language-flag" aria-hidden="true">🇬🇧</span><span><strong>English</strong><small>EN</small></span></div><div class="demo-language-copy"><div class="demo-word-line"><strong>development</strong><button class="demo-speak" type="button" data-speak-word="development" data-speak-lang="en-GB" aria-label="Pronounce development" title="Pronounce development">🔊</button></div><p class="demo-example" lang="en">The development of the city is moving quickly.</p></div></article></div>
    <button class="demo-add-language" id="demoAddLanguage" type="button" aria-haspopup="dialog" aria-expanded="false" aria-controls="demoLanguagePicker"><span class="demo-plus" aria-hidden="true">＋</span><span class="demo-add-text">${text.add}</span></button>
    <div class="demo-language-picker" id="demoLanguagePicker" role="dialog" aria-label="${text.choose}" hidden><div class="demo-picker-head"><div><strong>${text.choose}</strong><small>${text.hint}</small></div><button class="demo-picker-close" id="demoPickerClose" type="button" aria-label="Close language picker">×</button></div><div class="demo-language-grid" id="demoLanguageGrid" role="listbox" aria-label="Languages"></div></div></div>
    <div class="demo-hint" aria-hidden="true"><strong>Try it</strong>${text.hint}</div>`;
})();
