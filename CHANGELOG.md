# Changelog

Todas as mudanças notáveis do SDK Python do Keyrunes.

Gerado por `git-cliff` a partir dos commits convencionais — o corpo de cada
commit vira o texto da entrada. **Não edite à mão**: a próxima geração
sobrescreve. Para mudar o texto de uma entrada, reescreva a mensagem do commit
(`git rebase -i`); para mudar a forma, edite `cliff.toml` e rode
`poetry run task changelog`.

## [0.4.0] - 2026-09-15

### Adicionado

- **client**: change_password, que a API servia e o SDK não expunha

  `POST /api/user/change-password` existe no Keyrunes desde sempre. O SDK expunha
  `login`, `refresh_token`, `register_user` e as consultas de grupo — e não esta.

  Quem precisou dela montou o HTTP à mão: foi o que aconteceu no PlayfulLMS, e
  antes disso a conclusão foi pior — olhando só a superfície do SDK, dei a operação
  como inexistente, e a plataforma quase mandou as pessoas trocarem a senha no
  provedor.

  **Detalhes que custam caro se lidos errado**

  `/api/user/change-password`, e **não** `/api/change-password`: o router registra o
  primeiro. O handler por trás do segundo é código morto marcado
  `#[allow(dead_code)]`, e apontar para ele responde 404.

  O servidor responde erro em **texto puro** (`e.to_string()`), não em JSON — quem
  tratar como JSON recebe uma exceção de parsing no lugar da frase que explica o
  que houve.

  O erro é **400**, não 401, e por isso vira `NetworkError`: é a classe que este
  SDK já usa para tudo que não é 401/403/404. Trocá-la aqui mudaria o contrato de
  todo chamador por causa de um endpoint. A frase do servidor sobrevive, que é o
  que importa — "senha atual incorreta" e "senha muito curta" pedem ações opostas.

  Sem token, recusa **antes** de fazer a requisição: o servidor identifica quem
  troca pelo token, e nada no corpo escolhe isso.

  E o efeito que fecha o ciclo: o servidor limpa `first_login` ao trocar — a origem
  do `requires_password_change` que o login reporta. Está na docstring porque quem
  chama precisa saber que não há segunda chamada a fazer.

  Verificado contra um Keyrunes de verdade, e não só com dublê: registrar, trocar,
  e então a senha antiga recusada (401) e a nova aceita (200), com `first_login`
  virando falso no banco.

  5 testes de contrato; 194 da suíte passando. Pre-commit: black, isort, flake8,
  mypy e pytest passam. **`safety` foi pulado** — ele falha pedindo login da
  ferramenta, e medi que falha igual sem esta mudança (`git stash` e rodar).

### Corrigido

- **client**: conter `groups` malformado em vez de derrubar o cliente

  O fuzzer do próprio repositório achou: com `{"groups": true}` na resposta do
  servidor, a normalização estourava `TypeError: argument of type 'bool' is not a
  container or iterable`.

  `data.get("groups", []) or []` trata nulo e vazio, e **não** trata o resto:
  `True or []` é `True`, que sobrevive até o `"admins" in groups` logo abaixo.

  Um cliente que cai com resposta malformada é pior que um que a ignora: quem
  consome o SDK vê uma exceção de tipo vinda de dentro da biblioteca, longe da
  causa, e nada indica que o problema veio do servidor.

  Preexistente — `git stash` e a falha continua. Detecção medida: repor o `or []`
  reprova o teste de fuzz.

- **deps**: pyjwt 2.10.1 → 2.14.0 e idna 3.11 → 3.19 (avisos OSV)

  O hook `safety` não roda nesta máquina — pede login interativo e morre com
  `EOF when reading a line`. Em vez de pular a checagem de segurança e seguir,
  rodei as 90 versões travadas no `poetry.lock` contra a base OSV.

  Dois achados na árvore de execução:

  - `pyjwt` 2.10.1: nove avisos, quatro de severidade alta. Numa biblioteca de
    autenticação isto é a dependência que mais importa. Corrigido em 2.13.0; o
    `pyproject` já declarava `^2.9.0`, então nada muda de API — só o lock.
  - `idna` 3.11: dois avisos moderados, corrigido em 3.15. Chega via `httpx`.

  Depois da atualização a árvore de execução não tem nenhum aviso conhecido. Os
  194 testes passam sem alteração.

  O que sobra são avisos na árvore de desenvolvimento — `authlib`, `nltk`,
  `cryptography`, `requests`, `urllib3` — e vale dizer de onde vêm: **todos são
  dependências do próprio `safety`**. O scanner que não consegue rodar é também a
  maior fonte de pacotes vulneráveis no ambiente. Não mexi neles: são de
  desenvolvimento, não vão no pacote publicado, e resolver isso é decidir se o
  `safety` fica.

### Documentação

- **changelog**: registrar em 0.4.0 os dois commits que caíram depois da tag

  A tag `v0.4.0` ficou em `chore(release): 0.4.0`, e dois commits entraram depois
  dela: o conserto do `groups` malformado e a saída do `towncrier`. Como a tag
  **não foi publicada** (o remoto não a tem), o conserto ainda pode entrar na
  0.4.0 em vez de exigir uma 0.4.1 — e deve, porque é um `TypeError` que sai do
  SDK.

- **changelog**: gerar o CHANGELOG.md com git-cliff, corpo do commit incluído

  O changelog deste repositório era escrito à mão. A primeira tentativa de trocar
  por geração automática foi medida e **descartada**: com o modelo padrão do
  git-cliff, que usa só a linha de assunto, o arquivo caía de 246 para 61 linhas —
  sobrava o "o quê" e sumia o "porquê".

  O que resolve é incluir o **corpo** do commit. As mensagens daqui já explicam a
  decisão, então a informação nunca esteve só no changelog: estava duplicada.
  Agora o gerado tem 222 linhas, e cada entrada carrega o texto que a explica.

  Três detalhes do `cliff.toml`, cada um por um defeito visto na saída:

  - `indent(prefix="  ", first=true, blank=false)` no corpo. Sem `first=true` a
    primeira linha do corpo fica fora do item da lista; com `blank=true` as linhas
    vazias ganham dois espaços e o hook `trailing-whitespace` reprova o commit.
  - Um postprocessor rebaixa a título em negrito qualquer `#` que venha dentro de
    um corpo — indentado, ATX ainda é título (aceita até três espaços) e colidiria
    com os níveis do changelog. O padrão usa `[ \t]` e **não** `\s`: `\s` casa
    `\n`, e na primeira versão ele atravessou a quebra de linha e comeu o
    `## [0.4.0]` do próprio changelog, que virou negrito.
  - Outro postprocessor põe linha em branco antes de cada `## [versão]`, porque
    `trim = true` cola o título na última linha da versão anterior.

  Duas seções encolhem, e vale dizer quais: **0.1.0** (81 → 7 linhas) era um
  inventário da API — o mesmo que o README já traz — e **0.3.0** (55 → 11) perde o
  detalhe dos quatro bugs de contrato, porque o commit daquele release tem corpo
  curto. O texto antigo continua recuperável: `git show 173721f:CHANGELOG.md`.
  Daqui para a frente a regra é outra — o corpo do commit é a fonte, então
  mensagem magra vira entrada magra.

### Manutenção

- **deps**: tirar o towncrier, que estava declarado e não configurado

  `towncrier` era dependência de dev desde antes, **sem `[tool.towncrier]`** no
  `pyproject.toml`, sem `towncrier.toml` e sem diretório de fragmentos. Rodá-lo
  falha: "the config file does not contain 'version' or 'package'".

  O `NEWS.rst` está no formato que ele *produziria*, o que é pior que não ter nada:
  quem chega conclui que o arquivo é gerado e não mexe nele, ou tenta rodar a
  ferramenta e descobre que não dá. Eu mesmo caí nisso hoje — escrevi o changelog à
  mão sem perceber que havia ferramenta declarada.

  Dependência declarada e não usada é a mesma família do código morto. O changelog
  deste repositório é escrito à mão, e agora o `pyproject.toml` diz isso.


## [0.3.1] - 2026-09-04

### Corrigido

- **deps**: move mutmut out of the runtime dependencies; release 0.3.1

  mutmut was declared in [tool.poetry.dependencies] rather than the dev group,
  so installing this SDK pulled a mutation-testing tool and its whole tree
  (libcst, textual, rich, setproctitle, pyyaml-ft, markdown-it-py,
  mdit-py-plugins, mdurl, linkify-it-py, sortedcontainers) into every consumer,
  production images included.

  Nothing in keyrunes_sdk imports it, so upgrading only removes packages. The
  wheel now declares httpx, pydantic[email] and pyjwt and nothing else.

  Affected 0.2.0 and 0.3.0.


## [0.3.0] - 2026-09-03

### Adicionado

- **client**: carry the full server identity and add refresh; release 0.3.0

  Migrating a real consumer (an LMS keying its user rows off the JWT `sub`)
  surfaced four contract bugs against a live Keyrunes server and three fields
  the SDK was discarding.


## [0.2.0] - 2026-09-03

### Adicionado

- **tests**: add property-based, fuzz and contract suites; release 0.2.0

  Add three new test suites and the tooling to measure them:

  - tests/test_property_based.py (24 tests): Hypothesis invariants over base
    URL normalization, _normalize_user id precedence and is_admin derivation,
    JWT claim parsing, request URL construction, status-to-exception mapping
    and model validation bounds.
  - tests/test_fuzz.py (19 tests): hostile-input crawl of the public surface
    asserting only KeyrunesError and pydantic ValidationError ever escape.
  - tests/test_request_contract.py (33 tests): mocks only the httpx transport
    so the method, URL, headers and JSON body put on the wire are asserted.

  Hypothesis profiles (fast/dev/ci) are selected with HYPOTHESIS_PROFILE;
  fast is derandomized and database-free so mutmut judges every mutant
  against identical examples.

  Two defects the new suites uncovered are fixed:

  - A 2xx response with a non-JSON body raised a raw ValueError out of
    _make_request. It is now wrapped in NetworkError.
  - get_user, get_current_user and has_group carried unreachable
    "except UserNotFoundError" fallbacks that re-tested a condition already
    forced by an early return, swallowing genuine server 404s. Removed, and
    the duplicated claims-to-User block extracted into
    _user_from_token_claims().

### Manutenção

- add changelogs

- update lib version in pyproject

- add pypi url in README


## [0.1.0] - 2026-01-03

### Adicionado

- add organization key for keyrunes v0.2.0


## [0.0.1] - 2025-12-08

### Adicionado

- add login, register, check_admin, check_user, get_current_user features

### Corrigido

- fix lib version

### Infraestrutura

- fix lint errors and add pre-commit

### Manutenção

- add changelogs

### Outros

- Initial commit


<!-- gerado por git-cliff -->
