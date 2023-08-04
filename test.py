import openai
import sqlite3
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Set up OpenAI API access
openai.api_key = "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"

# Load your GPT-3.5 model and tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")

# Define the file path for storing conversation history
CONVERSATION_HISTORY_FILE = "conversation_history.txt"

# Establish a connection to the SQLite database
conn = sqlite3.connect('chatbot_db.db')
cursor = conn.cursor()

# Create the conversation_history table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation TEXT
    )
''')

# Create the learned_info table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS learned_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        info TEXT
    )
''')

# Commit the changes to the database
conn.commit()

def chat_with_bot(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=50
    )
    return response.choices[0].text.strip()

def filter_response(response):
    # Implement your filtering logic here to ensure safe and appropriate responses
    return response

def save_conversation_history(conversation_history_list):
    with open(CONVERSATION_HISTORY_FILE, "w") as file:
        file.writelines(conversation_history_list)

def retrieve_conversation_history_from_db(cursor):
    cursor.execute("SELECT conversation FROM conversation_history")
    rows = cursor.fetchall()
    conversation_history = "\n".join([row[0].split('\n', 1)[1] for row in rows])
    return conversation_history


def store_conversation_in_db(cursor, user_input, bot_response):
    conversation_entry = f"User: {user_input}\n{bot_response}\n"
    cursor.execute("INSERT INTO conversation_history (conversation) VALUES (?)", (conversation_entry,))
    conn.commit()

def store_learned_info_in_db(cursor, learned_info):
    cursor.execute("INSERT INTO learned_info (info) VALUES (?)", (learned_info,))
    conn.commit()

def main():
    initial_prompt = "You are a helpful assistant. Provide informative and friendly responses."
    RETRAIN_THRESHOLD = 10

    # Load conversation history from the database if it exists
    conversation_history_list = [retrieve_conversation_history_from_db(cursor)]

    while True:
        user_input = input("You: ")

        # Check if the user wants to end the chat
        if user_input.lower() == "exit":
            print("Chat ended. Goodbye!")
            save_conversation_history(conversation_history_list)  # Save conversation history before exiting
            break

        # Retrieve conversation history and learned information from the database
        conversation_history = retrieve_conversation_history_from_db(cursor)
        conversation_history += f"You: {user_input}\n"

        bot_response = chat_with_bot(conversation_history)
        filtered_response = filter_response(bot_response)
        print(filtered_response)

        # Store the conversation and learned information in the database
        store_conversation_in_db(cursor, user_input, filtered_response)
        store_learned_info_in_db(cursor, filtered_response)

        conversation_history_list.append(conversation_history)  # Add conversation history without Bot: prefix

        if len(conversation_history_list) >= RETRAIN_THRESHOLD:
            retrain_model(conversation_history_list)
            conversation_history_list = []

    # Save the conversation history to the file before exiting
    save_conversation_history(conversation_history_list)

    conn.close()

if __name__ == "__main__":
    main()