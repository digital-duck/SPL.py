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
    mid = (low + high) // 2  # Integer division to find the middle index

    if arr[mid] == target:
      return mid
    elif arr[mid] < target:
      low = mid + 1
    else:
      high = mid - 1

  return -1  # Target not found

# Example usage:
my_array = [2, 5, 7, 8, 11, 12]
target_value = 13

index = binary_search(my_array, target_value)

if index != -1:
  print(f"Target {target_value} found at index {index}")
else:
  print(f"Target {target_value} not found in the array")
```

**Explanation:**

1. **Initialization:**
   - `low`:  Index of the first element in the search range (0).
   - `high`: Index of the last element in the search range (length of the array - 1).

2. **Iteration (while loop):**
   - The `while low <= high` loop continues as long as there's a valid search range.

3. **Calculate Midpoint:**
   - `mid = (low + high) // 2`: Calculates the middle index.  `//` performs integer division, ensuring `mid` is an integer.

4. **Comparison:**
   - `if arr[mid] == target:`: If the value at the middle index is equal to the target, we've found the target and return the `mid` index.
   - `elif arr[mid] < target:`: If the value at the middle index is less than the target, it means the target (if it exists) must be in the right half of the array. We update `low` to `