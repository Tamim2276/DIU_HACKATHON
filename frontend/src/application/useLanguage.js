import { useCallback, useEffect, useState } from "react";

import { BANGLA, ENGLISH } from "../domain/format.js";
import { preferences } from "../infrastructure/preferences.js";

const KEY = "agam.language";
const LANGUAGES = [ENGLISH, BANGLA];

// The language of the whole app, kept across visits. It opens in English the first time.
export function useLanguage() {
  const [language, setLanguage] = useState(() => {
    const saved = preferences.load(KEY);
    return LANGUAGES.includes(saved) ? saved : ENGLISH;
  });

  // The page itself says which language it is in, for screen readers and for the browser's fonts.
  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  const choose = useCallback((next) => {
    if (!LANGUAGES.includes(next)) return;
    preferences.save(KEY, next);
    setLanguage(next);
  }, []);

  return [language, choose];
}
