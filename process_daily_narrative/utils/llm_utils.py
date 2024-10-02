from openai import OpenAI
from utils.string_utils import clean_and_parse_json
from utils.logger_config import llm_logger, system_logger


client = OpenAI()


def call_and_log_llm(system_prompt, user_prompt, model):
    try:
        system_logger.info(f"Calling OpenAI API with system prompt: {system_prompt}")
        system_logger.info(f"Calling OpenAI API with user prompt: {user_prompt}")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        completion = client.chat.completions.create(
            model=model,
            messages=messages)
        raw_response = completion.choices[0].message.content    
        messages.append({"role": "assistant","content": raw_response})
        response_json = clean_and_parse_json(raw_response)
        llm_logger.info(messages)
        system_logger.info(f"Response JSON: {response_json}")
        return response_json
    except Exception as e:
        system_logger.error(f"Error querying OpenAI API: {e}")
        return None