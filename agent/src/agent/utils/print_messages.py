def print_messages(messages):
    for idx, message in enumerate(messages, start=1):
        message_type = type(message).__name__
        print(f"{'=' * 30} Message {idx} ({message_type}) {'=' * 30}")
        print(message)