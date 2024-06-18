def proper_case(text):
    words = text.split()
    capitalized_words = [word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper() for word in words]
    return ' '.join(capitalized_words)
