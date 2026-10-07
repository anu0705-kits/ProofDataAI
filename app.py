import streamlit as st
import pandas as pd
import re
import hashlib
from datetime import datetime

from modules.data_profiler import profile_dataframe
from modules.question_parser import parse_question
from modules.code_executor import calculate
from modules.data_quality import check_data_quality, get_quality_status
from modules.currency_checker import check_currency_mismatch, currency_warning
from modules.verifier import verify_result
from modules.proof_certificate import create_certificate


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ProofDataAI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

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

html, body, p, div, span, label,
h1, h2, h3, h4, h5, h6 {
    color: #ffffff;
}

.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #ffffff !important;
}

.subtitle {
    font-size: 17px;
    color: #aaaaaa !important;
    margin-bottom: 30px;
}

.section-title {
    font-size: 25px;
    font-weight: 750;
    color: #ffffff !important;
    margin-top: 28px;
    margin-bottom: 15px;
}

/* SIDEBAR */

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
}

.sidebar-subtitle {
    font-size: 13px;
    color: #999999 !important;
    margin-bottom: 20px;
}

/* CARDS */

.metric-card {
    background-color: #111111;
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #303030;
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

.info-card {
    background-color: #111111;
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #303030;
}

/* VERIFIED */

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

/* REFUSED */

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

/* BUTTON */

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
}

/* INPUT */

div[data-baseweb="input"] {
    background-color: #111111;
    border: 1px solid #444444;
    border-radius: 8px;
}

div[data-baseweb="input"] input {
    background-color: #111111 !important;
    color: #ffffff !important;
}

/* SELECT */

div[data-baseweb="select"] > div {
    background-color: #111111 !important;
    color: #ffffff !important;
    border-color: #444444 !important;
}

/* FILE */

[data-testid="stFileUploader"] {
    background-color: #111111;
    border: 1px solid #333333;
    border-radius: 12px;
    padding: 10px;
}

/* TABLE */

[data-testid="stDataFrame"] {
    border: 1px solid #333333;
    border-radius: 10px;
}

/* CODE */

pre {
    background-color: #0b0b0b !important;
    border: 1px solid #333333 !important;
    border-radius: 10px;
}

/* FOOTER */

.footer {
    text-align: center;
    color: #777777 !important;
    font-size: 13px;
    padding-top: 30px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "df": None,
    "file_name": None,
    "last_result": None,
    "certificate": None,
    "proof_code": None,
    "verification": None,
    "last_question": None,
    "refusal_reason": None
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# FILE READER
# ============================================================

def read_file(uploaded_file):

    if uploaded_file.name.lower().endswith(".csv"):

        return pd.read_csv(uploaded_file)

    return pd.read_excel(uploaded_file)


# ============================================================
# LOAD SINGLE DATASET
# ============================================================

def load_dataset(uploaded_file):

    try:

        dataframe = read_file(uploaded_file)

        st.session_state.df = dataframe
        st.session_state.file_name = uploaded_file.name

        return True

    except Exception as e:

        st.error(
            "Unable to read file: " + str(e)
        )

        return False


# ============================================================
# FIND CURRENCY COLUMN
# ============================================================

def find_currency_column(df):

    possible = [
        "currency",
        "currencies",
        "currency_code"
    ]

    for column in df.columns:

        if column.lower() in possible:

            return column

    return None


# ============================================================
# FIND UNIT COLUMN
# ============================================================

def find_unit_columns(df):

    possible = [
        "unit",
        "units",
        "uom",
        "unit_type",
        "measurement_unit"
    ]

    result = []

    for column in df.columns:

        if column.lower() in possible:

            result.append(column)

    return result


# ============================================================
# GET CURRENCIES
# ============================================================

def get_currencies(df):

    currency_column = find_currency_column(df)

    if currency_column is None:

        return []

    values = (
        df[currency_column]
        .dropna()
        .astype(str)
        .str.upper()
        .str.strip()
        .unique()
    )

    return sorted(values.tolist())


# ============================================================
# GET UNITS
# ============================================================

def get_units(df):

    unit_columns = find_unit_columns(df)

    units = set()

    for column in unit_columns:

        values = (
            df[column]
            .dropna()
            .astype(str)
            .str.lower()
            .str.strip()
            .unique()
        )

        for value in values:

            units.add(value)

    return sorted(units)


# ============================================================
# FINANCIAL QUESTION
# ============================================================

def is_financial_question(question):

    words = [
        "revenue",
        "sales",
        "price",
        "cost",
        "profit",
        "amount",
        "income",
        "salary",
        "expense",
        "money"
    ]

    question = question.lower()

    return any(
        word in question
        for word in words
    )


# ============================================================
# DATE AMBIGUITY DETECTOR
# ============================================================

def detect_ambiguous_dates(question, df):

    warnings = []

    question_lower = question.lower()

    date_words = [
        "date",
        "day",
        "month",
        "year",
        "on ",
        "during"
    ]

    has_date_question = any(
        word in question_lower
        for word in date_words
    )

    if not has_date_question:

        return warnings

    # Check date-like columns
    for column in df.columns:

        column_lower = column.lower()

        if (
            "date" in column_lower
            or "day" in column_lower
        ):

            values = (
                df[column]
                .dropna()
                .astype(str)
                .head(100)
                .tolist()
            )

            for value in values:

                if re.match(
                    r"^\d{1,2}/\d{1,2}/\d{4}$",
                    value.strip()
                ):

                    warnings.append(
                        f"Ambiguous date format detected "
                        f"in column '{column}'. "
                        f"Values such as {value} can represent "
                        f"different dates depending on DD/MM or MM/DD format."
                    )

                    return warnings

    return warnings


# ============================================================
# DUPLICATE DETECTOR
# ============================================================

def detect_duplicates(df):

    count = int(
        df.duplicated().sum()
    )

    return count


# ============================================================
# MISSING DATA DETECTOR
# ============================================================

def detect_missing_for_column(df, column):

    if column not in df.columns:

        return 0

    return int(
        df[column].isna().sum()
    )


# ============================================================
# FIND REQUESTED CURRENCY FROM QUESTION
# ============================================================

def find_requested_currency(question, currencies):

    question_lower = question.lower()

    currency_names = {

        "usd": [
            "usd",
            "dollar",
            "dollars",
            "$"
        ],

        "eur": [
            "eur",
            "euro",
            "euros",
            "€"
        ],

        "inr": [
            "inr",
            "rupee",
            "rupees",
            "₹"
        ],

        "gbp": [
            "gbp",
            "pound",
            "pounds",
            "£"
        ]

    }

    for currency in currencies:

        currency_lower = currency.lower()

        if currency_lower in question_lower:

            return currency

        if currency_lower in currency_names:

            for keyword in currency_names[currency_lower]:

                if keyword in question_lower:

                    return currency

    return None


# ============================================================
# TRICK QUESTION CHECK
# ============================================================

def check_trick_question(
    question,
    df,
    selected_currency,
    column
):

    warnings = []

    # ----------------------------------------------
    # Requested currency does not exist
    # ----------------------------------------------

    currencies = get_currencies(df)

    if selected_currency:

        if selected_currency not in currencies:

            warnings.append(
                f"The question requests {selected_currency}, "
                f"but that currency does not exist in the dataset."
            )

    # ----------------------------------------------
    # Column does not contain usable data
    # ----------------------------------------------

    if column not in df.columns:

        warnings.append(
            f"The requested column '{column}' "
            f"does not exist."
        )

    # ----------------------------------------------
    # No rows
    # ----------------------------------------------

    if len(df) == 0:

        warnings.append(
            "The dataset contains no records."
        )

    return warnings


# ============================================================
# BUILD PROOF CODE
# ============================================================

def build_proof_code(
    file_name,
    column,
    operation,
    selected_currency
):

    code = f'''import pandas as pd

df = pd.read_csv("{file_name}")
'''

    if selected_currency:

        code += f'''
df = df[
    df["currency"]
    .astype(str)
    .str.upper()
    == "{selected_currency}"
]
'''

    code += f'''
values = pd.to_numeric(
    df["{column}"],
    errors="coerce"
).dropna()
'''

    if operation == "sum":

        code += """
result = values.sum()
"""

    elif operation == "average":

        code += """
result = values.mean()
"""

    elif operation == "max":

        code += """
result = values.max()
"""

    elif operation == "min":

        code += """
result = values.min()
"""

    code += """
print(result)
"""

    return code


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-brand">'
        '🛡️ ProofDataAI'
        '</div>',
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
            "⚠️ Contradiction Check",
            "🏆 Proof & Verification"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("### System Status")

    st.success("● AI Engine Ready")
    st.success("● Trap Detector Ready")
    st.success("● Verification Ready")

    st.divider()

    if st.session_state.df is not None:

        st.markdown("### Current Dataset")

        st.write(
            "📄 "
            + st.session_state.file_name
        )

    else:

        st.caption(
            "No dataset uploaded"
        )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    '🛡️ ProofDataAI'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Proof-Carrying Data Analyst — '
    'Analyze • Detect • Verify • Prove • Refuse'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    st.markdown(
        '<div class="section-title">'
        '📊 Dashboard Overview'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        "### 📂 Upload Dataset"
    )

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

    if st.session_state.df is None:

        st.info(
            "Upload a dataset to begin."
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
                Upload real-world data.
                </div>
                """,
                unsafe_allow_html=True
            )

        with b:

            st.markdown(
                """
                <div class="info-card">
                <h3>2️⃣ Detect</h3>
                Detect hidden data traps.
                </div>
                """,
                unsafe_allow_html=True
            )

        with c:

            st.markdown(
                """
                <div class="info-card">
                <h3>3️⃣ Calculate</h3>
                Generate reproducible analysis.
                </div>
                """,
                unsafe_allow_html=True
            )

        with d:

            st.markdown(
                """
                <div class="info-card">
                <h3>4️⃣ Verify</h3>
                Verify or safely refuse.
                </div>
                """,
                unsafe_allow_html=True
            )

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

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Rows",
            profile["rows"]
        )

        c2.metric(
            "Columns",
            profile["columns"]
        )

        c3.metric(
            "Missing Values",
            profile["missing_values"]
        )

        c4.metric(
            "Duplicate Rows",
            profile["duplicate_rows"]
        )

        st.markdown(
            "### 🛡️ Safety Status"
        )

        x, y, z = st.columns(3)

        with x:

            if status["status"] == "GOOD":

                st.success(
                    "✅ Data Quality GOOD"
                )

            else:

                st.warning(
                    "⚠️ Data Quality WARNING"
                )

        with y:

            currencies = get_currencies(df)

            if len(currencies) > 1:

                st.warning(
                    "⚠️ Multiple Currencies"
                )

            else:

                st.success(
                    "✅ Currency Safe"
                )

        with z:

            duplicate_count = detect_duplicates(
                df
            )

            if duplicate_count > 0:

                st.warning(
                    f"⚠️ {duplicate_count} Duplicate Rows"
                )

            else:

                st.success(
                    "✅ No Duplicates"
                )


# ============================================================
# DATASET ANALYSIS
# ============================================================

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

            load_dataset(
                uploaded_file
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

        st.markdown(
            "### 👀 Data Preview"
        )

        st.dataframe(
            df,
            use_container_width=True,
            height=350
        )

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

        # ----------------------------------------------
        # MISSING
        # ----------------------------------------------

        st.markdown(
            "### 🧹 Missing Data"
        )

        missing = (
            df.isnull()
            .sum()
        )

        missing = missing[
            missing > 0
        ]

        if len(missing) == 0:

            st.success(
                "✅ No missing values."
            )

        else:

            st.warning(
                "⚠️ Missing values detected."
            )

            st.dataframe(
                missing.rename(
                    "Missing Values"
                )
            )

        # ----------------------------------------------
        # DUPLICATES
        # ----------------------------------------------

        st.markdown(
            "### 🔁 Duplicate Rows"
        )

        duplicate_count = detect_duplicates(
            df
        )

        if duplicate_count == 0:

            st.success(
                "✅ No duplicate rows detected."
            )

        else:

            st.warning(
                f"⚠️ {duplicate_count} "
                "duplicate row(s) detected."
            )

        # ----------------------------------------------
        # CURRENCY
        # ----------------------------------------------

        st.markdown(
            "### 💰 Currency Guardian"
        )

        currencies = get_currencies(
            df
        )

        if len(currencies) > 1:

            st.error(
                "🚫 Multiple currencies detected: "
                + ", ".join(currencies)
            )

        elif len(currencies) == 1:

            st.success(
                "✅ Currency: "
                + currencies[0]
            )

        else:

            st.info(
                "No currency column detected."
            )

        # ----------------------------------------------
        # UNITS
        # ----------------------------------------------

        st.markdown(
            "### 📏 Unit Guardian"
        )

        units = get_units(df)

        if len(units) > 1:

            st.warning(
                "⚠️ Multiple units detected: "
                + ", ".join(units)
            )

        elif len(units) == 1:

            st.success(
                "✅ Unit: "
                + units[0]
            )

        else:

            st.info(
                "No unit column detected."
            )


# ============================================================
# QUESTION ANALYSIS
# ============================================================

elif page == "🔍 Question Analysis":

    st.markdown(
        '<div class="section-title">'
        '🔍 Question Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    if st.session_state.df is None:

        st.info(
            "Please upload a dataset first."
        )

    else:

        df = st.session_state.df

        st.success(
            "Dataset loaded: "
            + st.session_state.file_name
        )

        question = st.text_input(
            "Ask a question",
            placeholder=(
                "Example: What is the maximum amount in INR?"
            )
        )

        if question:

            operation = parse_question(
                question
            )

            numeric_columns = list(
                df.select_dtypes(
                    include="number"
                ).columns
            )

            a, b = st.columns(2)

            with a:

                st.markdown(
                    f"""
                    <div class="metric-card">
                    <div class="metric-title">
                    DETECTED OPERATION
                    </div>
                    <div class="metric-value">
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

            if operation == "unknown":

                st.error(
                    "🚫 Cannot determine a valid operation."
                )

                st.info(
                    "Try asking for total, average, "
                    "maximum or minimum."
                )

                st.stop()

            if not numeric_columns:

                st.error(
                    "🚫 No numerical column exists."
                )

                st.stop()

            column = st.selectbox(
                "Select numerical column",
                numeric_columns
            )

            if st.button(
                "🛡️ Analyze, Detect & Verify",
                use_container_width=True
            ):

                # ====================================================
                # SAFETY CHECK START
                # ====================================================

                trap_messages = []

                currencies = get_currencies(
                    df
                )

                units = get_units(
                    df
                )

                requested_currency = (
                    find_requested_currency(
                        question,
                        currencies
                    )
                )

                # ====================================================
                # TRAP 1 — CURRENCY
                # ====================================================

                if (
                    is_financial_question(question)
                    and len(currencies) > 1
                    and requested_currency is None
                ):

                    trap_messages.append(
                        "💰 Multiple currencies detected: "
                        + ", ".join(currencies)
                        + ". The question does not specify "
                        "which currency should be used."
                    )

                # ====================================================
                # TRAP 2 — REQUESTED CURRENCY DOES NOT EXIST
                # ====================================================

                question_lower = question.lower()

                currency_words = [
                    "usd",
                    "dollar",
                    "dollars",
                    "$",
                    "eur",
                    "euro",
                    "euros",
                    "€",
                    "inr",
                    "rupee",
                    "rupees",
                    "₹",
                    "gbp",
                    "pound",
                    "pounds",
                    "£"
                ]

                requested_currency_text = any(
                    word in question_lower
                    for word in currency_words
                )

                if (
                    requested_currency_text
                    and requested_currency is None
                    and len(currencies) > 0
                ):

                    trap_messages.append(
                        "🧠 The question requests a currency "
                        "that cannot be matched reliably with "
                        "the dataset."
                    )

                # ====================================================
                # TRAP 3 — UNIT MISMATCH
                # ====================================================

                unit_words = [
                    "kg",
                    "kilogram",
                    "kilograms",
                    "litre",
                    "liter",
                    "litres",
                    "liters",
                    "meter",
                    "metre",
                    "meters",
                    "metres"
                ]

                question_has_unit = any(
                    word in question_lower
                    for word in unit_words
                )

                if (
                    question_has_unit
                    and len(units) > 1
                ):

                    trap_messages.append(
                        "📏 Multiple units detected: "
                        + ", ".join(units)
                        + ". Values with different units "
                        "cannot be directly combined."
                    )

                # ====================================================
                # TRAP 4 — AMBIGUOUS DATE
                # ====================================================

                date_warnings = (
                    detect_ambiguous_dates(
                        question,
                        df
                    )
                )

                for warning in date_warnings:

                    trap_messages.append(
                        "📅 " + warning
                    )

                # ====================================================
                # TRAP 5 — DUPLICATES
                # ====================================================

                duplicate_count = (
                    detect_duplicates(df)
                )

                if duplicate_count > 0:

                    trap_messages.append(
                        f"🔁 {duplicate_count} duplicate "
                        "row(s) detected. Counting them may "
                        "double-count the result."
                    )

                # ====================================================
                # TRAP 6 — MISSING DATA
                # ====================================================

                missing_count = (
                    detect_missing_for_column(
                        df,
                        column
                    )
                )

                if missing_count > 0:

                    trap_messages.append(
                        f"❓ Column '{column}' contains "
                        f"{missing_count} missing value(s). "
                        "A complete answer cannot be guaranteed."
                    )

                # ====================================================
                # TRAP 7 — EMPTY DATA
                # ====================================================

                if len(df) == 0:

                    trap_messages.append(
                        "🚫 The dataset contains no records."
                    )

                # ====================================================
                # TRAP 8 — INVALID / TRICK QUESTION
                # ====================================================

                trick_warnings = (
                    check_trick_question(
                        question,
                        df,
                        requested_currency,
                        column
                    )
                )

                trap_messages.extend(
                    trick_warnings
                )

                # ====================================================
                # DISPLAY TRAPS
                # ====================================================

                if trap_messages:

                    st.markdown(
                        """
                        <div class="refused-card">
                        <div class="refused-title">
                        🚫 RESULT REFUSED
                        </div>
                        <br>
                        ProofDataAI detected one or more
                        reliability traps.
                        <br><br>
                        The system will not guess or
                        provide an unverified answer.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        "### 🛡️ Safety Checks"
                    )

                    for message in trap_messages:

                        st.warning(
                            message
                        )

                    st.markdown(
                        "### 💡 Safe Action"
                    )

                    if (
                        len(currencies) > 1
                        and requested_currency is None
                    ):

                        st.info(
                            "Specify the required currency. "
                            "Example: "
                            "**What is the total amount in INR?**"
                        )

                    elif duplicate_count > 0:

                        st.info(
                            "Remove duplicates or specify "
                            "how duplicate records should "
                            "be handled."
                        )

                    elif date_warnings:

                        st.info(
                            "Clarify whether the date is "
                            "DD/MM/YYYY or MM/DD/YYYY."
                        )

                    else:

                        st.info(
                            "Correct the data or clarify "
                            "the question before calculation."
                        )

                    st.stop()

                # ====================================================
                # SAFE FILTERING
                # ====================================================

                working_df = df.copy()

                if requested_currency:

                    currency_column = (
                        find_currency_column(
                            working_df
                        )
                    )

                    if currency_column:

                        working_df = working_df[
                            working_df[
                                currency_column
                            ]
                            .astype(str)
                            .str.upper()
                            ==
                            requested_currency
                            .upper()
                        ]

                # ====================================================
                # TRICK QUESTION — NO MATCHING RECORDS
                # ====================================================

                if len(working_df) == 0:

                    st.markdown(
                        """
                        <div class="refused-card">
                        <div class="refused-title">
                        🚫 NO VALID ANSWER
                        </div>
                        <br>
                        The requested condition produced
                        zero matching records.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.info(
                        "ProofDataAI refuses to create "
                        "an answer from nonexistent data."
                    )

                    st.stop()

                # ====================================================
                # CALCULATE
                # ====================================================

                try:

                    calculated_result = calculate(
                        working_df,
                        operation,
                        column
                    )

                    # ----------------------------------------------
                    # INDEPENDENT CALCULATION
                    # ----------------------------------------------

                    independent_values = pd.to_numeric(
                        working_df[column],
                        errors="coerce"
                    ).dropna()

                    if len(independent_values) == 0:

                        st.error(
                            "🚫 No valid numerical values."
                        )

                        st.stop()

                    if operation == "sum":

                        independent_result = sum(
                            independent_values.tolist()
                        )

                    elif operation == "average":

                        independent_result = (
                            sum(
                                independent_values.tolist()
                            )
                            /
                            len(
                                independent_values
                            )
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

                        st.error(
                            "🚫 Unsupported operation."
                        )

                        st.stop()

                    # ====================================================
                    # VERIFY
                    # ====================================================

                    verification = verify_result(
                        calculated_result,
                        independent_result
                    )

                    # ====================================================
                    # VERIFIED
                    # ====================================================

                    if verification["verified"]:

                        st.session_state.last_result = (
                            calculated_result
                        )

                        st.session_state.verification = (
                            verification
                        )

                        st.session_state.last_question = (
                            question
                        )

                        # ------------------------------------------
                        # PROOF CODE
                        # ------------------------------------------

                        proof_code = build_proof_code(
                            st.session_state.file_name,
                            column,
                            operation,
                            requested_currency
                        )

                        st.session_state.proof_code = (
                            proof_code
                        )

                        # ------------------------------------------
                        # CERTIFICATE
                        # ------------------------------------------

                        certificate = create_certificate(
                            question=question,
                            result=calculated_result,
                            dataset_name=
                            st.session_state.file_name,
                            operation=operation,
                            rows_used=len(
                                independent_values
                            ),
                            verification_status="VERIFIED"
                        )

                        st.session_state.certificate = (
                            certificate
                        )

                        st.markdown(
                            """
                            <div class="verified-card">
                            <div class="verified-title">
                            ✅ RESULT VERIFIED
                            </div>
                            <br>
                            All safety checks passed.
                            <br>
                            Primary calculation and
                            independent calculation match.
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
                                len(
                                    independent_values
                                )
                            )

                        with r3:

                            st.metric(
                                "Difference",
                                verification[
                                    "difference"
                                ]
                            )

                        st.success(
                            "🏆 Proof generated successfully."
                        )

                    else:

                        st.session_state.last_result = None

                        st.markdown(
                            """
                            <div class="refused-card">
                            <div class="refused-title">
                            🚫 VERIFICATION FAILED
                            </div>
                            <br>
                            The independent calculation
                            does not match the primary result.
                            <br><br>
                            ProofDataAI refuses to provide
                            the answer.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                except Exception as e:

                    st.error(
                        "❌ Calculation failed: "
                        + str(e)
                    )


# ============================================================
# CONTRADICTION CHECK
# ============================================================

elif page == "⚠️ Contradiction Check":

    st.markdown(
        '<div class="section-title">'
        '⚠️ Contradiction Check'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Upload two datasets. ProofDataAI compares "
        "common records and detects conflicting values."
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            "### 📄 Dataset 1"
        )

        file1 = st.file_uploader(
            "Upload first file",
            type=["csv", "xlsx"],
            key="contradiction_file1"
        )

    with col2:

        st.markdown(
            "### 📄 Dataset 2"
        )

        file2 = st.file_uploader(
            "Upload second file",
            type=["csv", "xlsx"],
            key="contradiction_file2"
        )

    if file1 is None or file2 is None:

        st.info(
            "Upload both files to perform "
            "contradiction detection."
        )

    else:

        try:

            df1 = read_file(file1)

            df2 = read_file(file2)

            st.success(
                "✅ Both files uploaded successfully."
            )

            st.markdown(
                "### 👀 Dataset Preview"
            )

            c1, c2 = st.columns(2)

            with c1:

                st.write(
                    "**" + file1.name + "**"
                )

                st.dataframe(
                    df1,
                    use_container_width=True,
                    height=300
                )

            with c2:

                st.write(
                    "**" + file2.name + "**"
                )

                st.dataframe(
                    df2,
                    use_container_width=True,
                    height=300
                )

            # ====================================================
            # FIND COMMON ID
            # ====================================================

            possible_ids = [
                "id",
                "customer_id",
                "order_id",
                "product_id",
                "transaction_id",
                "employee_id",
                "user_id"
            ]

            common_ids = []

            for column in possible_ids:

                if (
                    column in df1.columns
                    and
                    column in df2.columns
                ):

                    common_ids.append(
                        column
                    )

            if not common_ids:

                st.error(
                    "❌ No common ID column found."
                )

                st.info(
                    "Both datasets need a common "
                    "identifier such as customer_id "
                    "or order_id."
                )

            else:

                selected_id = st.selectbox(
                    "🔑 Select record ID",
                    common_ids
                )

                if st.button(
                    "🔍 Check Contradictions",
                    use_container_width=True
                ):

                    contradictions = []

                    ids1 = set(
                        df1[selected_id]
                        .dropna()
                        .astype(str)
                        .str.strip()
                    )

                    ids2 = set(
                        df2[selected_id]
                        .dropna()
                        .astype(str)
                        .str.strip()
                    )

                    common_records = (
                        ids1.intersection(ids2)
                    )

                    common_columns = [
                        column
                        for column in df1.columns
                        if column in df2.columns
                    ]

                    for record_id in common_records:

                        rows1 = df1[
                            df1[selected_id]
                            .astype(str)
                            .str.strip()
                            ==
                            record_id
                        ]

                        rows2 = df2[
                            df2[selected_id]
                            .astype(str)
                            .str.strip()
                            ==
                            record_id
                        ]

                        row1 = rows1.iloc[0]

                        row2 = rows2.iloc[0]

                        for column in common_columns:

                            if column == selected_id:

                                continue

                            value1 = row1[column]

                            value2 = row2[column]

                            if pd.isna(value1):

                                continue

                            if pd.isna(value2):

                                continue

                            value1_text = (
                                str(value1)
                                .strip()
                                .lower()
                            )

                            value2_text = (
                                str(value2)
                                .strip()
                                .lower()
                            )

                            if (
                                value1_text
                                !=
                                value2_text
                            ):

                                contradictions.append(
                                    {
                                        "Record ID":
                                            record_id,
                                        "Field":
                                            column,
                                        file1.name:
                                            value1,
                                        file2.name:
                                            value2
                                    }
                                )

                    # ====================================================
                    # RESULT
                    # ====================================================

                    if len(contradictions) == 0:

                        st.markdown(
                            """
                            <div class="verified-card">
                            <div class="verified-title">
                            ✅ NO CONTRADICTIONS FOUND
                            </div>
                            <br>
                            Common records are consistent
                            across both datasets.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    else:

                        st.markdown(
                            """
                            <div class="refused-card">
                            <div class="refused-title">
                            ❌ CONTRADICTION DETECTED
                            </div>
                            <br>
                            The same record contains
                            conflicting information.
                            <br><br>
                            <b>
                            ProofDataAI refuses to guess
                            which source is correct.
                            </b>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        result_df = pd.DataFrame(
                            contradictions
                        )

                        st.markdown(
                            "### 🔎 Conflicting Records"
                        )

                        st.dataframe(
                            result_df,
                            use_container_width=True,
                            hide_index=True
                        )

                        st.error(
                            f"🚫 {len(contradictions)} "
                            "contradiction(s) detected."
                        )

                        st.markdown(
                            "### 🧠 System Decision"
                        )

                        st.write(
                            "The system will not provide an "
                            "answer based on conflicting sources."
                        )

                        st.write(
                            "**Reason:** "
                            "The same record has different "
                            "values in the uploaded datasets."
                        )

        except Exception as e:

            st.error(
                "❌ Contradiction checking failed: "
                + str(e)
            )


# ============================================================
# PROOF & VERIFICATION
# ============================================================

elif page == "🏆 Proof & Verification":

    st.markdown(
        '<div class="section-title">'
        '🏆 Proof & Verification'
        '</div>',
        unsafe_allow_html=True
    )

    if st.session_state.last_result is None:

        st.info(
            "No verified result available."
        )

        st.write(
            "Go to **🔍 Question Analysis** "
            "and perform a verified calculation."
        )

    else:

        st.markdown(
            """
            <div class="verified-card">
            <div class="verified-title">
            ✅ VERIFIED RESULT
            </div>
            <br>
            The answer passed independent verification.
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

        if st.session_state.last_question:

            st.markdown(
                "### ❓ Question"
            )

            st.write(
                st.session_state.last_question
            )

        st.markdown(
            "### 🔐 Verification"
        )

        if st.session_state.verification:

            verification = (
                st.session_state.verification
            )

            c1, c2 = st.columns(2)

            with c1:

                st.success(
                    "✓ Primary Calculation"
                )

            with c2:

                st.success(
                    "✓ Independent Calculation"
                )

            st.write(
                "**Difference:**",
                verification[
                    "difference"
                ]
            )

        if st.session_state.proof_code:

            st.markdown(
                "### 📜 Reproducible Proof Code"
            )

            st.code(
                st.session_state.proof_code,
                language="python"
            )

        if st.session_state.certificate:

            st.markdown(
                "### 🏆 Proof Certificate"
            )

            st.json(
                st.session_state.certificate
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
    🛡️ ProofDataAI — Every numerical answer must carry proof.
    If proof fails, the system refuses.
    </div>
    """,
    unsafe_allow_html=True
)
