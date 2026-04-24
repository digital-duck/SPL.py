```python
def binary_search(arr, target):
  """
  Performs a binary search on a sorted array to find the index of a target value.

  Args:
    arr: A sorted list or array of numbers.
    target: The value to search for.

  Returns:
    The index of the target value in the array if found, otherwise -1.
  """
  low = 0
  high = len(arr) - 1

  while low <= high:
    mid = (low + high) // 2  # Integer division to find the middle index

    if arr[mid] == target:
      return mid  # Target found, return the index
    elif arr[mid] < target:
      low = mid + 1  # Target is in the right half
    else:
      high = mid - 1  # Target is in the left half

  return -1  # Target not found
```

**Explanation:**

1. **Initialization:**
   - `low`:  The index of the first element in the search space (initially 0).
   - `high`: The index of the last element in the search space (initially `len(arr) - 1`).

2. **Iteration (while loop):**
   - The `while low <= high` loop continues as long as there's a valid search space (i.e., the `low` index is not greater than the `high` index).

3. **Calculate Midpoint:**
   - `mid = (low + high) // 2`:  Calculates the middle index of the current search space.  The `//` operator performs integer division, ensuring that `mid` is an integer.

4. **Comparison:**
   - `if arr[mid] == target:`: If the value at the middle index is equal to the target, we've found the target and return its index (`mid`).
   - `elif arr[mid] < target:`: If the value at the middle index is less than the target, it means the target (if it exists) must be in the right half of the current search space.  So, we update `low` to `mid + 1` to narrow the search to the right half.
   - `else:`:  If the value at the middle index is greater than