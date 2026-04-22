(() => {
  const DB_NAME = "learn_words_db";
  const DB_VERSION = 1;
  const STORES = ["words", "lessons", "progress", "outbox", "meta/state"];

  let dbPromise = null;

  function openDb() {
    if (!("indexedDB" in window)) {
      return Promise.reject(new Error("IndexedDB is not supported"));
    }
    if (dbPromise) return dbPromise;

    dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = () => {
        const db = request.result;
        STORES.forEach((name) => {
          if (!db.objectStoreNames.contains(name)) {
            db.createObjectStore(name);
          }
        });
      };

      request.onsuccess = () => {
        const db = request.result;
        db.onversionchange = () => db.close();
        resolve(db);
      };

      request.onerror = () => reject(request.error);
      request.onblocked = () => {
        console.warn("[idb] open blocked by another connection");
      };
    });

    return dbPromise;
  }

  async function withStore(storeName, mode, handler) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, mode);
      const store = tx.objectStore(storeName);
      let result;

      try {
        result = handler(store);
      } catch (err) {
        reject(err);
        return;
      }

      tx.oncomplete = () => resolve(result);
      tx.onerror = () => reject(tx.error || new Error("Transaction failed"));
      tx.onabort = () => reject(tx.error || new Error("Transaction aborted"));
    });
  }

  const LocalDB = {
    open: openDb,
    stores: Object.freeze(STORES.slice()),
    get(storeName, key) {
      return withStore(storeName, "readonly", (store) => new Promise((resolve, reject) => {
        const req = store.get(key);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      }));
    },
    getAll(storeName) {
      return withStore(storeName, "readonly", (store) => new Promise((resolve, reject) => {
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      }));
    },
    entries(storeName) {
      return withStore(storeName, "readonly", (store) => new Promise((resolve, reject) => {
        const items = [];
        const req = store.openCursor();
        req.onsuccess = () => {
          const cursor = req.result;
          if (cursor) {
            items.push({ key: cursor.key, value: cursor.value });
            cursor.continue();
          } else {
            resolve(items);
          }
        };
        req.onerror = () => reject(req.error);
      }));
    },
    set(storeName, value, key) {
      return withStore(storeName, "readwrite", (store) => new Promise((resolve, reject) => {
        const req = store.put(value, key);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      }));
    },
    add(storeName, value, key) {
      return withStore(storeName, "readwrite", (store) => new Promise((resolve, reject) => {
        const req = store.add(value, key);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      }));
    },
    del(storeName, key) {
      return withStore(storeName, "readwrite", (store) => new Promise((resolve, reject) => {
        const req = store.delete(key);
        req.onsuccess = () => resolve(true);
        req.onerror = () => reject(req.error);
      }));
    },
    delMany(storeName, keys) {
      return withStore(storeName, "readwrite", (store) => {
        (keys || []).forEach((key) => store.delete(key));
        return (keys || []).length;
      });
    },
    clear(storeName) {
      return withStore(storeName, "readwrite", (store) => new Promise((resolve, reject) => {
        const req = store.clear();
        req.onsuccess = () => resolve(true);
        req.onerror = () => reject(req.error);
      }));
    }
  };

  window.LocalDB = LocalDB;
  openDb().catch((err) => console.warn("[idb] init failed", err));
})();
