import pandas as pd
import numpy as np
import random
import re
import unicodedata
from datetime import datetime, timedelta

def generate_keo_cute_sample_data(n_rows: int = 120) -> pd.DataFrame:
    """
    Generates a realistic, intentionally messy sample dataset for Kẹo Cute store.
    Contains realistic Vietnamese names, candy products, order statuses,
    phone numbers with irregular formats, mixed date formats, missing values, and duplicates.
    """
    random.seed(42)
    np.random.seed(42)

    categories = ['Kẹo dẻo Trái Cây', 'Kẹo Mút Cute', 'Marshmallow Cầu Vồng', 'Socola Hạnh Nhân', 'Kẹo Bông Gòn Pastel']
    products_by_cat = {
        'Kẹo dẻo Trái Cây': ['Kẹo dẻo gấu Haribo cute', 'Kẹo dẻo đào sữa ngọt ngào', 'Kẹo dẻo xoài dẻo dẻo', 'Kẹo dẻo trái tim dâu tây'],
        'Kẹo Mút Cute': ['Kẹo mút hoa cúc mật ong', 'Kẹo mút xoắn ốc pastel', 'Kẹo mút dưa hấu mát lạnh', 'Kẹo mút hình trái tim'],
        'Marshmallow Cầu Vồng': ['Marshmallow xoắn cầu vồng', 'Marshmallow nướng phô mai', 'Marshmallow kẹp bánh quy', 'Kẹo bông tuyết Marshmallow'],
        'Socola Hạnh Nhân': ['Socola thỏ ngọc trắng kem', 'Socola hạt dẻ giòn rụm', 'Socola matcha hạnh nhân', 'Socola đen nguyên chất 70%'],
        'Kẹo Bông Gòn Pastel': ['Kẹo bông đám mây hồng baby', 'Kẹo bông vị việt quất xanh', 'Kẹo bông vị đào tiên', 'Hộp kẹo bông ngũ sắc']
    }

    price_table = {
        'Kẹo dẻo gấu Haribo cute': 45000, 'Kẹo dẻo đào sữa ngọt ngào': 55000, 'Kẹo dẻo xoài dẻo dẻo': 48000, 'Kẹo dẻo trái tim dâu tây': 50000,
        'Kẹo mút hoa cúc mật ong': 25000, 'Kẹo mút xoắn ốc pastel': 30000, 'Kẹo mút dưa hấu mát lạnh': 28000, 'Kẹo mút hình trái tim': 32000,
        'Marshmallow xoắn cầu vồng': 65000, 'Marshmallow nướng phô mai': 75000, 'Marshmallow kẹp bánh quy': 68000, 'Kẹo bông tuyết Marshmallow': 80000,
        'Socola thỏ ngọc trắng kem': 95000, 'Socola hạt dẻ giòn rụm': 110000, 'Socola matcha hạnh nhân': 105000, 'Socola đen nguyên chất 70%': 120000,
        'Kẹo bông đám mây hồng baby': 40000, 'Kẹo bông vị việt quất xanh': 42000, 'Kẹo bông vị đào tiên': 45000, 'Hộp kẹo bông ngũ sắc': 60000
    }

    raw_names = [
        "nguyễn thị lan anh", "TRẦN VĂN MINH", "Lê  Thị  Hồng", "hoàng đức bảo", "VŨ THỊ MAI",
        "đặng ngọc hà", "phạm quốc tuấn", "Bùi   Thị Linh", "đỗ văn dũng", "Ngô  Thanh  Tâm",
        "dương như quỳnh", "Lý hải đăng", "Phan văn tiến", "Võ thu huyền", "trịnh bá thắng",
        "Mai ánh nguyệt", "Hà  Phương Thảo", "Lê  bảo  ngọc", "tạ văn trường", "nguyễn quỳnh nga"
    ]

    base_dates = [datetime(2024, random.randint(1, 12), random.randint(1, 28)) for _ in range(n_rows)]
    date_formats = [
        lambda d: d.strftime('%Y-%m-%d'),
        lambda d: d.strftime('%d/%m/%Y'),
        lambda d: d.strftime('%d-%m-%Y'),
        lambda d: d.strftime('%m/%d/%Y'),
        lambda d: d.strftime('%d.%m.%Y')
    ]

    branches = ['Kẹo Cute Quận 1', 'Kẹo Cute Quận 7', 'Kẹo Cute Cầu Giấy', 'Kẹo Cute Hải Châu', 'Kẹo Cute Online']
    statuses = ['Hoàn thành', 'Hoàn thành', 'Hoàn thành', 'Đang giao hàng', 'Chờ xác nhận', 'Đã hủy']

    records = []
    for i in range(n_rows):
        cat = random.choice(categories)
        prod = random.choice(products_by_cat[cat])
        qty = random.randint(1, 8)
        unit_price = price_table[prod]

        # Messy name format
        name = random.choice(raw_names)
        if random.random() < 0.2:
            name = name.lower()
        elif random.random() < 0.2:
            name = name.upper()

        # Messy phone number
        phone_core = f"{random.choice(['90', '91', '98', '97', '86', '35', '77'])}{random.randint(1000000, 9999999)}"
        phone_style = random.choice(['clean', 'plus84', 'dotted', 'spaced', 'dashed', 'missing'])
        if phone_style == 'clean':
            phone = f"0{phone_core}"
        elif phone_style == 'plus84':
            phone = f"+84 {phone_core}"
        elif phone_style == 'dotted':
            phone = f"0{phone_core[:3]}.{phone_core[3:6]}.{phone_core[6:]}"
        elif phone_style == 'spaced':
            phone = f"0{phone_core[:3]} {phone_core[3:6]} {phone_core[6:]}"
        elif phone_style == 'dashed':
            phone = f"0{phone_core[:3]}-{phone_core[3:]}"
        else:
            phone = None if random.random() < 0.4 else f"0{phone_core}"

        # Messy dates
        dt_obj = base_dates[i]
        date_str = random.choice(date_formats)(dt_obj) if random.random() > 0.05 else None

        # Messy prices / totals (some with VNĐ, some with negative numbers by mistake)
        total_val = qty * unit_price
        price_disp = str(unit_price)
        if random.random() < 0.2:
            price_disp = f"{unit_price:,} đ".replace(',', '.')
        elif random.random() < 0.1:
            price_disp = f"{unit_price} VNĐ"
        elif random.random() < 0.03:
            price_disp = str(-abs(unit_price)) # accidental negative entry

        branch = random.choice(branches)
        if random.random() < 0.08:
            branch = None # Missing branch

        status = random.choice(statuses)

        # Unaccented test cases to test diacritic harvesting from file
        prod_disp = prod
        branch_disp = branch
        if i in [4, 15, 28, 55, 78]:
            # Intentionally remove accents from product
            prod_unacc = unicodedata.normalize('NFD', prod)
            prod_unacc = re.sub(r'[\u0300-\u036f]', '', prod_unacc).replace('đ', 'd').replace('Đ', 'D')
            prod_disp = prod_unacc
        if i in [8, 22, 63] and branch:
            # Intentionally remove accents from branch
            branch_unacc = unicodedata.normalize('NFD', branch)
            branch_unacc = re.sub(r'[\u0300-\u036f]', '', branch_unacc).replace('đ', 'd').replace('Đ', 'D')
            branch_disp = branch_unacc

        records.append({
            'Mã Đơn Hàng': f"KC-{1000 + i}",
            'Tên Khách Hàng': name,
            'Số Điện Thoại': phone,
            'Ngày Mua': date_str,
            'Danh Mục': cat,
            'Sản Phẩm': prod_disp,
            'Số Lượng': qty,
            'Đơn Giá': price_disp,
            'Chi Nhánh': branch_disp,
            'Trạng Thái': status
        })

    # Add intentional duplicate rows to test deduplication
    for dup_idx in [3, 10, 25, 42, 60]:
        if dup_idx < len(records):
            records.append(dict(records[dup_idx]))

    df = pd.DataFrame(records)
    return df

if __name__ == '__main__':
    df = generate_keo_cute_sample_data(50)
    print("Sample data generated:", df.shape)
    print(df.head())

