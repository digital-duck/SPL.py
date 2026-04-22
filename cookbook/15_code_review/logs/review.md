from difflib import SequenceMatcher
import numpy as np

def calculate_severity_score(input_str1, input_str2):
    """
    This function calculates the severity score based on the two input strings.

    Args:
        input_str1 (str): The first input string to be evaluated.
        input_str2 (str): The second input string to be evaluated.

    Returns:
        int: The severity score of the difference between the two input strings.
    """

    # Define a dictionary to store the scores for each word
    scores = {
        'low': 1,
        'medium': 5,
        'high': 10
    }

    # Convert the input strings to lowercase
    input_str1 = input_str1.lower()
    input_str2 = input_str2.lower()

    # Split the input strings into words
    words1 = input_str1.split()
    words2 = input_str2.split()

    # Initialize the severity score to 0
    severity_score = 0

    # Iterate over each word in the first input string
    for word in words1:
        # Check if the word is in the scores dictionary
        if word in scores:
            # If the word is in the dictionary, add its score to the severity score
            severity_score += scores[word]

    # Initialize the severity score2 to 0
    severity_score2 = 0

    # Iterate over each word in the second input string
    for word in words2:
        # Check if the word is in the scores dictionary
        if word in scores:
            # If the word is in the dictionary, add its score to the severity score2
            severity_score2 += scores[word]

    # Calculate the ratio of matching characters to total characters
    ratio = SequenceMatcher(None, input_str1, input_str2).ratio()

    # Calculate the severity score based on the ratio
    severity_score3 = int(ratio * 10)

    # Return the final severity score
    return severity_score + severity_score2 + severity_score3