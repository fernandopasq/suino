# Vettora

Aplicação web desenvolvida com Django para gestão sanitária de animais de diferentes espécies.

## Estrutura do projeto

```text
SUINO/
├── README.md                     # Informações gerais e instruções do projeto
├── requirements.txt              # Dependências Python utilizadas pela aplicação
└── suino/
    ├── manage.py                 # Comandos administrativos do Django
    ├── db.sqlite3                # Banco de dados local SQLite
    ├── media/                    # Arquivos enviados pela aplicação
    │   └── animais/              # Imagens dos animais
    ├── saude/                    # Aplicação principal de gestão sanitária
    │   ├── migrations/           # Histórico das alterações no banco de dados
    │   ├── templates/saude/      # Páginas HTML do sistema
    │   │   ├── base.html         # Estrutura visual compartilhada
    │   │   ├── home.html         # Página inicial
    │   │   ├── login.html        # Página de acesso
    │   │   ├── perfil.html       # Dados e senha do usuário
    │   │   ├── lista_animais.html
    │   │   ├── animal_form.html
    │   │   ├── animal_detalhe.html
    │   │   └── calendario.html
    │   ├── admin.py              # Configuração dos modelos no painel administrativo
    │   ├── apps.py               # Configuração da aplicação `saude`
    │   ├── forms.py              # Formulários exibidos pelas páginas
    │   ├── models.py             # Definição das tabelas e regras dos dados
    │   ├── tests.py              # Testes automatizados da aplicação
    │   ├── urls.py               # Rotas específicas do app `saude`
    │   ├── utils.py              # Geração e recálculo automático das vacinas
    │   └── views.py              # Processamento das requisições e das páginas
    └── suino/                    # Configuração principal do projeto Django
        ├── settings.py           # Configurações do Django e do banco
        ├── urls.py               # Rotas principais, login e painel administrativo
        ├── asgi.py               # Ponto de entrada para servidores ASGI
        └── wsgi.py               # Ponto de entrada para servidores WSGI
```

### Arquivos principais

- **`models.py`**: define os modelos `Animal`, `PlanoVacina`, `DoseVacina` e `EventoSanitario`, além dos vínculos entre espécies, doses e registros sanitários.
- **`views.py`**: concentra as telas e ações da aplicação, como cadastrar e listar animais, alterar status, registrar vacinas e fornecer os eventos do calendário.
- **`forms.py`**: contém os formulários de animais, perfil, alteração de senha, status e registro da aplicação de vacinas.
- **`utils.py`**: gera o calendário de vacinação dos animais e recalcula as doses seguintes após uma aplicação realizada.
- **`urls.py`** (dentro de `saude/`): associa os endereços às páginas e à API de eventos sanitários.
- **`admin.py`**: personaliza o painel administrativo para cadastro das vacinas e seus planos de dose.
- **`settings.py`**: configura banco SQLite, idioma, segurança, autenticação, arquivos enviados e aplicações Django.
- **`manage.py`**: permite executar servidor, migrações, testes e outros comandos administrativos.
- **`migrations/`**: registra a evolução das tabelas do banco e contém a criação e ajuste dos modelos.
- **`templates/saude/`**: contém as páginas HTML; `base.html` define o layout compartilhado e os demais arquivos representam telas específicas. Não há necessidade de detalhar cada template individualmente.
- **`media/animais/`**: mantém os arquivos enviados pela aplicação, como fotos vinculadas aos animais.

## Cadastro de vacinas

O acesso e edição do banco de dados das vacinas é separado do sistema e feito exclusivamente por administradores.
Com o objetivo de ser uma base segura das vacinas, com baixa mutabilidade, para que o sistema automatize o calendário das vacinações.

No plano de vacinação, selecione a espécie e informe a idade da primeira dose em dias.
Use **Adicionar outra dose** para incluir da 2ª até a 5ª dose e informe, em cada uma,
quantos dias devem passar desde a dose anterior. A primeira dose é obrigatória; doses
adicionais são opcionais e devem ser cadastradas em sequência.
O plano e cada dose adicional também permitem configurar quantos dias após a previsão
a aplicação continua dentro da janela de vacinação (padrão: 7 dias).

O status cadastral do animal é **Ativo**, **Abatido** ou **Óbito**. Para animais ativos,
a situação sanitária (**Em dia** ou **Pendente**) é calculada automaticamente conforme
as vacinas dentro da janela de aplicação; animais abatidos ou com óbito não recebem essa
classificação. Na ficha, uma dose futura aparece como **Agendada**, uma dose dentro da
janela como **Pendente** e uma dose cuja janela terminou sem aplicação como **Não aplicada**.
Essa classificação considera a data prevista e o registro de aplicação de cada dose.
Quando uma dose é aplicada, as doses seguintes são recalculadas a partir da data real da
aplicação anterior, mesmo que ela tenha ocorrido após a janela prevista.

Os indivíduos são identificados visualmente por um prefixo da espécie seguido do número
cadastrado, como `s1` para suíno e `g1` para galináceo. O número pode se repetir entre
espécies, mas deve ser único dentro da mesma espécie.

## Ficha individual do animal

Na gestão de animais, use o ícone de visualização para abrir a ficha individual.
Ela reúne os dados do animal, o histórico de vacinas e remédios, permite registrar
a data de aplicação de vacinas pendentes e alterar o status sanitário. O atalho para
o calendário abre a agenda filtrada para aquele indivíduo.

## Preparar o ambiente

Clone o repositório e entre na pasta do projeto:

```bash
git clone https://github.com/fernandopasq/suino.git
cd suino
```

Crie o ambiente virtual na raiz do repositório:

```bash
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Para iniciar a aplicação localmente:

```bash
cd suino
python manage.py migrate
python manage.py runserver
```

## Organização das branches

- `main`: versão estável e funcional do projeto.
- `develop`: branch de desenvolvimento.
- `feature/<descricao>`: novas funcionalidades.
- `bug_fix/<descricao>`: correções de bugs.
