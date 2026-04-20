from collections import defaultdict
import re

def normalize_transcript(transcript):
    # Create a dictionary to store speakers and their messages
    speaker_messages = defaultdict(list)

    # Split the transcript into lines
    lines = transcript.split('\n')

    # Iterate over each line
    for line in lines:
        # Use regular expression to extract the speaker's name from the line
        match = re.match(r'(\w+): (.*)', line)
        
        if match:
            # If a match is found, extract the speaker and message
            speaker, message = match.groups()
            
            # Add the message to the speaker's list of messages
            speaker_messages[speaker].append(message)

    # Create a new string with normalized speaker names and sorted messages
    normalized_transcript = ''
    for speaker, messages in speaker_messages.items():
        normalized_transcript += f'{speaker}: {", ".join(messages)}\n'

    return normalized_transcript.strip()

# Test the function
transcript1 = """
Alice: we need to fix the login bug before Friday.
Bob: I'll handle it.
Alice: also need to update the docs
"""
print(normalize_transcript(transcript1))

transcript2 = """
Unknown:
"""
print(normalize_transcript(transcript2))

transcript3 = """
Unknown
"""
print(normalize_transcript(transcript3))

transcript4 = """
Alice:
"""
print(normalize_transcript(transcript4))