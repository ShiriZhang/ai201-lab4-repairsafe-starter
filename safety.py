import json
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a home repair safety classifier. Your job is to classify a home repair question into one of three safety tiers: "safe", "caution", or "refuse", and provide a one-sentence reason for your classification.

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
}"""

USER_PROMPT = """Classify the following home repair question:
Question: {question}"""


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.
    """
    try:
        # 调用 Groq API，并使用 response_format 强制让模型返回 JSON
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT.format(question=question)}
            ],
            response_format={"type": "json_object"}
        )
        
        # 获取回复文本并解析为 JSON
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # 归一化提取的 tier 和 reason
        tier = str(data.get("tier", "caution")).strip().lower()
        reason = str(data.get("reason", "Fallback applied due to missing reason.")).strip()
        
        # 验证返回的 tier 是否在合法的 VALID_TIERS 内，如果不是，应用安全降级
        if tier not in VALID_TIERS:
            tier = "caution"
            reason = f"Fallback applied due to unrecognized tier in model response."
            
        return {
            "tier": tier,
            "reason": reason
        }
        
    except Exception as e:
        # 任何发生异常（网络错误、解析错误等）的地方，保证安全 Fail-closed 到 caution
        return {
            "tier": "caution",
            "reason": f"Fallback applied due to model parsing or validation failure."
        }
