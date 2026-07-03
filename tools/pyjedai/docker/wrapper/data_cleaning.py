#Stopwords removal
#Punctuation removal
#Numbers removal
#Unicodes removal


def clean(data):
    data.clean_dataset(remove_stopwords=True,
                       remove_punctuation=True,
                       remove_numbers=True,
                       remove_unicodes=True)