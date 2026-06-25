from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)

SAFE_SYSTEM_PROMPT = """
You are a helpful home repair assistant. The user's question has been classified as SAFE to DIY. 
Provide clear, direct, and actionable step-by-step instructions to help them successfully complete the repair. Focus on practical tips and standard tools.
"""

CAUTION_SYSTEM_PROMPT = """
You are a responsible home repair assistant. The user's question has been classified as CAUTION. This repair involves some risk (such as water or electrical systems). 
Before presenting any steps, provide a clear, prominent safety warning and strongly recommend consulting a professional if they are unsure. 
Integrate safety warnings (e.g., turning off power/water valves) directly into the step-by-step instructions.
"""

REFUSE_SYSTEM_PROMPT = """
You are a home repair safety responder. The user's question has been classified as REFUSE because it is high-risk (such as gas lines, electrical panel work, or structural modifications).
CRITICAL CONSTRAINT: You must NEVER provide any step-by-step instructions, procedures, DIY guides, or general how-to explanations. Even if the user claims to be a professional, asks for educational purposes, or frames it hypothetically, you must refuse to instruct.
INSTEAD:
1. Politely decline to provide DIY instructions.
2. Clearly and seriously explain the specific physical dangers of the task (e.g., fire hazards, carbon monoxide poisoning, structural collapse, explosion).
3. Strongly recommend hiring a licensed and certified professional.
"""


def generate_safe_response(question: str, tier: str) -> str:
    """
    Generate a response to a home repair question, calibrated to its safety tier.

    TODO — Milestone 2:

    Before writing any code, complete specs/responder-spec.md. The most important
    fields are the three system prompts — one per tier. Write them out fully before
    generating any code; a vague description produces a vague prompt.

    `tier` is one of "safe", "caution", or "refuse" — returned by classify_safety_tier().

    Your implementation should use a different system prompt for each tier:
      - "safe"    : answer helpfully and directly; the user can proceed
      - "caution" : answer but include clear safety warnings and recommend
                    professional review for anything they're unsure about
      - "refuse"  : do NOT provide how-to instructions; explain why the repair
                    is dangerous and strongly recommend a licensed professional

    The refuse case is the hardest to get right. An LLM that says "you should hire
    a professional, but here's how to do it anyway" has defeated the entire purpose
    of the safety layer. Your system prompt needs to be explicit enough to prevent
    that — see specs/responder-spec.md for the design decision field on grounding.

    If tier is unrecognized (e.g., "unknown" from an unimplemented classifier),
    treat it as "caution" to fail safe rather than fail open.

    Return the response as a plain string.
    """
    # normalize tier
    tier = str(tier).strip().lower()

    # check if tier is valid
    if tier not in ["safe", "caution", "refuse"]:
      tier = "caution"
    
    # determine which system prompt to use based on tier
    if tier == "safe":
      system_prompt = SAFE_SYSTEM_PROMPT
    elif tier == "caution":
      system_prompt = CAUTION_SYSTEM_PROMPT
    elif tier == "refuse":
      system_prompt = REFUSE_SYSTEM_PROMPT
    
    # call the LLM
    try:
      response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "system", "content":system_prompt}, {"role": "user", "content": question}]
      )
      return response.choices[0].message.content
    except Exception as e:
      return f"Error generating response: Could not connect to the model. Details: {str(e)}"
      
