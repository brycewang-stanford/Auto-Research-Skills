# Free-Research-Crew v0.5 launch film: spec

GOAL:    a viewer leaves knowing that the crew's agents never grade their own work: a tool checks
         what happened, a Reviewer attacks every stage, a human approves four gates; and that six
         papers made it through.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, H.264, unnarrated, silent (no music source on this machine).
TIME:    76 s x 30 = 2280 frames. Scenes: hook 0-5.5, crew 5.5-16, flow 16-32, reviewer 31.5-53
         (0.5 s overlap for the iris), proof 53-67, close 66.5-76 (0.5 s overlap for the teal rise).
LOOK:    the repo poster's palette (assets/poster/build_poster.py): paper #fbf5e4, cream #f3e8cc,
         ink #3a2a1a, teal #4f8f86, amber #d39a3a (the one accent: one word or number per shot),
         rust #b8643a and red #b8463a only for Reviewer verdicts, brown #7a5232 for secondary text.
         Display: Nunito 900, 64-110 px, tracking -1%. Body: Nunito 700, 28-36 px. Chinese
         subtitles: Noto Sans SC (subset, OFL) 500, 30-40 px, under each English line.
         Code and file names: JetBrains Mono 26-30 px, only for real file names and real output.
         Medium: the poster's parchment cards (5 px #4a2e16 outline, 9 px #d9b67a inner frame) and
         role pills (4 px #2a1b10 outline, 14 px radius). Paper grain 4% (seeded feTurbulence).
OBJECTS: the workspace folder with its real files; role pills with the poster's one-line duties;
         the gate track (the poster's brown bench with four gates); a terminal strip with crew.py's
         real error text; the real metrics.json line, numbers.tex macro and paper sentence; review
         sheets quoting real review.json kill arguments, with ink verdict stamps; six paper cards.
MOTION:  enter expo.out / power4.out 0.5-0.7 s; moves power2.inOut 0.6 s; exits power3.in 0.3 s;
         stamps back.out(1.6) 0.35 s (position and scale only). Words stagger 0.08 s, list rows
         0.12-0.18 s. Titles land and hold still.
SHOTS:   1 hook: sentence inks in word by word from grey; "nothing" turns amber; Reviewer pill
           drops in where it will sit in shot 2.
         2 crew: folder lands, files tick in, nine role pills + PI fill two columns around it;
           headline swaps to "Files are the only handoff"; ink lines run from roles to files.
           Whip left.
         3 flow: gate track draws, gate 1 approved; track rises; terminal shows the refusal, lock on
           the design gate; design approved, lock opens; metrics.json -> numbers.tex -> paper chain,
           1,573 carried along it; results gate approved.
         4 reviewer: iris to the dark desk; three review sheets dealt onto it: LaLonde kill argument
           with five per-repetition lower bounds against zero (revise), hdm zero threshold $87 ->
           $0.36 (revise), the placebo that fails either way (block).
         5 proof: six paper cards with outcome and clean-rerun stamp; grid lifts; totals land:
           68 rounds, 12 / 210 / 373 findings, ~$58-103 per paper.
         6 close: teal flood; wordmark letters in; the two install commands type; URL; CC0 · v0.5.
BANNED:  dark void with floating specks; glow, particles; purple or blue gradients; glass cards;
         serif display with italic accents; small monospace caps labels; numbered 01/02 labels;
         everything fading and sliding up; titles drifting after landing; corner labels or
         brackets; logo docked in a corner; any logo of another company; any real person;
         any number not in the repo.
QA:      t = 0 (thumbnail reads), 3.5, 8, 14, 19, 22.5, 28, 35, 40, 46, 51, 57, 64, 74, 77:
         no text overflow or overlap, every number matches release-v0.5.md / gallery files.
