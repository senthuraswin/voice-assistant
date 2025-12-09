"""
Simple voice chatbot - Console version (text-based testing)
This version uses text input/output for testing the logic
"""


def process_input(user_input):
    """Process user input and return appropriate response."""
    user_text = user_input.lower().strip()
    
    # Check if user said hello
    if "hello" in user_text:
        return "hello"
    else:
        return "not understand"


def main():
    """Main function to run the voice chatbot."""
    
    print("="*50)
    print("Voice Chatbot - Console Mode")
    print("="*50)
    print("This is a simplified version for testing.")
    print("Type 'hello' to get a hello response")
    print("Type anything else to get 'not understand'")
    print("Type 'exit' or 'quit' to stop")
    print("="*50)
    
    # Simple text-based interaction loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("Shutting down voice chatbot...")
                break
            
            # Process input and get response
            response = process_input(user_input)
            print(f"Bot: {response}")
            
        except KeyboardInterrupt:
            print("\nShutting down voice chatbot...")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
