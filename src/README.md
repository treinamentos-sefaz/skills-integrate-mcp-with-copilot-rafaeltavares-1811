# API de Atividades da Mergington High School

Uma aplicação FastAPI super simples que permite aos estudantes visualizar e se inscrever em atividades extracurriculares.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Professores autenticados podem inscrever e remover estudantes
- Estudantes podem consultar atividades e participantes sem fazer login

## Contas de professores

As credenciais dos professores são armazenadas localmente em `src/teachers.json`; esse arquivo é ignorado pelo Git e não deve ser compartilhado. As senhas são armazenadas como hashes PBKDF2, não em texto simples. Para criar ou redefinir uma conta, execute na raiz do repositório:

```
python src/manage_teachers.py <nome-de-usuario>
```

O comando solicita a senha de forma interativa e grava o hash no arquivo local. Sessões duram até oito horas e são invalidadas ao reiniciar o servidor. Para usar cookies seguros em produção com HTTPS, defina `TEACHER_COOKIE_SECURE=true`.

O formato inicial é ilustrado em `src/teachers.example.json`. Não coloque credenciais reais nesse arquivo nem as envie ao Git.

O login da interface é feito pelo botão de usuário no cabeçalho. As rotas `POST /activities/{activity_name}/signup` e `DELETE /activities/{activity_name}/unregister` exigem uma sessão de professor; `GET /activities` continua público.

## Primeiros Passos

1. Instale as dependências:

   ```
   pip install fastapi uvicorn
   ```

2. Execute a aplicação:

   ```
   uvicorn src.app:app --reload
   ```

3. Abra seu navegador e vá para:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint                                                          | Descrição                                                           |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                          | Obter todas as atividades com seus detalhes e participantes públicos |
| POST   | `/auth/login`                                                          | Iniciar uma sessão de professor                                      |
| GET    | `/auth/status`                                                         | Verificar se há uma sessão de professor ativa                        |
| POST   | `/auth/logout`                                                         | Encerrar a sessão de professor                                       |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu`      | Inscrever um estudante (somente professor autenticado)               |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu`  | Remover uma inscrição (somente professor autenticado)                 |

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:

   - Descrição
   - Cronograma
   - Número máximo de participantes permitidos
   - Lista de emails de estudantes que estão inscritos

2. **Estudantes** - Usa email como identificador:
   - Nome
   - Nível da série

Todos os dados são armazenados na memória, o que significa que os dados serão resetados quando o servidor reiniciar.
