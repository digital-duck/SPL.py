```python
def binary_search(arr, target):
  """
  Performs a binary search on a sorted array to find the index of a target value.

  Args:
    arr: A sorted list or array.
    target: The value to search for.

  Returns:
    The index of the target value in the array if found, otherwise -1.
  """

  low = 0
  high = len(arr) - 1

  while low <= high:
    mid = (low + high) // 2  # Integer division to get the middle index

    if arr[mid] == target:
      return mid  # Target found at index mid
    elif arr[mid] < target:
      low = mid + 1  # Target is in the right half
    else:
      high = mid - 1  # Target is in the left half

  return -1  # Target not found in the array


# Example Usage:
if __name__ == '__main__':
  my_array = [2, 5, 7, 8, 11, 12]
  target_value = 13

  index = binary_search(my_array, target_value)

  if index != -1:
    print(f"Element {target_value} found at index {index}")
  else:
    print(f"Element {target_value} not found in the array")

  target_value = 11
  index = binary_search(my_array, target_value)
  if index != -1:
    print(f"Element {target_value} found at index {index}")
  else:
    print(f"Element {target_value} not found in the array")
```

**Explanation:**

1. **Initialization:**
   - `low`:  Initialized to 0, representing the index of the first element in the array.
   - `high`: Initialized to `len(arr) - 1`, representing the index of the last element in the array.

2. **Iteration (while loop):**
   - The `while low <= high` loop continues as long as there's a valid search space (i.e., the `low` index is less than or equal to the `high` index