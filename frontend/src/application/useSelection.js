import { useCallback, useState } from "react";

import { validSelection } from "../domain/selection.js";
import { selectionStore } from "../infrastructure/selectionStore.js";

// The chosen customer and day, shared by every screen and kept across reloads.
export function useSelection(users, meta) {
  const [selection, setSelection] = useState(() => validSelection(selectionStore.load(), users, meta));

  const choose = useCallback(
    (change) =>
      setSelection((before) => {
        const next = validSelection({ ...before, ...change }, users, meta);
        selectionStore.save(next);
        return next;
      }),
    [users, meta],
  );

  return [selection, choose];
}
