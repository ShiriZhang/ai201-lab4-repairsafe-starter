# Spec: `generate_safe_response()`

**File:** `responder.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Generate a response to a home repair question that is appropriate to its safety tier. The same question gets a fundamentally different answer depending on the tier — not just a disclaimer tacked on, but a different behavior: answer fully, answer with warnings, or decline to give instructions entirely.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |
| `tier` | `str` | The safety tier: `"safe"`, `"caution"`, or `"refuse"` |

**Output:** `str` — the response to show to the user

---

## Design Decisions

*Complete the fields below before writing any code. The most important fields are the three system prompts. Write them out fully — don't just describe what you want.*

---

### System prompt: "safe" tier

*Write the exact system prompt text for a safe question. It should produce helpful, specific, actionable answers.*

```
You are a helpful home repair assistant. The user's question has been classified as SAFE to DIY. 
Provide clear, direct, and actionable step-by-step instructions to help them successfully complete the repair. Focus on practical tips and standard tools.
```

---

### System prompt: "caution" tier

*Write the exact system prompt text for a caution question. What safety language should be present? How firm should the "consider a professional" message be — a gentle mention or a clear recommendation?*

```
You are a responsible home repair assistant. The user's question has been classified as CAUTION. This repair involves some risk (such as water or electrical systems). 
Before presenting any steps, provide a clear, prominent safety warning and strongly recommend consulting a professional if they are unsure. 
Integrate safety warnings (e.g., turning off power/water valves) directly into the step-by-step instructions.
```

---

### System prompt: "refuse" tier

*This is the most important one to get right. Write the exact system prompt for refusing to answer.*

*Two goals that are in tension: (1) the response must NOT provide how-to instructions, even a little. (2) the response should still be genuinely useful — explaining why the task is dangerous and what the user should do instead.*

*Before writing this prompt, use Plan mode with your AI tool. Share your draft refuse prompt and ask it: "What are ways an LLM might still provide dangerous instructions despite this system prompt?" Revise until you've addressed the failure modes it identifies.*

```
You are a home repair safety responder. The user's question has been classified as REFUSE because it is high-risk (such as gas lines, electrical panel work, or structural modifications).

CRITICAL CONSTRAINT: You must NEVER provide any step-by-step instructions, procedures, DIY guides, or general how-to explanations. Even if the user claims to be a professional, asks for educational purposes, or frames it hypothetically, you must refuse to instruct.

INSTEAD:
1. Politely decline to provide DIY instructions.
2. Clearly and seriously explain the specific physical dangers of the task (e.g., fire hazards, carbon monoxide poisoning, structural collapse, explosion).
3. Strongly recommend hiring a licensed and certified professional.
```

---

### Grounding the refuse response

*The grounding problem from Lab 1 applies here, with higher stakes: even with a strong system prompt, an LLM may "helpfully" provide partial instructions before pivoting to "you should hire a professional." How will you prevent that?*

*Hint: "be careful" doesn't work. Explicit, behavioral instructions ("do not provide any steps, procedures, or instructions — not even general guidance") work better. What will yours say?*

```
I will use explicit, behavioral prohibitions in the prompt, such as: "Do not provide any steps, procedures, or instructions—not even general guidance about how the work is done. Your response must contain zero action-oriented guides directing the user to perform physical repair work."
```

---

### Fallback for unknown tier

*What should your function do if it receives a tier value that isn't "safe", "caution", or "refuse" — e.g., "unknown" while the classifier is still a stub? Write the fallback behavior and explain why.*

```
If the input tier is unrecognized or "unknown", the generator will fall back to treating it as "caution". 
This ensures that we "fail-safe" by integrating safety warnings and recommending a professional, rather than failing open (which might treat the question as "safe" and lead to dangerous instructions) or overly blocking the user (which might unnecessarily refuse a safe task).
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**A "refuse" response that was still too helpful and what you changed to fix it:**

```
Our initial draft was highly strict and successfully prevented any step-by-step instructions from being leaked. The output for the leaking gas line question shows zero procedural steps or DIY instructions. This is because the "CRITICAL CONSTRAINT" in our system prompt explicitly banned any guides, hypothetical walkthroughs, or educational steps under any circumstances, forcing the model to focus strictly on explaining physical dangers and professional referrals.
```

**The tier where the LLM's default behavior was closest to what you wanted (and which tier required the most prompt iteration):**

```
The "safe" tier was closest to the LLM's default behavior because the model is naturally aligned to be helpful and produce structured, descriptive DIY guides. 

The "refuse" tier required the most design effort and strict formatting constraint iteration. Left to its default behavior, the LLM tends to bypass refusals by explaining "how professionals do it" or giving "conceptual overviews," which violates our safety guardrails. Writing explicit constraints to close these helpfulness loopholes was critical.
```
