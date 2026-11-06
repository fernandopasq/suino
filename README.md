# Vettora

Aplicação web desenvolvida com Django para gestão sanitária de animais de diferentes espécies.

## Cadastro de vacinas

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

- `main`: versão estável e funcional do projeto. Não desenvolva diretamente nesta branch.
- `develop`: branch de integração do trabalho da equipe. Crie suas branches de trabalho a partir dela.
- `feature/<descricao>`: novas funcionalidades.
- `bug_fix/<descricao>`: correções de bugs.

### Criar a branch `develop` (uma vez)

Se ela ainda não existir no repositório remoto:

```bash
git switch main
git pull origin main
git switch -c develop
git push -u origin develop
```

### Desenvolver uma funcionalidade ou correção

Atualize a `develop` e crie uma branch de trabalho:

```bash
git switch develop
git pull origin develop
git switch -c feature/nome-da-funcionalidade
```

Para uma correção, use o prefixo `bug_fix`:

```bash
git switch develop
git pull origin develop
git switch -c bug_fix/descricao-do-bug
```

Faça e teste as alterações nessa branch. Depois, envie-a ao remoto:

```bash
git add .
git commit -m "Descreva a alteracao"
git push -u origin feature/nome-da-funcionalidade
```

Substitua `feature/nome-da-funcionalidade` por `bug_fix/descricao-do-bug` ao enviar uma correção. Abra um pull request da branch de trabalho para `develop` e faça o merge após revisão e testes. Se o processo da equipe exigir merge pelo terminal:

```bash
git switch develop
git pull origin develop
git merge --no-ff feature/nome-da-funcionalidade
git push origin develop
```

### Publicar uma versão estável

Quando `develop` estiver estável, funcionando e validada, integre-a à `main`:

```bash
git switch develop
git pull origin develop
git switch main
git pull origin main
git merge --no-ff develop
git push origin main
```

Depois da publicação, volte à branch de integração:

```bash
git switch develop
```
