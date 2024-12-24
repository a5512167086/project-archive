def convert_search_to_line_text(search_items):
    line_texts = []
    for item in search_items:
        fields = [
            ("名稱", item.get("chinese_name")),
            ("英文名稱", item.get("english_name")),
            ("品牌", item.get("type")),
            ("描述", item.get("description")),
            ("價格", item.get("price")),
            ("使用說明", item.get("instruction")),
            ("成分", item.get("ingredient")),
            ("圖片", item.get("image_src")),
            ("更多資訊", item.get("url")),
        ]

        text = "\n".join(f"{label}: {value}" for label, value in fields if value)
        line_texts.append(text)

    return line_texts
