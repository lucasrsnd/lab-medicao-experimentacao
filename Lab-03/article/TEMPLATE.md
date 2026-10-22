# Template do artigo

O arquivo `sbc-template.sty` foi copiado sem alterações do pacote de modelos disponibilizado pela Sociedade Brasileira de Computação:

- Página: https://www.sbc.org.br/documentosinstitucionais/
- Pacote: https://www.sbc.org.br/wp-content/uploads/2024/07/modelosparapublicaodeartigos.zip
- Caminho no pacote: `Template_SBC/template-latex/sbc-template.sty`.
- Autoria indicada no arquivo: Jomi Hubner e Rafael Bordini; última atualização indicada: dezembro de 2017.

O artigo usa `main.tex` e as seções em `sections/`; as figuras vêm de `../analysis/` (`\graphicspath`). Com Tectonic disponível, execute a partir desta pasta:

```powershell
tectonic --keep-logs main.tex
```

A primeira compilação pode precisar baixar pacotes e criar o cache do compilador. O PDF só deve ser considerado pronto após compilação e inspeção visual; a presença dos fontes não comprova a geração.
