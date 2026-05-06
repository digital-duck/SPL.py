```python
TEST_CASES = [
    {
        "question": "What is the difference between a process and a thread in operating systems?",
        "response": (
            "A process is an independent program in execution with its own memory space, "
            "while a thread is a lighter-weight unit of execution that shares memory with "
            "other threads within the same process. Processes are isolated from each other, "
            "making them safer but slower to communicate; threads share the same address space, "
            "enabling faster communication at the cost of requiring synchronisation (e.g. locks) "
            "to avoid race conditions."
        ),
    },
    {
        "question": "Explain how backpropagation works in neural networks.",
        "response": (
            "Backpropagation is just gradient descent. You compute the loss and then "
            "update the weights. It's used in every neural network."
        ),
        # Intentionally incomplete to test a low-scoring response
    },
    {
        "question": "What is the CAP theorem and what are its practical implications for distributed databases?",
        "response": (
            "The CAP theorem states that a distributed system can guarantee at most two of three "
            "properties simultaneously: Consistency (every read receives the most recent write), "
            "Availability (every request receives a response), and Partition tolerance (the system "
            "continues operating despite network partitions). Since network partitions are "
            "unavoidable in practice, real systems must choose between CP (e.g. HBase, Zookeeper) "
            "or AP (e.g. Cassandra, DynamoDB). This trade-off directly influences schema design, "
            "conflict-resolution strategy, and SLA guarantees in production systems."
        ),
    },
]

if __name__ == "__main__":
    from flow import run_judge
    for i, tc in enumerate(TEST_CASES, 1):
        print(f"\n{'#'*60}\n# TEST CASE {i}\n{'#'*60}")
        result = run_judge(tc["question"], tc["response"])
        print(f"Verdict: {result.get('verdict')}  |  Overall: {result.get('overall_score_computed')}")
```