from markdown_pdf import MarkdownPdf
from markdown_pdf import Section

pdf = MarkdownPdf(toc_level=2)

with open("documentacao.md", "r", encoding="utf-8") as f:
    markdown_content = f.read()

pdf.add_section(Section(markdown_content))
pdf.save("Documentacao_AETHER.pdf")
print("PDF gerado com sucesso!")
