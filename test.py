print("hellow wolrd")
def is_palindrome(text):
    # Normalize the text: make lowercase and remove spaces
    text = text.lower().replace(" ", "")
    # Reverse the text using slicing


# Test cases
words = ["madam", "Race car", "hello", "nurses run"]
for word in words:
    result = is_palindrome(word)
    print(f"{word} is a palindrome? {result}")
