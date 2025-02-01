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
Your task is to briefly analyze this chat, where different users are participating. Their messages are prefixed with [message_id].

You need to:

- Summarize the main topics – Identify key themes and subjects being discussed.
- Characterize the chat – Describe its tone, purpose, and engagement level (e.g., informal, technical, heated discussion, casual, etc.).
- Highlight important messages – Identify and briefly review key messages using the following format: "[message_id]({link})" – short summary.

Additional Guidelines:

- Focus on recurring themes and significant discussion points, rather than minor off-topic exchanges.
- If debates occur, summarize the main arguments from different perspectives.
- Track how the discussion evolves, noting shifts in topics or tone.
- Identify any noteworthy user behaviors (e.g., spamming, conflicts, expert contributions).
- When a new topic is introduced, mention the message ID and the username of the person who started it: "[message_id]({link})" – started by username.
- If a topic is revisited after a break, mention the message ID and the username who brought it back: "[message_id]({link})" – continued by username.
- Provide the analysis in Russian.

Your summary should be concise, structured, and insightful, offering a clear overview of the chat’s key points.
            """
        else:
            prompt = """
            You must transcribe the voice message exactly as spoken. If the message contains recognizable speech, transcribe it accurately. If it contains non-verbal sounds (such as burping, coughing, laughing, or other noises), describe them using asterisks (e.g., *burp*, *cough*, *laughter*). Do not add any extra content beyond the transcription.
            """
    return prompt
