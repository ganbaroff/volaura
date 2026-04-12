# Neuroscience-Informed Design — Swarm Skill v1.0

## Trigger
Activate when: reviewing UI components, reward mechanics, assessment flow, achievement moments, cross-product integration, dashboard design, any user-facing experience.
Trigger words: "UX review", "UI design", "reward", "achievement", "gamification", "emotional", "user experience", "dashboard", "AURA display".

## Output
Per-principle checklist: PASS/FAIL for each of 7 Ramachandran principles.
Specific violations with fix recommendations. Anti-pattern flags.

## Purpose

Load this skill before reviewing any UI component, reward mechanic, assessment flow, achievement moment, or cross-product integration feature. It prevents the most common failure mode in rational-product design: building features that are logically correct but emotionally inert — what Ramachandran calls the Cotard pattern: the user's brain recognizes the product but feels nothing, so it treats the product as dead. This skill converts neuroscience findings into binary checks that agents can apply directly, without interpretation.

## Source

- V.S. Ramachandran — *The Tell-Tale Brain* (2011)
- V.S. Ramachandran — *Phantoms in the Brain* (1998)
- V.S. Ramachandran — *The Emerging Mind* (2003, Reith Lectures)
- David Eagleman — *Incognito: The Secret Lives of the Brain* (2011)

---

## 7 Core Principles → Design Rules

---

### 1. Brain Constructs Reality

**Neuroscience finding:** The brain does not record reality — it constructs a useful model of it. 30+ parallel visual processing zones operate simultaneously, each contributing a partial interpretation. What reaches consciousness is a consensus model, not ground truth. The model is optimized for action, not accuracy.

**Volaura implication:** AURA is not a measurement instrument — it is a useful self-model that enables better action. If the copy implies clinical precision ("your score is 84.3"), the brain receives it as a claim about objective truth and will reject it when it conflicts with self-image. If copy implies discovery ("AURA reveals what you already are"), the brain accepts it as a new frame to try on.

**Rules:**
- MUST: All copy describing AURA, badge tiers, and competency scores must use the vocabulary of revelation and discovery: "reveals," "surfaces," "discovers," "shows." Never "measures," "tests," "calculates," "rates."
- NEVER: Use decimal precision (84.3) on user-facing scores. Round to whole numbers. Precision implies false objectivity.
- CHECK: Does every AURA display screen include at least one sentence that frames the score as a model the user can act on — not a verdict they must accept?

---

### 2. Conscious → Unconscious

**Neuroscience finding:** All skilled behavior begins as explicit, deliberate, conscious processing and — with repetition — migrates to implicit, automatic, unconscious execution. Learning to drive requires full attention; an experienced driver can drive while having a conversation. The conscious system has a bottleneck (approximately 7±2 chunks); the unconscious system has no known capacity limit.

**Volaura implication:** The assessment flow must eliminate every decision point that forces the user to stop and think about the interface rather than the question. Each extra click, each unclear label, each loading pause is a context switch that pushes the user back into conscious mode and increases dropout probability. The goal is that completing an assessment feels like a conversation, not a form.

**Rules:**
- MUST: Every screen transition in the assessment flow must have a single, unambiguous next action. No two-button dilemmas mid-assessment.
- NEVER: Show progress as a fraction ("Question 3 of 12") during adaptive assessment — it anchors conscious awareness on remaining effort. Use a smooth progress bar only.
- CHECK: Can a user complete the full assessment flow without reading any label twice? If any label requires a re-read, it is not yet automatic.

---

### 3. Peak Shift

**Neuroscience finding:** Neurons responding to a stimulus respond even more strongly to an exaggerated version of that stimulus. A rat trained to respond to a rectangle will respond more strongly to a longer, thinner rectangle than to the original. Great art does not copy reality — it amplifies the features that trigger the relevant neural response. This is why a caricature is more recognizable than a photograph.

**Volaura implication:** Achievement moments (badge reveal, AURA milestone, crystal drop, skill verified) must not report what happened — they must amplify it. A flat notification ("You earned Gold badge") leaves the dopamine system inert. A choreographed reveal with animation, sound, copy escalation, and multi-layer response fires the system the way the achievement actually deserves. The moment must be MORE dramatic than the achievement, not equal to it.

**Rules:**
- MUST: Every badge reveal must include at minimum: a visual amplifier (animation or transition), copy that escalates (not states), and a secondary trigger (crystal drop, share prompt, or milestone unlock).
- NEVER: Use toast notifications for achievement moments. A toast is a report. Achievement moments require full-screen or modal treatment with an active dismiss.
- CHECK: If you removed all animation and copy and showed only the badge icon and name — would the moment still feel earned? If yes, the Peak Shift layer is missing.

---

### 4. Dopamine System

**Neuroscience finding:** The dopamine system encodes reward prediction and motivates approach behavior. Critically, dopamine fires on the anticipation of reward, not the receipt of it — and it fires in response to variable ratio schedules more than fixed ones. Dopamine is a pull system: it makes you move toward something. Negative reinforcement (avoid losing something) activates a different circuit — fear/avoidance — which produces anxiety, not engagement.

**Volaura implication:** Crystals, streaks, and badges must always be framed as things the user earns by doing — never as things the user keeps by not stopping. "Complete your assessment to earn 50 crystals" activates dopamine. "You'll lose your streak if you don't complete today" activates cortisol. The first creates a player; the second creates an anxious user who eventually churns to escape the pressure.

**Rules:**
- MUST: Every CTA and notification copy must be audited against this binary: does it describe earning something (dopamine) or avoiding losing something (fear)? Only dopamine-framed copy is acceptable.
- NEVER: Use streak-loss warnings, expiry countdowns, or "don't miss out" framing. These are fear activators. Delete them.
- CHECK: Read every push notification and email subject line aloud. If the sentence makes sense with "or else" at the end, it is fear-framed. Rewrite it.

---

### 5. Synesthesia / Cross-Modal Links

**Neuroscience finding:** In synesthetes, stimulation in one sensory modality automatically triggers a response in a connected modality — a specific number always appears as a specific color, a specific sound produces a specific taste. Ramachandran argues this is an amplified version of normal cross-modal binding that all brains perform. The binding creates a sense that the world is coherent and interconnected. When cross-modal binding fails (as in certain lesion cases), the world feels flat, disconnected, and unreal.

**Volaura implication:** When a user completes an assessment, multiple product layers must visibly respond simultaneously: AURA score updates, crystals appear, Life Sim character reacts, organization visibility changes. If only one thing responds, the world feels incoherent — like hitting a key on a piano and hearing only one string when you expected a chord. The ecosystem must behave like a coherent world, not a collection of separate features.

**Rules:**
- MUST: Every major user action (assessment completion, badge earned, skill verified) must trigger visible responses in at least 2 product layers within the same session. Define the response chain before shipping the feature.
- NEVER: Ship a feature that produces a single isolated response. Before any feature goes to review, the agent must be able to name at least 2 downstream reactions.
- CHECK: Draw the response chain for the action being reviewed. If the chain has only 1 node, the feature is not ready.

---

### 6. Savant Discovery

**Neuroscience finding:** Ramachandran's study of savant syndrome — exemplified by Nadia's extraordinary drawing ability — suggests that suppressing or bypassing one dominant cognitive module can allow latent capacity in another to surface. Nadia could not narrate her drawing; she bypassed the narrative system and accessed direct visual-motor processing unavailable to typical artists. The savant finding implies that hidden competencies exist in most people, masked by dominant framings of themselves.

**Volaura implication:** AURA must be designed to surface competencies users did not know they had — and to make that surfacing feel like a discovery, not a score. If a user scores above 75 in a competency they did not self-report as a strength, that moment must be treated as a revelation event. It is the most powerful retention hook in the product: "AURA found something in me I didn't see." If the product only confirms what users already know, it adds no self-model value.

**Rules:**
- MUST: Any competency score above 75 that was not listed as a self-reported strength must trigger a "discovery moment" UI state — distinct copy, distinct visual treatment, separate from standard score display.
- NEVER: Present all competency scores in a uniform grid with equal visual weight. Unexpected highs must be visually elevated — larger, brighter, or animated — to signal that the system found something.
- CHECK: In the current design, can a user achieve a discovery moment? Is there a UI state that is specifically triggered by unexpected competency strength? If that state does not exist, it must be built before assessment results are shipped.

---

### 7. Capgras / Cotard Warning

**Neuroscience finding:** In Capgras syndrome, the patient recognizes a loved one's face (the visual cortex pathway is intact) but the emotional response that should accompany recognition is severed (the limbic connection is cut). The result: the patient concludes the person must be an impostor — identical but not real. In Cotard's syndrome, the same disconnection is generalized: the patient recognizes their own existence but has no emotional response to it. Conclusion: "I am dead." Rational recognition without emotional connection produces a rejection response, not acceptance.

**Volaura implication:** If the emotional layer of Volaura — crystals, Life Sim character, discovery moments, badge drama — is removed, disabled, or broken, the rational layer (AURA score, competency breakdown, verified badge) becomes a "dead LinkedIn." Users will recognize it logically but feel nothing, and they will treat it as an impostor product that looks like something meaningful but isn't. Emotional hooks are not decoration. They are the connective tissue between rational recognition and felt reality.

**Rules:**
- MUST: Every rational feature (AURA display, competency score, badge status) must ship with at least one co-located emotional hook — an animation, a character reaction, a crystal event, or discovery copy. Rational features are never shipped naked.
- NEVER: A/B test the emotional layer against "clean" rational-only versions. The Capgras finding predicts the rational-only version will lose — but more dangerously, users who experience it will form a negative emotional association with the product that persists even if the emotional layer is restored.
- CHECK: Cover the emotional elements of any screen being reviewed. What remains? If what remains would be acceptable on a government form, the emotional layer is not integrated — it is decorating. Emotional elements must be load-bearing, not cosmetic.

---

## Brain Architecture Map (Ecosystem)

| Brain Structure | Ecosystem Component | Rule |
|---|---|---|
| Thalamus (sensory gating) | Onboarding + assessment entry | Only relevant stimuli pass through. Every screen must present exactly one primary stimulus. No competing CTAs at entry. |
| Visual cortex (30 parallel zones) | AURA radar chart | All 8 competencies must be simultaneously visible. Never paginate competency scores — the brain needs the full pattern, not sequential slices. |
| Limbic system (emotional tagging) | Crystal economy + badge reveals | Every achievement must carry an emotional tag strong enough to encode in memory. Flat UI = no limbic activation = no memory formation = no retention. |
| Basal ganglia (habit loops) | Daily assessment streak + return mechanics | Habits form through cue → routine → reward. Design the cue (notification) and the reward (crystals) before designing the routine (assessment). |
| Dopamine pathway (reward prediction) | Crystal drop timing | Crystals must drop at the moment of task completion, not after a delay. Delayed reward breaks the prediction signal. Immediate drop builds the loop. |
| Mirror neurons (social modeling) | Organization leaderboard + peer verification | Users calibrate self-assessment by watching others. Leaderboard must show aspirational peers (slightly above current user), not only top performers. |
| Cross-modal binding (synesthesia) | Assessment completion → multi-layer response | One action must produce multi-sensory output: visual (AURA update), social (org visibility), narrative (Life Sim), economic (crystals). All four must fire. |
| Peak shift (amplification) | Badge reveal screen | Badge reveal must be more dramatic than the badge itself. The brain responds to the amplified signal, not the baseline. Understate the reveal = understate the achievement. |
| Conscious → unconscious migration | Assessment UX flow | Measure completion time per screen. Any screen taking >30 seconds average is in conscious-processing territory. Target: users stop noticing they are navigating. |
| Hippocampus (episodic memory) | Discovery moments + savant reveals | Episodic memories are encoded by novelty and emotional salience. Discovery moments (unexpected competency strength) must be surprising AND emotionally charged to encode as lasting memory. |

---

## Swarm Review Checklist (run before approving any UI feature)

- [ ] Does this feature amplify the achievement (Peak Shift) or just report it?
- [ ] Does the user get a reward FROM action, never from avoiding inaction?
- [ ] Is there a savant discovery moment if the user scores unexpectedly high (>75 in non-self-reported competency)?
- [ ] Does one action trigger visible responses in 2+ product layers?
- [ ] Does this feature have an emotional hook, or is it purely functional?
- [ ] Does the copy use "reveals/discovers/surfaces" instead of "measures/tests/calculates"?
- [ ] Does the user journey move from conscious effort → automatic habit (no screen requires reading a label twice)?
- [ ] Is every rational feature co-located with at least one emotional hook?
- [ ] Does the achievement moment require active dismiss (not a toast notification)?
- [ ] Is the response chain for this feature's primary action documented with 2+ downstream nodes?

---

## Anti-Patterns to Reject

**1. "Assessment looks like a test"**
Violates Conscious → Unconscious. A test interface activates exam anxiety and pushes users into hyper-conscious, performance-monitoring mode. Completion rate drops. The interface must feel like a conversation or a game — not an evaluation. Reject any design that uses numbered question lists, submit buttons, or evaluation-frame copy ("your answers will be assessed").

**2. "Streak warning: you'll lose your progress"**
Violates the Dopamine System principle. This is fear-framing — it activates avoidance circuits, not approach circuits. Short-term completion may increase; long-term, users churn to escape the anxiety. Replace with: "Return today and earn [X] crystals." Same behavioral target, dopamine-framed.

**3. "AURA score displayed as a single number with decimal precision"**
Violates Brain Constructs Reality. Decimal precision implies clinical measurement. The user's brain will reject the score the moment it conflicts with self-image ("84.3? That can't be right"). A rounded score framed as a model ("Your AURA: 84 — Gold tier") is accepted as useful, not contested as inaccurate.

**4. "Badge earned — toast notification in the corner"**
Violates Peak Shift. A toast notification is a system-level message pattern. It signals "routine event." A badge is not a routine event. A toast badge notification is the Volaura equivalent of your best friend telling you they're getting married via text with no punctuation. The moment must match the magnitude. Reject any achievement delivery via toast.

**5. "We'll add the emotional layer later — ship the rational core first"**
Violates the Capgras/Cotard Warning. Users who experience the rational-only version form a "dead product" association that persists. The emotional layer is not a feature to be added — it is connective tissue that makes rational features feel real. Shipping rational features without emotional hooks is not an MVP; it is a Capgras prototype that will train users to feel nothing.

---

## When to Load This Skill

Load this skill whenever:
- Reviewing any new UI component or page before approval
- Writing or reviewing copy for any user-facing feature
- Designing any reward, achievement, badge, or gamification mechanic
- Reviewing or modifying the assessment flow UX
- Planning any cross-product integration feature (Volaura ↔ Life Sim ↔ MindShift ↔ BrandedBy)
- Evaluating notification or email copy for reward/engagement mechanics
- Auditing an existing feature that has low engagement despite high utility
- Any sprint that involves the crystal economy, AURA display, or badge system
