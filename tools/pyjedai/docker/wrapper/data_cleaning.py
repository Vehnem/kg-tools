def clean(
    data,
    remove_stopwords=True,
    remove_punctuation=True,
    remove_numbers=True,
    remove_unicodes=True,
):
    data.clean_dataset(
        remove_stopwords=remove_stopwords,
        remove_punctuation=remove_punctuation,
        remove_numbers=remove_numbers,
        remove_unicodes=remove_unicodes,
    )
    return data
