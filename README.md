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

## Interface HTML

Abra `front.html` diretamente no navegador para testar o treinamento local. A
interface oferece:

- análise manual de um currículo por área, com nome opcional;
- identificação das habilidades relacionadas à área selecionada;
- score de aderência de 8 a 100, calculado conforme a proporção de habilidades
	encontradas, com uma pequena variação simulada para prototipação;
- geração de 1 a 100 currículos sintéticos, para uma área específica ou para
	todas as áreas;
- painel com total de exemplos processados e última área analisada;
- tabela dos currículos sintéticos, com habilidades identificadas e score;
- persistência dos dados no `localStorage`, além de exportação em JSON e opção
	para apagar os dados salvos.

O treinamento no navegador não chama Python: é uma simulação independente para
prototipação do fluxo da interface. As habilidades reconhecidas são:

- **Desenvolvimento de Software:** Python, APIs REST, Git e SQL;
- **Análise de Dados:** Python, Pandas, SQL e Power BI;
- **Design de Produto:** Figma, Pesquisa UX, Prototipação e Design systems;
- **Gestão de Projetos:** Scrum, Kanban, Jira e Gestão de riscos.

A análise também aceita alguns aliases, como `API`/`REST`, `UX`, `design system`
e `risk management`. A normalização remove diferenças de maiúsculas e acentos.

## Update logs

### 2025-02-14 — Atualização da interface e do treinamento local

- Adicionado o dashboard de treinamento em `front.html`, com navegação entre
	treinamento, resultados e dados.
- Incluída análise manual de currículos e apresentação dos pontos fortes
	identificados.
- Adicionada geração de currículos sintéticos por quantidade e por área.
- Atualizado o cálculo do score para a fórmula proporcional implementada no
	HTML, limitado ao intervalo de 8 a 100.
- Adicionados aliases e normalização de texto para melhorar a detecção de
	habilidades.
- Incluídos armazenamento local, listagem dos dados gerados, exportação JSON e
	limpeza dos dados persistidos.

### 2025-02-14 — Documentação

- README ajustado para refletir as funcionalidades atuais de `front.html`.
- Documentadas as áreas, habilidades, limites da geração e comportamento do
	treinamento simulado.

## Próximas etapas

- Implementar a extração de texto dos PDFs;
- Definir os critérios e pesos do score;
- Criar testes automatizados com os dados sintéticos;
- Integrar o modelo ao projeto principal do MetroForm.