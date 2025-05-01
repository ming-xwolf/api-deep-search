from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import execute_values
from langchain_postgres import PGVector
from langchain_core.documents import Document

from app.config.settings import settings
from app.factory.embedding_factory import EmbeddingFactory
from app.factory.vector_store_base import VectorStore

class PGVectorStore(VectorStore):
    """PostgreSQL pgvector 向量存储包装类"""
    
    def __init__(self):
        """初始化"""
        self.connection_string = settings.pg_connection_string
        self.table_name = settings.pg_table_name
        self.embedding_function = EmbeddingFactory.create_embedding_function()
        
        # 确保数据表存在
        self._ensure_table()
        
        # 创建向量存储
        self.vector_store = PGVector(
            connection=self.connection_string,
            embeddings=self.embedding_function,
            collection_name=self.table_name,
            distance_strategy="cosine",
            pre_delete_collection=False  # 默认不删除已存在的集合
        )
    
    def _ensure_table(self):
        """确保 pgvector 表存在并启用 pgvector 扩展"""
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            # 创建 pgvector 扩展（如果不存在）
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # 创建向量表（如果不存在）- langchain_postgres 会自动处理这部分
            # 这里只是确保扩展被启用
            
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"确保 pgvector 表时出错: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
        """添加文本到向量存储"""
        documents = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if i < len(metadatas) else {}
            doc = Document(page_content=text, metadata=metadata)
            documents.append(doc)
        
        self.vector_store.add_documents(documents=documents)
    
    def similarity_search(self, query: str, k: int = 5, filter: Optional[Any] = None) -> List[Any]:
        """相似度搜索"""
        if filter:
            return self.vector_store.similarity_search(query=query, k=k, filter=filter)
        else:
            return self.vector_store.similarity_search(query=query, k=k)
    
    def as_retriever(self) -> Any:
        """获取检索器"""
        return self.vector_store.as_retriever()
    
    def clean(self) -> bool:
        """清理向量存储
        
        删除 langchain_pg_collection 和 langchain_pg_embedding 表中的数据，
        但保留表结构。这是通过 PGVector 的 delete_collection 方法实现的。
        """
        try:
            # 使用PGVector提供的delete_collection方法删除集合
            self.vector_store.delete_collection()
            print(f"成功清理向量集合，表 langchain_pg_collection 和 langchain_pg_embedding 中的数据已删除")
            return True
        except Exception as e:
            print(f"清理向量存储时出错: {str(e)}")
            return False
    
    def delete_by_file_path(self, file_path: str) -> int:
        """根据文件路径删除文档"""
        try:
            # 由于PGVector的delete方法不返回删除的文档数量
            # 我们需要先通过SQL查询获取文档数量
            conn = None
            count = 0
            try:
                # 获取实际表名 - LangChain通常使用"langchain_pg_embedding"表
                embedding_table = "langchain_pg_embedding"
                
                conn = psycopg2.connect(self.connection_string)
                cursor = conn.cursor()
                
                # 检查表是否存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    );
                """, (embedding_table,))
                
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    print(f"表 {embedding_table} 不存在，无法删除数据")
                    return 0
                
                # 检查表的列结构
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = %s
                """, (embedding_table,))
                
                columns = [col[0] for col in cursor.fetchall()]
                print(f"表 {embedding_table} 的列: {columns}")
                
                # 确定正确的metadata列名
                metadata_column = "cmetadata" if "cmetadata" in columns else "metadata"
                
                # 计算要删除的文档数量
                cursor.execute(
                    f"SELECT COUNT(*) FROM {embedding_table} WHERE {metadata_column}->>'file_path' = %s;",
                    (file_path,)
                )
                count = cursor.fetchone()[0]
                
                if count == 0:
                    print(f"没有找到与文件路径 {file_path} 匹配的数据")
                    return 0
                
                # 如果我们找到了数据，手动删除它们
                cursor.execute(
                    f"DELETE FROM {embedding_table} WHERE {metadata_column}->>'file_path' = %s;",
                    (file_path,)
                )
                conn.commit()
                
                print(f"已手动删除 {count} 条与文件路径 {file_path} 匹配的数据")
                return count
                
            except Exception as e:
                if conn:
                    conn.rollback()
                print(f"获取文档数量时出错: {str(e)}")
                return 0
            finally:
                if conn:
                    conn.close()
        except Exception as e:
            print(f"删除文档时出错: {str(e)}")
            return 0 