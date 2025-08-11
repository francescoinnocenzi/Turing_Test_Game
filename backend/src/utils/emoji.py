import re

def remove_emoji(text):
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # faccine ed emozioni
                           u"\U0001F300-\U0001F5FF"  # simboli & oggetti
                           u"\U0001F680-\U0001F6FF"  # trasporti & simboli
                           u"\U0001F1E0-\U0001F1FF"  # bandiere
                           u"\U00002700-\U000027BF"  # altri simboli vari
                           u"\U000024C2-\U0001F251"  # simboli diversi
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)