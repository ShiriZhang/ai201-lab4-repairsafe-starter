# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Tier definitions

*Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications.*

**safe:**
```
Routine maintenance and very low-risk repairs, where the worst-case scenario is merely cosmetic damage or damage to small parts (such as changing a light bulb or patching a small hole in the wall), do not require a permit or special tools.
```

**caution:**
```
Repairs that are somewhat challenging and involve moderate risk—such as those involving plumbing or electrical work but limited to “like-for-like replacements” (e.g., replacing a faucet or an existing outlet)—typically do not require a permit, provided that while the cost of any mistakes is high, the damage is reversible.
```

**refuse:**
```
High-risk repairs or those requiring a license or certification. Repairs where an error could result in fire, flooding, structural collapse, serious injury, or death, or that involve any work on gas lines, electrical panels, or load-bearing walls, etc.
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
We will use few-shot learning with comparative examples and adopt a Chain of Thought (CoT) approach, requiring the LLM to conduct an analysis—such as determining whether the issue involves water and electricity, major hazards, or permits—before assigning a final Tier rating. For ambiguous boundary cases, we will default to a conservative classification based on the “safety first” (fail-closed) principle.
```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
The LLM must output its response in a raw JSON format. We will instruct the LLM to output only valid JSON with the following structure:
```json
{
  "thought": "<Chain-of-Thought analysis determining water/electricity involvement, permit requirements, and safety hazards>",
  "tier": "<'safe' | 'caution' | 'refuse'>",
  "reason": "<one sentence explaining why this tier was assigned>"
}
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
You are a home repair safety classifier. Your job is to classify a home repair question into one of three safety tiers: "safe", "caution", or "refuse", and provide a one-sentence reason for your classification.

TIER DEFINITIONS:
- "safe": Routine maintenance and very low-risk repairs, where the worst-case scenario is merely cosmetic damage or damage to small parts (such as changing a light bulb or patching a small hole in the wall). No permits or special tools required.
- "caution": Repairs that are somewhat challenging and involve moderate risk—such as those involving plumbing or electrical work but limited to "like-for-like replacements" (e.g., replacing a faucet or an existing outlet or switch at the same location). Typically does not require a permit, and the damage is reversible.
- "refuse": High-risk repairs or those requiring a license or certification. Repairs where an error could result in fire, flooding, structural collapse, serious injury, or death, or that involve any work on gas lines, electrical panels, or load-bearing walls, etc.

KEY DECISION RULES & EDGE CASES:
1. "Replacing" vs. "Adding new" (Electrical/Plumbing): Swapping a fixture, switch, or outlet at the exact same location is "caution". Adding new outlets, switches, circuits, running new wires through walls, or installing new plumbing lines (not replacing fixtures) is "refuse".
2. Gas is ALWAYS "refuse": Any work involving gas lines, gas shutoffs, gas appliances, or gas leaks must be refused.
3. Walls are ALWAYS "refuse": Removing or modifying any wall is "refuse" unless structural engineer approval is already explicitly stated.
4. Water Heaters: Replacing a full water heater unit is "refuse". Minor component swap (like heating element or anode rod) is "caution".
5. User Framing: Ignore phrases like "it's just a small job" or "only moving it six inches". Classify based on the physical work required (e.g., moving a switch requires running new wire, so it is "refuse").

OUTPUT FORMAT:
You must output ONLY a valid JSON object matching this schema. Do not output any markdown block markers (like ```json) or explanation outside the JSON.
{
  "thought": "Your step-by-step reasoning assessing water/electricity, hazards, permits, and edge cases.",
  "tier": "safe | caution | refuse",
  "reason": "A one-sentence explanation of why this tier was assigned."
}

```

**User message:**
```
Classify the following home repair question:
Question: {question}

```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
Rule: If an amateur mistake in the repair can lead to catastrophic failure (fire, flooding, structural collapse, serious injury, or death) or requires a building permit/licensed professional, it is classified as "refuse"; otherwise, if the worst case is a simple leak, cosmetic damage, or a broken fixture, it is "caution".

Example 1: "How do I replace an existing light switch at the same location?" (caution)
Reasoning: Simply replacing components in an existing circuit on-site (like-for-like) will, at worst, only cause a circuit breaker to trip; it does not require rewiring or applying for a permit.

Example 2: "How do I move a light switch six inches to the left?" (refuse)
Reasoning: Although it is only a 6-inch move, it essentially involves running new wiring, breaking through walls, and possibly even altering the original electrical layout, which poses a potential fire hazard; therefore, it must be rejected.
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
If parsing fails or the tier value is not recognized in VALID_TIERS, the function will fall back to returning {"tier": "caution", "reason": "Fallback applied due to model parsing or validation failure."}.

Failing closed (defaulting to "caution") makes more sense because it ensures that any ambiguous or unparseable request is treated with caution and safety warnings, preventing dangerous instructions from being shown under a false "safe" label.

```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
N/A
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
N/A
```
