
import re

def test_regex(text):
    chunk_matches = re.findall(r"\[(\d+)\]\s*(.*?)(?=\[\d+\]|$)", text, re.DOTALL)
    print(f"Text length: {len(text)}")
    print(f"Matches: {len(chunk_matches)}")
    for m in chunk_matches:
        print(f"  [{m[0]}] {m[1][:20]}...")

# Case 1: Standard LightRAG format
text1 = """
[1] Title of Doc 1
Content of chunk 1...
[2] Title of Doc 2
Content of chunk 2...
"""

# Case 2: Missing title
text2 = """
[1] 
Content of chunk 1...
[2] 
Content of chunk 2...
"""

# Case 3: No newlines
text3 = "[1] Content1 [2] Content2"

# Case 4: With some header
text4 = """
Reference Document List
[1] Doc1
Content
"""

print("--- Case 1 ---")
test_regex(text1)
print("\n--- Case 2 ---")
test_regex(text2)
print("\n--- Case 3 ---")
test_regex(text3)
print("\n--- Case 4 ---")
test_regex(text4)
