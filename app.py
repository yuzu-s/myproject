import streamlit as st
import time
import google.genai as genai
import PyPDF2
import io

# アプリのタイトルを設定
st.title("💡 質疑応答支援AI")
st.markdown("---")

# GeminiのAPIキーをsecretsから取得し設定
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"モデルのロードに失敗しました: {e}")
    st.stop()

# PDFからテキストを抽出する関数
@st.cache_data
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page_text = pdf_reader.pages[page_num].extract_text()
            if page_text:
                text += page_text
        return text
    except Exception as e:
        st.error(f"PDFの読み込み中にエラーが発生しました: {e}")
        return ""

def get_ai_suggestion(memo_text, reference_text):
    """
    GeminiのAPIを呼び出し、質問に対する提案を取得する関数
    参考資料の内容もプロンプトに含めます
    """
    try:
        # 参考資料の内容をプロンプトに追加
        prompt_with_reference = (
            f"以下の発表資料を参考に、ユーザーのメモの疑問点に対する回答を提示してください。\n"
            f"もし疑問点が資料に記載されている場合は、該当する内容とページ番号を提示してください。\n"
            f"資料に記載がない場合は、発表者に対する質問の形式に整えてください。\n"
            f"また、システム使用者が発言したい！と思えるような、後押しとなるような一言を加えてください。\n"
            f"--- 発表資料のテキスト ---\n{reference_text}\n"
            f"--- ユーザーのメモ ---\n{memo_text}"
        )
        response = model.generate_content(prompt_with_reference)
        return response.text
    except Exception as e:
        st.error(f"AIとの通信中にエラーが発生しました: {e}")
        return None

# --- UIコンポーネント ---
st.subheader("ステップ1: 発表資料をアップロード")
uploaded_file = st.file_uploader("発表資料（PDF）をアップロードしてください", type="pdf")

if uploaded_file:
    st.success("✅ PDF資料がアップロードされました！")

st.subheader("ステップ2: メモを入力")
memo_input = st.text_area(
    "発表を聞きながらここにメモしてください。疑問点には「？」をつけてください。",
    height=300,
    placeholder="例: 実験は何名くらいを想定しているか？ 今後追加したい機能はあるか？"
)

st.subheader("ステップ3: AIに分析を依頼")
# メモとPDFが両方ある場合にのみボタンを有効にする
analyze_button = st.button(
    "AIに分析を依頼",
    disabled=not uploaded_file or not memo_input.strip() or ('？' not in memo_input and '?' not in memo_input)
)

# --- ユーザーアクションの処理 ---
if analyze_button:
    # 疑問符を含む行だけを抽出
    memo_lines = memo_input.split('\n')
    question_line = ""
    for line in reversed(memo_lines):
        if '？' in line or '?' in line:
            question_line = line.strip()
            break

    if not question_line:
        st.error("メモに疑問符「？」が含まれている行が見つかりませんでした。")
    else:
        st.info(f"AIが着目したテキスト：**'{question_line}'**")

        with st.spinner("AIが質問案を作成中です..."):
            reference_text = extract_text_from_pdf(uploaded_file)
            if not reference_text:
                st.warning("PDFからテキストを抽出できませんでした。スキャンされたPDFではないか確認してください。")
            
            ai_suggestion = get_ai_suggestion(question_line, reference_text)
        
        if ai_suggestion:
            st.markdown("---")
            st.markdown("#### AIからの提案：")
            st.write(ai_suggestion)
            
st.caption(f"最終更新: {time.strftime('%H:%M:%S')}")

