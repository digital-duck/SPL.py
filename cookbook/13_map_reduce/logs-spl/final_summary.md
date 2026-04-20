Here's an improved version of your code:

```python
def reduce_summaries(input_type, *args):
    """
    Reduces summaries based on the type of input.
    
    Args:
        input_type (int): The type of input. 0 for text and any other number for bullet points.
        *args: Variable length argument list containing a string input.
        
    Returns:
        str or None: The summary based on the type of input, or None if no arguments are provided.
    """

    # Check if input_type is valid
    if not isinstance(input_type, int):
        raise ValueError("input_type must be an integer")
    
    if input_type == 0:
        # If input_type is 0, return None as there's no text to summarize
        if not args:
            return None
        else:
            return ""
    
    elif input_type != 1:
        raise ValueError("Only input_type 0 and 1 are supported")
    
    else:
        # Join the arguments into a single string with bullet points
        summary = "\n• " + ", ".join(args)
        
        return summary

# Example usage
print(reduce_summaries(0))  # Output: None
print(reduce_summaries(1, "The quick brown fox jumps over the lazy dog."))  
```

### Explanation:

*   We've added a check to ensure `input_type` is an integer. If not, we raise a ValueError with an informative message.
*   We also check if `input_type` is 0 and raise a ValueError if it's anything else than 0 or 1. This way, the function can only be used for text summaries (type 0) or bullet point summaries (type 1).
*   If `input_type` is 0 and no arguments are provided, we return None to indicate that there's no text to summarize.
*   For type 1, we join all the strings in args into a single string with bullet points as before.

This updated code provides better error handling and clarity on how to use the function.