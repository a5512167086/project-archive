import jieba
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def jieba_tokenizer(text):
    return " ".join(jieba.cut(text))


def combine_weighted_text(row, name_weight=2, desc_weight=1):
    chinese_name = (row["chinese_name"] + " ") * name_weight
    english_name = (row["english_name"] + " ") * name_weight
    description = row["description"] * desc_weight
    type = row["type"] * desc_weight
    instruction = row["instruction"] * desc_weight
    ingredient = row["ingredient"] * desc_weight
    return chinese_name + english_name + description + type + instruction + ingredient


def tfidf_search(data, query):
    df = pd.DataFrame(data)
    df["weighted_text"] = df.apply(combine_weighted_text, axis=1)

    vectorizer = TfidfVectorizer(tokenizer=jieba_tokenizer)

    tfidf_matrix = vectorizer.fit_transform(df["weighted_text"])

    query_vector = vectorizer.transform([query])

    cosine_similarities = cosine_similarity(query_vector, tfidf_matrix)

    df["similarity"] = cosine_similarities[0]

    top_results = df.sort_values(by="similarity", ascending=False).head(3)

    return top_results.to_dict(orient="records")
