import json
from datetime import datetime

def print_messages(messages):
    """Pretty print all messages with colors and emojis based on type"""
    if not messages:
        print("📭 No messages in conversation")
        return
    
    print(f"\n{'🎯' * 20}")
    print(f"📝 Conversation Messages - Total: {len(messages)}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'🎯' * 20}")
    
    for idx, message in enumerate(messages, start=1):
        message_type = type(message).__name__
        
        # Choose color and emoji based on message type
        if message_type == "HumanMessage":
            emoji = "👤"
            color = "\033[96m"  # Cyan
            prefix = "USER"
        elif message_type == "AIMessage":
            emoji = "🤖"
            color = "\033[92m"  # Green
            # Try to get node and model info
            node_info = ""
            if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                node = message.additional_kwargs.get('node', '')
                model = message.additional_kwargs.get('model', '')
                if node and model:
                    node_info = f"[{node}/{model}]"
                elif node:
                    node_info = f"[{node}]"
            prefix = f"AI{node_info}"
        elif message_type == "ToolMessage":
            emoji = "🔧"
            color = "\033[93m"  # Yellow
            tool_name = getattr(message, 'name', 'unknown')
            prefix = f"TOOL[{tool_name}]"
        elif message_type == "RemoveMessage":
            emoji = "🗑️"
            color = "\033[91m"  # Red
            prefix = "REMOVE"
        else:
            emoji = "📄"
            color = "\033[94m"  # Blue
            prefix = "OTHER"
        
        reset = "\033[0m"
        
        # Adjust prefix width to accommodate longer AI prefixes
        prefix_width = max(15, len(prefix))
        print(f"\n{color}{emoji} [{idx:2d}] {prefix:<{prefix_width}}{reset}", end="")
        
        # Print content preview
        if hasattr(message, 'content') and message.content:
            content = str(message.content)
            
            # For JSON content, try to extract key info
            if content.strip().startswith('{'):
                try:
                    parsed = json.loads(content)
                    if "status" in parsed and "data" in parsed:
                        # Prometheus response
                        status = parsed.get("status", "unknown")
                        result_count = len(parsed.get("data", {}).get("result", []))
                        print(f" - Prometheus {status}, {result_count} series")
                    else:
                        print(f" - JSON data ({len(content)} chars)")
                except json.JSONDecodeError:
                    # Show first 60 chars
                    preview = content[:60].replace('\n', ' ')
                    print(f" - {preview}{'...' if len(content) > 60 else ''}")
            else:
                # Show first 60 chars
                preview = content[:60].replace('\n', ' ')
                print(f" - {preview}{'...' if len(content) > 60 else ''}")
        
        # Show tool calls if any
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_names = [tc.get('name', 'unknown') for tc in message.tool_calls]
            print(f"\n{' ' * 12}🔧 Tools: {', '.join(tool_names)}")
        
        # Show tool info for ToolMessage
        # if message_type == "ToolMessage" and hasattr(message, 'name'):
        #     print(f"{' ' * 12}🏷️  Parameters: {message.name}")
    
    print(f"\n{'🏁' * 20}")
    print("✅ End of conversation")
    print(f"{'🏁' * 20}\n")