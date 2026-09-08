/** FastAPI's 422 body: one entry per rejected field. */
type ValidationItem = { type: string; loc: (string | number)[]; msg: string };

export class ApiError extends Error {
  readonly detail: string;
  /** field name -> message, for 422s. Empty for every other status. */
  readonly fields: Record<string, string>;

  constructor(
    readonly status: number,
    body: string | ValidationItem[] | undefined,
  ) {
    super(typeof body === "string" ? body : `Request failed with ${status}`);
    this.fields = {};
    if (Array.isArray(body)) {
      for (const item of body) {
        // loc is ["body", "amount"] or ["query", "year"]; the field is last.
        const field = String(item.loc[item.loc.length - 1]);
        this.fields[field] = item.msg;
      }
      this.detail = body.map((i) => i.msg).join("; ");
    } else {
      this.detail = body ?? `Request failed with ${status}`;
    }
  }
}
