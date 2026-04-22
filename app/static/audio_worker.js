/* app/static/audio_worker.js
 * [v1.0] Клиент для генерации озвучек через /api/audio/ensure.
 * Экспортирует window.AudioWorker: warmup(), ensureForItems(items), ensureForWord(word, lang)
 */
(function(){
  function hasAudio(value){
    return typeof value === "string" && value.trim() !== "";
  }
  function hasAudioForLang(word, lang){
    if (!word) return false;
    if (lang === "nl") return hasAudio(word.audio_nl) || hasAudio(word.nl_audio);
    if (lang === "en") return hasAudio(word.audio_en) || hasAudio(word.en_audio);
    if (lang === "ru") return hasAudio(word.audio_ru) || hasAudio(word.ru_audio);
    return false;
  }
  function needForWord(word, lang){
    return !hasAudioForLang(word, lang);
  }

  async function callEnsure(ids, langs){
    if (!ids || !ids.length) return null;
    try{
      const r = await window.apiFetch("/api/audio/ensure", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ ids, langs: langs && langs.length ? langs : ["nl","en","ru"] })
      });
      const js = await r.json();
      if (!js || js.ok !== true) return null;
      // ожидается: js.items = [ {id, nl, en, ru} ]
      return js.items || [];
    }catch(e){
      console.warn("[AudioWorker] ensure failed", e);
      return null;
    }
  }

  window.AudioWorker = {
    warmup(){ /* можно прогреть TTS/кэш, сейчас пусто */ },

    // Обрабатывает массив слов; возвращает новый массив с дописанными audio_* где были пустые
    async ensureForItems(items){
      const ids = (items||[])
        .filter(w => ["nl", "en", "ru"].some(lang => needForWord(w, lang)))
        .map(w => w.id);
      if (!ids.length) return items||[];
      const ensured = await callEnsure(ids, ["nl","en","ru"]);
      if (!ensured) return items||[];
      const map = new Map(ensured.map(x => [x.id, x]));
      return (items||[]).map(w => {
        const u = map.get(w.id);
        if (u){
          if (u.nl) w.audio_nl = u.nl;
          if (u.en) w.audio_en = u.en;
          if (u.ru) w.audio_ru = u.ru;
        }
        return w;
      });
    },

    // Обеспечивает аудио для одного слова и одного языка; возвращает ОБНОВЛЁННОЕ слово
    async ensureForWord(word, lang, opts){
      const force = !!(opts && opts.force);
      if (!force && !needForWord(word, lang)) return word;
      const items = await callEnsure([word.id], [lang]);
      const u = (items && items[0]) ? items[0] : null;
      if (!u) return word;
      // дописываем поля
      if (u.nl) word.audio_nl = u.nl;
      if (u.en) word.audio_en = u.en;
      if (u.ru) word.audio_ru = u.ru;
      return word;
    }
  };
})();
