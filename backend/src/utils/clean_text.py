import re

def clean_text(text: str) -> str:
    # 1. Rimuovi emoji
    emoji_pattern = re.compile("[" 
        u"\U0001F600-\U0001F64F"  # emoticon
        u"\U0001F300-\U0001F5FF"  # simboli e pittogrammi
        u"\U0001F680-\U0001F6FF"  # trasporti
        u"\U0001F1E0-\U0001F1FF"  # bandiere
        u"\U00002700-\U000027BF"  # simboli vari
        u"\U000024C2-\U0001F251"  # simboli diversi
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)

    # 2. Rimuovi i simboli tipici del markdown
    # asterischi, backtick, trattini all'inizio riga, #
    text = re.sub(r"[*_`>#\-]+", " ", text)

    # 3. Normalizza spazi multipli → singolo spazio
    text = re.sub(r"\s+", " ", text)

    # 4. Strip finale
    return text.strip()
