import chromadb
c = chromadb.PersistentClient(path='.chroma').get_or_create_collection('knowledge')
print('Total:', c.count())
for d, m in zip(c.get()['documents'], c.get()['metadatas']):
    print(f"[{m['source']}] {d[:60]}")