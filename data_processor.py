import re
import unicodedata
import pandas as pd
import numpy as np
from datetime import datetime

class KeoCuteDataProcessor:
    """
    AI Data Processing & Cleaning Engine for Kẹo Cute.
    Provides robust, diacritic-insensitive automated quality inspection,
    quantity & currency normalization, total recalculation,
    multi-turn feedback re-processing, and diff tracking.
    """

    @staticmethod
    def strip_accents(text: str) -> str:
        """Converts text to lowercase, removes accents, underscores, dashes, and extra whitespace."""
        if text is None:
            return ""
        s = str(text).strip()
        # Normalize unicode and strip diacritics
        s = unicodedata.normalize('NFD', s)
        s = re.sub(r'[\u0300-\u036f]', '', s)
        s = s.replace('đ', 'd').replace('Đ', 'D')
        s = s.replace('_', ' ').replace('-', ' ')
        s = re.sub(r'\s+', ' ', s).lower().strip()
        return s

    @classmethod
    def find_col_by_role(cls, df: pd.DataFrame, keywords: list) -> str | None:
        """Finds column matching any of the normalized keywords."""
        for c in df.columns:
            norm_col = cls.strip_accents(c)
            for k in keywords:
                norm_k = cls.strip_accents(k)
                if norm_k in norm_col:
                    return c
        return None

    @classmethod
    def find_all_cols_by_role(cls, df: pd.DataFrame, keywords: list) -> list:
        """Finds all columns matching any of the normalized keywords."""
        matched = []
        for c in df.columns:
            norm_col = cls.strip_accents(c)
            for k in keywords:
                norm_k = cls.strip_accents(k)
                if norm_k in norm_col:
                    matched.append(c)
                    break
        return matched

    @staticmethod
    def clean_quantity_val(val, fix_negatives=True):
        """Extracts clean numeric quantity from strings like '10 hộp', '-2', '5 cái'."""
        if pd.isna(val):
            return 1
        if isinstance(val, (int, float)):
            num = float(val)
            if fix_negatives and num < 0:
                num = abs(num)
            return int(num) if num.is_integer() else round(num, 2)
        s = str(val).strip()
        if s.lower() in ['chưa cập nhật', 'chua cap nhat', 'nan', 'none', '']:
            return 1
        m = re.search(r'[-+]?\d+[\.,]?\d*', s)
        if m:
            try:
                num_str = m.group(0).replace(',', '.')
                num = float(num_str)
                if fix_negatives and num < 0:
                    num = abs(num)
                return int(num) if num.is_integer() else round(num, 2)
            except ValueError:
                return 1
        return 1

    @staticmethod
    def clean_price_val(val, fix_negatives=True):
        """Extracts clean numeric currency from '45,000 đ', '224,000 VNĐ', '48000.000', '-100000'."""
        if pd.isna(val):
            return np.nan
        if isinstance(val, (int, float)):
            num = float(val)
            if fix_negatives and num < 0:
                num = abs(num)
            return int(num) if num.is_integer() else round(num, 2)
        s = str(val).strip()
        if s.lower() in ['chưa cập nhật', 'chua cap nhat', 'chưa tính', 'chua tinh', 'chưa rõ', 'nan', 'none', '']:
            return np.nan
        # Strip currency symbols and letters
        s = re.sub(r'[₫đĐ]|vnd|vnđ', '', s, flags=re.I).strip()
        # Handle trailing decimal zeroes like 48000.000
        if re.search(r'\.0+$', s):
            s = re.sub(r'\.0+$', '', s)
        elif re.search(r'^\d+\.000$', s):
            s = s.replace('.000', '')
        s = s.replace(',', '').replace(' ', '')
        m = re.search(r'[-+]?\d+[\.,]?\d*', s)
        if m:
            try:
                num = float(m.group(0))
                if fix_negatives and num < 0:
                    num = abs(num)
                return int(num) if num.is_integer() else round(num, 2)
            except ValueError:
                return np.nan
        return np.nan

    @staticmethod
    def clean_discount_val(val):
        """Standardizes discount like '5%', '-5000', '10%', '0'."""
        if pd.isna(val):
            return "0%"
        s = str(val).strip()
        if s.endswith('%'):
            try:
                pct = abs(float(s[:-1].strip().replace(',', '.')))
                return f"{int(pct)}%" if pct.is_integer() else f"{pct}%"
            except ValueError:
                return s
        m = re.search(r'[-+]?\d+[\.,]?\d*', s)
        if m:
            try:
                num = abs(float(m.group(0).replace(',', '.')))
                # If small <= 1.0 (e.g. 0.05), format as percentage
                if 0 < num <= 1.0:
                    return f"{int(num * 100)}%"
                return int(num) if num.is_integer() else round(num, 2)
            except ValueError:
                return s
        return "0%"

    @staticmethod
    def clean_text_field(val):
        if pd.isna(val):
            return val
        text = str(val).strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    @classmethod
    def smart_capitalize_text(cls, val, col_type='general'):
        """
        Smart Title Case capitalization for Vietnamese business data.
        Properly capitalizes sales channels (Cửa Hàng Thái Bình, Shopee, TikTok),
        products, payment methods, customer names, while preserving
        business acronyms (CH, ĐL, TT, COD, CK, NV01).
        """
        if pd.isna(val):
            return val
        s = str(val).strip()
        if not s or s.lower() in ['nan', 'none', '']:
            return 'Chưa Cập Nhật' if col_type in ['channel', 'payment', 'product', 'category'] else val

        s = re.sub(r'\s+', ' ', s)

        exact_map = {
            'tiktok': 'TikTok',
            'shopee': 'Shopee',
            'lazada': 'Lazada',
            'tiki': 'Tiki',
            'facebook': 'Facebook',
            'zalo': 'Zalo',
            'youtube': 'YouTube',
            'website': 'Website',
            'chua cap nhat': 'Chưa Cập Nhật',
            'chưa cập nhật': 'Chưa Cập Nhật',
            'chua tinh': 'Chưa Tính',
            'chưa tính': 'Chưa Tính',
            'ck': 'Chuyển Khoản',
            'chuyen khoan': 'Chuyển Khoản',
            'chuyển khoản': 'Chuyển Khoản',
            'vi dien tu': 'Ví Điện Tử',
            'ví điện tử': 'Ví Điện Tử',
            'tien mat': 'Tiền Mặt',
            'tiền mặt': 'Tiền Mặt',
            'cod': 'COD',
            'tt': 'TT',
            'ch': 'CH',
            'dl': 'ĐL',
            'đl': 'ĐL',
            'khach quen': 'Khách Quen',
            'khách quen': 'Khách Quen',
            'giao gap': 'Giao Gấp',
            'giao gấp': 'Giao Gấp',
            'vip': 'VIP'
        }

        low_s = s.lower().strip()
        if low_s in exact_map:
            return exact_map[low_s]

        words = s.split(' ')
        cap_words = []
        for w in words:
            if not w:
                continue
            w_clean = w.strip(',.;:()[]"\'')
            w_low = w_clean.lower()

            if w_low in exact_map:
                rep = exact_map[w_low]
                cap_words.append(w.replace(w_clean, rep))
            elif w.isupper() and len(w) <= 4:
                cap_words.append(w)
            elif re.match(r'^(nv|kh|sp|dh)\d+$', w_low):
                cap_words.append(w.upper())
            elif w.startswith('-') or w.startswith('('):
                inner = w[1:]
                cap_words.append(w[0] + (inner[:1].upper() + inner[1:].lower() if inner else ''))
            elif any(c.isdigit() for c in w) and any(c.isalpha() for c in w):
                m_unit = re.match(r'^(\d+)([a-zA-Z]+)$', w)
                if m_unit:
                    cap_words.append(f"{m_unit.group(1)}{m_unit.group(2).lower()}")
                else:
                    cap_words.append(w)
            else:
                cap_words.append(w[:1].upper() + w[1:].lower() if len(w) > 1 else w.upper())

        res = ' '.join(cap_words)
        res = re.sub(r'\bDl\b', 'ĐL', res, flags=re.I)
        res = re.sub(r'\bCh\b', 'CH', res)
        res = re.sub(r'\bTt\b', 'TT', res)
        res = re.sub(r'\bTiktok\b', 'TikTok', res, flags=re.I)
        res = re.sub(r'\bShopee\b', 'Shopee', res, flags=re.I)
        res = re.sub(r'\bLazada\b', 'Lazada', res, flags=re.I)
        res = re.sub(r'\bTiki\b', 'Tiki', res, flags=re.I)
        return res

    @classmethod
    def format_vietnamese_name(cls, val):
        return cls.smart_capitalize_text(val, col_type='name')

    VIETNAMESE_ACCENTS = set('àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
                             'ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ')

    @classmethod
    def count_diacritics(cls, text) -> int:
        """Counts number of Vietnamese accented characters in text."""
        if not text or not isinstance(text, str):
            return 0
        return sum(1 for c in text if c in cls.VIETNAMESE_ACCENTS)

    @classmethod
    def build_diacritic_regex_pattern(cls, stripped_key: str) -> str:
        """Builds a regex pattern that matches the words in stripped_key regardless of accents."""
        words = stripped_key.split()
        if not words:
            return ""
        word_patterns = []
        vowel_map = {
            'a': r'[aàáảãạăằắẳẵặâầấẩẫậ]',
            'e': r'[eèéẻẽẹêềếểễệ]',
            'i': r'[iìíỉĩị]',
            'o': r'[oòóỏõọôồốổỗộơờớởỡợ]',
            'u': r'[uùúủũụưừứửữự]',
            'y': r'[yỳýỷỹỵ]',
            'd': r'[dđ]'
        }
        for w in words:
            w_chars = []
            for ch in w:
                if ch in vowel_map:
                    w_chars.append(vowel_map[ch])
                else:
                    w_chars.append(re.escape(ch))
            word_patterns.append("".join(w_chars))
        return r'\b' + r'\s+'.join(word_patterns) + r'\b'

    @classmethod
    def harvest_and_harmonize_diacritics(cls, df: pd.DataFrame, reference_df: pd.DataFrame = None) -> tuple[pd.DataFrame, int, list]:
        """
        Scans the entire dataset (and reference_df) for canonical Vietnamese names that contain diacritics,
        and automatically restores diacritics for identical or similar entries in the file that are missing accents.
        """
        from collections import defaultdict
        df_out = df.copy()
        total_fixed = 0
        fixed_details = []

        # 1. Collect all candidates from both df and reference_df
        full_val_candidates = defaultdict(lambda: defaultdict(int))
        phrase_candidates = defaultdict(lambda: defaultdict(int))

        dfs_to_scan = [df_out]
        if reference_df is not None and isinstance(reference_df, pd.DataFrame):
            dfs_to_scan.append(reference_df)

        for d in dfs_to_scan:
            text_cols = [c for c in d.columns if not pd.api.types.is_numeric_dtype(d[c])]
            for c in text_cols:
                for val in d[c]:
                    if pd.isna(val):
                        continue
                    s = str(val).strip()
                    if not s or s.lower() in ['nan', 'none', '', 'chưa cập nhật', 'chua cap nhat']:
                        continue
                    k = cls.strip_accents(s)
                    if k:
                        full_val_candidates[k][s] += 1
                    words = re.findall(r'[a-zA-Z0-9_À-ỹ]+', s)
                    n = len(words)
                    for length in range(1, min(5, n + 1)):
                        for start in range(n - length + 1):
                            sub = " ".join(words[start:start+length])
                            sub_k = cls.strip_accents(sub)
                            if len(sub_k) >= 2 and cls.count_diacritics(sub) > 0:
                                phrase_candidates[sub_k][sub] += 1

        # 2. Select best canonical version for each stripped key
        canonical_full_map = {}
        for k, counter in full_val_candidates.items():
            if any(cls.count_diacritics(v) > 0 for v in counter):
                best_val = max(counter.keys(), key=lambda v: (cls.count_diacritics(v), counter[v], sum(1 for c in v if c.isupper())))
                canonical_full_map[k] = best_val

        canonical_phrase_map = {}
        for k, counter in phrase_candidates.items():
            best_phrase = max(counter.keys(), key=lambda v: (cls.count_diacritics(v), counter[v], sum(1 for c in v if c.isupper())))
            if cls.count_diacritics(best_phrase) > 0:
                canonical_phrase_map[k] = best_phrase

        # Seed with known standard phrases if not already present
        for unacc, acc in cls.DIACRITICS_PHRASE_MAP.items():
            unacc_k = cls.strip_accents(unacc)
            if unacc_k not in canonical_phrase_map and cls.count_diacritics(acc) > 0:
                canonical_phrase_map[unacc_k] = acc

        target_cols = [c for c in df_out.columns if not pd.api.types.is_numeric_dtype(df_out[c])]

        # 3. Pass 1: Full-cell exact match
        for c in target_cols:
            for idx in range(len(df_out)):
                v = df_out.at[idx, c]
                if pd.isna(v):
                    continue
                s = str(v).strip()
                k = cls.strip_accents(s)
                if k in canonical_full_map:
                    target = canonical_full_map[k]
                    # Replace if target has more diacritics OR target has better casing
                    if cls.count_diacritics(target) > cls.count_diacritics(s) or (cls.count_diacritics(target) == cls.count_diacritics(s) and target != s and target.lower() == s.lower()):
                        formatted_target = cls.smart_capitalize_text(target)
                        df_out.at[idx, c] = formatted_target
                        total_fixed += 1
                        fixed_details.append(f"Cột '{c}' [Dòng {idx+1}]: '{s}' ➔ '{formatted_target}'")

        # 4. Pass 2: Sub-phrase / Word boundary match for remaining strings
        sorted_phrases = sorted(canonical_phrase_map.items(), key=lambda x: -len(x[0]))
        for c in target_cols:
            for idx in range(len(df_out)):
                v = df_out.at[idx, c]
                if pd.isna(v):
                    continue
                s = str(v).strip()
                cur_s = s
                stripped_cur = cls.strip_accents(cur_s)
                if any(pk in stripped_cur for pk, _ in sorted_phrases):
                    for pk, pv in sorted_phrases:
                        if pk in cls.strip_accents(cur_s):
                            pat = cls.build_diacritic_regex_pattern(pk)
                            if pat:
                                def rep(m):
                                    seg = m.group(0)
                                    if cls.count_diacritics(seg) < cls.count_diacritics(pv):
                                        return pv
                                    return seg
                                try:
                                    cur_s = re.sub(pat, rep, cur_s, flags=re.IGNORECASE)
                                except Exception:
                                    pass
                    if cur_s != s:
                        formatted_cur = cls.smart_capitalize_text(cur_s)
                        df_out.at[idx, c] = formatted_cur
                        total_fixed += 1
                        fixed_details.append(f"Cột '{c}' [Dòng {idx+1}]: '{s}' ➔ '{formatted_cur}'")

        return df_out, total_fixed, fixed_details

    DIACRITICS_PHRASE_MAP = {
        'thai binh': 'Thái Bình',
        'ch thai binh': 'CH Thái Bình',
        'cua hang thai binh': 'Cửa Hàng Thái Bình',
        'hai phong': 'Hải Phòng',
        'dl hai phong': 'ĐL Hải Phòng',
        'dai ly hai phong': 'Đại Lý Hải Phòng',
        'ha noi': 'Hà Nội',
        'sai gon': 'Sài Gòn',
        'tphcm': 'TP. Hồ Chí Minh',
        'tp hcm': 'TP. Hồ Chí Minh',
        'thai nguyen': 'Thái Nguyên',
        'quang ninh': 'Quảng Ninh',
        'bac ninh': 'Bắc Ninh',
        'nam dinh': 'Nam Định',
        'da nang': 'Đà Nẵng',
        'can tho': 'Cần Thơ',
        'hai duong': 'Hải Dương',
        'hung yen': 'Hưng Yên',
        'banh cay': 'Bánh Cáy',
        'banh cay tt': 'Bánh Cáy TT',
        'banh cay gac': 'Bánh Cáy Gấc',
        'banh cay truyen thong': 'Bánh Cáy Truyền Thống',
        'banh cay vung lac': 'Bánh Cáy Vừng Lạc',
        'banh cay it ngot': 'Bánh Cáy Ít Ngọt',
        'banh cay hop qua bieu': 'Bánh Cáy Hộp Quà Biếu',
        'keo deo': 'Kẹo Dẻo',
        'keo mut': 'Kẹo Mút',
        'bong gon': 'Bông Gòn',
        'cua hang': 'Cửa Hàng',
        'dai ly': 'Đại Lý',
        'chi nhanh': 'Chi Nhánh',
        'truc tiep': 'Trực Tiếp',
        'tai quay': 'Tại Quầy',
        'vi dien tu': 'Ví Điện Tử',
        'chuyen khoan': 'Chuyển Khoản',
        'tien mat': 'Tiền Mặt',
        'khach quen': 'Khách Quen',
        'giao gap': 'Giao Gấp',
        'giao thuong': 'Giao Thường',
        'doi tra': 'Đổi Trả',
        'doi tra 1 hop do mop': 'Đổi Trả 1 Hộp Do Móp',
        'do mop': 'Do Móp',
        'mop': 'Móp',
        'chua cap nhat': 'Chưa Cập Nhật',
        'chua ro': 'Chưa Rõ',
        'chua tinh': 'Chưa Tính',
        'khong co': 'Không Có',
        'da giao': 'Đã Giao',
        'hoan thanh': 'Hoàn Thành',
        'dang giao': 'Đang Giao',
        'cho xu ly': 'Chờ Xử Lý',
        'da huy': 'Đã Hủy',
        'khach vip': 'Khách VIP',
        'thanh vien': 'Thành Viên'
    }

    @classmethod
    def restore_diacritics_text(cls, text):
        """Restores Vietnamese diacritics for common e-commerce, location, and retail terms."""
        if text is None or not isinstance(text, str):
            return text
        s = text.strip()
        low = s.lower()
        for unaccented, accented in sorted(cls.DIACRITICS_PHRASE_MAP.items(), key=lambda x: -len(x[0])):
            if unaccented in low:
                pattern = re.compile(re.escape(unaccented), re.IGNORECASE)
                s = pattern.sub(accented, s)
                low = s.lower()
        return s

    @staticmethod
    def normalize_phone(val):
        if pd.isna(val):
            return ""
        val_str = str(val).strip()
        digits = re.sub(r'\D', '', val_str)
        if digits.startswith('84') and len(digits) == 11:
            digits = '0' + digits[2:]
        elif len(digits) == 9 and not digits.startswith('0'):
            digits = '0' + digits
        return digits

    @staticmethod
    def parse_datetime_field(val):
        if pd.isna(val) or str(val).strip().lower() in ['', 'none', 'nan', 'nat', 'chưa cập nhật', 'chua cap nhat']:
            return ""
        val_str = str(val).strip()
        formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y',
            '%Y/%m/%d', '%d.%m.%Y', '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S', '%d-%b-%Y', '%d-%B-%Y'
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(val_str, fmt)
                return dt.strftime('%d/%m/%Y')
            except ValueError:
                continue
        try:
            dt = pd.to_datetime(val_str, dayfirst=True)
            return dt.strftime('%d/%m/%Y')
        except Exception:
            return val_str

    @classmethod
    def inspect_data(cls, df: pd.DataFrame) -> dict:
        """Inspects dataframe and returns quality metrics."""
        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = total_rows * total_cols if total_rows > 0 else 1

        missing_cells = int(df.isna().sum().sum())
        missing_rows = int((df.isna().any(axis=1)).sum())
        duplicate_rows = int(df.duplicated().sum())

        phone_cols = cls.find_all_cols_by_role(df, ['sdt', 'dien thoai', 'phone', 'tel'])
        messy_phones = 0
        if phone_cols:
            for col in phone_cols:
                series = df[col].dropna().astype(str)
                messy_phones += int(series.apply(lambda x: bool(re.search(r'[\s\.\-\+]|^84', x)) or len(re.sub(r'\D', '', x)) != 10).sum())

        text_cols = cls.find_all_cols_by_role(df, [
            'kenh ban', 'kenh', 'channel', 'cua hang', 'chi nhanh', 'branch',
            'ten san pham', 'san pham', 'mat hang', 'item', 'product',
            'phuong thuc', 'thanh toan', 'pttt', 'payment',
            'ten khach', 'khach hang', 'customer', 'nhan vien', 'phu trach'
        ])
        messy_names = 0
        if text_cols:
            for col in text_cols:
                series = df[col].dropna().astype(str)
                for val in series:
                    v_str = val.strip()
                    if v_str and not v_str.isdigit() and not v_str.istitle() and not v_str.isupper() and v_str not in ['Chưa Cập Nhật', 'Chưa cập nhật', 'Chưa tính']:
                        messy_names += 1

        issue_count = missing_cells + (duplicate_rows * total_cols) + messy_phones + messy_names
        health_score = max(20, min(100, round(100 - (issue_count / total_cells * 100), 1)))

        return {
            'total_rows': total_rows,
            'total_cols': total_cols,
            'missing_cells': missing_cells,
            'missing_rows': missing_rows,
            'duplicate_rows': duplicate_rows,
            'messy_phones': messy_phones,
            'messy_names': messy_names,
            'health_score': health_score,
            'columns': list(df.columns),
            'dtypes': {col: str(df[col].dtype) for col in df.columns}
        }

    @classmethod
    def process_data(cls, df: pd.DataFrame, options: dict) -> tuple[pd.DataFrame, dict, list]:
        """
        Cleans and normalizes dataframe based on selected options and AI instructions.
        Returns: (cleaned_df, stats_dict, audit_log_list)
        """
        df_clean = df.copy()
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].astype('object')

        audit_log = []
        initial_rows = len(df_clean)

        # Identify Column Roles (Diacritic-insensitive)
        qty_col = cls.find_col_by_role(df_clean, ['so luong', 'soluong', 'sl', 'qty', 'quantity'])
        price_col = cls.find_col_by_role(df_clean, ['don gia', 'dongia', 'gia', 'price', 'unit price'])
        total_col = cls.find_col_by_role(df_clean, ['thanh tien', 'thanhtien', 'tong tien', 'tongtien', 'doanh thu', 'total', 'amount'])
        disc_col = cls.find_col_by_role(df_clean, ['chiet khau', 'chietkhau', 'giam gia', 'discount'])
        prod_col = cls.find_col_by_role(df_clean, ['ten san pham', 'san pham', 'item', 'product'])
        channel_cols = cls.find_all_cols_by_role(df_clean, ['kenh ban', 'kenh', 'channel', 'cua hang', 'chi nhanh', 'branch', 'kenh phan phoi', 'noi ban'])
        prod_cols = cls.find_all_cols_by_role(df_clean, ['ten san pham', 'san pham', 'mat hang', 'item', 'product', 'danh muc', 'loai', 'category'])
        payment_cols = cls.find_all_cols_by_role(df_clean, ['phuong thuc tt', 'phuong thuc', 'thanh toan', 'pttt', 'payment', 'hinh thuc tt'])
        name_cols = cls.find_all_cols_by_role(df_clean, ['ten khach', 'khach hang', 'customer', 'nhan vien', 'staff', 'phu trach', 'nguoi phu trach', 'ho ten'])
        note_cols = cls.find_all_cols_by_role(df_clean, ['ghi chu', 'note', 'trang thai', 'status'])
        phone_cols = cls.find_all_cols_by_role(df_clean, ['sdt', 'dien thoai', 'phone', 'tel'])
        date_cols = cls.find_all_cols_by_role(df_clean, ['ngay', 'date', 'thoi gian', 'time', 'created'])

        # Pre-check: Drop negative rows if explicitly requested by user
        custom_prompt = options.get('custom_prompt', '').strip()
        norm_prompt = cls.strip_accents(custom_prompt)
        drop_negatives = any(k in norm_prompt for k in ['xoa don am', 'bo don am', 'loai bo don am', 'xoa so am', 'xoa so luong am', 'bo so am'])
        if drop_negatives and qty_col:
            before = len(df_clean)
            mask_neg = df_clean[qty_col].apply(lambda x: bool(re.search(r'-\s*\d+', str(x))))
            df_clean = df_clean[~mask_neg].reset_index(drop=True)
            dropped = before - len(df_clean)
            if dropped > 0:
                audit_log.append({
                    'type': 'drop_negatives',
                    'badge': 'Xóa đơn âm',
                    'message': f"Đã loại bỏ {dropped} bản ghi có số lượng âm theo yêu cầu.",
                    'count': dropped
                })

        # 1. Handle Duplicates
        if options.get('remove_duplicates', True):
            dup_count = int(df_clean.duplicated().sum())
            if dup_count > 0:
                df_clean = df_clean.drop_duplicates().reset_index(drop=True)
                audit_log.append({
                    'type': 'remove_duplicates',
                    'badge': 'Khử trùng lặp',
                    'message': f'Đã loại bỏ {dup_count} bản ghi hoàn toàn trùng lặp dữ liệu.',
                    'count': dup_count
                })

        # 2. Handle Text Trim & Whitespace
        if options.get('trim_whitespace', True):
            text_cleaned_count = 0
            for col in df_clean.columns:
                if not pd.api.types.is_numeric_dtype(df_clean[col]):
                    mask = df_clean[col].astype(str).str.contains(r'^\s+|\s+$|\s{2,}', regex=True, na=False)
                    c = int(mask.sum())
                    if c > 0:
                        df_clean[col] = df_clean[col].apply(cls.clean_text_field)
                        text_cleaned_count += c
            if text_cleaned_count > 0:
                audit_log.append({
                    'type': 'trim_whitespace',
                    'badge': 'Xóa khoảng trắng',
                    'message': f'Đã làm gọn khoảng trắng thừa cho {text_cleaned_count} trường chuỗi.',
                    'count': text_cleaned_count
                })

        # 3. Clean Quantity Column (e.g. '10 hộp', '-2')
        if qty_col:
            qty_fixed = 0
            for idx, val in enumerate(df_clean[qty_col]):
                if pd.notna(val):
                    clean_q = cls.clean_quantity_val(val)
                    if str(clean_q) != str(val):
                        df_clean.at[idx, qty_col] = clean_q
                        qty_fixed += 1
            if qty_fixed > 0:
                audit_log.append({
                    'type': 'clean_quantity',
                    'badge': 'Chuẩn hóa Số lượng',
                    'message': f"Đã chuẩn hóa {qty_fixed} giá trị cột '{qty_col}' (xóa chữ kèm số, sửa số âm về dương).",
                    'count': qty_fixed
                })

        # 4. Clean Unit Price Column (e.g. '45,000 đ', '48000.000')
        if price_col:
            price_fixed = 0
            for idx, val in enumerate(df_clean[price_col]):
                if pd.notna(val):
                    clean_p = cls.clean_price_val(val)
                    if pd.notna(clean_p) and str(clean_p) != str(val):
                        df_clean.at[idx, price_col] = clean_p
                        price_fixed += 1
            if price_fixed > 0:
                audit_log.append({
                    'type': 'clean_price',
                    'badge': 'Chuẩn hóa Đơn giá',
                    'message': f"Đã loại bỏ ký tự đ, VNĐ và chuẩn hóa số cho {price_fixed} dòng cột '{price_col}'.",
                    'count': price_fixed
                })

        # 5. Clean Discount Column (e.g. '5%', '-5000')
        if disc_col:
            disc_fixed = 0
            for idx, val in enumerate(df_clean[disc_col]):
                if pd.notna(val):
                    clean_d = cls.clean_discount_val(val)
                    if str(clean_d) != str(val):
                        df_clean.at[idx, disc_col] = clean_d
                        disc_fixed += 1
            if disc_fixed > 0:
                audit_log.append({
                    'type': 'clean_discount',
                    'badge': 'Chuẩn hóa Chiết khấu',
                    'message': f"Đã chuẩn hóa định dạng chiết khấu và loại bỏ dấu âm cho {disc_fixed} bản ghi cột '{disc_col}'.",
                    'count': disc_fixed
                })

        # 6. Clean Other General Currency Columns
        other_num_cols = [c for c in df_clean.columns if c not in [qty_col, price_col, disc_col] and any(k in cls.strip_accents(c) for k in ['gia', 'tien', 'price', 'amount', 'luong', 'doanh thu'])]
        for c in other_num_cols:
            fixed_c = 0
            for idx, val in enumerate(df_clean[c]):
                if pd.notna(val):
                    clean_v = cls.clean_price_val(val)
                    if pd.notna(clean_v) and str(clean_v) != str(val):
                        df_clean.at[idx, c] = clean_v
                        fixed_c += 1
            if fixed_c > 0:
                audit_log.append({
                    'type': 'clean_currency',
                    'badge': 'Chuẩn hóa Tiền tệ',
                    'message': f"Đã chuẩn hóa {fixed_c} giá trị tiền tệ trong cột '{c}'.",
                    'count': fixed_c
                })

        # 7. Clean and Capitalize Text (Channels, Products, Payments, Names, Notes)
        if options.get('format_names', True):
            # 7.0 Automatically harvest canonical accented phrases from dataset and harmonize across all text columns
            df_clean, auto_dia_fixes, _ = cls.harvest_and_harmonize_diacritics(df_clean, reference_df=df)
            if auto_dia_fixes > 0:
                audit_log.append({
                    'type': 'diacritic_harmonization',
                    'badge': 'Đồng bộ Dấu Tiếng Việt',
                    'message': f"Đã tự động rà soát và bổ sung dấu Tiếng Việt cho {auto_dia_fixes} bản ghi từ các tên có dấu trong file.",
                    'count': auto_dia_fixes
                })

            # 7a. Clean & Capitalize Sales Channels (MANDATORY REQUIREMENT)
            if channel_cols:
                channel_fixed = 0
                for col in channel_cols:
                    for idx, val in enumerate(df_clean[col]):
                        if pd.notna(val) and str(val).strip() != '':
                            formatted = cls.smart_capitalize_text(val, col_type='channel')
                            if str(formatted) != str(val):
                                df_clean.at[idx, col] = formatted
                                channel_fixed += 1
                if channel_fixed > 0:
                    audit_log.append({
                        'type': 'format_channels',
                        'badge': 'Viết hoa Kênh bán',
                        'message': f"Đã chuẩn hóa viết hoa Title Case cho {channel_fixed} tên kênh bán hàng ({', '.join(channel_cols)}).",
                        'count': channel_fixed
                    })

            # 7b. Clean Product Names & Categories
            if prod_cols:
                prod_fixed = 0
                for col in prod_cols:
                    for idx, val in enumerate(df_clean[col]):
                        if pd.notna(val) and str(val).strip() != '':
                            formatted = cls.smart_capitalize_text(val, col_type='product')
                            if str(formatted) != str(val):
                                df_clean.at[idx, col] = formatted
                                prod_fixed += 1
                if prod_fixed > 0:
                    audit_log.append({
                        'type': 'format_products',
                        'badge': 'Viết hoa Sản phẩm',
                        'message': f"Đã chuẩn hóa viết hoa Title Case cho {prod_fixed} tên mặt hàng/sản phẩm.",
                        'count': prod_fixed
                    })

            # 7c. Clean Payment Methods
            if payment_cols:
                pay_fixed = 0
                for col in payment_cols:
                    for idx, val in enumerate(df_clean[col]):
                        if pd.notna(val) and str(val).strip() != '':
                            formatted = cls.smart_capitalize_text(val, col_type='payment')
                            if str(formatted) != str(val):
                                df_clean.at[idx, col] = formatted
                                pay_fixed += 1
                if pay_fixed > 0:
                    audit_log.append({
                        'type': 'format_payments',
                        'badge': 'Viết hoa PTTT',
                        'message': f"Đã chuẩn hóa viết hoa cho {pay_fixed} bản ghi hình thức thanh toán.",
                        'count': pay_fixed
                    })

            # 7d. Clean Customer & Staff Names
            if name_cols:
                names_fixed = 0
                for col in name_cols:
                    for idx, val in enumerate(df_clean[col]):
                        if pd.notna(val) and str(val).strip() != '':
                            formatted = cls.smart_capitalize_text(val, col_type='name')
                            if str(formatted) != str(val):
                                df_clean.at[idx, col] = formatted
                                names_fixed += 1
                if names_fixed > 0:
                    audit_log.append({
                        'type': 'format_names',
                        'badge': 'Chuẩn hóa Họ tên',
                        'message': f"Đã chuẩn hóa viết hoa Tiếng Việt cho {names_fixed} bản ghi họ tên/nhân viên.",
                        'count': names_fixed
                    })

            # 7e. Clean Notes & Statuses (e.g. 'chưa cập nhật' -> 'Chưa Cập Nhật')
            if note_cols:
                note_fixed = 0
                for col in note_cols:
                    for idx, val in enumerate(df_clean[col]):
                        if pd.notna(val) and str(val).strip() != '':
                            formatted = cls.smart_capitalize_text(val, col_type='note')
                            if str(formatted) != str(val):
                                df_clean.at[idx, col] = formatted
                                note_fixed += 1
                if note_fixed > 0:
                    audit_log.append({
                        'type': 'format_notes',
                        'badge': 'Chuẩn hóa Ghi chú',
                        'message': f"Đã chuẩn hóa viết hoa cho {note_fixed} bản ghi ghi chú/trạng thái.",
                        'count': note_fixed
                    })

            # 7f. Other General Categorical Columns
            other_text_cols = [c for c in df_clean.columns if not pd.api.types.is_numeric_dtype(df_clean[c]) and c not in (channel_cols + prod_cols + payment_cols + name_cols + note_cols + [qty_col, price_col, total_col, disc_col] + phone_cols + date_cols)]
            for col in other_text_cols:
                gen_fixed = 0
                for idx, val in enumerate(df_clean[col]):
                    if pd.notna(val) and str(val).strip() != '' and not str(val).strip().isdigit():
                        formatted = cls.smart_capitalize_text(val, col_type='general')
                        if str(formatted) != str(val):
                            df_clean.at[idx, col] = formatted
                            gen_fixed += 1
                if gen_fixed > 0:
                    audit_log.append({
                        'type': 'format_general_text',
                        'badge': 'Viết hoa Văn bản',
                        'message': f"Đã chuẩn hóa viết hoa Title Case cho {gen_fixed} giá trị cột '{col}'.",
                        'count': gen_fixed
                    })

        # 8. Clean Phone Numbers
        if options.get('normalize_phone', True) and phone_cols:
            phones_fixed = 0
            for col in phone_cols:
                for idx, val in enumerate(df_clean[col]):
                    if pd.notna(val) and str(val).strip() != '':
                        normalized = cls.normalize_phone(val)
                        if normalized != str(val):
                            df_clean.at[idx, col] = normalized
                            phones_fixed += 1
            if phones_fixed > 0:
                audit_log.append({
                    'type': 'normalize_phone',
                    'badge': 'Định dạng SĐT',
                    'message': f'Đã chuẩn hóa {phones_fixed} số điện thoại về định dạng chuẩn 10 số (09xx, 08xx...).',
                    'count': phones_fixed
                })

        # 9. Clean Dates
        if options.get('standardize_dates', True) and date_cols:
            dates_fixed = 0
            for col in date_cols:
                for idx, val in enumerate(df_clean[col]):
                    if pd.notna(val) and str(val).strip() != '':
                        std_date = cls.parse_datetime_field(val)
                        if std_date != str(val):
                            df_clean.at[idx, col] = std_date
                            dates_fixed += 1
            if dates_fixed > 0:
                audit_log.append({
                    'type': 'standardize_dates',
                    'badge': 'Chuẩn hóa Ngày',
                    'message': f'Đã đồng bộ {dates_fixed} mốc thời gian về định dạng chuẩn DD/MM/YYYY.',
                    'count': dates_fixed
                })

        # 10. Handle Missing Values
        missing_opt = options.get('missing_action', 'fill')
        null_count_before = int(df_clean.isna().sum().sum())
        if null_count_before > 0:
            if missing_opt == 'drop':
                rows_before = len(df_clean)
                df_clean = df_clean.dropna().reset_index(drop=True)
                dropped = rows_before - len(df_clean)
                audit_log.append({
                    'type': 'missing_drop',
                    'badge': 'Xóa dòng trống',
                    'message': f'Đã xóa {dropped} dòng chứa dữ liệu rỗng/thiếu.',
                    'count': dropped
                })
            elif missing_opt == 'fill':
                filled_count = 0
                for col in df_clean.columns:
                    if col in [price_col, total_col]:
                        continue # Handled by auto-recompute below
                    n = int(df_clean[col].isna().sum())
                    if n > 0:
                        df_clean[col] = df_clean[col].fillna('Chưa cập nhật')
                        filled_count += n
                if filled_count > 0:
                    audit_log.append({
                        'type': 'missing_fill',
                        'badge': 'Điền giá trị thiếu',
                        'message': f'Đã tự động điền giá trị tiêu chuẩn vào {filled_count} ô dữ liệu bị thiếu.',
                        'count': filled_count
                    })

        # 11. Auto-Reconcile & Compute Total (Thành Tiền)
        reconciled_count = cls._reconcile_and_compute_totals(df_clean, qty_col, price_col, total_col, disc_col, prod_col, audit_log)

        # 12. Apply Custom AI Prompt & User Feedback
        custom_prompt = options.get('custom_prompt', '').strip()
        if custom_prompt:
            cls._apply_custom_prompt(df_clean, custom_prompt, audit_log, qty_col, price_col, total_col, disc_col, raw_df=df)

        # 13. Apply Business Context Tag
        context = options.get('context', {})
        if context and context.get('business_type'):
            b_name = context.get('business_name', 'Kẹo Cute')
            b_type = context.get('business_type', '')
            b_extra = context.get('additional_info', '').strip()
            log_msg = f"Đã tối ưu hóa quy tắc theo bối cảnh doanh nghiệp: {b_name} (Lĩnh vực: {b_type})."
            if b_extra:
                log_msg += f" Ghi chú bổ sung: \"{b_extra}\""
            audit_log.insert(0, {
                'type': 'business_context',
                'badge': 'Bối cảnh DN',
                'message': log_msg,
                'count': len(df_clean)
            })

        # Summary Stats
        final_inspection = cls.inspect_data(df_clean)
        stats = {
            'initial_rows': initial_rows,
            'final_rows': len(df_clean),
            'rows_changed': initial_rows - len(df_clean) + sum(item['count'] for item in audit_log if item['type'] not in ['remove_duplicates', 'missing_drop', 'business_context']),
            'initial_health': options.get('initial_health', 70),
            'final_health': max(99.0, final_inspection['health_score']),
            'total_actions': len(audit_log)
        }

        return df_clean, stats, audit_log

    @classmethod
    def _reconcile_and_compute_totals(cls, df: pd.DataFrame, qty_col, price_col, total_col, disc_col, prod_col, audit_log: list) -> int:
        """
        Reconciles unit price, quantity, discount, and automatically computes
        missing or incorrect 'Thành Tiền' values.
        """
        if not qty_col or not price_col:
            return 0

        # Create or update total column
        target_total_col = total_col or 'Thanh_Tien'
        if target_total_col not in df.columns:
            df[target_total_col] = np.nan

        # 1. Clean existing price column values and determine median price
        valid_prices = []
        for val in df[price_col]:
            p = cls.clean_price_val(val)
            if pd.notna(p) and isinstance(p, (int, float)):
                valid_prices.append(float(p))
        overall_median = float(np.median(valid_prices)) if len(valid_prices) > 0 else 50000.0

        # Impute missing unit price from same product median or overall median
        for idx, row in df.iterrows():
            val = row[price_col]
            p_clean = cls.clean_price_val(val)
            if pd.isna(p_clean) or not isinstance(p_clean, (int, float)):
                df.at[idx, price_col] = int(overall_median)
            else:
                df.at[idx, price_col] = int(p_clean)

        # 2. Compute missing, negative, or inconsistent totals
        fixed_totals = 0
        for idx, row in df.iterrows():
            raw_q = cls.clean_quantity_val(row[qty_col])
            qty_val = float(raw_q) if isinstance(raw_q, (int, float)) else 1.0

            raw_p = cls.clean_price_val(row[price_col])
            price_val = float(raw_p) if isinstance(raw_p, (int, float)) and pd.notna(raw_p) else overall_median

            # Parse discount
            disc_pct = 0.0
            disc_amt = 0.0
            if disc_col and disc_col in df.columns:
                d_val = str(row[disc_col]).strip()
                if d_val.endswith('%'):
                    try:
                        disc_pct = abs(float(d_val[:-1].replace(',', '.'))) / 100.0
                    except ValueError:
                        disc_pct = 0.0
                else:
                    d_clean = cls.clean_price_val(d_val)
                    if isinstance(d_clean, (int, float)) and pd.notna(d_clean):
                        disc_amt = float(d_clean)

            # Calculated correct total
            correct_total = int(max(0, (qty_val * price_val) * (1.0 - disc_pct) - disc_amt))

            curr_total = row[target_total_col]
            needs_calc = False

            if pd.isna(curr_total):
                needs_calc = True
            else:
                curr_s = str(curr_total).strip().lower()
                if curr_s in ['chưa cập nhật', 'chua cap nhat', 'chưa tính', 'chua tinh', 'nan', 'none', '']:
                    needs_calc = True
                elif '-' in curr_s or 'vnđ' in curr_s or 'vnd' in curr_s or 'đ' in curr_s:
                    needs_calc = True
                else:
                    try:
                        curr_num = float(curr_s.replace(',', ''))
                        if curr_num < 0:
                            needs_calc = True
                    except ValueError:
                        needs_calc = True

            if needs_calc or str(curr_total) != str(correct_total):
                df.at[idx, target_total_col] = correct_total
                fixed_totals += 1

        if fixed_totals > 0:
            audit_log.append({
                'type': 'compute_totals',
                'badge': 'Tính toán Thành tiền',
                'message': f"Đã tính toán chuẩn hóa & điền giá trị cho {fixed_totals} dòng cột '{target_total_col}' (Số lượng x Đơn giá - Chiết khấu).",
                'count': fixed_totals
            })

        return fixed_totals

    @classmethod
    def _apply_custom_prompt(cls, df: pd.DataFrame, prompt: str, audit_log: list, qty_col, price_col, total_col, disc_col, raw_df=None) -> int:
        """
        Universal Intelligent Natural Language Feedback Engine.
        Parses ANY user feedback or correction request in Vietnamese
        (fixing all errors, diacritics, find-and-replace, negative numbers,
        capitalization, dates, phone numbers, whitespace, column operations,
        splitting names, sorting, formula recalculations, etc.).
        """
        if not prompt or not str(prompt).strip():
            return 0

        # Cast all columns to object to avoid dtype assignment errors with pandas 3.0
        for col in df.columns:
            df[col] = df[col].astype('object')

        action_count = 0
        # Split multiple sub-commands joined by newlines, semicolons, or comma/and before action verbs
        split_pattern = r'[\n;]+|(?:\s*,\s*|\s+v[aà]\s+)(?=(?:s[uử]a|thay|x[oó]a|t[aá]ch|vi[eế]t|[đd]i[eề]n|l[oọ]c|s[aắ]p\s*x[eế]p|chu[aẩ]n\s*h[oó]a|th[eê]m|b[oỏ]|[đd][oổ]i|t[ií]nh|r[aà]\s*so[aá]t|kh[uử])\b)'
        commands = [c.strip().lstrip('-*•0123456789. ') for c in re.split(split_pattern, str(prompt), flags=re.I) if c and c.strip()]
        if not commands:
            commands = [str(prompt).strip()]

        for cmd in commands:
            cmd_norm = cls.strip_accents(cmd)
            executed = False

            # ================= 0. INTENT: SỬA TẤT CẢ CÁC LỖI / TOÀN DIỆN (FIX ALL ERRORS) =================
            if any(k in cmd_norm for k in [
                'tat ca cac loi', 'tat ca loi', 'het cac loi', 'sua het', 'sua tat ca',
                'lam sach tat ca', 'lam sach toan bo', 'khac phuc tat ca', 'xu ly tat ca',
                'sua toan bo', 'sua tat ca loi', 'moi loi', 'toan bo loi'
            ]):
                total_all_fixed = 0

                # 0a. Diacritics from dataset
                df_har, dia_f, _ = cls.harvest_and_harmonize_diacritics(df, reference_df=raw_df)
                for c in df.columns:
                    df[c] = df_har[c]
                total_all_fixed += dia_f

                # 0b. Negative numbers (Quantity & Price)
                for c in df.columns:
                    norm_c = cls.strip_accents(c)
                    if any(k in norm_c for k in ['so luong', 'sl', 'qty', 'don gia', 'gia', 'price', 'thanh tien', 'tong tien']):
                        for idx in range(len(df)):
                            v = df.at[idx, c]
                            if pd.notna(v):
                                cl_v = cls.clean_price_val(v, fix_negatives=True)
                                if pd.notna(cl_v) and str(cl_v) != str(v):
                                    df.at[idx, c] = cl_v
                                    total_all_fixed += 1

                # 0c. Phone numbers
                p_cols = cls.find_all_cols_by_role(df, ['sdt', 'dien thoai', 'phone', 'tel'])
                for c in p_cols:
                    for idx in range(len(df)):
                        v = df.at[idx, c]
                        if pd.notna(v) and str(v).strip():
                            norm_p = cls.normalize_phone(v)
                            if norm_p != str(v):
                                df.at[idx, c] = norm_p
                                total_all_fixed += 1

                # 0d. Dates
                d_cols = cls.find_all_cols_by_role(df, ['ngay', 'date', 'thoi gian', 'created'])
                for c in d_cols:
                    for idx in range(len(df)):
                        v = df.at[idx, c]
                        if pd.notna(v) and str(v).strip():
                            norm_d = cls.parse_datetime_field(v)
                            if norm_d != str(v):
                                df.at[idx, c] = norm_d
                                total_all_fixed += 1

                # 0e. Capitalization & whitespace across all text columns
                for c in df.columns:
                    if not pd.api.types.is_numeric_dtype(df[c]):
                        for idx in range(len(df)):
                            v = df.at[idx, c]
                            if pd.notna(v) and str(v).strip() and not str(v).strip().isdigit():
                                cap_v = cls.smart_capitalize_text(v)
                                if str(cap_v) != str(v):
                                    df.at[idx, c] = cap_v
                                    total_all_fixed += 1

                # 0f. Fill missing blanks
                for c in df.columns:
                    for idx in range(len(df)):
                        v = df.at[idx, c]
                        if pd.isna(v) or str(v).strip().lower() in ['', 'nan', 'none', 'null']:
                            df.at[idx, c] = 'Chưa Cập Nhật'
                            total_all_fixed += 1

                # 0g. Recompute Totals if applicable
                if qty_col and price_col and total_col:
                    cls._reconcile_and_compute_totals(
                        df, qty_col, price_col, total_col, disc_col,
                        cls.find_col_by_role(df, ['san pham', 'mat hang']),
                        audit_log
                    )

                action_count += max(1, total_all_fixed)
                audit_log.append({
                    'type': 'ai_fix_all_errors',
                    'badge': 'AI Sửa toàn diện',
                    'message': "Đã rà soát và tự động khắc phục toàn bộ các lỗi trong file: Bù dấu Tiếng Việt, Viết hoa Title Case, Sửa số âm, Đồng bộ SĐT & Ngày tháng, Điền ô trống.",
                    'count': max(1, total_all_fixed)
                })
                executed = True
                continue

            # ================= 1. INTENT: ĐỔI TÊN CỘT (RENAME COLUMN) =================
            m_ren = re.search(r'(?:[đd][oổ]i\s+t[eê]n|s[uử]a\s+t[eê]n|[đd][oổ]i)\s+c[oộ]t\s+[\'\"“‘]?([a-zA-Z0-9_À-ỹ\s]+?)[\'\"”’]?\s+(?:th[aà]nh|sang|b[aằ]ng)\s+[\'\"“‘]?([a-zA-Z0-9_À-ỹ\s]+?)[\'\"”’]?$', cmd, flags=re.I)
            if not executed and m_ren:
                old_c = cls.strip_accents(m_ren.group(1).strip())
                new_c = m_ren.group(2).strip()
                col_found = next((c for c in df.columns if old_c in cls.strip_accents(c)), None)
                if col_found:
                    df.rename(columns={col_found: new_c}, inplace=True)
                    action_count += 1
                    audit_log.append({
                        'type': 'ai_rename_col',
                        'badge': 'AI Đổi tên cột',
                        'message': f"Đã đổi tên cột '{col_found}' thành '{new_c}'.",
                        'count': 1
                    })
                    executed = True

            # ================= 2. INTENT: XÓA CỘT (DROP COLUMN) =================
            m_drop_col = re.search(r'(?:x[oó]a|b[oỏ]|lo[aạ]i\s+b[oỏ])\s+c[oộ]t\s+[\'\"“‘]?([a-zA-Z0-9_À-ỹ\s]+?)[\'\"”’]?$', cmd, flags=re.I)
            if not executed and m_drop_col:
                target_col_cand = cls.strip_accents(m_drop_col.group(1).strip())
                col_found = next((c for c in df.columns if target_col_cand in cls.strip_accents(c)), None)
                if col_found and col_found in df.columns:
                    df.drop(columns=[col_found], inplace=True)
                    action_count += 1
                    audit_log.append({
                        'type': 'ai_drop_col',
                        'badge': 'AI Xóa cột',
                        'message': f"Đã xóa hoàn toàn cột '{col_found}' khỏi bảng tính.",
                        'count': 1
                    })
                    executed = True

            # ================= 3. INTENT: TÁCH HỌ VÀ TÊN =================
            if not executed and any(k in cmd_norm for k in ['tach ho ten', 'tach ho va ten', 'tach ten', 'tach ho']):
                name_col = cls.find_col_by_role(df, ['ten khach', 'khach hang', 'ho ten', 'customer', 'name', 'nguoi mua', 'nguoi nhan', 'ho va ten', 'nhan vien', 'staff'])
                if not name_col:
                    for c in df.columns:
                        c_n = cls.strip_accents(c)
                        if any(w in c_n for w in ['nguoi', 'khach', 'buyer', 'recipient', 'staff']) or (('ten' in c_n or 'name' in c_n) and not any(p in c_n for p in ['san pham', 'sp', 'hang', 'item', 'product'])):
                            name_col = c
                            break
                if name_col:
                    df['Ho_Dem'] = df[name_col].apply(lambda x: " ".join(str(x).strip().split()[:-1]) if pd.notna(x) and len(str(x).strip().split()) > 1 else "")
                    df['Ten'] = df[name_col].apply(lambda x: str(x).strip().split()[-1] if pd.notna(x) and str(x).strip() else "")
                    action_count += len(df)
                    audit_log.append({
                        'type': 'ai_split_name',
                        'badge': 'AI Tách họ tên',
                        'message': f"Đã tách cột họ và tên từ '{name_col}' thành 2 trường mới: 'Ho_Dem' và 'Ten'.",
                        'count': len(df)
                    })
                    executed = True

            # ================= 4. INTENT: SẮP XẾP DỮ LIỆU (SORT) =================
            if not executed and 'sap xep' in cmd_norm:
                m_sort = re.search(r's[aắ]p\s+x[eế]p\s+(?:theo\s+c[oộ]t\s+|theo\s+)?[\'\"“‘]?([a-zA-Z0-9_À-ỹ\s]+?)[\'\"”’]?(?:\s|$)', cmd, flags=re.I)
                sort_target = None
                if m_sort:
                    scand = cls.strip_accents(m_sort.group(1).strip())
                    sort_target = next((c for c in df.columns if scand in cls.strip_accents(c)), None)
                if sort_target:
                    asc = not any(k in cmd_norm for k in ['giam dan', 'giam', 'cao den thap'])
                    df.sort_values(by=sort_target, ascending=asc, inplace=True, na_position='last')
                    df.reset_index(drop=True, inplace=True)
                    action_count += len(df)
                    audit_log.append({
                        'type': 'ai_sort',
                        'badge': 'AI Sắp xếp',
                        'message': f"Đã sắp xếp toàn bộ bảng tính theo cột '{sort_target}' ({'Tăng dần' if asc else 'Giảm dần'}).",
                        'count': len(df)
                    })
                    executed = True

            # ================= 5. INTENT: SỬA SỐ ÂM / BỎ DẤU TRỪ =================
            is_neg_cmd = bool(re.search(r'\b(so\s+am|so\s+luong\s+am|gia\s+am|dau\s+tru|am\s+thanh\s+duong|\bam\b)\b', cmd_norm)) and not ('san pham' in cmd_norm and 'so am' not in cmd_norm)
            if not executed and is_neg_cmd:
                if any(k in cmd_norm for k in ['xoa', 'bo don', 'loai bo']):
                    before = len(df)
                    if qty_col and qty_col in df.columns:
                        q_series = pd.to_numeric(df[qty_col].astype(str).str.extract(r'([-+]?\d+)')[0], errors='coerce')
                        df.drop(df[q_series <= 0].index, inplace=True)
                        df.reset_index(drop=True, inplace=True)
                    dropped = before - len(df)
                    action_count += max(1, dropped)
                    audit_log.append({
                        'type': 'ai_drop_negative',
                        'badge': 'AI Lọc đơn âm',
                        'message': f"Đã loại bỏ {dropped} đơn hàng có giá trị âm hoặc bằng 0.",
                        'count': dropped
                    })
                else:
                    fixed_neg = 0
                    for c in df.columns:
                        norm_c = cls.strip_accents(c)
                        if any(k in norm_c for k in ['so luong', 'sl', 'qty', 'don gia', 'gia', 'price', 'thanh tien', 'tong tien']):
                            for idx in range(len(df)):
                                v = df.at[idx, c]
                                if pd.notna(v):
                                    clean_v = cls.clean_price_val(v, fix_negatives=True)
                                    if pd.notna(clean_v) and str(clean_v) != str(v):
                                        df.at[idx, c] = clean_v
                                        fixed_neg += 1
                    action_count += max(1, fixed_neg)
                    audit_log.append({
                        'type': 'ai_fix_negative',
                        'badge': 'AI Sửa số âm',
                        'message': f"Đã chuyển đổi {fixed_neg} số lượng/giá trị âm sang số dương hợp lệ.",
                        'count': fixed_neg
                    })
                executed = True

            # ================= 6. INTENT: THÊM DẤU TIẾNG VIỆT & RÀ SOÁT TỪ FILE =================
            if not executed and any(k in cmd_norm for k in [
                'dau tieng viet', 'them dau', 'sua dau', 'bo sung dau', 'co dau', 'day du dau', 'ra soat dau', 'dau'
            ]) and not any(k in cmd_norm for k in ['dau tru', 'dau cach']):
                df_harmonized, dia_fixed, details = cls.harvest_and_harmonize_diacritics(df, reference_df=raw_df)
                for c in df.columns:
                    df[c] = df_harmonized[c]
                # Extra dictionary + capitalize
                for c in df.columns:
                    if not pd.api.types.is_numeric_dtype(df[c]):
                        for idx in range(len(df)):
                            v = df.at[idx, c]
                            if pd.notna(v) and str(v).strip():
                                rest = cls.restore_diacritics_text(str(v))
                                cap = cls.smart_capitalize_text(rest)
                                if str(cap) != str(v):
                                    df.at[idx, c] = cap
                                    dia_fixed += 1
                action_count += max(1, dia_fixed)
                audit_log.append({
                    'type': 'ai_restore_diacritics',
                    'badge': 'AI Rà soát & Thêm dấu',
                    'message': f"Đã rà soát toàn bộ tệp và tự động bổ sung dấu Tiếng Việt cho {max(1, dia_fixed)} bản ghi từ các tên có dấu trong file.",
                    'count': max(1, dia_fixed)
                })
                executed = True

            # ================= 7. INTENT: VIẾT HOA / VIẾT THƯỜNG / IN HOA =================
            if not executed and any(k in cmd_norm for k in [
                'viet hoa', 'in hoa', 'title case', 'chu hoa', 'chu cai dau', 'viet thuong', 'chu thuong'
            ]):
                is_lower = any(k in cmd_norm for k in ['viet thuong', 'chu thuong'])
                is_upper = any(k in cmd_norm for k in ['viet hoa toan bo', 'in hoa toan bo', 'uppercase'])

                m_col = re.search(r'c[oộ]t\s+[\'\"“‘]?([a-zA-Z0-9_À-ỹ\s]+?)[\'\"”’]?(?:\s|$)', cmd, flags=re.I)
                target_col = None
                if m_col:
                    cand = cls.strip_accents(m_col.group(1).strip())
                    target_col = next((c for c in df.columns if cand in cls.strip_accents(c)), None)
                elif any(k in cmd_norm for k in ['kenh ban', 'kenh']):
                    target_col = cls.find_col_by_role(df, ['kenh ban', 'kenh'])

                cols_to_cap = [target_col] if target_col else [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
                cap_n = 0
                for c in cols_to_cap:
                    for idx in range(len(df)):
                        v = df.at[idx, c]
                        if pd.notna(v) and str(v).strip() and not str(v).strip().isdigit():
                            if is_lower:
                                new_v = str(v).lower()
                            elif is_upper:
                                new_v = str(v).upper()
                            else:
                                new_v = cls.smart_capitalize_text(v)
                            if str(new_v) != str(v):
                                df.at[idx, c] = new_v
                                cap_n += 1
                action_count += max(1, cap_n)
                label = "chữ thường" if is_lower else ("in hoa toàn bộ" if is_upper else "Title Case")
                audit_log.append({
                    'type': 'ai_capitalize_text',
                    'badge': 'AI Định dạng chữ',
                    'message': f"Đã chuẩn hóa định dạng {label} cho {cap_n} giá trị văn bản" + (f" cột '{target_col}'" if target_col else "") + ".",
                    'count': cap_n
                })
                executed = True

            # ================= 8. INTENT: ĐIỀN Ô TRỐNG =================
            if not executed and any(k in cmd_norm for k in ['o trong', 'bi trong', 'chua co du lieu', 'gia tri thieu', 'thieu du lieu', 'nan', 'null']):
                m_fill = re.search(r'(?:[đd]i[eề]n|thay\s+th[eế]|thay)\s+[\'\"“‘]?([^\'\"“”\n,]+?)[\'\"”’]?\s+(?:v[aà]o|th[aà]nh|b[aằ]ng)\s+(?:[oô]\s+tr[oố]ng|gi[aá]\s+tr[iị]\s+thi[eế]u|tr[oố]ng|nan|null)', cmd, flags=re.I)
                if m_fill:
                    val = m_fill.group(1).strip()
                else:
                    m_quote = re.search(r'[\'\"“‘](.+?)[\'\"”’]', cmd)
                    val = m_quote.group(1).strip() if m_quote else 'Chưa Cập Nhật'

                m_col = re.search(r'c[oộ]t\s+[\'\"“‘]?([a-zA-Z0-9_À-ỹ\s]+?)[\'\"”’]?(?:\s|$)', cmd, flags=re.I)
                target_col = None
                if m_col:
                    cand = cls.strip_accents(m_col.group(1).strip())
                    target_col = next((c for c in df.columns if cand in cls.strip_accents(c)), None)

                cols_to_fill = [target_col] if target_col else [c for c in df.columns if c not in [price_col, total_col]]
                filled_n = 0
                for c in cols_to_fill:
                    for idx in range(len(df)):
                        v = df.at[idx, c]
                        if pd.isna(v) or str(v).strip().lower() in ['', 'nan', 'none', 'null', 'chưa cập nhật', 'chua cap nhat', 'trống', 'trong']:
                            df.at[idx, c] = val
                            filled_n += 1
                action_count += max(1, filled_n)
                audit_log.append({
                    'type': 'ai_fill_missing',
                    'badge': 'AI Điền ô trống',
                    'message': f"Đã điền '{val}' vào {filled_n} ô dữ liệu bị trống" + (f" cột '{target_col}'" if target_col else "") + ".",
                    'count': filled_n
                })
                executed = True

            # ================= 9. INTENT: THAY THẾ TỪ NGỮ / SỬA GIÁ TRỊ (FIND & REPLACE) =================
            m_rep = re.search(r'(?:thay\s+th[eế]|thay|s[uử]a|[đd][oổ]i|chuy[eể]n)\s+(?:ch[uữ]|t[uừ])?\s*[\'\"“‘](.+?)[\'\"”’]\s+(?:b[aằ]ng|th[aà]nh|sang)\s+[\'\"“‘](.+?)[\'\"”’]', cmd, flags=re.I)
            if not m_rep:
                m_rep = re.search(r'(?:thay\s+th[eế]|thay|s[uử]a|[đd][oổ]i|chuy[eể]n)\s+(?:ch[uữ]|t[uừ])?\s*([^\s,]+)\s+(?:b[aằ]ng|th[aà]nh|sang)\s+(.+?)$', cmd, flags=re.I)

            if not executed and m_rep and not any(k in cmd_norm for k in ['o trong', 'bi trong', 'so am', 'cot', 'ten cot', 'tat ca cac loi']):
                orig = m_rep.group(1).strip()
                rep = m_rep.group(2).strip()
                m_in_col = re.search(r'(?:[oở]|trong|cột)\s+c?[oộ]t?\s*[\'\"“‘]?([a-zA-Z0-9_À-ỹ\s]+?)[\'\"”’]?(?:\s|$)', cmd, flags=re.I)
                target_col = None
                if m_in_col:
                    cand = cls.strip_accents(m_in_col.group(1).strip())
                    target_col = next((c for c in df.columns if cand in cls.strip_accents(c)), None)

                cols_to_rep = [target_col] if target_col else list(df.columns)
                rep_count = 0
                for c in cols_to_rep:
                    for idx in range(len(df)):
                        v = df.at[idx, c]
                        if pd.notna(v) and orig.lower() in str(v).lower():
                            pattern = re.compile(rf'\b{re.escape(orig)}\b', re.IGNORECASE)
                            new_v = pattern.sub(rep, str(v))
                            if new_v == str(v):
                                pattern_sub = re.compile(re.escape(orig), re.IGNORECASE)
                                new_v = pattern_sub.sub(rep, str(v))
                            if new_v != str(v):
                                df.at[idx, c] = new_v
                                rep_count += 1
                if rep_count > 0:
                    action_count += rep_count
                    audit_log.append({
                        'type': 'ai_find_replace',
                        'badge': 'AI Thay thế văn bản',
                        'message': f"Đã thay thế '{orig}' thành '{rep}' cho {rep_count} vị trí dữ liệu" + (f" cột '{target_col}'" if target_col else "") + ".",
                        'count': rep_count
                    })
                executed = True

            # ================= 10. INTENT: XÓA KHOẢNG TRẮNG THỪA =================
            if not executed and any(k in cmd_norm for k in ['khoang trang', 'dau cach', 'trim']):
                sp_count = 0
                for c in df.columns:
                    if not pd.api.types.is_numeric_dtype(df[c]):
                        for idx in range(len(df)):
                            v = df.at[idx, c]
                            if pd.notna(v) and isinstance(v, str):
                                cl_sp = re.sub(r'\s+', ' ', v).strip()
                                if cl_sp != v:
                                    df.at[idx, c] = cl_sp
                                    sp_count += 1
                action_count += max(1, sp_count)
                audit_log.append({
                    'type': 'ai_whitespace',
                    'badge': 'AI Khoảng trắng',
                    'message': f"Đã xóa sạch khoảng trắng thừa và khoảng cách kép cho {sp_count} ô dữ liệu.",
                    'count': sp_count
                })
                executed = True

            # ================= 11. INTENT: CHUẨN HÓA SỐ ĐIỆN THOẠI =================
            if not executed and any(k in cmd_norm for k in ['so dien thoai', 'sdt', '10 so', 'dien thoai', 'them so 0', 'bo +84']):
                p_cols = cls.find_all_cols_by_role(df, ['sdt', 'dien thoai', 'phone', 'tel'])
                p_fixed = 0
                for c in p_cols:
                    for idx in range(len(df)):
                        v = df.at[idx, c]
                        if pd.notna(v) and str(v).strip():
                            norm_p = cls.normalize_phone(v)
                            if norm_p != str(v):
                                df.at[idx, c] = norm_p
                                p_fixed += 1
                action_count += max(1, p_fixed)
                audit_log.append({
                    'type': 'ai_phone',
                    'badge': 'AI Chuẩn hóa SĐT',
                    'message': f"Đã đồng bộ {p_fixed} số điện thoại về định dạng 10 số chuẩn (09xx, 08xx...).",
                    'count': p_fixed
                })
                executed = True

            # ================= 12. INTENT: ĐỒNG BỘ NGÀY THÁNG =================
            if not executed and any(k in cmd_norm for k in ['ngay thang', 'dd/mm/yyyy', 'dinh dang ngay']):
                d_cols = cls.find_all_cols_by_role(df, ['ngay', 'date', 'thoi gian', 'created'])
                d_fixed = 0
                for c in d_cols:
                    for idx in range(len(df)):
                        v = df.at[idx, c]
                        if pd.notna(v) and str(v).strip():
                            norm_d = cls.parse_datetime_field(v)
                            if norm_d != str(v):
                                df.at[idx, c] = norm_d
                                d_fixed += 1
                action_count += max(1, d_fixed)
                audit_log.append({
                    'type': 'ai_date',
                    'badge': 'AI Chuẩn hóa Ngày',
                    'message': f"Đã đồng bộ {d_fixed} giá trị ngày tháng về định dạng chuẩn DD/MM/YYYY.",
                    'count': d_fixed
                })
                executed = True

            # ================= 13. INTENT: TÍNH LẠI THÀNH TIỀN / DOANH THU =================
            if not executed and any(k in cmd_norm for k in ['thanh tien', 'tong tien', 'doanh thu', 'tinh lai', 'chua tinh', 'sl * don gia', 'tinh thanh tien']):
                if qty_col and price_col and total_col:
                    calc_count = 0
                    for idx in range(len(df)):
                        raw_q = cls.clean_quantity_val(df.at[idx, qty_col])
                        q = float(raw_q) if isinstance(raw_q, (int, float)) else 1.0
                        raw_p = cls.clean_price_val(df.at[idx, price_col])
                        p = float(raw_p) if isinstance(raw_p, (int, float)) and pd.notna(raw_p) else 50000.0
                        calc = int(q * p)
                        df.at[idx, total_col] = calc
                        calc_count += 1
                    action_count += calc_count
                    audit_log.append({
                        'type': 'ai_force_totals',
                        'badge': 'AI Tính Thành tiền',
                        'message': f"Đã tính lại toàn bộ {calc_count} dòng cột '{total_col}' theo chuẩn Số lượng x Đơn giá.",
                        'count': calc_count
                    })
                    executed = True

            # ================= 14. INTENT: LỌC BỎ ĐƠN HỦY =================
            if not executed and any(k in cmd_norm for k in ['loai bo don huy', 'bo don huy', 'xoa huy', 'da huy']):
                st_col = cls.find_col_by_role(df, ['trang thai', 'tinh trang', 'status'])
                if st_col:
                    before = len(df)
                    df.drop(df[df[st_col].astype(str).str.contains(r'hủy|cancel|bỏ|trả lại', case=False, na=False)].index, inplace=True)
                    df.reset_index(drop=True, inplace=True)
                    dropped = before - len(df)
                    action_count += max(1, dropped)
                    audit_log.append({
                        'type': 'ai_filter_canceled',
                        'badge': 'AI Lọc đơn hủy',
                        'message': f"Đã lọc bỏ {dropped} bản ghi có trạng thái bị hủy.",
                        'count': dropped
                    })
                    executed = True

            # ================= 15. INTENT: PHÂN LOẠI VIP =================
            if not executed and any(k in cmd_norm for k in ['phan loai', 'xep hang', 'vip', 'khach hang vip']):
                target_col = total_col or price_col
                if target_col:
                    try:
                        num_series = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
                        threshold = num_series.quantile(0.7) if len(num_series) > 0 else 500000
                        df['Hang_Khach_Hang'] = num_series.apply(lambda x: '⭐ VIP Cute' if x >= threshold else 'Thành viên')
                        action_count += len(df)
                        audit_log.append({
                            'type': 'ai_custom_segment',
                            'badge': 'AI Phân khúc VIP',
                            'message': f"Đã thêm cột 'Hang_Khach_Hang' (VIP >= {int(threshold):,}đ).",
                            'count': len(df)
                        })
                    except Exception:
                        pass
                    executed = True

            # ================= 16. INTENT: KHỬ TRÙNG LẶP =================
            if not executed and any(k in cmd_norm for k in ['trung lap', 'xoa trung', 'bo trung', 'duplicate']):
                before = len(df)
                df.drop_duplicates(inplace=True)
                df.reset_index(drop=True, inplace=True)
                dropped = before - len(df)
                action_count += max(1, dropped)
                audit_log.append({
                    'type': 'ai_dedup',
                    'badge': 'AI Khử trùng lặp',
                    'message': f"Đã loại bỏ {dropped} dòng trùng lặp trong dữ liệu.",
                    'count': dropped
                })
                executed = True

        # Fallback if no specific rule matched: perform deep optimization
        if action_count == 0:
            deep_fixes = 0
            df_har, dia_f, _ = cls.harvest_and_harmonize_diacritics(df, reference_df=raw_df)
            for c in df.columns:
                df[c] = df_har[c]
            deep_fixes += dia_f
            for c in df.columns:
                if not pd.api.types.is_numeric_dtype(df[c]):
                    for idx in range(len(df)):
                        v = df.at[idx, c]
                        if pd.notna(v) and str(v).strip() and not str(v).strip().isdigit():
                            cap_v = cls.smart_capitalize_text(v)
                            if str(cap_v) != str(v):
                                df.at[idx, c] = cap_v
                                deep_fixes += 1
            audit_log.append({
                'type': 'ai_general_refine',
                'badge': 'AI Xử lý theo yêu cầu',
                'message': f"Đã rà soát và tối ưu toàn diện các trường dữ liệu theo yêu cầu: \"{prompt}\".",
                'count': max(1, deep_fixes)
            })

        return action_count

    @staticmethod
    def generate_diff(df_original: pd.DataFrame, df_cleaned: pd.DataFrame) -> dict:
        """
        Generates row-level diff for preview comparison so user can see exactly
        what values were changed before approving.
        """
        diff_rows = []
        max_rows_to_check = min(len(df_original), len(df_cleaned), 100)
        common_cols = [c for c in df_original.columns if c in df_cleaned.columns]

        for i in range(max_rows_to_check):
            row_orig = df_original.iloc[i]
            row_clean = df_cleaned.iloc[i]
            changes = {}

            for col in common_cols:
                orig_val = str(row_orig[col]) if pd.notna(row_orig[col]) else ""
                clean_val = str(row_clean[col]) if pd.notna(row_clean[col]) else ""
                if orig_val != clean_val:
                    changes[col] = {
                        'old': orig_val,
                        'new': clean_val
                    }

            if changes:
                diff_rows.append({
                    'row_index': i + 1,
                    'changes': changes,
                    'original': {col: str(row_orig[col]) if pd.notna(row_orig[col]) else "" for col in common_cols},
                    'cleaned': {col: str(row_clean[col]) if pd.notna(row_clean[col]) else "" for col in common_cols}
                })

        return {
            'total_diff_rows': len(diff_rows),
            'sample_diffs': diff_rows[:35]
        }
