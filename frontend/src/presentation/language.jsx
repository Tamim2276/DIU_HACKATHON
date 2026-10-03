import { createContext, useContext, useMemo } from "react";

import { ENGLISH, formatter } from "../domain/format.js";
import bangla from "./text/bn.js";
import english from "./text/en.js";

const TEXTS = { en: english, bn: bangla };

const LanguageContext = createContext(ENGLISH);

export const LanguageProvider = LanguageContext.Provider;

// What a component needs to speak the chosen language:
// `t` holds every sentence, `f` writes numbers and dates, `language` is "en" or "bn".
export function useText() {
  const language = useContext(LanguageContext);
  return useMemo(() => ({ language, t: TEXTS[language] ?? english, f: formatter(language) }), [language]);
}
