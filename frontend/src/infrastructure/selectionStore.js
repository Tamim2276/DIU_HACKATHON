// Remembers the chosen customer and day in the browser, so a reload comes back to the same view.
// A browser may refuse storage (a private window, blocked site data). The app then simply forgets.

const KEY = "agam.selection";

export const selectionStore = {
  load() {
    try {
      return JSON.parse(window.localStorage.getItem(KEY));
    } catch {
      return null;
    }
  },

  save(selection) {
    try {
      window.localStorage.setItem(KEY, JSON.stringify(selection));
    } catch {
      // nothing to do: the choice lasts until the page is closed
    }
  },
};
