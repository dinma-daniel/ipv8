import hashlib

def find_hash_with_difficulty(id, difficulty):
    target_prefix = '0' * difficulty
    a = 0

    while True:
        hash_input = f"{id}{a}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()
        if hash_value.startswith(target_prefix):
            return a, hash_value
        a += 1

initial_id = "dinma"
difficulty_k = 6

solution_a, solution_hash = find_hash_with_difficulty(initial_id, difficulty_k)
print(f"Secret value: {solution_a}")
print(f"Hash value: {solution_hash}")
