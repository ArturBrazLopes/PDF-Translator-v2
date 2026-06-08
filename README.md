# 📄 Tradutor de PDF

Um tradutor de PDF com interface gráfica simples, powered by **Google Gemini** (gratuito).  
Lê qualquer PDF com texto, traduz mantendo a estrutura de parágrafos e gera um novo PDF formatado.

---

## ✨ Funcionalidades

- Traduz PDFs para **10 idiomas** (Português, Inglês, Espanhol, Francês, Alemão, Italiano, Japonês, Chinês, Russo, Árabe)
- **Preserva a estrutura** de parágrafos e o contexto da tradução
- **Interface simples** — arraste, configure e clique em traduzir
- **Leve** — roda em qualquer computador com Python
- Barra de progresso por página
- Abre o PDF traduzido automaticamente ao finalizar

---

## 🚀 Instalação

### 1. Instale o Python 3.9+
Baixe em: https://www.python.org/downloads/

### 2. Clone ou baixe este projeto
```bash
git clone https://github.com/seu-usuario/pdf-translator
cd pdf-translator
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Obtenha sua chave de API do Google Gemini (gratuita)
1. Acesse: https://aistudio.google.com/app/apikey
2. Clique em **"Create API Key"**
3. Copie a chave gerada

---

## ▶️ Como usar

### Executar a interface gráfica:
```bash
python interface.py
```

### Passos na interface:
1. **Escolha o PDF** que deseja traduzir
2. **Escolha onde salvar** o PDF traduzido (opcional — sugerido automaticamente)
3. **Selecione o idioma** de destino
4. **Cole sua chave de API** do Google Gemini
5. Clique em **🚀 Traduzir PDF**

---

## 💡 Dica: Salve a API Key como variável de ambiente

Para não digitar a chave toda vez, salve-a como variável de ambiente:

**Windows (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "sua_chave_aqui", "User")
```

**Linux / macOS:**
```bash
echo 'export GEMINI_API_KEY="sua_chave_aqui"' >> ~/.bashrc
source ~/.bashrc
```

---

## ⚠️ Limitações

- Funciona melhor com PDFs de texto (não funciona com PDFs escaneados/imagens)
- O plano gratuito do Gemini tem limite de ~1.500 requisições/dia
- PDFs muito grandes podem demorar mais (processado página a página)

---

## 🛠️ Estrutura do projeto

```
pdf-translator/
├── interface.py      # Interface gráfica (Tkinter)
├── translator.py     # Lógica de extração, tradução e geração do PDF
├── requirements.txt  # Dependências Python
└── README.md         # Este arquivo
```

---

## 📦 Dependências

| Biblioteca | Uso |
|---|---|
| `pdfplumber` | Extração de texto do PDF com layout |
| `reportlab` | Geração do PDF traduzido |
| `google-generativeai` | API do Google Gemini para tradução |
| `tkinter` | Interface gráfica (inclusa no Python) |

---

## 📸 Demonstração

```
[PDF Original em Inglês] → [Gemini Traduz] → [PDF em Português]
```

---

## 📃 Licença

MIT License — livre para usar, modificar e distribuir.
