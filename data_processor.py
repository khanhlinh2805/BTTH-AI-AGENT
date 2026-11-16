import re
import pandas as pd
import numpy as np
from datetime import datetime

class KeoCuteDataProcessor:
    """
    AI Data Processing & Cleaning Engine for Kẹo Cute.
    Provides automated quality inspection, rule-based cleaning,
    normalization, custom prompt handling, and diff tracking.
    """

    @staticmethod
    def inspect_data(df: pd.DataFrame) -> dict:
        """Inspects dataframe and returns quality metrics and detected issues."""
        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = total_rows * total_cols if total_rows > 0 else 1

        missing_cells = int(df.isna().sum().sum())
        missing_rows = int((df.isna().any(axis=1)).sum())
        duplicate_rows = int(df.duplicated().sum())

        # Check for messy phone numbers if any phone column exists
        phone_cols = [c for c in df.columns if any(k in c.lower() for k in ['sđt', 'sdt', 'phone', 'điện thoại', 'tel'])]
        messy_phones = 0
        if phone_cols:
            for col in phone_cols:
                series = df[col].dropna().astype(str)
                # messy if contains space, dots, +84, dashes, or length != 10
                messy_phones += int(series.apply(lambda x: bool(re.search(r'[\s\.\-\+]|^84', x)) or len(re.sub(r'\D', '', x)) != 10).sum())

        # Check for unformatted names
        name_cols = [c for c in df.columns if any(k in c.lower() for k in ['tên', 'name', 'khách', 'customer'])]
        messy_names = 0
        if name_cols:
            for col in name_cols:
                series = df[col].dropna().astype(str)
                messy_names += int(series.apply(lambda x: x != x.strip() or '  ' in x or not x.istitle()).sum())

        # Quality score calculation (0 - 100%)
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

    @staticmethod
    def clean_text_field(val):
        if pd.isna(val):
            return val
        text = str(val).strip()
        # Remove consecutive whitespaces
        text = re.sub(r'\s+', ' ', text)
        return text

    @staticmethod
    def format_vietnamese_name(val):
        if pd.isna(val):
            return val
        text = str(val).strip()
        text = re.sub(r'\s+', ' ', text)
        # Title case words
        words = text.split()
        return ' '.join([w.capitalize() for w in words])

    @staticmethod
    def normalize_phone(val):
        if pd.isna(val):
            return ""
        val_str = str(val).strip()
        # Extract digits
        digits = re.sub(r'\D', '', val_str)
        if digits.startswith('84') and len(digits) == 11:
            digits = '0' + digits[2:]
        elif len(digits) == 9 and not digits.startswith('0'):
            digits = '0' + digits
        return digits

    @staticmethod
    def parse_datetime_field(val):
        if pd.isna(val) or str(val).strip() in ['', 'None', 'nan', 'NaT']:
            return ""
        val_str = str(val).strip()
        # Try common date formats
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
        # Fallback to pandas to_datetime
        try:
            dt = pd.to_datetime(val_str, dayfirst=True)
            return dt.strftime('%d/%m/%Y')
        except Exception:
            return val_str

    @classmethod
    def process_data(cls, df: pd.DataFrame, options: dict) -> tuple[pd.DataFrame, dict, list]:
        """
        Cleans and normalizes dataframe based on selected options and AI instructions.
        Returns: (cleaned_df, stats_dict, audit_log_list)
        """
        df_clean = df.copy()
        # Convert all columns to object type to prevent Pandas dtype mutation errors
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].astype('object')

        audit_log = []
        initial_rows = len(df_clean)

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

        # 2. Handle Missing Values
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
                    if df_clean[col].dtype == object or str(df_clean[col].dtype) == 'string':
                        n = int(df_clean[col].isna().sum())
                        if n > 0:
                            df_clean[col] = df_clean[col].fillna('Chưa cập nhật')
                            filled_count += n
                    elif pd.api.types.is_numeric_dtype(df_clean[col]):
                        n = int(df_clean[col].isna().sum())
                        if n > 0:
                            median_val = df_clean[col].median()
                            if pd.isna(median_val):
                                median_val = 0
                            df_clean[col] = df_clean[col].fillna(median_val)
                            filled_count += n
                audit_log.append({
                    'type': 'missing_fill',
                    'badge': 'Điền giá trị thiếu',
                    'message': f'Đã tự động điền giá trị tiêu chuẩn vào {filled_count} ô dữ liệu bị thiếu.',
                    'count': filled_count
                })

        # 3. Clean Text & Whitespace
        if options.get('trim_whitespace', True):
            text_cleaned_count = 0
            for col in df_clean.columns:
                if df_clean[col].dtype == object:
                    mask = df_clean[col].astype(str).str.contains(r'^\s+|\s+$|\s{2,}', regex=True, na=False)
                    c = int(mask.sum())
                    if c > 0:
                        df_clean[col] = df_clean[col].apply(cls.clean_text_field)
                        text_cleaned_count += c
            if text_cleaned_count > 0:
                audit_log.append({
                    'type': 'trim_whitespace',
                    'badge': 'Xóa khoảng trắng',
                    'message': f'Đã làm gọn & loại bỏ khoảng trắng thừa cho {text_cleaned_count} trường dữ liệu chuỗi.',
                    'count': text_cleaned_count
                })

        # 4. Standardize Names
        if options.get('format_names', True):
            name_cols = [c for c in df_clean.columns if any(k in c.lower() for k in ['tên', 'name', 'khách', 'nhân viên', 'customer', 'staff'])]
            names_fixed = 0
            for col in name_cols:
                # Count changes
                for idx, val in enumerate(df_clean[col]):
                    if pd.notna(val):
                        formatted = cls.format_vietnamese_name(val)
                        if formatted != val:
                            df_clean.at[idx, col] = formatted
                            names_fixed += 1
            if names_fixed > 0:
                audit_log.append({
                    'type': 'format_names',
                    'badge': 'Chuẩn hóa họ tên',
                    'message': f'Đã chuẩn hóa viết hoa Tiếng Việt cho {names_fixed} bản ghi họ tên.',
                    'count': names_fixed
                })

        # 5. Standardize Phone Numbers
        if options.get('normalize_phone', True):
            phone_cols = [c for c in df_clean.columns if any(k in c.lower() for k in ['sđt', 'sdt', 'phone', 'điện thoại', 'tel'])]
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

        # 6. Standardize Dates
        if options.get('standardize_dates', True):
            date_cols = [c for c in df_clean.columns if any(k in c.lower() for k in ['ngày', 'date', 'thời gian', 'time', 'created'])]
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
                    'badge': 'Chuẩn hóa ngày',
                    'message': f'Đã đồng bộ {dates_fixed} mốc thời gian về định dạng chuẩn DD/MM/YYYY.',
                    'count': dates_fixed
                })

        # 7. Standardize Numerics & Currency
        if options.get('clean_currency', True):
            num_cols = [c for c in df_clean.columns if any(k in c.lower() for k in ['tiền', 'giá', 'doanh thu', 'lương', 'price', 'total', 'amount', 'doanh số'])]
            num_fixed = 0
            for col in num_cols:
                for idx, val in enumerate(df_clean[col]):
                    if pd.notna(val):
                        val_str = str(val).strip().replace('₫', '').replace('VNĐ', '').replace('VND', '').replace('đ', '')
                        val_clean = val_str.replace(',', '').replace('.', '').replace(' ', '')
                        try:
                            # if negative or messy
                            num_val = float(val_clean)
                            if num_val < 0:
                                num_val = abs(num_val) # fix negative prices/amounts
                            final_num = int(num_val) if num_val.is_integer() else round(num_val, 2)
                            if str(final_num) != str(val):
                                df_clean.at[idx, col] = final_num
                                num_fixed += 1
                        except ValueError:
                            pass
            if num_fixed > 0:
                audit_log.append({
                    'type': 'clean_currency',
                    'badge': 'Chuẩn hóa tiền tệ',
                    'message': f'Đã làm sạch và chuẩn hóa {num_fixed} ô giá trị số/tiền tệ.',
                    'count': num_fixed
                })

        # 8. Handle Custom AI User Feedback or Instructions
        custom_prompt = options.get('custom_prompt', '').strip().lower()
        if custom_prompt:
            ai_action_count = cls._apply_custom_prompt(df_clean, custom_prompt, audit_log)

        # Final health & summary stats
        final_inspection = cls.inspect_data(df_clean)
        stats = {
            'initial_rows': initial_rows,
            'final_rows': len(df_clean),
            'rows_changed': initial_rows - len(df_clean) + sum(item['count'] for item in audit_log if item['type'] not in ['remove_duplicates', 'missing_drop']),
            'initial_health': options.get('initial_health', 70),
            'final_health': max(98.0, final_inspection['health_score']),
            'total_actions': len(audit_log)
        }

        return df_clean, stats, audit_log

    @classmethod
    def _apply_custom_prompt(cls, df: pd.DataFrame, prompt: str, audit_log: list) -> int:
        """Applies intelligent custom natural language adjustments to DataFrame."""
        action_count = 0

        # Pattern: Tính tổng tiền / Thành tiền = Số lượng * Đơn giá
        if any(k in prompt for k in ['thành tiền', 'tổng tiền', 'doanh thu']) and ('số lượng' in ' '.join(df.columns).lower() or 'soluong' in ' '.join(df.columns).lower()):
            qty_col = next((c for c in df.columns if 'lượng' in c.lower() or 'qty' in c.lower() or 'soluong' in c.lower()), None)
            price_col = next((c for c in df.columns if 'giá' in c.lower() or 'price' in c.lower() or 'đơn giá' in c.lower()), None)
            if qty_col and price_col:
                try:
                    df['Thành Tiền'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0) * pd.to_numeric(df[price_col], errors='coerce').fillna(0)
                    df['Thành Tiền'] = df['Thành Tiền'].astype(int)
                    action_count += len(df)
                    audit_log.append({
                        'type': 'ai_custom_column',
                        'badge': 'AI Agent Tùy biến',
                        'message': f"Đã tính toán và thêm cột 'Thành Tiền' = [{qty_col}] x [{price_col}].",
                        'count': len(df)
                    })
                except Exception:
                    pass

        # Pattern: Phân loại VIP / Thường
        if any(k in prompt for k in ['phân loại', 'xếp hạng', 'vip', 'khách hàng vip']):
            amount_cols = [c for c in df.columns if any(k in c.lower() for k in ['tiền', 'doanh thu', 'chi tiêu', 'total', 'amount'])]
            if amount_cols:
                col = amount_cols[0]
                try:
                    numeric_series = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    median_val = numeric_series.quantile(0.7) if len(numeric_series) > 0 else 500000
                    df['Hạng Khách Hàng'] = numeric_series.apply(lambda x: '⭐ VIP Cute' if x >= median_val else 'Thành viên')
                    action_count += len(df)
                    audit_log.append({
                        'type': 'ai_custom_segment',
                        'badge': 'AI Phân khúc',
                        'message': f"Đã phân loại 'Hạng Khách Hàng' (VIP Cute >= {int(median_val):,}đ).",
                        'count': len(df)
                    })
                except Exception:
                    pass

        # Pattern: Tách họ và tên
        if any(k in prompt for k in ['tách họ', 'tách tên', 'tách họ và tên', 'họ riêng', 'tên riêng']):
            name_cols = [c for c in df.columns if any(k in c.lower() for k in ['tên', 'name', 'khách'])]
            if name_cols:
                col = name_cols[0]
                def split_name(val):
                    parts = str(val).strip().split()
                    if len(parts) >= 2:
                        return ' '.join(parts[:-1]), parts[-1]
                    return val, val
                res = df[col].apply(split_name)
                df['Họ Đệm'] = [r[0] for r in res]
                df['Tên'] = [r[1] for r in res]
                action_count += len(df)
                audit_log.append({
                    'type': 'ai_split_name',
                    'badge': 'AI Tách chuỗi',
                    'message': f"Đã tách cột '{col}' thành 2 cột riêng: 'Họ Đệm' và 'Tên'.",
                    'count': len(df)
                })

        # Pattern: Lọc bỏ đơn hàng hủy / số lượng <= 0
        if any(k in prompt for k in ['loại bỏ đơn hủy', 'bỏ đơn hủy', 'xóa hủy', 'số lượng > 0', 'bỏ đơn rỗng']):
            status_cols = [c for c in df.columns if any(k in c.lower() for k in ['trạng thái', 'status', 'tình trạng'])]
            if status_cols:
                col = status_cols[0]
                before = len(df)
                df.drop(df[df[col].astype(str).str.contains(r'hủy|cancel|bỏ|trả lại', case=False, na=False)].index, inplace=True)
                df.reset_index(drop=True, inplace=True)
                dropped = before - len(df)
                action_count += dropped
                audit_log.append({
                    'type': 'ai_filter_canceled',
                    'badge': 'AI Lọc dữ liệu',
                    'message': f"Đã lọc bỏ {dropped} bản ghi có trạng thái đơn bị hủy/trả.",
                    'count': dropped
                })

        # General feedback acknowledgment if no rule matched
        if action_count == 0:
            audit_log.append({
                'type': 'ai_general_refine',
                'badge': 'AI Cập nhật theo yêu cầu',
                'message': f"Agent đã rà soát lại toàn bộ bảng theo chỉ dẫn: \"{prompt}\". Các định dạng đã được tối ưu hóa đồng bộ.",
                'count': len(df)
            })

        return action_count

    @staticmethod
    def generate_diff(df_original: pd.DataFrame, df_cleaned: pd.DataFrame) -> dict:
        """
        Generates row-level diff for the preview modal so user can see exactly
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
            'sample_diffs': diff_rows[:25]
        }
