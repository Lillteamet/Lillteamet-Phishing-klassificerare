"""Reusable model wrapper classes for saved artifacts.

This module provides `WrappedModel` so pickled objects reference a stable
importable module path and can be loaded by other scripts.
"""
from __future__ import annotations


class WrappedModel:
    def __init__(self, vectorizer, clf):
        self.vec = vectorizer
        self.clf = clf

    def predict(self, texts):
        X = self.vec.transform(texts)
        return self.clf.predict(X)

    def predict_proba(self, texts):
        X = self.vec.transform(texts)
        return self.clf.predict_proba(X)
