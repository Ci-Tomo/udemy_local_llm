import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Local LLM Chat")

st.sidebar.write("設定")
model = st.sidebar.text_input("モデル名", value="llama3.1")
temparature = st.sidebar.slider(
    "temperature", min_value=0.0, max_value=2.0, value=0.3, step=0.1
)
system_prompt = st.sidebar.text_area(
    "system prompt", value="あなたは有能なアシスタントです。日本語で回答してください"
)

st.title(" Local LLM Chat")

print(st.session_state)

if "messages" not in st.session_state:
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

    # 送信用のメッセージ(履歴は変更せず、新しいリストを作る)
    messages = st.session_state.messages + [{"role": "user", "content": prompt}]
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
