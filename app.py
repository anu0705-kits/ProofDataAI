import streamlit as st
import pandas as pd

from modules.data_profiler import profile_dataframe
from modules.question_parser import parse_question
from modules.code_executor import calculate
from modules.data_quality import check_data_quality, get_quality_status
from modules.currency_checker import check_currency_mismatch, currency_warning
from modules.ambiguity_detector import detect_question_ambiguity, is_ambiguous
from modules.verifier import verify_result
from modules.proof_certificate import create_certificate


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="ProofDataAI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# DARK THEME + UI DESIGN
# =========================================================

st.markdown("""
<style>

/* ==============================
   MAIN BACKGROUND
   ============================== */

.stApp {
    background-color: #000000;
    color: #ffffff;
}

.main .block-container {
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
    padding-bottom: 3rem;
}


/* ==============================
   GLOBAL TEXT
   ============================== */

html,
body,
p,
div,
span,
label,
h1,
h2,
h3,
h4,
h5,
h6 {
    color: #ffffff;
}


/* ==============================
   MAIN TITLE
   ============================== */

.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #ffffff !important;
    margin-bottom: 5px;
}

.subtitle {
    font-size: 17px;
    color: #b5b5b5 !important;
    margin-bottom: 30px;
}


/* ==============================
   SECTION TITLE
   ============================== */

.section-title {
    font-size: 25px;
    font-weight: 750;
    color: #ffffff !important;
    margin-top: 28px;
    margin-bottom: 15px;
}


/* ==============================
   SIDEBAR
   ============================== */

section[data-testid="stSidebar"] {
    background-color: #090909;
    border-right: 1px solid #292929;
}

section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

.sidebar-brand {
    font-size: 25px;
    font-weight: 800;
    color: #ffffff !important;
}

.sidebar-subtitle {
    font-size: 13px;
    color: #999999 !important;
    margin-bottom: 20px;
}


/* ==============================
   SIDEBAR NAVIGATION
   ============================== */

section[data-testid="stSidebar"]
div[role="radiogroup"] {
    gap: 8px;
}

section[data-testid="stSidebar"]
div[role="radiogroup"] label {
    background-color: #151515;
    border: 1px solid #292929;
    border-radius: 9px;
    padding: 10px 12px;
    color: #ffffff !important;
    font-size: 15px;
}

section[data-testid="stSidebar"]
div[role="radiogroup"] label:hover {
    background-color: #252525;
    border-color: #555555;
}


/* ==============================
   METRIC CARDS
   ============================== */

.metric-card {
    background-color: #111111;
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #303030;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    min-height: 105px;
}

.metric-title {
    font-size: 13px;
    font-weight: 600;
    color: #aaaaaa !important;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 30px;
    font-weight: 800;
    color: #ffffff !important;
}


/* ==============================
   INFORMATION CARDS
   ============================== */

.info-card {
    background-color: #111111;
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #303030;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
}

.info-card h3 {
    color: #ffffff !important;
}


/* ==============================
   VERIFIED CARD
   ============================== */

.verified-card {
    background-color: #071a0d;
    border: 1px solid #16803c;
    padding: 25px;
    border-radius: 15px;
}

.verified-title {
    font-size: 27px;
    font-weight: 800;
    color: #4ade80 !important;
}


/* ==============================
   REFUSED CARD
   ============================== */

.refused-card {
    background-color: #1c080b;
    border: 1px solid #dc2626;
    padding: 25px;
    border-radius: 15px;
}

.refused-title {
    font-size: 27px;
    font-weight: 800;
    color: #f87171 !important;
}


/* ==============================
   BUTTON
   ============================== */

.stButton > button {
    width: 100%;
    background-color: #ffffff;
    color: #000000 !important;
    border: none;
    border-radius: 9px;
    font-size: 16px;
    font-weight: 700;
    padding: 11px;
}

.stButton > button:hover {
    background-color: #dddddd;
    color: #000000 !important;
}


/* ==============================
   TEXT INPUT
   ============================== */

div[data-baseweb="input"] {
    background-color: #111111;
    border: 1px solid #444444;
    border-radius: 8px;
}

div[data-baseweb="input"] input {
    background-color: #111111 !important;
    color: #ffffff !important;
    font-size: 16px;
}

div[data-baseweb="input"] input::placeholder {
    color: #888888 !important;
}


/* ==============================
   SELECT BOX
   ============================== */

div[data-baseweb="select"] {
    background-color: #111111;
}

div[data-baseweb="select"] > div {
    background-color: #111111 !important;
    color: #ffffff !important;
    border-color: #444444 !important;
}

div[data-baseweb="select"] span {
    color: #ffffff !important;
}


/* ==============================
   FILE UPLOADER
   ============================== */

[data-testid="stFileUploader"] {
    background-color: #111111;
    border: 1px solid #333333;
    border-radius: 12px;
    padding: 10px;
}

[data-testid="stFileUploader"] * {
    color: #ffffff !important;
}


/* ==============================
   DATAFRAME
   ============================== */

[data-testid="stDataFrame"] {
    border: 1px solid #333333;
    border-radius: 10px;
}


/* ==============================
   EXPANDER
   ============================== */

[data-testid="stExpander"] {
    background-color: #111111;
    border: 1px solid #333333;
    border-radius: 10px;
}


/* ==============================
   CODE BLOCK
   ============================== */

pre {
    background-color: #0b0b0b !important;
    border: 1px solid #333333 !important;
    border-radius: 10px;
}


/* ==============================
   STREAMLIT METRICS
   ============================== */

[data-testid="stMetric"] {
    background-color: #111111;
    border: 1px solid #333333;
    border-radius: 10px;
    padding: 12px;
}

[data-testid="stMetricLabel"] {
    color: #aaaaaa !important;
}

[data-testid="stMetricValue"] {
    color: #ffffff !important;
}


/* ==============================
   FOOTER
   ============================== */

.footer {
    text-align: center;
    color: #777777 !important;
    font-size: 13px;
    padding-top: 30px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

if "df" not in st.session_state:
    st.session_state.df = None

if "file_name" not in st.session_state:
    st.session_state.file_name = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "certificate" not in st.session_state:
    st.session_state.certificate = None

if "proof_code" not in st.session_state:
    st.session_state.proof_code = None

if "verification" not in st.session_state:
    st.session_state.verification = None


# =========================================================
# LOAD DATASET FUNCTION
# =========================================================

def load_dataset(uploaded_file):

    try:

        if uploaded_file.name.endswith(".csv"):
            dataframe = pd.read_csv(uploaded_file)

        else:
            dataframe = pd.read_excel(uploaded_file)

        st.session_state.df = dataframe
        st.session_state.file_name = uploaded_file.name

        return True

    except Exception as e:

        st.error(
            f"Unable to read the file: {e}"
        )

        return False


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-brand">🛡️ ProofDataAI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sidebar-subtitle">'
        'Proof-Carrying Data Analyst'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### Navigation")

    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "📂 Dataset Analysis",
            "🔍 Question Analysis",
            "🏆 Proof & Verification"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("### System Status")

    st.success("● AI Engine Ready")
    st.success("● Safety Engine Ready")
    st.success("● Verification Ready")

    st.divider()

    if st.session_state.df is not None:

        st.markdown("### Current Dataset")

        st.write(
            "📄 " + st.session_state.file_name
        )

    else:

        st.caption(
            "No dataset uploaded"
        )


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🛡️ ProofDataAI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Proof-Carrying Data Analyst — '
    'Analyze • Verify • Prove • Refuse'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# DASHBOARD
# =========================================================

if page == "📊 Dashboard":

    st.markdown(
        '<div class="section-title">'
        '📊 Dashboard Overview'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("### 📂 Upload Dataset")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx"],
        key="dashboard_upload"
    )

    if uploaded_file is not None:

        if (
            st.session_state.file_name
            != uploaded_file.name
        ):

            if load_dataset(uploaded_file):

                st.success(
                    "✅ Dataset uploaded successfully!"
                )


    # -----------------------------------------------------
    # NO DATASET
    # -----------------------------------------------------

    if st.session_state.df is None:

        st.info(
            "Upload a dataset to begin your analysis."
        )

        st.markdown("---")

        st.markdown(
            "### How ProofDataAI Works"
        )

        a, b, c, d = st.columns(4)

        with a:

            st.markdown(
                """
                <div class="info-card">
                <h3>1️⃣ Upload</h3>
                Upload messy real-world data.
                </div>
                """,
                unsafe_allow_html=True
            )

        with b:

            st.markdown(
                """
                <div class="info-card">
                <h3>2️⃣ Detect</h3>
                Detect data quality,
                ambiguity and mismatches.
                </div>
                """,
                unsafe_allow_html=True
            )

        with c:

            st.markdown(
                """
                <div class="info-card">
                <h3>3️⃣ Calculate</h3>
                Generate and execute
                reproducible analysis.
                </div>
                """,
                unsafe_allow_html=True
            )

        with d:

            st.markdown(
                """
                <div class="info-card">
                <h3>4️⃣ Verify</h3>
                Independently verify
                or safely refuse.
                </div>
                """,
                unsafe_allow_html=True
            )


    # -----------------------------------------------------
    # DATASET EXISTS
    # -----------------------------------------------------

    else:

        df = st.session_state.df

        profile = profile_dataframe(df)

        quality = check_data_quality(df)

        status = get_quality_status(
            quality
        )


        st.markdown(
            f"### 📄 {st.session_state.file_name}"
        )


        # METRIC CARDS

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.markdown(
                f"""
                <div class="metric-card">
                <div class="metric-title">
                TOTAL ROWS
                </div>
                <div class="metric-value">
                {profile["rows"]}
                </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:

            st.markdown(
                f"""
                <div class="metric-card">
                <div class="metric-title">
                COLUMNS
                </div>
                <div class="metric-value">
                {profile["columns"]}
                </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:

            st.markdown(
                f"""
                <div class="metric-card">
                <div class="metric-title">
                MISSING VALUES
                </div>
                <div class="metric-value">
                {profile["missing_values"]}
                </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c4:

            st.markdown(
                f"""
                <div class="metric-card">
                <div class="metric-title">
                DUPLICATE ROWS
                </div>
                <div class="metric-value">
                {profile["duplicate_rows"]}
                </div>
                </div>
                """,
                unsafe_allow_html=True
            )


        st.markdown(
            '<div class="section-title">'
            '🛡️ System Status'
            '</div>',
            unsafe_allow_html=True
        )


        x, y, z = st.columns(3)


        with x:

            if status["status"] == "GOOD":

                st.success(
                    "✅ Data Quality: GOOD"
                )

            else:

                st.warning(
                    "⚠️ Data Quality: WARNING"
                )


        with y:

            currency_result = check_currency_mismatch(
                [df]
            )

            if currency_result["mismatch"]:

                st.warning(
                    "⚠️ Currency: MIXED"
                )

            else:

                st.success(
                    "✅ Currency: SAFE"
                )


        with z:

            if st.session_state.last_result is not None:

                st.success(
                    "✅ Last Result: VERIFIED"
                )

            else:

                st.info(
                    "ℹ️ No analysis yet"
                )


# =========================================================
# DATASET ANALYSIS
# =========================================================

elif page == "📂 Dataset Analysis":

    st.markdown(
        '<div class="section-title">'
        '📂 Dataset Analysis'
        '</div>',
        unsafe_allow_html=True
    )


    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx"],
        key="dataset_upload"
    )


    if uploaded_file is not None:

        if (
            st.session_state.file_name
            != uploaded_file.name
        ):

            if load_dataset(uploaded_file):

                st.success(
                    "✅ Dataset uploaded successfully!"
                )


    if st.session_state.df is None:

        st.info(
            "Please upload a dataset first."
        )


    else:

        df = st.session_state.df


        st.markdown(
            f"### 📄 {st.session_state.file_name}"
        )


        # DATA PREVIEW

        st.markdown(
            "### 👀 Data Preview"
        )

        st.dataframe(
            df,
            use_container_width=True,
            height=350
        )


        # STATISTICS

        profile = profile_dataframe(df)


        st.markdown(
            "### 📊 Dataset Statistics"
        )


        a, b, c, d = st.columns(4)


        a.metric(
            "Rows",
            profile["rows"]
        )

        b.metric(
            "Columns",
            profile["columns"]
        )

        c.metric(
            "Missing Values",
            profile["missing_values"]
        )

        d.metric(
            "Duplicate Rows",
            profile["duplicate_rows"]
        )


        # QUALITY

        st.markdown(
            "### 🧹 Data Quality"
        )


        quality_report = check_data_quality(
            df
        )


        quality_status = get_quality_status(
            quality_report
        )


        if quality_status["status"] == "GOOD":

            st.success(
                "✅ No major data quality problems detected."
            )

        else:

            st.warning(
                "⚠️ Data quality problems detected."
            )

            for problem in quality_status["problems"]:

                st.write(
                    "• " + problem
                )


        # CURRENCY

        st.markdown(
            "### 💰 Currency / Unit Guardian"
        )


        currency_result = check_currency_mismatch(
            [df]
        )


        if currency_result["mismatch"]:

            st.warning(
                currency_warning(
                    currency_result
                )
            )

        elif currency_result["has_currency"]:

            st.success(
                currency_warning(
                    currency_result
                )
            )

        else:

            st.info(
                "No currency column detected."
            )


# =========================================================
# QUESTION ANALYSIS
# =========================================================

elif page == "🔍 Question Analysis":

    st.markdown(
        '<div class="section-title">'
        '🔍 Question Analysis'
        '</div>',
        unsafe_allow_html=True
    )


    if st.session_state.df is None:

        st.info(
            "Please upload a dataset from the "
            "Dashboard or Dataset Analysis page first."
        )


    else:

        df = st.session_state.df


        st.success(
            "Dataset loaded: "
            + st.session_state.file_name
        )


        # QUESTION

        question = st.text_input(
            "Ask a question about your dataset",
            placeholder=
            "Example: What is the maximum amount in INR?"
        )


        if question:

            question_lower = question.lower()


            # OPERATION

            operation = parse_question(
                question
            )


            a, b = st.columns(2)


            with a:

                st.markdown(
                    f"""
                    <div class="metric-card">
                    <div class="metric-title">
                    DETECTED OPERATION
                    </div>
                    <div class="metric-value"
                    style="font-size:22px">
                    {operation.upper()}
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


            with b:

                st.markdown(
                    f"""
                    <div class="metric-card">
                    <div class="metric-title">
                    DATASET
                    </div>
                    <div class="metric-value"
                    style="font-size:18px">
                    {st.session_state.file_name}
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


            # UNKNOWN OPERATION

            if operation == "unknown":

                st.warning(
                    "⚠️ I could not reliably identify "
                    "the required operation."
                )

                st.stop()


            # NUMERICAL COLUMNS

            numeric_columns = list(
                df.select_dtypes(
                    include="number"
                ).columns
            )


            if not numeric_columns:

                st.error(
                    "❌ No numerical columns found."
                )

                st.stop()


            # COLUMN

            column = st.selectbox(
                "Select numerical column",
                numeric_columns
            )


            # CURRENCY

            currency_result = check_currency_mismatch(
                [df]
            )


            selected_currency = None


            if currency_result["has_currency"]:

                for currency in currency_result["currencies"]:

                    if currency.lower() in question_lower:

                        selected_currency = currency


            if selected_currency:

                st.info(
                    "💰 Currency filter detected: "
                    + selected_currency
                )


            # ANALYZE

            if st.button(
                "🔎 Analyze & Verify",
                use_container_width=True
            ):

                try:

                    # -------------------------------------
                    # WORKING DATA
                    # -------------------------------------

                    working_df = df.copy()


                    # -------------------------------------
                    # CURRENCY FILTER
                    # -------------------------------------

                    if selected_currency:

                        currency_column = None


                        for col in working_df.columns:

                            if col.lower() in [
                                "currency",
                                "currencies",
                                "currency_code"
                            ]:

                                currency_column = col

                                break


                        if currency_column:

                            working_df = working_df[
                                working_df[
                                    currency_column
                                ]
                                .astype(str)
                                .str.upper()
                                == selected_currency
                            ]


                    # -------------------------------------
                    # MIXED CURRENCY REFUSAL
                    # -------------------------------------

                    elif currency_result["mismatch"]:

                        financial_words = [
                            "revenue",
                            "sales",
                            "price",
                            "cost",
                            "profit",
                            "amount",
                            "income"
                        ]


                        is_financial = any(
                            word in question_lower
                            for word in financial_words
                        )


                        if is_financial:

                            st.session_state.last_result = None


                            st.markdown(
                                """
                                <div class="refused-card">

                                <div class="refused-title">
                                🚫 RESULT REFUSED
                                </div>

                                <br>

                                Multiple currencies were detected.

                                <br><br>

                                ProofDataAI will not combine
                                INR, USD and EUR without a
                                valid conversion rule.

                                <br><br>

                                <b>
                                Safe action:
                                specify a currency.
                                </b>

                                </div>
                                """,
                                unsafe_allow_html=True
                            )


                            st.info(
                                "Example: "
                                "What is the total amount in INR?"
                            )


                            st.stop()


                    # -------------------------------------
                    # VALUES
                    # -------------------------------------

                    values = pd.to_numeric(
                        working_df[column],
                        errors="coerce"
                    ).dropna()


                    if len(values) == 0:

                        st.error(
                            "❌ No valid numerical values found."
                        )

                        st.stop()


                    # -------------------------------------
                    # PRIMARY CALCULATION
                    # -------------------------------------

                    calculated_result = calculate(
                        working_df,
                        operation,
                        column
                    )


                    # -------------------------------------
                    # INDEPENDENT CALCULATION
                    # -------------------------------------

                    independent_values = pd.to_numeric(
                        working_df[column],
                        errors="coerce"
                    ).dropna()


                    if operation == "sum":

                        independent_result = sum(
                            independent_values.tolist()
                        )


                    elif operation == "average":

                        independent_result = (
                            sum(
                                independent_values.tolist()
                            )
                            / len(independent_values)
                        )


                    elif operation == "max":

                        independent_result = max(
                            independent_values.tolist()
                        )


                    elif operation == "min":

                        independent_result = min(
                            independent_values.tolist()
                        )


                    else:

                        independent_result = None


                    # -------------------------------------
                    # VERIFICATION
                    # -------------------------------------

                    verification = verify_result(
                        calculated_result,
                        independent_result
                    )


                    # =====================================
                    # VERIFIED
                    # =====================================

                    if verification["verified"]:


                        st.session_state.last_result = (
                            calculated_result
                        )


                        st.session_state.verification = (
                            verification
                        )


                        # ---------------------------------
                        # PROOF CODE
                        # ---------------------------------

                        proof_code = f'''import pandas as pd

df = pd.read_csv(
    "{st.session_state.file_name}"
)
'''


                        if selected_currency:

                            proof_code += f'''
df = df[
    df["currency"].astype(str).str.upper()
    == "{selected_currency}"
]
'''


                        proof_code += f'''
values = pd.to_numeric(
    df["{column}"],
    errors="coerce"
).dropna()
'''


                        if operation == "sum":

                            proof_code += """
result = values.sum()
"""


                        elif operation == "average":

                            proof_code += """
result = values.mean()
"""


                        elif operation == "max":

                            proof_code += """
result = values.max()
"""


                        elif operation == "min":

                            proof_code += """
result = values.min()
"""


                        proof_code += """

print(result)
"""


                        st.session_state.proof_code = (
                            proof_code
                        )


                        # ---------------------------------
                        # CERTIFICATE
                        # ---------------------------------

                        certificate = create_certificate(

                            question=question,

                            result=calculated_result,

                            dataset_name=
                            st.session_state.file_name,

                            operation=operation,

                            rows_used=len(values),

                            verification_status=
                            "VERIFIED"
                        )


                        st.session_state.certificate = (
                            certificate
                        )


                        # ---------------------------------
                        # VERIFIED UI
                        # ---------------------------------

                        st.markdown(
                            """
                            <div class="verified-card">

                            <div class="verified-title">
                            ✅ RESULT VERIFIED
                            </div>

                            <br>

                            Primary calculation and
                            independent calculation
                            match successfully.

                            </div>
                            """,
                            unsafe_allow_html=True
                        )


                        r1, r2, r3 = st.columns(3)


                        with r1:

                            st.metric(
                                "Verified Answer",
                                f"{calculated_result:,.2f}"
                            )


                        with r2:

                            st.metric(
                                "Rows Used",
                                len(values)
                            )


                        with r3:

                            st.metric(
                                "Difference",
                                verification[
                                    "difference"
                                ]
                            )


                        st.success(
                            "🏆 Proof generated successfully!"
                        )


                        st.info(
                            "Go to "
                            "🏆 Proof & Verification "
                            "from the sidebar to view "
                            "the complete proof."
                        )


                    # =====================================
                    # REJECTED
                    # =====================================

                    else:

                        st.session_state.last_result = None


                        st.markdown(
                            """
                            <div class="refused-card">

                            <div class="refused-title">
                            🚫 RESULT REJECTED
                            </div>

                            <br>

                            Independent verification
                            failed.

                            <br><br>

                            ProofDataAI will not provide
                            an unverified numerical answer.

                            </div>
                            """,
                            unsafe_allow_html=True
                        )


                except Exception as e:

                    st.error(
                        "❌ Analysis failed: "
                        + str(e)
                    )


# =========================================================
# PROOF & VERIFICATION
# =========================================================

elif page == "🏆 Proof & Verification":

    st.markdown(
        '<div class="section-title">'
        '🏆 Proof & Verification'
        '</div>',
        unsafe_allow_html=True
    )


    if st.session_state.last_result is None:

        st.info(
            "No verified result available yet."
        )


        st.write(
            "Go to **🔍 Question Analysis**, "
            "ask a question and click "
            "**Analyze & Verify**."
        )


    else:

        # -----------------------------------------------
        # VERIFIED RESULT
        # -----------------------------------------------

        st.markdown(
            """
            <div class="verified-card">

            <div class="verified-title">
            ✅ VERIFIED RESULT
            </div>

            <br>

            The numerical result passed
            independent verification.

            </div>
            """,
            unsafe_allow_html=True
        )


        st.markdown(
            "### 📊 Verified Answer"
        )


        st.metric(
            "Result",
            f"{st.session_state.last_result:,.2f}"
        )


        # -----------------------------------------------
        # VERIFICATION DETAILS
        # -----------------------------------------------

        st.markdown(
            "### 🔐 Verification Details"
        )


        if st.session_state.verification:

            verification = (
                st.session_state.verification
            )


            a, b = st.columns(2)


            with a:

                st.success(
                    "✓ Primary Calculation"
                )


            with b:

                st.success(
                    "✓ Independent Calculation"
                )


            st.write(
                "**Verification Difference:**",
                verification["difference"]
            )


        # -----------------------------------------------
        # PROOF CODE
        # -----------------------------------------------

        if st.session_state.proof_code:

            st.markdown(
                "### 📜 Reproducible Proof Code"
            )


            st.code(
                st.session_state.proof_code,
                language="python"
            )


        # -----------------------------------------------
        # PROOF CERTIFICATE
        # -----------------------------------------------

        if st.session_state.certificate:

            st.markdown(
                "### 🏆 Proof Certificate"
            )


            st.json(
                st.session_state.certificate
            )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
    🛡️ ProofDataAI — Every numerical answer must carry proof.
    If proof fails, the system refuses.
    </div>
    """,
    unsafe_allow_html=True
)