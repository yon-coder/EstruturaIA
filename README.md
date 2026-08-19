# EstruturaIA

IA do projeto **MetroForm**.

Este repositório concentra o desenvolvimento e os testes da inteligência artificial
que será posteriormente integrada ao repositório principal.

## Objetivo

A solução deverá:

1. Receber portfólios ou currículos em PDF;
2. Extrair e transformar o conteúdo em texto estruturado;
3. Analisar as informações relevantes;
4. Gerar um score para apoiar a avaliação dos candidatos.

## Dados de treino sintéticos

O arquivo `Portifólios_treino/Generator.py` gera currículos fictícios em PDF para
testes, sem representar pessoas reais. Os documentos incluem nome, área de atuação,
perfil, experiência, formação e habilidades.

As áreas disponíveis são:

- Desenvolvimento de Software;
- Análise de Dados;
- Design de Produto;
- Gestão de Projetos.

### Como gerar os PDFs

Instale a dependência:

```bash
pip install reportlab
```

Gere um currículo:

```bash
python Portifólios_treino/Generator.py
```

Para gerar vários arquivos e reproduzir os mesmos resultados:

```bash
python Portifólios_treino/Generator.py --quantidade 10 --seed 42
```

`--quantidade` aceita valores de 1 a 1000. Os PDFs são salvos na própria pasta
`Portifólios_treino/`.

## Próximas etapas

- Implementar a extração de texto dos PDFs;
- Definir os critérios e pesos do score;
- Criar testes automatizados com os dados sintéticos;
- Integrar o modelo ao projeto principal do MetroForm.