import re

def is_valid_tacz_namespace(namespace_str):
    """Checks if the given string is a valid TACZ namespace."""
    if not namespace_str:
        return False, "Namespace cannot be empty."
    if not re.match("^[a-z0-9_]+$", namespace_str):
        return False, ("Namespace contains invalid characters. "
                      "Only lowercase English letters, numbers, and underscores are allowed.")
    # Potentially add a check for reserved keywords if TACZ has any.
    # For now, pattern matching is the primary check.
    return True, "Namespace is valid."

if __name__ == "__main__":
    # Test cases
    valid_namespaces = ["test_pack", "myguns123", "another_one"]
    invalid_namespaces = ["TestPack", "my-guns", "namespace!", "", " leading_space"]

    print("Validating namespaces:")
    for ns in valid_namespaces:
        is_valid, msg = is_valid_tacz_namespace(ns)
        print(f"Namespace 	'{ns}	': {is_valid} - {msg}")

    print("\nInvalidating namespaces:")
    for ns in invalid_namespaces:
        is_valid, msg = is_valid_tacz_namespace(ns)
        print(f"Namespace 	'{ns}	': {is_valid} - {msg}")

