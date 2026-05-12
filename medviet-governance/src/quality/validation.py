# src/quality/validation.py
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite

def build_patient_expectation_suite() -> ExpectationSuite:
    """
    TODO: Tạo expectation suite cho anonymized patient data.
    """
    context = gx.get_context()
    suite = context.add_expectation_suite("patient_data_suite")

    # Lấy validator
    df = pd.read_csv("data/raw/patients_raw.csv")
    validator = context.sources.pandas_default.read_dataframe(df)

    # --- TASK: Thêm các expectations ---

    # 1. patient_id không được null
    validator.expect_column_values_to_not_be_null("patient_id")

    # 2. TODO: cccd phải có đúng 12 ký tự
    validator.expect_column_value_lengths_to_equal(column="cccd", value=12)

    # 3. TODO: ket_qua_xet_nghiem phải trong khoảng [0, 50]
    validator.expect_column_values_to_be_between(
        column="ket_qua_xet_nghiem",
        min_value=0,
        max_value=50
    )

    # 4. TODO: benh phải thuộc danh sách hợp lệ
    valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
    validator.expect_column_values_to_be_in_set(
        column="benh",
        value_set=valid_conditions
    )

    # 5. TODO: email phải match regex pattern
    validator.expect_column_values_to_match_regex(
        column="email",
        regex=r"^[\w\.\+\-]+@[\w\-]+\.[\w\.-]+$"
    )

    # 6. TODO: Không được có duplicate patient_id
    validator.expect_column_values_to_be_unique(column="patient_id")

    validator.save_expectation_suite()
    return suite


def validate_anonymized_data(filepath: str) -> dict:
    """
    TODO: Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: Không còn CCCD gốc dạng số thuần túy
    # (sau anonymization, cccd phải là fake hoặc masked)
    if "cccd" in df.columns:
        raw_cccd_mask = df["cccd"].astype(str).str.fullmatch(r"\d{12}")
        if bool(raw_cccd_mask.any()):
            results["success"] = False
            results["failed_checks"].append("cccd_contains_raw_12_digit_values")

    # Check 2: Không có null values trong các cột quan trọng
    critical_columns = [col for col in ["patient_id", "benh", "ket_qua_xet_nghiem"] if col in df.columns]
    for column in critical_columns:
        if df[column].isna().any():
            results["success"] = False
            results["failed_checks"].append(f"null_values_in_{column}")

    # Check 3: Số rows phải bằng original
    original_path = "data/raw/patients_raw.csv"
    try:
        original_rows = len(pd.read_csv(original_path))
        if len(df) != original_rows:
            results["success"] = False
            results["failed_checks"].append("row_count_mismatch")
    except FileNotFoundError:
        results["success"] = False
        results["failed_checks"].append("missing_original_raw_data")

    return results
