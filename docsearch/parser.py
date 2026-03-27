"""Flag parsing for docsearch CLI."""

import os
import re
import shutil

from docsearch.constants import SUPPORTED_TYPES, OCR_IMAGE_TYPES, _default_cores


def parse_flags(args, config):
    """Parse CLI flags from args list, merging with config defaults.

    Modifies args in place (consumes flags, leaves search terms).

    Returns a dict with all parsed values on success, or
    (exit_code, error_message) on validation error.
    """
    match_all = "-a" in args or "--all" in args or config.get("match_all", False)
    recursive = "-r" in args or config.get("recursive", False)
    use_regex = "-x" in args or config.get("regex", False)

    use_ocr = "-O" in args or "--ocr" in args or config.get("ocr", False)
    if "-O" in args:
        args.remove("-O")
    if "--ocr" in args:
        args.remove("--ocr")

    if use_ocr and not shutil.which("tesseract"):
        return (2,
            "Tesseract OCR is not installed. The -O flag requires Tesseract.\n\n"
            "Install Tesseract:\n"
            "  macOS:   brew install tesseract\n"
            "  Ubuntu:  sudo apt install tesseract-ocr\n"
            "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n")

    if use_ocr:
        try:
            import pytesseract  # noqa: F401
        except ImportError:
            return (2,
                "OCR requires the pytesseract Python package, which is not installed.\n\n"
                "Install it with:  pip install pytesseract\n"
                "Or reinstall docsearch:  pip install --upgrade docsearch\n")
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            return (2,
                "OCR requires the Pillow Python package, which is not installed.\n\n"
                "Install it with:  pip install Pillow\n"
                "Or reinstall docsearch:  pip install --upgrade docsearch\n")

    use_fuzzy = "-z" in args or config.get("fuzzy", False)
    if "-z" in args:
        args.remove("-z")

    if use_fuzzy:
        try:
            import rapidfuzz  # noqa: F401
        except ImportError:
            return (2,
                "Fuzzy search requires the rapidfuzz Python package, which is not installed.\n\n"
                "Install it with:  pip install rapidfuzz\n"
                "Or reinstall docsearch:  pip install --upgrade docsearch\n")

    use_wildcard = "-w" in args or config.get("wildcard", False)
    if "-w" in args:
        args.remove("-w")

    use_whole_word = "-W" in args or config.get("whole_word", False)
    if "-W" in args:
        args.remove("-W")

    if use_fuzzy and use_regex:
        return (2, "Cannot combine fuzzy (-z) and regex (-x) search modes.\n")
    if use_wildcard and use_regex:
        return (2, "Cannot combine wildcard (-w) and regex (-x) search modes.\n")
    if use_wildcard and use_fuzzy:
        return (2, "Cannot combine wildcard (-w) and fuzzy (-z) search modes.\n")

    exclude_terms = []
    if "-n" in args:
        idx = args.index("-n")
        if idx + 1 >= len(args):
            return (2, "No exclude terms provided. Usage: docsearch -n draft,obsolete budget\n")
        exclude_terms = [t.strip() for t in args[idx + 1].split(",")]
        args[:] = args[:idx] + args[idx + 2:]

    expression = None
    expression_ast = None
    if "-e" in args:
        idx = args.index("-e")
        if idx + 1 >= len(args):
            return (2, 'No expression provided. Usage: docsearch -e "(bob AND amy) OR fred"\n')
        expression = args[idx + 1]
        args[:] = args[:idx] + args[idx + 2:]

    file_types = None
    if "-t" in args:
        idx = args.index("-t")
        if idx + 1 >= len(args):
            return (2, "No file types provided. Usage: docsearch -t pdf,docx search_term\n")
        raw_types = args[idx + 1].split(",")
        file_types = set()
        valid_types = SUPPORTED_TYPES | OCR_IMAGE_TYPES if use_ocr else SUPPORTED_TYPES
        for t in raw_types:
            ext = "." + t.strip().lower().lstrip(".")
            if ext not in valid_types:
                supported_list = "docx, pdf, csv, odt, txt, html, xlsx, md, json, rtf, pptx, xml, log, yaml, yml, tsv, epub, ods, odp, toml, rst, tex, ini, cfg, sql"
                if use_ocr:
                    supported_list += ", jpg, jpeg, png, tiff, tif, bmp"
                return (2, f"Unsupported file type: {t.strip()}. Supported types: {supported_list}\n")
            file_types.add(ext)
        args[:] = args[:idx] + args[idx + 2:]
    elif "file_types" in config:
        raw_types = config["file_types"].split(",")
        file_types = set()
        valid_types = SUPPORTED_TYPES | OCR_IMAGE_TYPES if use_ocr else SUPPORTED_TYPES
        for t in raw_types:
            ext = "." + t.strip().lower().lstrip(".")
            if ext in valid_types:
                file_types.add(ext)

    file_names = None
    if "-f" in args:
        idx = args.index("-f")
        if idx + 1 >= len(args):
            return (2, "No file names provided. Usage: docsearch -f report.pdf,notes.txt search_term\n")
        file_names = [n.strip() for n in args[idx + 1].split(",")]
        valid_types_f = SUPPORTED_TYPES | OCR_IMAGE_TYPES if use_ocr else SUPPORTED_TYPES
        for n in file_names:
            ext = os.path.splitext(n)[1].lower()
            if ext not in valid_types_f:
                supported_list = "docx, pdf, csv, odt, txt, html, xlsx, md, json, rtf, pptx, xml, log, yaml, yml, tsv, epub, ods, odp, toml, rst, tex, ini, cfg, sql"
                if use_ocr:
                    supported_list += ", jpg, jpeg, png, tiff, tif, bmp"
                return (2, f"Unsupported file type in '{n}'. Supported types: {supported_list}\n")
        args[:] = args[:idx] + args[idx + 2:]

    if file_types is not None and file_names is not None:
        return (2, "Cannot use -f and -t together. Use -f to search specific files or -t to filter by file type.\n")

    context_before = config.get("context_before", 0)
    if "-B" in args:
        idx = args.index("-B")
        if idx + 1 >= len(args):
            return (2, "No count provided. Usage: docsearch -B 5 search_term\n")
        try:
            context_before = int(args[idx + 1])
            if context_before < 0:
                raise ValueError
        except ValueError:
            return (2, f"Invalid count for -B: {args[idx + 1]}. Must be a positive integer.\n")
        args[:] = args[:idx] + args[idx + 2:]

    context_after = config.get("context_after", 0)
    if "-A" in args:
        idx = args.index("-A")
        if idx + 1 >= len(args):
            return (2, "No count provided. Usage: docsearch -A 5 search_term\n")
        try:
            context_after = int(args[idx + 1])
            if context_after < 0:
                raise ValueError
        except ValueError:
            return (2, f"Invalid count for -A: {args[idx + 1]}. Must be a positive integer.\n")
        args[:] = args[:idx] + args[idx + 2:]

    proximity = 0
    if "-p" in args:
        idx = args.index("-p")
        if idx + 1 >= len(args):
            return (2, "No count provided. Usage: docsearch -p 5 budget revenue\n")
        try:
            proximity = int(args[idx + 1])
            if proximity < 1:
                raise ValueError
        except ValueError:
            return (2, f"Invalid count for -p: {args[idx + 1]}. Must be a positive integer.\n")
        args[:] = args[:idx] + args[idx + 2:]

    use_proximity = proximity > 0
    if use_proximity:
        match_all = True

    append_name = None
    if "-sa" in args:
        idx = args.index("-sa")
        if idx + 1 >= len(args):
            return (2, "No filename provided. Usage: docsearch -sa my_report budget revenue\n")
        append_name = args[idx + 1]
        args[:] = args[:idx] + args[idx + 2:]

    cores = config.get("cores", _default_cores())
    if "-c" in args:
        idx = args.index("-c")
        if idx + 1 >= len(args):
            return (2, "No count provided. Usage: docsearch -c 4 search_term\n")
        try:
            cores = int(args[idx + 1])
            if cores < 1:
                raise ValueError
        except ValueError:
            return (2, f"Invalid count for -c: {args[idx + 1]}. Must be a positive integer.\n")
        args[:] = args[:idx] + args[idx + 2:]

    output_formats = []
    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 >= len(args):
            return (2, "No format provided. Usage: docsearch -o csv search_term\n")
        valid_formats = {"csv", "json"}
        requested = [fmt.strip().lower() for fmt in args[idx + 1].split(",")]
        for fmt in requested:
            if fmt not in valid_formats:
                return (2, f"Invalid output format '{fmt}'. Supported formats: csv, json\n")
        output_formats = requested
        args[:] = args[:idx] + args[idx + 2:]

    use_context = context_before > 0 or context_after > 0

    inverse = "--inverse" in args
    if "--inverse" in args:
        args.remove("--inverse")

    if expression is not None:
        if match_all:
            return (2, "Cannot combine -e (expression) with -a (AND mode). Use AND/OR in the expression.\n")
        if exclude_terms:
            return (2, "Cannot combine -e (expression) with -n (exclude). Use NOT in the expression.\n")
        if use_proximity:
            return (2, "Cannot combine -e (expression) with -p (proximity).\n")
        from docsearch.expr_parser import parse_expression, extract_terms
        try:
            expression_ast = parse_expression(expression)
        except ValueError as e:
            return (2, f"Invalid expression: {e}\n")
        search_terms = extract_terms(expression_ast)
        if use_regex:
            for term in search_terms:
                try:
                    re.compile(term)
                except re.error as e:
                    return (2, f"Invalid regex pattern '{term}' in expression: {e}\n")
    else:
        search_terms = [a for a in args if a not in ("-a", "--all", "-r", "-x", "-z", "-w", "-W", "-n")]

        if not search_terms:
            return (2, "No search terms provided.\n")

        if use_proximity and len(search_terms) < 2:
            return (2, "Proximity search (-p) requires at least 2 search terms.\n")

        if use_regex:
            for term in search_terms:
                try:
                    re.compile(term)
                except re.error as e:
                    return (2, f"Invalid regex pattern '{term}': {e}\n")

    # Console mode string (uses AND/OR)
    if expression is not None:
        mode = "EXPR"
        report_mode = "EXPR"
        if use_wildcard:
            mode += "+WILDCARD"
            report_mode += "+WILDCARD"
        if use_regex:
            mode += "+REGEX"
            report_mode += "+REGEX"
        if use_fuzzy:
            mode += "+FUZZY"
            report_mode += "+FUZZY"
        if use_whole_word:
            mode += "+WORD"
            report_mode += "+WORD"
        if use_ocr:
            mode += "+OCR"
            report_mode += "+OCR"
    else:
        if use_wildcard and match_all:
            mode = "WILDCARD+AND"
        elif use_wildcard:
            mode = "WILDCARD"
        elif use_regex and match_all:
            mode = "REGEX+AND"
        elif use_regex:
            mode = "REGEX"
        elif match_all:
            mode = "AND"
        else:
            mode = "OR"
        if use_fuzzy:
            mode += "+FUZZY"
        if use_whole_word:
            mode += "+WORD"
        if exclude_terms:
            mode += "+NOT"
        if use_ocr:
            mode += "+OCR"

        # Report mode string (uses ALL/ANY)
        if use_wildcard and match_all:
            report_mode = "WILDCARD+AND"
        elif use_wildcard:
            report_mode = "WILDCARD"
        elif use_regex and match_all:
            report_mode = "REGEX+AND"
        elif use_regex:
            report_mode = "REGEX"
        elif match_all:
            report_mode = "ALL"
        else:
            report_mode = "ANY"
        if use_fuzzy:
            report_mode += "+FUZZY"
        if use_whole_word:
            report_mode += "+WORD"
        if exclude_terms:
            report_mode += "+NOT"
        if use_ocr:
            report_mode += "+OCR"

    return {
        "match_all": match_all,
        "recursive": recursive,
        "use_regex": use_regex,
        "use_ocr": use_ocr,
        "use_fuzzy": use_fuzzy,
        "use_wildcard": use_wildcard,
        "use_whole_word": use_whole_word,
        "exclude_terms": exclude_terms,
        "file_types": file_types,
        "file_names": file_names,
        "context_before": context_before,
        "context_after": context_after,
        "use_context": use_context,
        "proximity": proximity,
        "use_proximity": use_proximity,
        "append_name": append_name,
        "cores": cores,
        "output_formats": output_formats,
        "search_terms": search_terms,
        "inverse": inverse,
        "expression": expression,
        "expression_ast": expression_ast,
        "mode": mode,
        "report_mode": report_mode,
    }
