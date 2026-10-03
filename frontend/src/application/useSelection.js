import { useCallback, useState } from "react";

import { validSelection } from "../domain/selection.js";
import { preferences } from "../infrastructure/preferences.js";

const KEY = "agam.selection";

// The chosen customer and day, and the customer's savings goal if they set one.
// Shared by every screen and kept across reloads. A goal belongs to one customer:
// choosing another customer drops it.
export function useSelection(users, meta) {
  const [selection, setSelection] = useState(() => validSelection(preferences.load(KEY), users, meta));

  const choose = useCallback(
    (change) =>
      setSelection((before) => {
        const another = change.userId !== undefined && change.userId !== before.userId;
        const next = validSelection({ ...before, ...(another ? { goal: null } : {}), ...change }, users, meta);
        preferences.save(KEY, next);
        return next;
      }),
    [users, meta],
  );

  return [selection, choose];
}
