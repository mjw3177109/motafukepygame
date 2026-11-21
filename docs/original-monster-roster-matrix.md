# Full original monster roster: encounter estimate regression (not 1:1 signoff)

Source: `game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`.
The 33 monster arrays in `data/original_combat_tables.json` were separately audited against FFDec `frame_4346/DoAction.as`, while the field semantics and encounter gate were audited against `frame_4346/DoAction_2.as`.

Previously the Pygame and HTML5 entry probes shared only 11 hand-picked fixture vectors. This change checks **all 33 original monster IDs** across four synthetic hero profiles per monster (132 combinations in each runtime): denied attack, ordinary stats, high stats, and attack one point above monster defense. The special map tiles `188 -> 31` and `198 -> 32` are included.

Both tests compare the entry result to a separately written arithmetic oracle, verify the full source roster, and assert input immutability. The Python and Node tests also hash the checked-in `game.swf` bytes against the source anchor. Existing CI commands already run these test modules; no workflow broadening is needed.

**Strict limits:** These are deterministic *synthetic* hero inputs derived from original monster arrays, **not** recordings of the Flash player. They verify only the `Move_arrow` encounter estimate; they do not establish live Flash timing, random criticals, full battle, final HP, rewards, animation, map/plot/ending, or Pygame/HTML5 gameplay parity. RL/Gymnasium and Kaggle remain blocked pending complete original replay and manual signoff.
