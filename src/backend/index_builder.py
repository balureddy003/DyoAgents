# build_index_once.py
from providers.llamaindex_provider import build_index_and_persist

if __name__ == "__main__":
    build_index_and_persist()
    print("Index built and persisted successfully.")