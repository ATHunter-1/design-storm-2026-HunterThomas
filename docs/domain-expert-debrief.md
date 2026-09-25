# Domain Expert Debrief: Denver Water (Scenario 2)

Questions for the debrief, in priority order. If time is short, ask the top five.

## Must-ask (top 5)

1. **Where does Foothills take its water from in Strontia, and at what depth?** Can they choose the depth (multiple intake levels)? This decides whether a mid-depth plume matters.
2. **"Walk us through Aug 14-15 from your side."** Who noticed, when, and what did they change? This gives us the real operator workflow.
3. **What decision would earlier warning change, and how much lead time is useful?** Hours or days? What would they do with it?
4. **What turbidity at the intake triggers action?** Are there other triggers, such as TOC, pH, or algae?
5. **Show them the depth table** in [scenario-2-planning.md](scenario-2-planning.md) and ask whether the pattern matches what they believe happened: a mid-depth peak on Aug 16, deeper by Aug 18-19, surface clear.

## Data questions (answered by Jake)

- Is "Vertical Position" in feet or metres, and how deep is the water where the sonde hangs? (Jake says metres)
- Where is the sonde relative to the intake and the dam, and how often does it cast? (The sonde is in the middle of the reservoir, and intake closer to the dam, maybe a 400m gap. It measures every 6 hours.)
- Was the conductance reading of 38 at 1 PM on Aug 14 a sensor glitch? probably a glitch. How do they handle bad or provisional readings? we are still working through how to deal with that - probably exclude the outliers
- Flow at Trumbull barely changed (139 to 147 cfs). Where did the runoff come in: a tributary below Trumbull, or a burn scar?
- Travel time: `guide.md` says about 4 hours from the gage to the intake, but the models use lags of several days. Which should we use for arrival? we'll stay with 4 hours
- Are there other storms in the sonde period worth comparing? The weather station shows rain of 0.5 or more on May 6, May 19, Jul 24, and Aug 14.

## Domain and language (for DDD)

- What counts as a "storm event" to them? Do they name events or keep a log of them?
- Their exact words for the plume, the layers, the intake, and turnover. These become our shared vocabulary.
- Besides turbidity, which parameters matter after a storm? Does turbidity tell them anything about TOC?
- Who is the real user: plant operators, water quality analysts, or the raw water group? How do they get this information today (dashboards, SCADA, email)?

## Scope for tomorrow

- What would make this useful to them rather than just interesting?
- Is anything off-limits, or do they have an existing tool we should avoid duplicating?
- Can we follow up with someone by email tomorrow?

## Interview tips

- Ask for **stories** ("the last time..."), not opinions ("what would you want...").
- Record their **exact phrases**; don't translate them into our own terms.
- Don't lead. Show the depth table and ask "what do you see?" before explaining our read of it.
- Note anything they call wrong or unimportant. That tells us where the model's boundaries are.

## Notes

| Question | Answer | Who said it |
| --- | --- | --- |
| Sensor locations | "Everywhere" | Denver Water |
| Magic-wand problem | "Biggest problem we have is we don't have visualization." | Denver Water |
| Intake depth | | |
| Aug 14-15 operator story | | |
| Useful lead time | | |
| Action thresholds | | |
| Depth-table reaction | | |
| Vertical Position units | Metres below the surface (replaces the earlier "feet") | Jake |
| Sonde location and cadence | Middle of the reservoir, roughly 400 m from the intake, which is nearer the dam; casts every 6 hours | Jake |
| Conductance 38 on Aug 14 | Probably a glitch; handling of bad readings still being worked out, probably excluding outliers | Jake |
| Travel time for arrival | Stay with about 4 hours, gage to intake | Jake |
| Terms they use | | |
| Follow-up contact | | |
