# src/pii/anonymizer.py
import hashlib

import pandas as pd
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        TODO: Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        - "generalize": chỉ dùng cho tuổi/năm sinh
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        def fake_cccd() -> str:
            return "".join(str(fake.random_digit()) for _ in range(12))

        def fake_phone() -> str:
            return f"0{fake.random_element(elements=('3', '5', '7', '8', '9'))}{''.join(str(fake.random_digit()) for _ in range(8))}"

        def apply_manual_replacements(replacement_fn) -> str:
            output = text
            for result in sorted(results, key=lambda item: item.start, reverse=True):
                output = output[:result.start] + replacement_fn(result, output[result.start:result.end]) + output[result.end:]
            return output

        if strategy == "replace":
            replacement_map = {
                "PERSON": fake.name(),
                "EMAIL_ADDRESS": fake.email(),
                "VN_CCCD": fake_cccd(),
                "VN_PHONE": fake_phone(),
            }
            return apply_manual_replacements(
                lambda result, value: replacement_map.get(result.entity_type, value)
            )
        elif strategy == "mask":
            return apply_manual_replacements(
                lambda result, value: value[0] + "*" * max(len(value) - 1, 1)
            )
        elif strategy == "hash":
            return apply_manual_replacements(
                lambda result, value: hashlib.sha256(value.encode("utf-8")).hexdigest()
            )

        return text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        TODO: Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        for column in ["ho_ten", "dia_chi", "email", "bac_si_phu_trach", "ngay_sinh", "ngay_kham"]:
            if column in df_anon.columns:
                df_anon[column] = df_anon[column].astype(str).apply(lambda value: self.anonymize_text(value, strategy="replace"))

        if "cccd" in df_anon.columns:
            df_anon["cccd"] = ["".join(str(fake.random_digit()) for _ in range(12)) for _ in range(len(df_anon))]

        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = [f"0{fake.random_element(elements=('3', '5', '7', '8', '9'))}{''.join(str(fake.random_digit()) for _ in range(8))}" for _ in range(len(df_anon))]

        return df_anon

    def calculate_detection_rate(self, 
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        TODO: Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
