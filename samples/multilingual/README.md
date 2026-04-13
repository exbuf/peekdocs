# Multilingual Sample Documents

These files demonstrate peekdocs's ability to search documents in any language.

## Files

| File | Language | Format | Content |
|------|----------|--------|---------|
| `multilingual_budget_report.txt` | 14 languages | .txt | "The budget report is ready for review" in English, Chinese, Japanese, Korean, Arabic, Hindi, Russian, Greek, Spanish, German, French, Portuguese, Thai, and Hebrew |
| `chinese_financial_report.docx` | Chinese | .docx | Quarterly financial report with budget figures in Chinese yuan |
| `greek_quarterly_report.docx` | Greek | .docx | Quarterly financial report with budget figures in euros |
| `spanish_invoice.docx` | Spanish | .docx | Consulting services invoice with contact details |
| `arabic_contract.docx` | Arabic | .docx | Contract summary for consulting services |

## Try it

```bash
cd samples/multilingual

# Search for Chinese text
peekdocs 预算

# Search for Greek text
peekdocs προϋπολογισμού

# Search for Arabic text
peekdocs الميزانية

# Search for Spanish text
peekdocs factura

# Search across all files for dollar amounts
peekdocs -x "\$[\d,]+"

# Run the automated 14-language test
python ../../tests/language_test.py
```
