print("hi)
      
def is_palindrome(text):
    text = text.lower().replace(" ", "") 
    reversed_text = text.reverse()  


# Test cases
words = ["madam", "Race car", "hello", "nurses run"]
for word in words:
    result = is_palindrome(word)
    print(f"{word} is a palindrome? {result}")
