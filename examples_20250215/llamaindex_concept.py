from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, load_index_from_storage, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5")
Settings.embed_model = embed_model

persist_dir = "./index_persist"
# 数据向量化，存入向量数据库
documents = SimpleDirectoryReader(input_files=["data/SQL题库.pdf"]).load_data()
# 需要嵌入模型，把文本转化为数字
index = VectorStoreIndex.from_documents(documents, show_progress=True)
# 保存向量数据库
index.storage_context.persist(persist_dir="./index_persist")
print(len(documents))
print(documents)
print(index)
# 从向量数据库中加载向量数据库
index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir=persist_dir)
    )
# 直接从向量库中查询数据，与大模型没有交互,
# similarity_top_k=1表示只返回最相似的结果，该参数的设置为1的缺点：找不到相关答案，数据的高质量入库和召回问题需要对该参数进行调试
# r = index.as_retriever(similarity_top_k=1)
# data = r.retrieve("第50题sql的答案是什么？")
# print(data)
q = index.as_query_engine()
data = q.query("第50题sql的答案是什么？")
print(data)

