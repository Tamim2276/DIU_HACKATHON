// Small things the browser remembers between visits: the chosen customer and day, and the language.
// A browser may refuse storage (a private window, blocked site data). The app then simply forgets.

export const preferences = {
  load(key) {
    try {
      return JSON.parse(window.localStorage.getItem(key));
    } catch {
      return null;
    }
  },

  save(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // nothing to do: the choice lasts until the page is closed
    }
  },
};
