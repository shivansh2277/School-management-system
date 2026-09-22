# Subagent packet reports

One file per packet, named for it: `packet-0-write-layer.md`,
`packet-1-admission.md`, and so on. The required structure is in
`FRONTEND-HANDOFF.md` Part Five — follow it exactly, because the owner reads
these against the diff and a section that is missing reads as a section that
was skipped.

These are the record of what was actually done and actually verified, so they
are committed with the work rather than kept outside the repo. A packet's
commit and its report land together.

**The two rules that matter more than the format:**

1. **Report what you ran, not what you intended to run.** Paste real command
   output. If a check failed and you moved on, that belongs here. A green
   summary over a red run makes the whole process worthless.
2. **A screen you did not open does not work.** Type-checking proves the shape
   of the code, not the behaviour of the product. Name the screens you opened
   and the screens you did not.

An honest "not verified" is worth more than a confident claim that turns out to
be a summary of something nobody ran.
