print("hellow wolrd")
def is_palindrome(text):
    # Normalize the text: make lowercase and remove spaces
    text = text.lower().replace(" ", "")
    # Reverse the text using slicing
    reversed_text = text[::-1]
    # Check if the original and reversed texts are the same
    return text == reversed_text

# Test cases
words = ["madam", "Race car", "hello", "nurses run"]
for word in words:
    result = is_palindrome(word)
    print(f"{word} is a palindrome? {result}")
if(0)
{
    else
    {
    }
