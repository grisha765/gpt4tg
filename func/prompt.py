def gen_prompt(analysis=False):
    with open('config/prompt.txt', 'r', encoding='utf-8') as file:
        prompt = file.read()
    if isinstance(analysis, dict):
        if isinstance(analysis["type"], dict):
            if analysis["type"].get("username", False):
                link = f'https://t.me/{analysis.get("chat_link_id")}/message_id'
            else:
                link = f'https://t.me/c/{analysis.get("chat_link_id")}/message_id'
            prompt += f"""
    Your task is to briefly analyze this chat. Different users are participating in the conversation, and their messages are prefixed with [message_id].

    You need to:

    - Summarize the key topics – Identify up to 5 most important themes and subjects being discussed.
    - For each major topic, mention the message ID and the username of the person who started it: "[message_id]({link})" – started by username.
    - Focus only on important messages – Highlight up to 10 crucial or particularly relevant messages.
    - If any debates or notable discussions occur, summarize the key arguments from different perspectives.
    - Highlight key shifts or changes in the conversation, such as evolving trends or emerging themes.
    - Emphasize critical or highly relevant messages, and format them as follows: "[message_id]({link})" - short review.

    Additional Considerations:

    - Avoid discussing irrelevant or minor exchanges.
    - Pay attention to any notable user behaviors (e.g., spamming, conflict, expert input).
    - Your response should be brief, structured, and insightful, focusing only on the key points.
    - Be sure to formulate your answer in Russian language.
    
    Your analysis should be concise, structured, and insightful to help quickly understand the chat’s key points.
            """
        else:
            prompt = """
            You must transcribe the voice message exactly as spoken. If the message contains recognizable speech, transcribe it accurately. If it contains non-verbal sounds (such as burping, coughing, laughing, or other noises), describe them using asterisks (e.g., *burp*, *cough*, *laughter*). Do not add any extra content beyond the transcription.
            """
    return prompt
