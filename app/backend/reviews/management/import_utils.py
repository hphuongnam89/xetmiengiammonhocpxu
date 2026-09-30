def resolve_columns(sheet, header_row, field_specs):
    values = next(sheet.iter_rows(min_row=header_row, max_row=header_row, values_only=True))
    by_header = {}
    for index, value in enumerate(values, start=1):
        if value is not None:
            by_header.setdefault(str(value).strip(), []).append(index)
    columns = {}
    missing = []
    for field, spec in field_specs.items():
        if isinstance(spec, int):
            columns[field] = spec
        elif isinstance(spec, dict) and "header" in spec:
            matches = by_header.get(str(spec["header"]).strip(), [])
            occurrence = int(spec.get("occurrence", 1)) - 1
            if 0 <= occurrence < len(matches):
                columns[field] = matches[occurrence]
            else:
                missing.append(str(spec["header"]))
        else:
            matches = by_header.get(str(spec).strip(), [])
            if matches:
                columns[field] = matches[0]
            else:
                missing.append(str(spec))
    return columns, missing, by_header
