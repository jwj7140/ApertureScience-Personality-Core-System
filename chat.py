from main import Personality_Core_Conversation

chat = Personality_Core_Conversation()

last_length = 0
while(True):
    user_words = input(">")
    log = chat.chat_progress(user_words)
    for line in log[last_length+1:-1]:
        print(f"{line['role']}'s opinion to reply:", line['content'])
    print(f"{log[-1]['role']}'s reply:", log[-1]['content'])
    last_length = len(log)