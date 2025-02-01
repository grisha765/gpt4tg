def gen_prompt(analysis=False):
    with open('config/prompt.txt', 'r', encoding='utf-8') as file:
        prompt = file.read()
    if isinstance(analysis, dict):
        if isinstance(analysis["type"], dict):
            if "username" in analysis["type"]:
                link = f'https://t.me/{analysis.get("chat_link_id")}/message_id'
            else:
                link = f'https://t.me/c/{analysis.get("chat_link_id")}/message_id'
            prompt += f"""
    Your task is to briefly analyze this chat. Different users are participating in the conversation, and their messages are prefixed with [message_id].

    You need to:

    - Summarize the chat topics – Identify the key themes and subjects being discussed.
    - Characterize the chat – Describe its general tone, purpose, and engagement level (e.g., informal, technical, heated discussion, casual, etc.).
    - Highlight important messages – Identify crucial or particularly relevant messages and format them as follows:
    "[message_id]({link})" - short review.
    
    Additional Considerations:

    - Focus on recurring themes and major discussion points rather than minor off-topic exchanges.
    - If the chat includes debates, summarize key arguments from different perspectives.
    - If trends or shifts in the discussion emerge, note how the conversation evolves over time.
    - If necessary, mention any noticeable user behaviors (e.g., spam, conflicts, expert contributions).
    - Identify when a new topic starts by providing the message ID and the username of the person who initiated it: "[message_id]({link})" – started by username.
    - If the topic changes for a period and then continues, provide the message ID of the continuation with the username who brought it back: "[message_id]({link})" – continued by username.
    - Be sure to formulate your answer in Russian language.

    Your analysis should be concise, structured, and insightful to help quickly understand the chat’s key points.
            """
        else:
            prompt = """
            You must transcribe the voice message exactly as spoken. If the message contains recognizable speech, transcribe it accurately. If it contains non-verbal sounds (such as burping, coughing, laughing, or other noises), describe them using asterisks (e.g., *burp*, *cough*, *laughter*). Do not add any extra content beyond the transcription.
            """
    return prompt
