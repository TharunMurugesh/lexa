import time
from openai import OpenAI

from config import settings


def _mock_response(system_prompt: str, user_content: str) -> str:
    prompt = system_prompt.lower()
    sample = " ".join(user_content.split())[:280]
    if "extract facts" in prompt:
        return (
            '{"facts":["Case document reviewed","Allegations and events identified"],'
            '"people":["Complainant","Accused"],"dates":[],"events":["Incident described in uploaded case"]}'
        )
    if "prosecutor" in prompt:
        return f"The prosecution argues that the documented facts support liability. Key case material: {sample}"
    if "defense counsel" in prompt:
        return "The defense challenges identity, intent, reliability of evidence, and the link between facts and cited law."
    if "factual conflicts" in prompt:
        return '[{"statement_a":"Prosecution relies on the complaint","statement_b":"Defense disputes proof beyond doubt","conflict":"Evidentiary sufficiency"}]'
    if "impartially" in prompt:
        return "The court weighs the cited law against the extracted facts. The record supports a cautious finding because some facts need corroboration."
    if "vote independently" in prompt:
        return '{"verdict":"Insufficient Evidence","confidence":0.62,"votes":{"guilty":1,"not_guilty":1,"abstain":3}}'
    if "procedural errors" in prompt:
        return "Appeal review finds no clear procedural error, but recommends fuller evidence collection before a final adverse finding."
    return sample or "No content supplied."


def call_agent(system_prompt: str, user_content: str) -> str:
    if settings.use_mock_llm or not settings.nim_api_key:
        return _mock_response(system_prompt, user_content)

    client = OpenAI(base_url=settings.nim_base_url, api_key=settings.nim_api_key)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=settings.nim_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"NIM request failed after 3 attempts: {last_error}")
