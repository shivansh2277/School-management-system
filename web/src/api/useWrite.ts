/**
 * The one way a screen performs a write.
 *
 * A thin wrapper over react-query's `useMutation`, which is already a
 * dependency and already the idiom on every existing page - this is not a
 * replacement for it. It removes the two things each of those pages repeated by
 * hand and could get wrong independently:
 *
 *  - `useQueryClient()` plus an `onSuccess` that invalidates. A write whose
 *    query key is forgotten leaves the clerk looking at the figure from before
 *    their own payment, which reads as the payment not having been taken.
 *  - digging the message out of a caught error. `fieldErrors` below pairs with
 *    `FormField`'s `error` prop so a 422 lands next to the input the backend
 *    named, rather than in a toast that vanishes before it is read.
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "./errors";

/**
 * field name -> the backend's message, for a 422. Empty for anything else, so
 * a call site can index it without checking the status first.
 */
export function fieldErrors(error: unknown): Record<string, string> {
  return error instanceof ApiError ? error.fields : {};
}

export function useWrite<TArgs = void, TResult = unknown>({
  write,
  invalidates,
  onDone,
}: {
  write: (args: TArgs) => Promise<TResult>;
  /**
   * Query keys to refetch on success, as prefixes - `["fees"]` invalidates
   * `["fees", studentId]` too. Every list the write could have changed belongs
   * here, not just the one on screen.
   */
  invalidates?: readonly unknown[][];
  onDone?: (result: TResult) => void;
}) {
  const qc = useQueryClient();
  const m = useMutation({
    mutationFn: write,
    onSuccess: (result) => {
      for (const key of invalidates ?? []) qc.invalidateQueries({ queryKey: key });
      onDone?.(result);
    },
  });

  return {
    run: m.mutate,
    runAsync: m.mutateAsync,
    busy: m.isPending,
    error: m.error as unknown,
    /** Per-field messages for a 422, to hand to `FormField`'s `error` prop. */
    fields: fieldErrors(m.error),
    reset: m.reset,
  };
}
