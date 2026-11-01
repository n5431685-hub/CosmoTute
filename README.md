# 🪐 CosmoTute — Adaptive Learning Engine

**India-focused adaptive assessment for Classes 6–10, powered by Bayesian Knowledge Tracing**

Built for Code Kernel '26 (X-Kernel, GRIET) — Decode & Build rounds.

[![Watch the demo](https://img.youtube.com/vi/YOUR_VIDEO_ID/0.jpg)](https://youtu.be/YOUR_VIDEO_ID)

**🎥 Demo video:** [YouTube link](https://youtu.be/YOUR_VIDEO_ID)
**🌐 Live deployment:** [link, if hosted — otherwise remove this line]

---

## The Problem

Every Indian classroom moves at one pace — fast learners get bored, strugglers
fall behind, and gaps from Class 6–7 silently compound by the time board-exam
pressure hits in Class 10. Teachers want to help everyone but can't see who
needs what in a full classroom. Most adaptive-learning apps are built for
other markets and ignore India's reality: multiple boards and syllabi, large
class sizes, many languages, and uneven device/internet access.

## Our Idea

CosmoTute continuously tracks what each student actually understands —
skill by skill — using **Bayesian Knowledge Tracing (BKT)**, the same
probabilistic model used in systems like Khan Academy and ALEKS. Instead of
one end-of-chapter test, every question answered anywhere in the app updates
a live mastery estimate, so the system always knows where a student stands.

### How it adapts across Learn, Solve, Test

| Phase | How CosmoTute adapts |
|---|---|
| **Learn** | Checks mastery of prerequisite skills before a new topic; auto-recaps a weak prerequisite instead of letting gaps compound |
| **Solve** | Picks question difficulty live based on current mastery probability — moves a student up or down the difficulty ladder after every answer, not after a block of questions |
| **Test** | No single high-stakes test — mastery is assessed continuously and shown as a per-skill confidence score |

### Beyond right/wrong: error-type tagging

Wrong answers are classified as **conceptual gap**, **careless slip**, or
**language/translation confusion** — directly addressing the brief's "many
languages" problem, where a student can be mathematically fine but trip on
a word problem phrased differently from how they think in their first
language.

### Empowering the teacher, not replacing them

The teacher dashboard shows a skill × student mastery heatmap and flags
students who need attention — and why. The engine never auto-teaches; it
only surfaces insight so the teacher decides the intervention.

## Tech Stack
