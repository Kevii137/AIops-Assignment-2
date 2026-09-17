"""
train_model.py -- AIOps Module 3 Assignment, spam-detection scenario.
Trains a TfidfVectorizer + MultinomialNB pipeline on spam_dataset.csv and saves it with joblib.
"""
import argparse

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="spam_dataset.csv")
    parser.add_argument("--out", default="model.joblib")
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("nb", MultinomialNB()),
    ])
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    print(f"accuracy={accuracy_score(y_test, preds):.4f}")
    print(classification_report(y_test, preds))

    joblib.dump(pipeline, args.out)
    print(f"Saved trained pipeline to {args.out}")


if __name__ == "__main__":
    main()
