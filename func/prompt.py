def gen_prompt(analysis=False):
    with open('config/prompt.txt', 'r', encoding='utf-8') as file:
        prompt = file.read()
    if isinstance(analysis, dict):
        print(analysis)
        prompt += f"""
Your task is to briefly analyze this chat. Different users are participating in the conversation, and their messages are prefixed with [message_id].

You need to:

- Summarize the chat topics – Identify the key themes and subjects being discussed.
- Characterize the chat – Describe its general tone, purpose, and engagement level (e.g., informal, technical, heated discussion, casual, etc.).
- Highlight important messages – Identify crucial or particularly relevant messages and format them as follows:
"[message_id](https://t.me/c/{analysis.get("chat_link_id")}/message_id)" - short review.

Additional Considerations:

- Focus on recurring themes and major discussion points rather than minor off-topic exchanges.
- If the chat includes debates, summarize key arguments from different perspectives.
- If trends or shifts in the discussion emerge, note how the conversation evolves over time.
- If necessary, mention any noticeable user behaviors (e.g., spam, conflicts, expert contributions).
- Be sure to formulate your answer in Russian language.

Your analysis should be concise, structured, and insightful to help quickly understand the chat’s key points. 
        """
    return prompt
