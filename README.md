# ALIVE CAMP — Dashboard de Inscrições

Dashboard gerado automaticamente a partir da planilha de inscrições.

## 🚀 Como atualizar o site

1. Acesse o repositório no GitHub
2. Entre na pasta **`dados/`**
3. Clique no arquivo `inscricoes.xlsx` → **ícone de lápis (editar)** ou arraste a nova versão
4. Confirme o envio (commit)
5. O site atualiza automaticamente em ~1 minuto ✅

## 📁 Estrutura

```
├── index.html              ← site gerado automaticamente (não editar)
├── gerar_dashboard.py      ← script que lê a planilha e gera o HTML
├── dados/
│   └── inscricoes.xlsx     ← 👈 AQUI você sobe a planilha atualizada
└── .github/
    └── workflows/
        └── atualizar.yml   ← receita de automação
```

## ⚙️ Configuração inicial (só na primeira vez)

1. Crie o repositório no GitHub
2. Vá em **Settings → Pages → Branch: main → / (root)** → Save
3. Suba todos os arquivos deste repositório
4. Pronto! O link será: `https://seuusuario.github.io/nome-do-repo`

## 📋 Colunas esperadas na planilha

| Coluna | Descrição |
|--------|-----------|
| `Carimbo de data/hora` | Data/hora da inscrição |
| `Nome completo` | Nome do inscrito |
| `Idade` | Idade |
| `Você é membro de alguma igreja? Qual?` | Igreja |
| `Você possui alguma restrição alimentar? Qual?` | Restrição |
| `✅ COMO DESEJA PARTICIPAR?` | Forma de pagamento |
| `Valores Pagos` | Valor já pago |
| `Falta pagar` | Saldo em aberto |
