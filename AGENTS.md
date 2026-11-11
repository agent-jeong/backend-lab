# AGENTS.md

백엔드 개념과 실무 사례를 정리하는 Obsidian 저장소다. `main`에 push하면 https://agent-jeong.github.io/backend-lab/ 블로그로 바로 배포된다. **이 저장소에 쓰는 모든 글은 공개된다.**

## 공개 기준 (먼저 지킬 것)

공개 글에는 일반화한 이름만 쓴다: `order`, `payment`, `user`, `example-service`, `https://api.example.com`.

이것들은 공개 글에 넣지 않는다:

- 회사·서비스·내부 시스템 이름, 실제 테이블·클래스 이름, 실제 URL
- 운영 로그 원문, 계정·이메일·고객 데이터, 키·토큰·비밀값
- 조직이나 사람을 알아볼 수 있는 장애 세부, 운영 중인 시스템의 보안 약점

원본 맥락은 `_private/`(Git 제외)에 둔다. 실무 사례의 원본 메모는 `_private/work-cases/<공개 글 이름>-private.md`다. `_private/`의 내용을 공개 글로 옮길 때는 위 기준으로 일반화한 뒤에 옮긴다.

## 폴더

| 폴더 | 담는 것 |
|---|---|
| `00-home` | 홈(`index.md`), 소개, 용어집. 작업용 문서(`daily-study-board`, `mastery-map`, `learning-principles`)는 블로그에 올리지 않는다 |
| `01-core`, `02-practical-backend` | 개념 노트. 주제 폴더마다 폴더와 같은 이름의 안내 글이 있다 |
| `03-work-cases` | 직접 겪은 문제를 일반화한 사례 |
| `04-design-cases` | 자주 부딪히는 설계 문제를 공식 문서 근거로 풀어 본 사례 |
| `05-ai-workflows` | AI 활용 |
| `site/` | 블로그 빌드 설정과 스크립트 |

## 글을 고치거나 쓸 때

1. 같은 주제의 기존 글이 있으면 그 글을 고친다. 새 글은 기존 글에 들어가지 않을 때만 만든다.
2. 문체와 구조는 [`00-home/learning-principles.md`](00-home/learning-principles.md)의 "문체 기준"을 따른다. 새 글은 `_templates/`의 템플릿에서 시작한다(개념: `concept-template.md`, 사례: `case-study-template.md`).
3. 사실은 확인한 것만 쓴다. 버전에 따라 달라지는 동작은 기준 버전을 적고, 개념 노트의 "참고"에는 실제로 열어 본 공식 문서 링크를 넣는다.
4. 새 글은 그 주제의 안내 글과, 이어지는 내 사례가 있으면 사례 쪽 "내 사례"에서 링크한다.
5. `npm run wiki:build`가 성공하고 빌드 결과에 깨진 링크(`internal broken`)가 0개면 끝이다.

## 링크와 이름

- 파일·폴더 이름은 `kebab-case`. 이름을 바꾸면 블로그 주소가 바뀌므로, 예전 경로를 앞머리 `aliases`에 남겨 리다이렉트한다.
- 내부 링크는 `[[글-이름]]`. 이름이 겹칠 때만 경로를 쓴다.
- 링크 별칭에 `/`를 쓰지 않는다(블로그에서 잘린다). `I/O` 대신 `입출력`, `CI/CD` 대신 `CI·CD`.

## 커밋과 배포

- 커밋과 push는 사용자가 요청할 때만 한다. push가 곧 배포다.
- 커밋 메시지: `docs: <바꾼 주제>` 한 줄. 회사·시스템 이름을 쓰지 않는다.
