import streamlit as st
from openai import OpenAI
import chromadb
from docx import Document
import requests
import uuid

# ChromaDBのクライアントを作成
DB_DIR = "./chroma_db"
chroma_client = chromadb.PersistentClient(path=DB_DIR)

st.session_state.collection = chroma_client.get_or_create_collection(name="locla_docs")


# ollamaからインストールしたモデルを使ったベクトル化関数
def ollama_embed(text):
    response = requests.post(
        "http://localhost:12000/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text},
    )

    data = response.json()
    return data["embedding"]


# Wordファイルを読み込む関数
def load_word_document(file):
    return "\n".join(p.text for p in Document(file).paragraphs)


# テキスト分割関数
def split_text(text):
    chunk_size = 200
    overlap = 50
    chunks = []
    start = 0
    while start < len(text):
        print("進捗：", start / len(text))
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


st.sidebar.write("設定")
model = st.sidebar.text_input("モデル名", value="llama3.1")
temparature = st.sidebar.slider(
    "temperature", min_value=0.0, max_value=2.0, value=0.3, step=0.1
)
system_prompt = st.sidebar.text_area(
    "system prompt", value="あなたは有能なアシスタントです。日本語で回答してください"
)

# ドキュメントのアップロード
uploaded_files = st.sidebar.file_uploader(
    "Wordファイルをアップロード",
    type=["docx"],
    accept_multiple_files=True,
)

if st.sidebar.button("インデックスを作成"):
    if not uploaded_files:
        st.sidebar.warning("先にWordファイルをアップロードしてください")
    else:
        for file in uploaded_files:
            text = load_word_document(file)
            chunks = split_text(text)
            print(chunks)
            for i, chunk in enumerate(chunks):
                embedding = ollama_embed(chunk)
                # ファイル名+連番の決まったIDにすることで、
                # 同じファイルを再インデックスしても重複せず上書きされる
                st.session_state.collection.upsert(
                    documents=[chunk],
                    embeddings=[embedding],
                    ids=[f"{file.name}_{i}"],
                    metadatas=[{"file_name": file.name}],
                )
            st.sidebar.success(f"ドキュメント{file.name}をインデックスに追加しました")
        st.sidebar.success(
            f"{len(uploaded_files)}件のドキュメントのインデックス作成が完了しました"
        )

# title
st.title("Local LLM Chat")

print(st.session_state)

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.sidebar.button("ドキュメントを削除"):
    st.session_state.collection.delete()

    st.session_state.messages = []

if st.sidebar.button("会話をリセット"):
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

prompt = st.chat_input("メッセージを入力してください")
client = OpenAI(api_key="ollama", base_url="http://localhost:12000/v1")

if prompt:
    # ユーザーのプロンプトを表示
    with st.chat_message("user"):
        st.write(prompt)

    # RAG検索
    query_embed = ollama_embed(prompt)
    results = st.session_state.collection.query(
        query_embeddings=[query_embed],
        n_results=3,
    )

    if results["documents"] and results["documents"][0]:
        context_text = "\n".join(results["documents"][0])
        rag_prompt = f"""
以下は関連ドキュメントの抜粋です。
        {context_text}
この情報を参考に以下の質問に答えてください。
        {prompt}
        """
        final_user_prompt = rag_prompt
    else:
        final_user_prompt = prompt

    # 送信用のメッセージ(履歴は変更せず、新しいリストを作る)
    messages = st.session_state.messages + [
        {"role": "user", "content": final_user_prompt}
    ]
    if system_prompt.strip():
        messages = [{"role": "system", "content": system_prompt}] + messages

    # LLMの回答を表示
    with st.chat_message("assistant"):
        placeholder = st.empty()
        stream_response = ""
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temparature,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                stream_response += chunk.choices[0].delta.content
                placeholder.write(stream_response)

    # 会話履歴を保存
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": stream_response})
